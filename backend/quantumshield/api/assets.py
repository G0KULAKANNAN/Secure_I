"""
Asset Inventory REST API Endpoints.
Supports both /api/v1/assets and /api/assets route conventions.
"""

from flask import Blueprint, request, jsonify, current_app
from quantumshield.storage.repositories import AssetRepository
from quantumshield.models.asset import Asset
from quantumshield.core.exceptions import ValidationError, NotFoundError


assets_bp = Blueprint("assets", __name__)


def get_repo() -> AssetRepository:
    """Helper to instantiate AssetRepository with the current app's configured database path."""
    db_path = current_app.config.get("DATABASE_PATH")
    return AssetRepository(db_path)


# -------------------------------------------------------------
# GET /api/v1/assets & GET /api/assets - List & Filter Assets
# -------------------------------------------------------------
@assets_bp.route("/api/v1/assets", methods=["GET"])
@assets_bp.route("/api/assets", methods=["GET"])
def list_assets():
    repo = get_repo()
    search = request.args.get("search", "")
    asset_type = request.args.get("asset_type")
    environment = request.args.get("environment")
    criticality = request.args.get("criticality")
    status = request.args.get("status")

    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        raise ValidationError("Limit and offset must be valid integers.")

    assets, total = repo.list_assets(
        search=search,
        asset_type=asset_type,
        environment=environment,
        criticality=criticality,
        status=status,
        limit=limit,
        offset=offset,
    )

    return jsonify({
        "status": "ok",
        "assets": [a.to_dict() for a in assets],
        "total": total,
        "limit": limit,
        "offset": offset,
    }), 200


# -------------------------------------------------------------
# GET /api/v1/assets/<id> & GET /api/assets/<id> - Get Single Asset
# -------------------------------------------------------------
@assets_bp.route("/api/v1/assets/<asset_id>", methods=["GET"])
@assets_bp.route("/api/assets/<asset_id>", methods=["GET"])
def get_asset(asset_id: str):
    repo = get_repo()
    asset = repo.get_by_id(asset_id)
    if not asset:
        raise NotFoundError(f"Asset with ID '{asset_id}' not found.")

    return jsonify({
        "status": "ok",
        "asset": asset.to_dict(),
    }), 200


# -------------------------------------------------------------
# POST /api/v1/assets & POST /api/assets - Create Asset
# -------------------------------------------------------------
@assets_bp.route("/api/v1/assets", methods=["POST"])
@assets_bp.route("/api/assets", methods=["POST"])
def create_asset():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        raise ValidationError("Invalid JSON payload provided.")

    asset = Asset.from_dict(data)
    asset.validate()

    repo = get_repo()
    created = repo.create(asset)

    return jsonify({
        "status": "ok",
        "message": "Asset registered successfully.",
        "asset": created.to_dict(),
    }), 201


# -------------------------------------------------------------
# PUT /api/v1/assets/<id> & PUT /api/assets/<id> - Update Asset
# -------------------------------------------------------------
@assets_bp.route("/api/v1/assets/<asset_id>", methods=["PUT"])
@assets_bp.route("/api/assets/<asset_id>", methods=["PUT"])
def update_asset(asset_id: str):
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        raise ValidationError("Invalid JSON payload provided.")

    repo = get_repo()
    existing = repo.get_by_id(asset_id)
    if not existing:
        raise NotFoundError(f"Asset with ID '{asset_id}' not found.")

    # Update mutable fields
    if "name" in data:
        existing.name = str(data["name"])
    if "asset_type" in data:
        existing.asset_type = str(data["asset_type"])
    if "environment" in data:
        existing.environment = str(data["environment"])
    if "hostname" in data:
        existing.hostname = data["hostname"]
    if "ip_address" in data:
        existing.ip_address = data["ip_address"]
    if "owner" in data:
        existing.owner = data["owner"]
    if "description" in data:
        existing.description = data["description"]
    if "criticality" in data:
        existing.criticality = str(data["criticality"])
    if "status" in data:
        existing.status = str(data["status"])

    existing.validate()
    updated = repo.update(existing)

    return jsonify({
        "status": "ok",
        "message": "Asset updated successfully.",
        "asset": updated.to_dict(),
    }), 200


# -------------------------------------------------------------
# DELETE /api/v1/assets/<id> & DELETE /api/assets/<id> - Delete Asset
# -------------------------------------------------------------
@assets_bp.route("/api/v1/assets/<asset_id>", methods=["DELETE"])
@assets_bp.route("/api/assets/<asset_id>", methods=["DELETE"])
def delete_asset(asset_id: str):
    repo = get_repo()
    existing = repo.get_by_id(asset_id)
    if not existing:
        raise NotFoundError(f"Asset with ID '{asset_id}' not found.")

    success = repo.delete(asset_id)
    if not success:
        raise NotFoundError(f"Failed to delete asset '{asset_id}'.")

    return jsonify({
        "status": "ok",
        "message": f"Asset '{asset_id}' deleted successfully.",
        "id": asset_id,
    }), 200
