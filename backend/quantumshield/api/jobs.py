"""
Scan Job Management REST API Endpoints.
Supports both /api/v1/jobs and /api/jobs route conventions.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.storage.job_repository import JobRepository
from quantumshield.storage.repositories import AssetRepository
from quantumshield.models.job import ScanJob
from quantumshield.core.exceptions import ValidationError, NotFoundError

jobs_bp = Blueprint("jobs", __name__)


def get_job_repo() -> JobRepository:
    """Helper to instantiate JobRepository with current app's configured database path."""
    db_path = current_app.config.get("DATABASE_PATH")
    return JobRepository(db_path)


def get_asset_repo() -> AssetRepository:
    """Helper to instantiate AssetRepository."""
    db_path = current_app.config.get("DATABASE_PATH")
    return AssetRepository(db_path)


# -------------------------------------------------------------
# GET /api/v1/jobs & GET /api/jobs - List Scan Jobs
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/jobs", methods=["GET"])
@jobs_bp.route("/api/jobs", methods=["GET"])
def list_jobs():
    repo = get_job_repo()
    asset_id = request.args.get("asset_id")
    status = request.args.get("status")
    job_type = request.args.get("job_type")

    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        raise ValidationError("Limit and offset must be valid integers.")

    jobs, total = repo.list_jobs(
        asset_id=asset_id,
        status=status,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        "status": "ok",
        "jobs": [j.to_dict() for j in jobs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/jobs/<job_id> & GET /api/jobs/<job_id> - Get Single Job
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/jobs/<job_id>", methods=["GET"])
@jobs_bp.route("/api/jobs/<job_id>", methods=["GET"])
def get_job(job_id: str):
    repo = get_job_repo()
    job = repo.get_by_id(job_id)
    if not job:
        raise NotFoundError(f"Job with ID '{job_id}' not found.")

    return jsonify({
        "status": "ok",
        "job": job.to_dict(),
    }), 200


# -------------------------------------------------------------
# POST /api/v1/jobs & POST /api/jobs - Create & Enqueue Job
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/jobs", methods=["POST"])
@jobs_bp.route("/api/jobs", methods=["POST"])
def create_job():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        raise ValidationError("Invalid JSON payload provided.")

    asset_id = data.get("asset_id")
    if not asset_id:
        raise ValidationError("Field 'asset_id' is required.")

    # Verify asset exists in database
    asset_repo = get_asset_repo()
    asset = asset_repo.get_by_id(asset_id)
    if not asset:
        raise NotFoundError(f"Target asset '{asset_id}' does not exist.")

    job = ScanJob.from_dict(data)
    job.validate()

    job_manager = current_app.extensions.get("job_manager")
    if job_manager:
        created = job_manager.enqueue(job)
    else:
        repo = get_job_repo()
        job.status = "queued"
        created = repo.create(job)

    return jsonify({
        "status": "ok",
        "message": "Scan job enqueued successfully.",
        "job": created.to_dict(),
    }), 201


# -------------------------------------------------------------
# POST /api/v1/jobs/<job_id>/cancel & POST /api/jobs/<job_id>/cancel
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/jobs/<job_id>/cancel", methods=["POST"])
@jobs_bp.route("/api/jobs/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id: str):
    repo = get_job_repo()
    job = repo.get_by_id(job_id)
    if not job:
        raise NotFoundError(f"Job with ID '{job_id}' not found.")

    cancelled = repo.cancel(job_id)
    if not cancelled:
        raise ValidationError(f"Job '{job_id}' cannot be cancelled in its current state ({job.status}).")

    updated = repo.get_by_id(job_id)
    return jsonify({
        "status": "ok",
        "message": f"Job '{job_id}' has been cancelled.",
        "job": updated.to_dict() if updated else None,
    }), 200


# -------------------------------------------------------------
# POST /api/v1/jobs/<job_id>/retry & POST /api/jobs/<job_id>/retry
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/jobs/<job_id>/retry", methods=["POST"])
@jobs_bp.route("/api/jobs/<job_id>/retry", methods=["POST"])
def retry_job(job_id: str):
    repo = get_job_repo()
    job = repo.get_by_id(job_id)
    if not job:
        raise NotFoundError(f"Job with ID '{job_id}' not found.")

    retried = repo.retry(job_id)
    if not retried:
        raise ValidationError(
            f"Job '{job_id}' cannot be retried. Maximum retries ({job.max_retries}) reached or invalid state."
        )

    # Wake background worker if active
    job_manager = current_app.extensions.get("job_manager")
    if job_manager:
        job_manager._wake_event.set()

    return jsonify({
        "status": "ok",
        "message": f"Job '{job_id}' has been re-queued for execution.",
        "job": retried.to_dict(),
    }), 200
