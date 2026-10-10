"""
Direct Scanner Endpoints for File Uploads and Interactive Probing.
Supports Certificate File Upload, Source File Upload, and Direct Scans.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.scanner.certificate_scanner import CertificateScanner
from quantumshield.scanner.static_scanner import StaticScanner
from quantumshield.scanner.tls_scanner import TlsScanner
from quantumshield.storage.repositories import AssetRepository
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.job_repository import JobRepository
from quantumshield.models.finding import Finding
from quantumshield.models.job import ScanJob
from quantumshield.models.asset import Asset
from quantumshield.core.exceptions import ValidationError, NotFoundError

scanners_bp = Blueprint("scanners", __name__)


def get_db_path():
    return current_app.config.get("DATABASE_PATH")


# -------------------------------------------------------------
# POST /api/v1/scanners/certificate & POST /api/scanners/certificate
# -------------------------------------------------------------
@scanners_bp.route("/api/v1/scanners/certificate", methods=["POST"])
@scanners_bp.route("/api/scanners/certificate", methods=["POST"])
def scan_certificate_file():
    """
    Direct certificate scanner endpoint.
    Accepts multipart file upload or JSON payload containing PEM/DER.
    """
    db_path = get_db_path()
    asset_repo = AssetRepository(db_path)
    finding_repo = FindingRepository(db_path)
    job_repo = JobRepository(db_path)

    cert_data = None
    file_name = "uploaded_certificate.pem"
    asset_id = None

    if "file" in request.files:
        file_obj = request.files["file"]
        file_name = file_obj.filename or file_name
        cert_data = file_obj.read()
        asset_id = request.form.get("asset_id")
    else:
        json_data = request.get_json(silent=True) or {}
        cert_data = json_data.get("certificate_data")
        asset_id = json_data.get("asset_id")
        file_name = json_data.get("file_name", file_name)

    if not cert_data:
        raise ValidationError("No certificate file or certificate_data provided.")

    # Target asset resolution
    target_asset = None
    if asset_id:
        target_asset = asset_repo.get_by_id(asset_id)
        if not target_asset:
            raise NotFoundError(f"Target asset '{asset_id}' not found.")
    else:
        # Create an ephemeral or ad-hoc asset record for tracking
        target_asset = Asset(
            name=f"Certificate Upload: {file_name}",
            asset_type="certificate",
            environment="production",
            description=f"Direct upload of certificate file {file_name}",
            criticality="high",
        )
        asset_repo.create(target_asset)

    # Create background job in Job Center for auditability
    job = ScanJob(
        job_type="certificate_scan",
        asset_id=target_asset.id,
        operation=f"inspect_{file_name}",
        priority=7,
        status="running",
    )
    job_repo.create(job)

    # Execute scanner
    scanner = CertificateScanner()
    result = scanner.scan(target_asset, {"certificate_data": cert_data, "file_name": file_name})

    if result.status == "failed" and "Security Policy Violation" in (result.error_message or ""):
        job.status = "failed"
        job.error_message = result.error_message
        job_repo.update(job)
        raise ValidationError(result.error_message)

    # Persist findings
    saved_findings = []
    for f_dict in result.findings:
        f = Finding(
            asset_id=target_asset.id,
            job_id=job.id,
            scanner_type="certificate_scan",
            algorithm=f_dict.get("algorithm", "Unknown"),
            cryptographic_primitive=f_dict.get("cryptographic_primitive", "digital_signature"),
            quantum_vulnerable=f_dict.get("quantum_vulnerable", True),
            recommended_pqc=f_dict.get("recommended_pqc", "ML-DSA-65 (FIPS 204)"),
            rule_id=f_dict.get("rule_id", "PQC-CERT"),
            title=f_dict.get("title", ""),
            description=f_dict.get("description", ""),
            severity=f_dict.get("severity", "high"),
            evidence=f_dict.get("evidence", ""),
            file_path=file_name,
            line_number=1,
            confidence="high",
            remediation_status="potential_exposure",
        )
        finding_repo.save_finding(f)
        saved_findings.append(f.to_dict())

    # Complete job
    job.status = "completed" if result.status == "completed" else "failed"
    job.progress = 100
    job.result_json = result.to_dict()
    job.error_message = result.error_message
    job_repo.update(job)

    return jsonify({
        "status": "ok",
        "job_id": job.id,
        "asset_id": target_asset.id,
        "scan_result": result.to_dict(),
        "findings": saved_findings,
    }), 200


# -------------------------------------------------------------
# POST /api/v1/scanners/source & POST /api/scanners/source
# -------------------------------------------------------------
@scanners_bp.route("/api/v1/scanners/source", methods=["POST"])
@scanners_bp.route("/api/scanners/source", methods=["POST"])
def scan_source_code():
    """
    Direct source code / configuration scanner endpoint.
    Accepts file upload or JSON payload with source_content or target_directory.
    """
    db_path = get_db_path()
    asset_repo = AssetRepository(db_path)
    finding_repo = FindingRepository(db_path)
    job_repo = JobRepository(db_path)

    source_content = None
    file_name = "source_code.py"
    target_directory = None
    asset_id = None

    if "file" in request.files:
        file_obj = request.files["file"]
        file_name = file_obj.filename or file_name
        source_content = file_obj.read().decode("utf-8", errors="ignore")
        asset_id = request.form.get("asset_id")
    else:
        json_data = request.get_json(silent=True) or {}
        source_content = json_data.get("source_content")
        target_directory = json_data.get("target_directory")
        file_name = json_data.get("file_name", file_name)
        asset_id = json_data.get("asset_id")

    if not source_content and not target_directory:
        raise ValidationError("Provide either an uploaded file, source_content, or target_directory.")

    # Target asset
    target_asset = None
    if asset_id:
        target_asset = asset_repo.get_by_id(asset_id)
        if not target_asset:
            raise NotFoundError(f"Target asset '{asset_id}' not found.")
    else:
        target_asset = Asset(
            name=f"Source Scan: {file_name if source_content else target_directory}",
            asset_type="application",
            environment="production",
            description="Direct source code cryptographic scan",
            criticality="high",
        )
        asset_repo.create(target_asset)

    # Job tracking
    job = ScanJob(
        job_type="static_scan",
        asset_id=target_asset.id,
        operation=f"static_audit_{file_name}",
        priority=6,
        status="running",
    )
    job_repo.create(job)

    scanner = StaticScanner()
    scan_opts = {}
    if source_content:
        scan_opts = {"source_content": source_content, "file_name": file_name}
    elif target_directory:
        scan_opts = {"target_directory": target_directory}

    result = scanner.scan(target_asset, scan_opts)

    # Persist findings
    saved_findings = []
    for f_dict in result.findings:
        f = Finding(
            asset_id=target_asset.id,
            job_id=job.id,
            scanner_type="static_scan",
            algorithm=f_dict.get("algorithm", "Unknown"),
            cryptographic_primitive=f_dict.get("cryptographic_primitive", "key_establishment"),
            quantum_vulnerable=f_dict.get("quantum_vulnerable", True),
            recommended_pqc=f_dict.get("recommended_pqc", "ML-KEM-768"),
            rule_id=f_dict.get("rule_id", "PQC-STATIC"),
            title=f_dict.get("title", ""),
            description=f_dict.get("description", ""),
            severity=f_dict.get("severity", "high"),
            evidence=f_dict.get("evidence", ""),
            file_path=f_dict.get("file_path", file_name),
            line_number=f_dict.get("line_number", 1),
            confidence="needs_review",
            remediation_status="potential_exposure",
        )
        finding_repo.save_finding(f)
        saved_findings.append(f.to_dict())

    job.status = "completed" if result.status == "completed" else "failed"
    job.progress = 100
    job.result_json = result.to_dict()
    job.error_message = result.error_message
    job_repo.update(job)

    return jsonify({
        "status": "ok",
        "job_id": job.id,
        "asset_id": target_asset.id,
        "scan_result": result.to_dict(),
        "findings": saved_findings,
    }), 200


# -------------------------------------------------------------
# POST /api/v1/scanners/tls & POST /api/scanners/tls - Live Server Scan
# -------------------------------------------------------------
@scanners_bp.route("/api/v1/scanners/tls", methods=["POST"])
@scanners_bp.route("/api/scanners/tls", methods=["POST"])
def scan_live_server():
    """
    Live server TLS handshake inspection endpoint.
    Requires explicit authorization confirmation.
    """
    db_path = get_db_path()
    asset_repo = AssetRepository(db_path)
    finding_repo = FindingRepository(db_path)
    job_repo = JobRepository(db_path)

    data = request.get_json(silent=True) or {}
    hostname = data.get("hostname", "").strip()
    port = int(data.get("port") or 443)
    authorized = data.get("authorized", False)

    if not hostname:
        raise ValidationError("Hostname is required to scan live server.")

    if not authorized:
        raise ValidationError("Explicit authorization confirmation is required before scanning a network server.")

    # Find or create asset
    assets, _ = asset_repo.list_assets(search=hostname, limit=1)
    target_asset = assets[0] if assets else None

    if not target_asset:
        target_asset = Asset(
            name=f"Server: {hostname}:{port}",
            asset_type="website" if port == 443 else "server",
            environment="production",
            hostname=hostname,
            description=f"Live server TLS target {hostname}:{port}",
            criticality="high",
        )
        asset_repo.create(target_asset)

    # Job tracking
    job = ScanJob(
        job_type="tls_scan",
        asset_id=target_asset.id,
        operation=f"tls_handshake_{hostname}:{port}",
        priority=7,
        status="running",
    )
    job_repo.create(job)

    # Execute TLS scan
    scanner = TlsScanner(allow_local_lab=True)
    result = scanner.scan(target_asset, {"port": port})

    # Persist findings
    saved_findings = []
    for f_dict in result.findings:
        f = Finding(
            asset_id=target_asset.id,
            job_id=job.id,
            scanner_type="tls_scan",
            algorithm=f_dict.get("algorithm", "Unknown"),
            cryptographic_primitive="key_establishment",
            quantum_vulnerable=True,
            recommended_pqc=f_dict.get("recommended_pqc", "ML-KEM-768 Hybrid"),
            rule_id=f_dict.get("rule_id", "PQC-TLS"),
            title=f_dict.get("title", ""),
            description=f_dict.get("description", ""),
            severity=f_dict.get("severity", "high"),
            evidence=f_dict.get("evidence", ""),
            file_path=f"{hostname}:{port}",
            line_number=0,
            confidence="high",
            remediation_status="potential_exposure",
        )
        finding_repo.save_finding(f)
        saved_findings.append(f.to_dict())

    job.status = "completed" if result.status == "completed" else "failed"
    job.progress = 100
    job.result_json = result.to_dict()
    job.error_message = result.error_message
    job_repo.update(job)

    return jsonify({
        "status": "ok",
        "job_id": job.id,
        "asset_id": target_asset.id,
        "scan_result": result.to_dict(),
        "findings": saved_findings,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/scanners/system/config & GET /api/scanners/system/config
# -------------------------------------------------------------
@scanners_bp.route("/api/v1/scanners/system/config", methods=["GET"])
@scanners_bp.route("/api/scanners/system/config", methods=["GET"])
def get_system_scan_config():
    """Return default and recommended configuration for system file scanner."""
    from pathlib import Path
    from quantumshield.scanner.system_file_scanner import (
        DEFAULT_MAX_FILE_SIZE_BYTES,
        DEFAULT_MAX_FILES_TO_SCAN,
        DEFAULT_EXCLUDED_DIRS,
        DEFAULT_SUPPORTED_EXTENSIONS,
    )
    
    # Project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    
    return jsonify({
        "status": "ok",
        "config": {
            "default_scope": "project",
            "project_root": str(project_root),
            "max_file_size_bytes": DEFAULT_MAX_FILE_SIZE_BYTES,
            "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_BYTES // (1024 * 1024),
            "max_files_to_scan": DEFAULT_MAX_FILES_TO_SCAN,
            "supported_extensions": sorted(list(DEFAULT_SUPPORTED_EXTENSIONS)),
            "excluded_directories": sorted(list(DEFAULT_EXCLUDED_DIRS)),
            "safety_model": {
                "read_only": True,
                "secret_redaction": True,
                "symlink_protection": True,
                "private_keys_protected": True,
            },
        },
    }), 200


# -------------------------------------------------------------
# POST /api/v1/scanners/system & POST /api/scanners/system
# -------------------------------------------------------------
@scanners_bp.route("/api/v1/scanners/system", methods=["POST"])
@scanners_bp.route("/api/scanners/system", methods=["POST"])
def scan_system_files():
    """
    Start automatic recursive system file scan on authorized scope.
    Runs as a persistent background job with live progress reporting.
    """
    from pathlib import Path
    from quantumshield.scanner.system_file_scanner import DEFAULT_MAX_FILE_SIZE_BYTES

    db_path = get_db_path()
    asset_repo = AssetRepository(db_path)
    job_repo = JobRepository(db_path)

    data = request.get_json(silent=True) or {}
    scope_type = data.get("target_scope", "project")
    target_directory = data.get("target_directory")
    asset_id = data.get("asset_id")

    project_root = Path(__file__).resolve().parent.parent.parent.parent

    # Determine authorized path
    if scope_type == "project" or not target_directory:
        scan_dir = str(project_root)
    else:
        # Validate target directory
        p = Path(target_directory).resolve()
        if not p.exists() or not p.is_dir():
            raise ValidationError(f"Target directory '{target_directory}' does not exist or is not a directory.")
        scan_dir = str(p)

    # Resolve or create target asset
    target_asset = None
    if asset_id:
        target_asset = asset_repo.get_by_id(asset_id)
        if not target_asset:
            raise NotFoundError(f"Target asset '{asset_id}' not found.")
    else:
        # Look for existing system file asset or create
        assets, _ = asset_repo.list_assets(search="System Project Files", limit=1)
        if assets:
            target_asset = assets[0]
        else:
            target_asset = Asset(
                id="system_files",
                name="System Project Files",
                asset_type="application",
                environment="production",
                description="Automatic system filesystem cryptographic discovery scope",
                criticality="high",
            )
            try:
                target_asset = asset_repo.create(target_asset)
            except Exception:
                target_asset = asset_repo.get_by_id("system_files") or target_asset

    # Build job payload
    payload = {
        "target_directory": scan_dir,
        "max_file_size_bytes": data.get("max_file_size_bytes", DEFAULT_MAX_FILE_SIZE_BYTES),
        "include_extensions": data.get("include_extensions"),
        "exclude_directories": data.get("exclude_directories"),
        "scan_scope_type": scope_type,
    }

    # Create job in Job Center
    job = ScanJob(
        job_type="system_scan",
        asset_id=target_asset.id,
        operation=f"system_scan_{Path(scan_dir).name}",
        priority=8,
        status="queued",
        payload_json=payload,
    )

    job_manager = current_app.extensions.get("job_manager")
    if job_manager:
        job = job_manager.enqueue(job)
    else:
        job = job_repo.create(job)
        # In testing or single-thread mode without workers, execute synchronously
        if current_app.config.get("TESTING", False):
            from quantumshield.services.job_worker import BackgroundJobManager
            temp_worker = BackgroundJobManager(db_path, max_workers=1)
            try:
                temp_worker._handle_system_scan(job)
                job = job_repo.get_by_id(job.id) or job
            except Exception as exc:
                job.status = "failed"
                job.error_message = str(exc)
                job_repo.update(job)

    return jsonify({
        "status": "ok",
        "message": "Automatic system file scan enqueued successfully.",
        "job_id": job.id,
        "asset_id": target_asset.id,
        "scope": scan_dir,
        "job": job.to_dict(),
    }), 201

