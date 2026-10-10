"""
Reports and Data Export REST API Endpoints.
Provides sanitized CSV downloads of cryptographic findings and audit summaries.
"""

from flask import Blueprint, request, Response, jsonify, current_app
from quantumshield.reports.exporter import ReportExporter
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.scan_repository import ScanRepository

reports_bp = Blueprint("reports", __name__)


def get_exporter():
    db_path = current_app.config.get("DATABASE_PATH")
    return ReportExporter(db_path)


# -------------------------------------------------------------
# GET /api/v1/reports/export & GET /api/reports/export - CSV Export
# -------------------------------------------------------------
@reports_bp.route("/api/v1/reports/export", methods=["GET"])
@reports_bp.route("/api/reports/export", methods=["GET"])
def export_csv():
    asset_id = request.args.get("asset_id")
    exporter = get_exporter()
    csv_data = exporter.export_findings_csv(asset_id=asset_id)

    filename = "quantumshield_findings_report.csv"
    if asset_id:
        filename = f"quantumshield_findings_{asset_id}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


# -------------------------------------------------------------
# GET /api/v1/reports/summary & GET /api/reports/summary
# -------------------------------------------------------------
@reports_bp.route("/api/v1/reports/summary", methods=["GET"])
@reports_bp.route("/api/reports/summary", methods=["GET"])
def get_reports_summary():
    db_path = current_app.config.get("DATABASE_PATH")
    finding_repo = FindingRepository(db_path)
    scan_repo = ScanRepository(db_path)

    stats = finding_repo.get_stats()
    _, total_scans = scan_repo.list_scan_runs(limit=1)

    return jsonify({
        "status": "ok",
        "total_scans": total_scans,
        "findings_stats": stats,
    }), 200
