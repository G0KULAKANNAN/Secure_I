"""
Hybrid Cryptography Staging REST API Endpoints.
Supports both /api/v1/ and /api/ conventions.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.services.hybrid_engine import HybridStagingEngine
from quantumshield.core.exceptions import ValidationError, NotFoundError

hybrid_bp = Blueprint("hybrid", __name__)


def get_engine() -> HybridStagingEngine:
    db_path = current_app.config.get("DATABASE_PATH")
    return HybridStagingEngine(db_path)


@hybrid_bp.route("/api/v1/hybrid/capabilities", methods=["GET"])
@hybrid_bp.route("/api/hybrid/capabilities", methods=["GET"])
def get_capabilities():
    engine = get_engine()
    host_caps = engine.detect_host_capabilities()
    capabilities = engine.repo.list_capabilities()
    return jsonify({
        "status": "ok",
        "host_provider": host_caps,
        "capabilities": [c.to_dict() for c in capabilities],
    }), 200


@hybrid_bp.route("/api/v1/hybrid/profiles", methods=["GET"])
@hybrid_bp.route("/api/hybrid/profiles", methods=["GET"])
def list_profiles():
    engine = get_engine()
    profiles = engine.repo.list_profiles()
    return jsonify({
        "status": "ok",
        "profiles": [p.to_dict() for p in profiles],
        "total": len(profiles),
    }), 200


@hybrid_bp.route("/api/v1/hybrid/profiles", methods=["POST"])
@hybrid_bp.route("/api/hybrid/profiles", methods=["POST"])
def create_profile():
    data = request.get_json(silent=True) or {}
    profile_name = data.get("profile_name", "").strip()
    classical = data.get("classical_component", "X25519").strip()
    pqc = data.get("pqc_component", "ML-KEM-768").strip()
    operator = data.get("operator", "local_operator").strip()

    if not profile_name:
        raise ValidationError("Field 'profile_name' is required.")

    engine = get_engine()
    profile = engine.create_staging_profile(
        profile_name=profile_name,
        classical_component=classical,
        pqc_component=pqc,
        operator=operator,
    )
    return jsonify({
        "status": "ok",
        "message": f"Hybrid profile '{profile.profile_name}' created.",
        "profile": profile.to_dict(),
    }), 201


@hybrid_bp.route("/api/v1/hybrid/profiles/<profile_id>", methods=["GET"])
@hybrid_bp.route("/api/hybrid/profiles/<profile_id>", methods=["GET"])
def get_profile(profile_id: str):
    engine = get_engine()
    profile = engine.repo.get_profile_by_id(profile_id)
    if not profile:
        raise NotFoundError(f"Hybrid profile '{profile_id}' not found.")

    runs = engine.repo.list_runs_for_profile(profile_id)
    return jsonify({
        "status": "ok",
        "profile": profile.to_dict(),
        "runs": [r.to_dict() for r in runs],
    }), 200


@hybrid_bp.route("/api/v1/hybrid/profiles/<profile_id>/test", methods=["POST"])
@hybrid_bp.route("/api/hybrid/profiles/<profile_id>/test", methods=["POST"])
def run_test(profile_id: str):
    data = request.get_json(silent=True) or {}
    test_mode = data.get("test_mode", "simulation")
    operator = data.get("operator", "local_operator")

    engine = get_engine()
    run = engine.execute_interoperability_test(
        profile_id=profile_id,
        test_mode=test_mode,
        operator=operator,
    )
    return jsonify({
        "status": "ok",
        "verification_run": run.to_dict(),
    }), 200


@hybrid_bp.route("/api/v1/hybrid/profiles/<profile_id>/approve", methods=["POST"])
@hybrid_bp.route("/api/hybrid/profiles/<profile_id>/approve", methods=["POST"])
def approve_profile(profile_id: str):
    data = request.get_json(silent=True) or {}
    approved_by = data.get("approved_by", "local_operator")

    engine = get_engine()
    profile = engine.approve_profile(profile_id=profile_id, approved_by=approved_by)
    return jsonify({
        "status": "ok",
        "message": f"Hybrid profile '{profile.profile_name}' approved.",
        "profile": profile.to_dict(),
    }), 200


@hybrid_bp.route("/api/v1/hybrid/profiles/<profile_id>/rollback", methods=["POST"])
@hybrid_bp.route("/api/hybrid/profiles/<profile_id>/rollback", methods=["POST"])
def rollback_profile(profile_id: str):
    data = request.get_json(silent=True) or {}
    operator = data.get("operator", "local_operator")

    engine = get_engine()
    profile = engine.rollback_profile(profile_id=profile_id, operator=operator)
    return jsonify({
        "status": "ok",
        "message": f"Hybrid profile '{profile.profile_name}' rolled back to previous configuration.",
        "profile": profile.to_dict(),
    }), 200


@hybrid_bp.route("/api/v1/hybrid/profiles/<profile_id>", methods=["DELETE"])
@hybrid_bp.route("/api/hybrid/profiles/<profile_id>", methods=["DELETE"])
def delete_profile(profile_id: str):
    engine = get_engine()
    profile = engine.repo.get_profile_by_id(profile_id)
    if not profile:
        raise NotFoundError(f"Hybrid profile '{profile_id}' not found.")

    engine.repo.delete_profile(profile_id)
    return jsonify({
        "status": "ok",
        "message": f"Hybrid profile '{profile.profile_name}' deleted.",
    }), 200
