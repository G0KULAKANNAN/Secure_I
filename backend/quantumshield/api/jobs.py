"""
Scan Job Management REST API Endpoints.
Milestone 1: Dual route support (/api/jobs and /api/v1/jobs), worker health status,
cancellation, retry, and validation of job types and target assets.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.storage.job_repository import JobRepository
from quantumshield.storage.repositories import AssetRepository
from quantumshield.models.job import ScanJob, VALID_JOB_TYPES
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
# GET /api/v1/worker/status & GET /api/worker/status
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/worker/status", methods=["GET"])
@jobs_bp.route("/api/worker/status", methods=["GET"])
def get_worker_status():
    """Return status and health metrics of the background job worker engine."""
    job_manager = current_app.extensions.get("job_manager")
    if job_manager:
        worker_info = job_manager.get_status()
    else:
        # Fallback query from repository when workers run out-of-process
        repo = get_job_repo()
        _, pending_count = repo.list_jobs(status="pending", limit=1)
        _, queued_count = repo.list_jobs(status="queued", limit=1)
        _, running_count = repo.list_jobs(status="running", limit=1)
        _, total = repo.list_jobs(limit=1)

        worker_info = {
            "engine": "QuantumShield Background Job Worker",
            "status": "idle",
            "uptime_seconds": 0.0,
            "max_workers": 3,
            "active_workers": running_count,
            "queue_depth": pending_count + queued_count,
            "processed_count": total,
            "succeeded_count": 0,
            "failed_count": 0,
            "retried_count": 0,
        }

    return jsonify({
        "status": "ok",
        "worker": worker_info,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/jobs & GET /api/jobs - List Scan Jobs
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/jobs", methods=["GET"])
@jobs_bp.route("/api/jobs", methods=["GET"])
def list_jobs():
    """List jobs with filtering and pagination."""
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
    """Retrieve detailed state and execution data for a single job."""
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
    """
    Enqueue a new job for persistent background processing.
    Validates job type, optional target asset existence, and priority.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        raise ValidationError("Invalid JSON payload provided.")

    job_type = data.get("job_type")
    if not job_type:
        raise ValidationError("Field 'job_type' is required.")

    if job_type.lower() not in VALID_JOB_TYPES:
        raise ValidationError(
            f"Invalid job_type '{job_type}'. Must be one of: {', '.join(sorted(VALID_JOB_TYPES))}"
        )

    asset_id = data.get("asset_id")
    if asset_id:
        asset_id = str(asset_id).strip()
        asset_repo = get_asset_repo()
        asset = asset_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundError(f"Target asset '{asset_id}' does not exist.")
    else:
        # Check if asset is mandatory for specific types
        if job_type.lower() == "asset_validation":
            raise ValidationError("Field 'asset_id' is required for asset_validation job.")
        asset_id = None

    job = ScanJob.from_dict({
        **data,
        "asset_id": asset_id,
        "status": "queued",
    })
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
    """
    Request cancellation of a job.
    Pending/queued jobs cancel immediately; running jobs trigger cooperative cancel.
    """
    repo = get_job_repo()
    job = repo.get_by_id(job_id)
    if not job:
        raise NotFoundError(f"Job with ID '{job_id}' not found.")

    cancelled = repo.request_cancellation(job_id)
    if not cancelled:
        raise ValidationError(f"Job '{job_id}' cannot be cancelled in its current state ({job.status}).")

    return jsonify({
        "status": "ok",
        "message": f"Cancellation requested for job '{job_id}'.",
        "job": cancelled.to_dict(),
    }), 200


# -------------------------------------------------------------
# POST /api/v1/jobs/<job_id>/retry & POST /api/jobs/<job_id>/retry
# -------------------------------------------------------------
@jobs_bp.route("/api/v1/jobs/<job_id>/retry", methods=["POST"])
@jobs_bp.route("/api/jobs/<job_id>/retry", methods=["POST"])
def retry_job(job_id: str):
    """
    Retry a failed or cancelled job with exponential backoff.
    """
    repo = get_job_repo()
    job = repo.get_by_id(job_id)
    if not job:
        raise NotFoundError(f"Job with ID '{job_id}' not found.")

    if job.attempt_count >= job.max_attempts:
        raise ValidationError(
            f"Job '{job_id}' cannot be retried. Maximum retries ({job.max_attempts}) reached."
        )

    retried = repo.retry(job_id)
    if not retried:
        raise ValidationError(
            f"Job '{job_id}' cannot be retried from its current state ({job.status})."
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
