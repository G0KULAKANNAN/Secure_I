"""
Classical Cryptography Decommissioning REST API Endpoints.
Supports both /api/v1/ and /api/ conventions.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.services.decommissioning_engine import DecommissioningEngine
from quantumshield.models.decommissioning import DecommissioningPolicy, CryptoDependency
from quantumshield.core.exceptions import ValidationError, NotFoundError

decommissioning_bp = Blueprint("decommissioning", __name__)


def get_engine() -> DecommissioningEngine:
    db_path = current_app.config.get("DATABASE_PATH")
    return DecommissioningEngine(db_path)


# --- Policies ---
@decommissioning_bp.route("/api/v1/decommissioning/policies", methods=["GET"])
@decommissioning_bp.route("/api/decommissioning/policies", methods=["GET"])
def list_policies():
    engine = get_engine()
    status = request.args.get("status")
    category = request.args.get("category")
    policies = engine.repo.list_policies(status=status, category=category)
    return jsonify({
        "status": "ok",
        "policies": [p.to_dict() for p in policies],
        "total": len(policies),
    }), 200


@decommissioning_bp.route("/api/v1/decommissioning/policies", methods=["POST"])
@decommissioning_bp.route("/api/decommissioning/policies", methods=["POST"])
def create_policy():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    algorithm = data.get("algorithm", "").strip()
    category = data.get("primitive_category", "key_exchange").strip()
    status = data.get("status", "MIGRATION_REQUIRED").strip()
    conditions = data.get("conditions")
    deadline = data.get("enforcement_deadline")
    rationale = data.get("rationale")

    if not name or not algorithm:
        raise ValidationError("Fields 'name' and 'algorithm' are required.")

    import uuid
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    policy = DecommissioningPolicy(
        id=f"pol_{uuid.uuid4().hex[:12]}",
        name=name,
        algorithm=algorithm,
        primitive_category=category,
        status=status,
        conditions=conditions,
        enforcement_deadline=deadline,
        rationale=rationale,
        created_at=now,
        updated_at=now,
    )
    engine = get_engine()
    created = engine.repo.create_policy(policy)
    return jsonify({"status": "ok", "policy": created.to_dict()}), 201


# --- Dependencies ---
@decommissioning_bp.route("/api/v1/decommissioning/dependencies", methods=["GET"])
@decommissioning_bp.route("/api/decommissioning/dependencies", methods=["GET"])
def list_dependencies():
    engine = get_engine()
    status = request.args.get("status")
    category = request.args.get("primitive_category")
    service = request.args.get("service_name")
    deps = engine.repo.list_dependencies(status=status, primitive_category=category, service_name=service)
    # If empty, discover automatically
    if not deps:
        deps = engine.discover_dependencies()
    return jsonify({
        "status": "ok",
        "dependencies": [d.to_dict() for d in deps],
        "total": len(deps),
    }), 200


@decommissioning_bp.route("/api/v1/decommissioning/dependencies/discover", methods=["POST"])
@decommissioning_bp.route("/api/decommissioning/dependencies/discover", methods=["POST"])
def discover_dependencies():
    engine = get_engine()
    deps = engine.discover_dependencies()
    return jsonify({
        "status": "ok",
        "dependencies": [d.to_dict() for d in deps],
        "total": len(deps),
    }), 200


@decommissioning_bp.route("/api/v1/decommissioning/dependencies/<dep_id>", methods=["PATCH"])
@decommissioning_bp.route("/api/decommissioning/dependencies/<dep_id>", methods=["PATCH"])
def update_dependency(dep_id: str):
    data = request.get_json(silent=True) or {}
    engine = get_engine()
    updated = engine.repo.update_dependency(dep_id, data)
    if not updated:
        raise NotFoundError(f"Dependency '{dep_id}' not found.")
    return jsonify({"status": "ok", "dependency": updated.to_dict()}), 200


# --- Plans ---
@decommissioning_bp.route("/api/v1/decommissioning/plans", methods=["GET"])
@decommissioning_bp.route("/api/decommissioning/plans", methods=["GET"])
def list_plans():
    engine = get_engine()
    state = request.args.get("state")
    plans = engine.repo.list_plans(state=state)
    return jsonify({
        "status": "ok",
        "plans": [p.to_dict() for p in plans],
        "total": len(plans),
    }), 200


@decommissioning_bp.route("/api/v1/decommissioning/plans", methods=["POST"])
@decommissioning_bp.route("/api/decommissioning/plans", methods=["POST"])
def create_plan():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    target_primitive = data.get("target_primitive", "").strip()
    affected_services = data.get("affected_services", [])
    rollback_instructions = data.get("rollback_instructions")

    if not name or not target_primitive:
        raise ValidationError("Fields 'name' and 'target_primitive' are required.")

    engine = get_engine()
    try:
        plan = engine.create_decommissioning_plan(
            name=name,
            target_primitive=target_primitive,
            affected_services=affected_services,
            rollback_instructions=rollback_instructions,
        )
        return jsonify({"status": "ok", "plan": plan.to_dict()}), 201
    except ValueError as e:
        raise ValidationError(str(e))


@decommissioning_bp.route("/api/v1/decommissioning/plans/<plan_id>", methods=["GET"])
@decommissioning_bp.route("/api/decommissioning/plans/<plan_id>", methods=["GET"])
def get_plan(plan_id: str):
    engine = get_engine()
    plan = engine.repo.get_plan(plan_id)
    if not plan:
        raise NotFoundError(f"Decommissioning plan '{plan_id}' not found.")
    return jsonify({"status": "ok", "plan": plan.to_dict()}), 200


@decommissioning_bp.route("/api/v1/decommissioning/plans/<plan_id>/assess-readiness", methods=["POST"])
@decommissioning_bp.route("/api/decommissioning/plans/<plan_id>/assess-readiness", methods=["POST"])
def assess_readiness(plan_id: str):
    engine = get_engine()
    try:
        assessment = engine.evaluate_readiness_gates(plan_id)
        return jsonify({"status": "ok", "assessment": assessment}), 200
    except ValueError as e:
        raise ValidationError(str(e))


@decommissioning_bp.route("/api/v1/decommissioning/plans/<plan_id>/approve", methods=["POST"])
@decommissioning_bp.route("/api/decommissioning/plans/<plan_id>/approve", methods=["POST"])
def approve_plan(plan_id: str):
    data = request.get_json(silent=True) or {}
    approver = data.get("approved_by")
    if approver is not None:
        approver = approver.strip()
    else:
        approver = data.get("operator", "").strip()

    if not approver:
        raise ValidationError("Field 'approved_by' or 'operator' is required and cannot be empty.")

    role = data.get("role", "CISO").strip()
    engine = get_engine()
    try:
        plan = engine.approve_plan(plan_id, approver, role=role)
        return jsonify({"status": "ok", "plan": plan.to_dict()}), 200
    except ValueError as e:
        raise ValidationError(str(e))


@decommissioning_bp.route("/api/v1/decommissioning/plans/<plan_id>/execute", methods=["POST"])
@decommissioning_bp.route("/api/decommissioning/plans/<plan_id>/execute", methods=["POST"])
def execute_plan(plan_id: str):
    data = request.get_json(silent=True) or {}
    operator = data.get("operator", "security_engineer").strip()
    engine = get_engine()
    try:
        plan = engine.execute_decommissioning(plan_id, operator=operator)
        return jsonify({"status": "ok", "plan": plan.to_dict()}), 200
    except ValueError as e:
        raise ValidationError(str(e))


@decommissioning_bp.route("/api/v1/decommissioning/plans/<plan_id>/rollback", methods=["POST"])
@decommissioning_bp.route("/api/decommissioning/plans/<plan_id>/rollback", methods=["POST"])
def rollback_plan(plan_id: str):
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "Operator manual rollback").strip()
    operator = data.get("operator", "security_engineer").strip()
    engine = get_engine()
    try:
        plan = engine.execute_rollback(plan_id, reason=reason, operator=operator)
        return jsonify({"status": "ok", "plan": plan.to_dict()}), 200
    except ValueError as e:
        raise ValidationError(str(e))
