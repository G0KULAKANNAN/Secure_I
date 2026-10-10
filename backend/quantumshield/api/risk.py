"""
Risk Assessment REST API Endpoints.
Provides explainable, factor-weighted risk scoring, interactive simulation,
and Monday Morning Remediation Queue management.
"""

from flask import Blueprint, jsonify, request, current_app
from quantumshield.risk.engine import (
    RiskEngine,
    calculate_finding_risk_score,
    MODEL_VERSION,
    MODEL_DISCLAIMER,
    SCORE_THRESHOLDS,
)
from quantumshield.storage.finding_repository import FindingRepository

risk_bp = Blueprint("risk", __name__)


def get_risk_engine():
    db_path = current_app.config.get("DATABASE_PATH")
    return RiskEngine(db_path)


def get_finding_repo():
    db_path = current_app.config.get("DATABASE_PATH")
    return FindingRepository(db_path)


# -------------------------------------------------------------
# GET /api/v1/risk/formula & GET /api/risk/formula
# -------------------------------------------------------------
@risk_bp.route("/api/v1/risk/formula", methods=["GET"])
@risk_bp.route("/api/risk/formula", methods=["GET"])
def get_formula_metadata():
    """Return model formula, non-NIST project disclaimer, and factor definitions."""
    return jsonify({
        "status": "ok",
        "model_version": MODEL_VERSION,
        "disclaimer": MODEL_DISCLAIMER,
        "formula": "Risk Score = round(((S + E + L) / 15) * 100)",
        "scale": "0 to 100",
        "thresholds": SCORE_THRESHOLDS,
        "factors": {
            "S": {
                "name": "Data Sensitivity",
                "scale": "1 to 5",
                "levels": {
                    "1": "Public data",
                    "2": "Internal, low-sensitivity data",
                    "3": "Confidential business data",
                    "4": "Sensitive personal or financial data",
                    "5": "Highly confidential or critical data",
                },
            },
            "E": {
                "name": "Exposure",
                "scale": "1 to 5",
                "levels": {
                    "1": "Isolated test environment",
                    "2": "Restricted internal system",
                    "3": "Internal system accessible by multiple teams",
                    "4": "Externally accessible or internet-facing system",
                    "5": "Highly exposed critical endpoint or broadly accessible service",
                },
            },
            "L": {
                "name": "Confidentiality Lifetime",
                "scale": "1 to 5",
                "levels": {
                    "1": "Confidentiality required for less than 1 year",
                    "2": "1-2 years",
                    "3": "3-5 years",
                    "4": "6-10 years",
                    "5": "More than 10 years",
                },
            },
        },
    }), 200


# -------------------------------------------------------------
# POST /api/v1/risk/calculate & POST /api/risk/calculate
# -------------------------------------------------------------
@risk_bp.route("/api/v1/risk/calculate", methods=["POST"])
@risk_bp.route("/api/risk/calculate", methods=["POST"])
def simulate_risk_calculation():
    """Interactive What-If risk score simulator."""
    data = request.get_json(silent=True) or {}
    s = data.get("sensitivity") or data.get("data_sensitivity")
    e = data.get("exposure")
    l = data.get("lifetime") or data.get("confidentiality_lifetime")

    score, category, rationale = calculate_finding_risk_score(s, e, l)

    return jsonify({
        "status": "ok",
        "risk_score": score,
        "risk_category": category,
        "score_rationale": rationale,
        "model_version": MODEL_VERSION,
        "disclaimer": MODEL_DISCLAIMER,
        "factors": {"sensitivity": s, "exposure": e, "lifetime": l},
    }), 200


# -------------------------------------------------------------
# GET /api/v1/risk/summary & GET /api/risk/summary
# -------------------------------------------------------------
@risk_bp.route("/api/v1/risk/summary", methods=["GET"])
@risk_bp.route("/api/risk/summary", methods=["GET"])
def get_risk_summary():
    """Return aggregated risk portfolio summary."""
    repo = get_finding_repo()
    stats = repo.get_stats()
    return jsonify({
        "status": "ok",
        "model_version": MODEL_VERSION,
        "disclaimer": MODEL_DISCLAIMER,
        "stats": stats,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/risk/queue & GET /api/risk/queue
# -------------------------------------------------------------
@risk_bp.route("/api/v1/risk/queue", methods=["GET"])
@risk_bp.route("/api/risk/queue", methods=["GET"])
def get_remediation_queue():
    """Return Monday Morning Remediation Queue."""
    repo = get_finding_repo()
    return jsonify({
        "status": "ok",
        "queue": repo.get_remediation_queue(),
    }), 200


# -------------------------------------------------------------
# GET /api/v1/risk & GET /api/risk - Assess All Assets
# -------------------------------------------------------------
@risk_bp.route("/api/v1/risk", methods=["GET"])
@risk_bp.route("/api/risk", methods=["GET"])
def assess_all():
    engine = get_risk_engine()
    results = engine.assess_all_assets()
    return jsonify({
        "status": "ok",
        "assessments": results,
        "total": len(results),
    }), 200


# -------------------------------------------------------------
# GET /api/v1/risk/assets/<asset_id> & GET /api/risk/assets/<asset_id>
# -------------------------------------------------------------
@risk_bp.route("/api/v1/risk/assets/<asset_id>", methods=["GET"])
@risk_bp.route("/api/risk/assets/<asset_id>", methods=["GET"])
def assess_single(asset_id: str):
    engine = get_risk_engine()
    result = engine.assess_asset(asset_id)
    return jsonify({
        "status": "ok",
        "assessment": result,
    }), 200
