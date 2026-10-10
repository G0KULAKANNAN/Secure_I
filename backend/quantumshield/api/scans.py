"""
Scan Orchestration and Findings Management REST API Endpoints.
Supports both /api/v1/ and /api/ route conventions.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.services.scan_orchestrator import ScanOrchestrator
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.job_repository import JobRepository
from quantumshield.core.exceptions import ValidationError, NotFoundError

scans_bp = Blueprint("scans", __name__)


def get_orchestrator() -> ScanOrchestrator:
    db_path = current_app.config.get("DATABASE_PATH")
    job_manager = current_app.extensions.get("job_manager")
    return ScanOrchestrator(db_path, job_manager)


def get_finding_repo() -> FindingRepository:
    db_path = current_app.config.get("DATABASE_PATH")
    return FindingRepository(db_path)


def get_job_repo() -> JobRepository:
    db_path = current_app.config.get("DATABASE_PATH")
    return JobRepository(db_path)


# -------------------------------------------------------------
# POST /api/v1/scans & POST /api/scans - Request Scan Run
# -------------------------------------------------------------
@scans_bp.route("/api/v1/scans", methods=["POST"])
@scans_bp.route("/api/scans", methods=["POST"])
def request_scan():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        raise ValidationError("Invalid JSON body.")

    asset_id = data.get("asset_id")
    if not asset_id:
        raise ValidationError("Field 'asset_id' is required.")

    scanner_types = data.get("scanner_types")
    if not scanner_types or not isinstance(scanner_types, list):
        raise ValidationError("Field 'scanner_types' must be a non-empty list of scanner names.")

    options = data.get("options", {})
    orchestrator = get_orchestrator()
    run = orchestrator.request_scan(asset_id, scanner_types, options=options)

    return jsonify({
        "status": "ok",
        "message": "Scan run enqueued successfully.",
        "scan_run": run.to_dict(),
    }), 201


# -------------------------------------------------------------
# GET /api/v1/scans & GET /api/scans - List Scan Runs
# -------------------------------------------------------------
@scans_bp.route("/api/v1/scans", methods=["GET"])
@scans_bp.route("/api/scans", methods=["GET"])
def list_scans():
    orchestrator = get_orchestrator()
    asset_id = request.args.get("asset_id")
    status = request.args.get("status")

    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        raise ValidationError("Limit and offset must be valid integers.")

    runs, total = orchestrator.scan_repo.list_scan_runs(
        asset_id=asset_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    # Sync child job states
    synced_runs = []
    for r in runs:
        if r.status in ("queued", "running"):
            synced_runs.append(orchestrator.get_scan_run_status(r.id))
        else:
            synced_runs.append(r)

    return jsonify({
        "status": "ok",
        "scan_runs": [r.to_dict() for r in synced_runs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/scans/<scan_run_id> & GET /api/scans/<scan_run_id>
# -------------------------------------------------------------
@scans_bp.route("/api/v1/scans/<scan_run_id>", methods=["GET"])
@scans_bp.route("/api/scans/<scan_run_id>", methods=["GET"])
def get_scan(scan_run_id: str):
    orchestrator = get_orchestrator()
    run = orchestrator.get_scan_run_status(scan_run_id)
    if not run:
        raise NotFoundError(f"Scan run '{scan_run_id}' not found.")

    return jsonify({
        "status": "ok",
        "scan_run": run.to_dict(),
    }), 200


# -------------------------------------------------------------
# GET /api/v1/scans/<scan_run_id>/jobs & GET /api/scans/<scan_run_id>/jobs
# -------------------------------------------------------------
@scans_bp.route("/api/v1/scans/<scan_run_id>/jobs", methods=["GET"])
@scans_bp.route("/api/scans/<scan_run_id>/jobs", methods=["GET"])
def get_scan_jobs(scan_run_id: str):
    job_repo = get_job_repo()
    jobs = job_repo.list_by_scan_run(scan_run_id)
    return jsonify({
        "status": "ok",
        "jobs": [j.to_dict() for j in jobs],
        "total": len(jobs),
    }), 200


# -------------------------------------------------------------
# POST /api/v1/scans/<scan_run_id>/cancel & POST /api/scans/<scan_run_id>/cancel
# -------------------------------------------------------------
@scans_bp.route("/api/v1/scans/<scan_run_id>/cancel", methods=["POST"])
@scans_bp.route("/api/scans/<scan_run_id>/cancel", methods=["POST"])
def cancel_scan(scan_run_id: str):
    orchestrator = get_orchestrator()
    run = orchestrator.cancel_scan_run(scan_run_id)
    return jsonify({
        "status": "ok",
        "message": f"Scan run '{scan_run_id}' cancellation requested.",
        "scan_run": run.to_dict(),
    }), 200


# -------------------------------------------------------------
# GET /api/v1/assets/<asset_id>/scans & GET /api/assets/<asset_id>/scans
# -------------------------------------------------------------
@scans_bp.route("/api/v1/assets/<asset_id>/scans", methods=["GET"])
@scans_bp.route("/api/assets/<asset_id>/scans", methods=["GET"])
def get_asset_scans(asset_id: str):
    orchestrator = get_orchestrator()
    runs, total = orchestrator.scan_repo.list_scan_runs(asset_id=asset_id, limit=50)
    return jsonify({
        "status": "ok",
        "asset_id": asset_id,
        "scan_runs": [r.to_dict() for r in runs],
        "total": total,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/findings & GET /api/findings - List Findings
# -------------------------------------------------------------
@scans_bp.route("/api/v1/findings", methods=["GET"])
@scans_bp.route("/api/findings", methods=["GET"])
def list_findings():
    repo = get_finding_repo()
    asset_id = request.args.get("asset_id")
    scan_run_id = request.args.get("scan_run_id")
    severity = request.args.get("severity")
    scanner_type = request.args.get("scanner_type")
    status = request.args.get("status")

    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        raise ValidationError("Limit and offset must be valid integers.")

    findings, total = repo.list_findings(
        asset_id=asset_id,
        scan_run_id=scan_run_id,
        severity=severity,
        scanner_type=scanner_type,
        status=status,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        "status": "ok",
        "findings": [f.to_dict() for f in findings],
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/findings/<finding_id> & GET /api/findings/<finding_id>
# -------------------------------------------------------------
@scans_bp.route("/api/v1/findings/<finding_id>", methods=["GET"])
@scans_bp.route("/api/findings/<finding_id>", methods=["GET"])
def get_finding(finding_id: str):
    repo = get_finding_repo()
    finding = repo.get_by_id(finding_id)
    if not finding:
        raise NotFoundError(f"Finding with ID '{finding_id}' not found.")

    return jsonify({
        "status": "ok",
        "finding": finding.to_dict(),
    }), 200


# -------------------------------------------------------------
# PATCH /api/v1/findings/<finding_id> & PATCH /api/findings/<finding_id>
# -------------------------------------------------------------
@scans_bp.route("/api/v1/findings/<finding_id>", methods=["PATCH"])
@scans_bp.route("/api/findings/<finding_id>", methods=["PATCH"])
def update_finding_status(finding_id: str):
    data = request.get_json(silent=True) or {}
    new_status = data.get("remediation_status") or data.get("status")
    if not new_status:
        raise ValidationError("Field 'remediation_status' is required.")

    valid_statuses = {"potential_exposure", "verified_usage", "needs_review", "remediated", "accepted_risk"}
    if new_status.lower() not in valid_statuses:
        raise ValidationError(f"Invalid remediation status. Must be one of: {', '.join(sorted(valid_statuses))}")

    repo = get_finding_repo()
    updated = repo.update_status(finding_id, new_status)
    if not updated:
        raise NotFoundError(f"Finding with ID '{finding_id}' not found.")

    return jsonify({
        "status": "ok",
        "message": f"Finding status updated to '{new_status}'.",
        "finding": updated.to_dict(),
    }), 200


# -------------------------------------------------------------
# GET /api/v1/findings/stats & GET /api/findings/stats
# -------------------------------------------------------------
@scans_bp.route("/api/v1/findings/stats", methods=["GET"])
@scans_bp.route("/api/findings/stats", methods=["GET"])
def get_finding_stats():
    asset_id = request.args.get("asset_id")
    repo = get_finding_repo()
    stats = repo.get_stats(asset_id=asset_id)
    return jsonify({
        "status": "ok",
        "stats": stats,
    }), 200
