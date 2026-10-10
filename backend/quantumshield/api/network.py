"""
Network MTU and Middlebox Verification REST API Endpoints.
Supports both /api/v1/ and /api/ route conventions.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.services.network_engine import NetworkVerificationEngine
from quantumshield.models.network import NetworkProfile
from quantumshield.core.exceptions import ValidationError, NotFoundError, ConflictError

network_bp = Blueprint("network", __name__)


def get_network_engine() -> NetworkVerificationEngine:
    db_path = current_app.config.get("DATABASE_PATH")
    return NetworkVerificationEngine(db_path)


@network_bp.route("/api/v1/network/profiles", methods=["GET"])
@network_bp.route("/api/network/profiles", methods=["GET"])
def list_profiles():
    engine = get_network_engine()
    profiles = engine.repo.list_profiles()
    return jsonify({
        "status": "ok",
        "profiles": [p.to_dict() for p in profiles],
        "total": len(profiles),
    }), 200


@network_bp.route("/api/v1/network/profiles", methods=["POST"])
@network_bp.route("/api/network/profiles", methods=["POST"])
def create_profile():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    target_host = data.get("target_host", "127.0.0.1").strip()
    target_port = int(data.get("target_port", 443))
    environment = data.get("environment", "local_lab")
    test_profile = data.get("test_profile", "standard_mtu")
    test_mode = data.get("test_mode", "simulation")
    expected_mtu = int(data.get("expected_mtu", 1500))
    authorized = bool(data.get("authorized_by_operator", False))
    operator_notes = data.get("operator_notes")

    if not name:
        raise ValidationError("Field 'name' is required.")

    engine = get_network_engine()
    existing = engine.repo.get_profile_by_name(name)
    if existing:
        raise ConflictError(f"Network profile '{name}' already exists.")

    profile = NetworkProfile(
        name=name,
        target_host=target_host,
        target_port=target_port,
        environment=environment,
        test_profile=test_profile,
        test_mode=test_mode,
        expected_mtu=expected_mtu,
        is_allowlisted=target_host in ("127.0.0.1", "localhost"),
        authorized_by_operator=authorized,
        operator_notes=operator_notes,
    )

    saved = engine.repo.create_profile(profile)
    return jsonify({
        "status": "ok",
        "message": f"Network verification profile '{saved.name}' created.",
        "profile": saved.to_dict(),
    }), 201


@network_bp.route("/api/v1/network/profiles/<profile_id>", methods=["GET"])
@network_bp.route("/api/network/profiles/<profile_id>", methods=["GET"])
def get_profile(profile_id: str):
    engine = get_network_engine()
    profile = engine.repo.get_profile_by_id(profile_id)
    if not profile:
        raise NotFoundError(f"Network profile '{profile_id}' not found.")

    results = engine.repo.list_results(profile_id=profile_id, limit=20)
    return jsonify({
        "status": "ok",
        "profile": profile.to_dict(),
        "results": [r.to_dict() for r in results],
    }), 200


@network_bp.route("/api/v1/network/profiles/<profile_id>/run", methods=["POST"])
@network_bp.route("/api/network/profiles/<profile_id>/run", methods=["POST"])
def run_verification(profile_id: str):
    data = request.get_json(silent=True) or {}
    operator = data.get("operator", "local_operator")

    engine = get_network_engine()
    result = engine.run_verification(profile_id=profile_id, operator=operator)
    return jsonify({
        "status": "ok",
        "message": "Network verification test executed successfully.",
        "result": result.to_dict(),
    }), 200


@network_bp.route("/api/v1/network/results", methods=["GET"])
@network_bp.route("/api/network/results", methods=["GET"])
def list_results():
    engine = get_network_engine()
    profile_id = request.args.get("profile_id")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    results = engine.repo.list_results(profile_id=profile_id, limit=limit, offset=offset)
    return jsonify({
        "status": "ok",
        "results": [r.to_dict() for r in results],
        "total": len(results),
    }), 200


@network_bp.route("/api/v1/network/profiles/<profile_id>", methods=["DELETE"])
@network_bp.route("/api/network/profiles/<profile_id>", methods=["DELETE"])
def delete_profile(profile_id: str):
    engine = get_network_engine()
    profile = engine.repo.get_profile_by_id(profile_id)
    if not profile:
        raise NotFoundError(f"Network profile '{profile_id}' not found.")

    engine.repo.delete_profile(profile_id)
    return jsonify({
        "status": "ok",
        "message": f"Network profile '{profile.name}' deleted.",
    }), 200
