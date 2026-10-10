"""
Audit Trail REST API Endpoint for querying immutable system logs.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.storage.audit_repository import AuditRepository

audit_bp = Blueprint("audit", __name__)


def get_audit_repo() -> AuditRepository:
    db_path = current_app.config.get("DATABASE_PATH")
    return AuditRepository(db_path)


@audit_bp.route("/api/v1/audit", methods=["GET"])
@audit_bp.route("/api/audit", methods=["GET"])
@audit_bp.route("/api/v1/audit/events", methods=["GET"])
@audit_bp.route("/api/audit/events", methods=["GET"])
def list_audit_events():
    repo = get_audit_repo()
    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    events = repo.list_events(entity_type=entity_type, entity_id=entity_id, limit=limit, offset=offset)
    return jsonify({
        "status": "ok",
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }), 200
