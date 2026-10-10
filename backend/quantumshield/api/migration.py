"""
PQC Migration Guidance REST API Endpoints.
Provides NIST FIPS 203/204/205 alignment plans, testing checklists, and migration roadmaps.
"""

from flask import Blueprint, jsonify, current_app
from quantumshield.migration.engine import MigrationEngine

migration_bp = Blueprint("migration", __name__)


def get_migration_engine():
    db_path = current_app.config.get("DATABASE_PATH")
    return MigrationEngine(db_path)


# -------------------------------------------------------------
# GET /api/v1/migration & GET /api/migration - Global PQC Summary
# -------------------------------------------------------------
@migration_bp.route("/api/v1/migration", methods=["GET"])
@migration_bp.route("/api/migration", methods=["GET"])
def get_global_migration():
    engine = get_migration_engine()
    summary = engine.get_global_summary()
    return jsonify({
        "status": "ok",
        "migration_summary": summary,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/migration/assets/<asset_id> & GET /api/migration/assets/<asset_id>
# -------------------------------------------------------------
@migration_bp.route("/api/v1/migration/assets/<asset_id>", methods=["GET"])
@migration_bp.route("/api/migration/assets/<asset_id>", methods=["GET"])
def get_asset_migration_plan(asset_id: str):
    engine = get_migration_engine()
    plan = engine.get_asset_plan(asset_id)
    return jsonify({
        "status": "ok",
        "migration_plan": plan,
    }), 200
