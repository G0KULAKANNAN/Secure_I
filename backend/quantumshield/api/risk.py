"""
Risk Assessment REST API Endpoints.
Provides explainable, factor-weighted risk scoring for all inventory assets.
"""

from flask import Blueprint, jsonify, current_app
from quantumshield.risk.engine import RiskEngine

risk_bp = Blueprint("risk", __name__)


def get_risk_engine():
    db_path = current_app.config.get("DATABASE_PATH")
    return RiskEngine(db_path)


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
