"""
Rollout Management REST API Endpoints.
Supports both /api/v1/ and /api/ conventions.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.services.rollout_engine import RolloutEngine
from quantumshield.core.exceptions import ValidationError, NotFoundError

rollout_bp = Blueprint("rollout", __name__)


def get_engine() -> RolloutEngine:
    db_path = current_app.config.get("DATABASE_PATH")
    return RolloutEngine(db_path)


@rollout_bp.route("/api/v1/rollout/environments", methods=["GET"])
@rollout_bp.route("/api/rollout/environments", methods=["GET"])
def list_environments():
    engine = get_engine()
    environments = engine.rollout_repo.list_environments()
    return jsonify({
        "status": "ok",
        "environments": [e.to_dict() for e in environments],
        "total": len(environments),
    }), 200


@rollout_bp.route("/api/v1/rollout/environments/<env_id>", methods=["GET"])
@rollout_bp.route("/api/rollout/environments/<env_id>", methods=["GET"])
def get_environment(env_id: str):
    engine = get_engine()
    env = engine.rollout_repo.get_environment(env_id)
    if not env:
        raise NotFoundError(f"Deployment environment '{env_id}' not found.")
    return jsonify({"status": "ok", "environment": env.to_dict()}), 200


@rollout_bp.route("/api/v1/rollout/plans", methods=["GET"])
@rollout_bp.route("/api/rollout/plans", methods=["GET"])
def list_plans():
    engine = get_engine()
    env_id = request.args.get("environment_id")
    state = request.args.get("state")
    plans = engine.rollout_repo.list_rollout_plans(environment_id=env_id, state=state)
    return jsonify({
        "status": "ok",
        "plans": [p.to_dict() for p in plans],
        "total": len(plans),
    }), 200


@rollout_bp.route("/api/v1/rollout/plans", methods=["POST"])
@rollout_bp.route("/api/rollout/plans", methods=["POST"])
def create_plan():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    environment_id = data.get("environment_id", "").strip()
    target_config = data.get("target_config")
    previous_config = data.get("previous_config")
    rollback_threshold = data.get("rollback_threshold_failure_rate", 2.0)
    deployment_mode = data.get("deployment_mode", "simulation")

    if not name:
        raise ValidationError("Field 'name' is required.")
    if not environment_id:
        raise ValidationError("Field 'environment_id' is required.")
    if not target_config or not isinstance(target_config, dict):
        raise ValidationError("Field 'target_config' must be a valid configuration object.")

    engine = get_engine()
    try:
        plan = engine.create_plan(
            name=name,
            environment_id=environment_id,
            target_config=target_config,
            previous_config=previous_config,
            rollback_threshold_failure_rate=float(rollback_threshold),
            deployment_mode=deployment_mode,
        )
        return jsonify({"status": "ok", "plan": plan.to_dict()}), 201
    except ValueError as e:
        raise ValidationError(str(e))


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>", methods=["GET"])
@rollout_bp.route("/api/rollout/plans/<plan_id>", methods=["GET"])
def get_plan(plan_id: str):
    engine = get_engine()
    plan = engine.rollout_repo.get_rollout_plan(plan_id)
    if not plan:
        raise NotFoundError(f"Rollout plan '{plan_id}' not found.")
    telemetry = engine.rollout_repo.get_telemetry_for_rollout(plan_id, limit=20)
    return jsonify({
        "status": "ok",
        "plan": plan.to_dict(),
        "recent_telemetry": [t.to_dict() for t in telemetry],
    }), 200


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>/assess-readiness", methods=["POST"])
@rollout_bp.route("/api/rollout/plans/<plan_id>/assess-readiness", methods=["POST"])
def assess_readiness(plan_id: str):
    engine = get_engine()
    try:
        result = engine.evaluate_readiness_gates(plan_id)
        return jsonify({"status": "ok", "assessment": result}), 200
    except ValueError as e:
        raise ValidationError(str(e))


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>/approve", methods=["POST"])
@rollout_bp.route("/api/rollout/plans/<plan_id>/approve", methods=["POST"])
def approve_plan(plan_id: str):
    data = request.get_json(silent=True) or {}
    approver = data.get("approved_by")
    if approver is not None:
        approver = approver.strip()
    else:
        approver = data.get("operator", "").strip()

    if not approver:
        raise ValidationError("Field 'approved_by' or 'operator' is required and cannot be empty.")

    engine = get_engine()
    try:
        plan = engine.approve_plan(plan_id, approver)
        return jsonify({"status": "ok", "plan": plan.to_dict()}), 200
    except ValueError as e:
        raise ValidationError(str(e))


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>/advance", methods=["POST"])
@rollout_bp.route("/api/rollout/plans/<plan_id>/advance", methods=["POST"])
def advance_canary(plan_id: str):
    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))
    engine = get_engine()
    try:
        result = engine.advance_canary_stage(plan_id, force=force)
        return jsonify({"status": "ok", "result": result}), 200
    except ValueError as e:
        raise ValidationError(str(e))


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>/telemetry", methods=["POST"])
@rollout_bp.route("/api/rollout/plans/<plan_id>/telemetry", methods=["POST"])
def record_telemetry(plan_id: str):
    data = request.get_json(silent=True) or {}
    engine = get_engine()
    try:
        result = engine.record_telemetry(plan_id, data)
        return jsonify({"status": "ok", "result": result}), 201
    except ValueError as e:
        raise ValidationError(str(e))


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>/telemetry", methods=["GET"])
@rollout_bp.route("/api/rollout/plans/<plan_id>/telemetry", methods=["GET"])
def get_telemetry(plan_id: str):
    engine = get_engine()
    limit = int(request.args.get("limit", 50))
    telemetry = engine.rollout_repo.get_telemetry_for_rollout(plan_id, limit=limit)
    return jsonify({
        "status": "ok",
        "telemetry": [t.to_dict() for t in telemetry],
        "total": len(telemetry),
    }), 200


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>/simulate-traffic", methods=["POST"])
@rollout_bp.route("/api/rollout/plans/<plan_id>/simulate-traffic", methods=["POST"])
def simulate_traffic(plan_id: str):
    data = request.get_json(silent=True) or {}
    healthy = bool(data.get("healthy", True))
    engine = get_engine()
    try:
        result = engine.simulate_canary_traffic(plan_id, healthy=healthy)
        return jsonify({"status": "ok", "result": result}), 200
    except ValueError as e:
        raise ValidationError(str(e))


@rollout_bp.route("/api/v1/rollout/plans/<plan_id>/rollback", methods=["POST"])
@rollout_bp.route("/api/rollout/plans/<plan_id>/rollback", methods=["POST"])
def rollback_plan(plan_id: str):
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "Operator manual rollback").strip()
    actor = data.get("operator", "sre_operator").strip()
    engine = get_engine()
    try:
        plan = engine.execute_rollback(plan_id, reason=reason, actor=actor)
        return jsonify({"status": "ok", "plan": plan.to_dict()}), 200
    except ValueError as e:
        raise ValidationError(str(e))
