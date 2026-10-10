"""
Automated Unit Tests for Asset Inventory API and Storage.
"""

import json


def test_create_valid_asset(client):
    """Test creating a valid asset via POST /api/v1/assets."""
    payload = {
        "name": "Auth Gateway Server",
        "asset_type": "server",
        "environment": "production",
        "hostname": "auth.internal.corp",
        "ip_address": "10.0.1.50",
        "owner": "Security Engineering",
        "description": "Critical authentication and token issuance proxy",
        "criticality": "critical",
        "status": "active",
    }
    response = client.post(
        "/api/v1/assets",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "ok"
    assert "asset" in data
    asset = data["asset"]
    assert asset["name"] == "Auth Gateway Server"
    assert asset["asset_type"] == "server"
    assert asset["environment"] == "production"
    assert asset["criticality"] == "critical"
    assert asset["id"].startswith("ast_")


def test_list_assets_empty_and_populated(client):
    """Test listing assets returns empty list initially, and includes newly created items."""
    # Empty
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    data = response.get_json()
    assert data["assets"] == []
    assert data["total"] == 0

    # Create 2 items
    client.post("/api/v1/assets", json={"name": "Server A", "asset_type": "server", "environment": "staging"})
    client.post("/api/v1/assets", json={"name": "Website B", "asset_type": "website", "environment": "production"})

    # Check list
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["assets"]) == 2
    assert data["total"] == 2


def test_get_asset_by_id(client):
    """Test retrieving an existing asset by ID."""
    res = client.post("/api/v1/assets", json={"name": "Database Cluster", "asset_type": "database", "environment": "production"})
    asset_id = res.get_json()["asset"]["id"]

    response = client.get(f"/api/v1/assets/{asset_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["asset"]["id"] == asset_id
    assert data["asset"]["name"] == "Database Cluster"


def test_get_nonexistent_asset_returns_404(client):
    """Test retrieving a missing asset returns structured 404."""
    response = client.get("/api/v1/assets/ast_nonexistent_999")
    assert response.status_code == 404
    data = response.get_json()
    assert data["status"] == "error"
    assert "not found" in data["error"].lower()


def test_update_asset(client):
    """Test updating an existing asset via PUT /api/v1/assets/<id>."""
    res = client.post("/api/v1/assets", json={"name": "Legacy TLS App", "asset_type": "application", "environment": "testing"})
    asset_id = res.get_json()["asset"]["id"]

    update_payload = {
        "name": "Upgraded TLS App",
        "criticality": "high",
        "status": "under_review",
    }
    response = client.put(f"/api/v1/assets/{asset_id}", json=update_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["asset"]["name"] == "Upgraded TLS App"
    assert data["asset"]["criticality"] == "high"
    assert data["asset"]["status"] == "under_review"


def test_delete_asset(client):
    """Test deleting an asset via DELETE /api/v1/assets/<id>."""
    res = client.post("/api/v1/assets", json={"name": "Temporary Server", "asset_type": "server", "environment": "development"})
    asset_id = res.get_json()["asset"]["id"]

    # Delete
    del_res = client.delete(f"/api/v1/assets/{asset_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["status"] == "ok"

    # Confirm 404
    get_res = client.get(f"/api/v1/assets/{asset_id}")
    assert get_res.status_code == 404


def test_reject_invalid_asset_fields(client):
    """Test server-side validation rejects invalid names, types, or environments."""
    # Missing / empty name
    res1 = client.post("/api/v1/assets", json={"name": "   ", "asset_type": "server", "environment": "production"})
    assert res1.status_code == 400
    assert "name is required" in res1.get_json()["error"].lower()

    # Invalid asset_type
    res2 = client.post("/api/v1/assets", json={"name": "Valid Name", "asset_type": "quantum_core", "environment": "production"})
    assert res2.status_code == 400
    assert "invalid asset_type" in res2.get_json()["error"].lower()

    # Invalid environment
    res3 = client.post("/api/v1/assets", json={"name": "Valid Name", "asset_type": "server", "environment": "sandbox_env"})
    assert res3.status_code == 400
    assert "invalid environment" in res3.get_json()["error"].lower()


def test_search_and_filtering(client):
    """Test searching by name/hostname and filtering by environment/type/criticality."""
    client.post("/api/v1/assets", json={
        "name": "Payment Vault",
        "asset_type": "database",
        "environment": "production",
        "criticality": "critical",
        "hostname": "vault.pay.internal",
    })
    client.post("/api/v1/assets", json={
        "name": "Frontend Portal",
        "asset_type": "website",
        "environment": "production",
        "criticality": "medium",
        "hostname": "www.corp.com",
    })
    client.post("/api/v1/assets", json={
        "name": "Dev Build Server",
        "asset_type": "server",
        "environment": "development",
        "criticality": "low",
        "hostname": "ci.dev.local",
    })

    # Search by keyword
    res = client.get("/api/v1/assets?search=Vault")
    data = res.get_json()
    assert len(data["assets"]) == 1
    assert data["assets"][0]["name"] == "Payment Vault"

    # Filter by environment
    res = client.get("/api/v1/assets?environment=production")
    data = res.get_json()
    assert len(data["assets"]) == 2

    # Filter by criticality
    res = client.get("/api/v1/assets?criticality=critical")
    data = res.get_json()
    assert len(data["assets"]) == 1
    assert data["assets"][0]["name"] == "Payment Vault"


def test_pagination(client):
    """Test pagination parameters limit and offset."""
    for i in range(5):
        client.post("/api/v1/assets", json={"name": f"Asset {i:02d}", "asset_type": "server", "environment": "development"})

    # Limit 2
    res = client.get("/api/v1/assets?limit=2&offset=0")
    data = res.get_json()
    assert len(data["assets"]) == 2
    assert data["total"] == 5

    # Offset 2, limit 2
    res2 = client.get("/api/v1/assets?limit=2&offset=2")
    data2 = res2.get_json()
    assert len(data2["assets"]) == 2
    assert data2["total"] == 5


def test_sql_injection_safety(client):
    """Verify malicious SQL injection string inputs are safely parameterized without executing."""
    injection_name = "Server'; DROP TABLE assets; --"
    res = client.post("/api/v1/assets", json={"name": injection_name, "asset_type": "server", "environment": "production"})
    assert res.status_code == 201
    asset_id = res.get_json()["asset"]["id"]

    # Table still exists and record is retrievable intact
    get_res = client.get(f"/api/v1/assets/{asset_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["asset"]["name"] == injection_name


def test_persistence_across_reconnect(app, client):
    """Verify data persisted in SQLite remains accessible across new connections."""
    res = client.post("/api/v1/assets", json={"name": "Persistent Asset", "asset_type": "certificate", "environment": "production"})
    asset_id = res.get_json()["asset"]["id"]

    # Read using fresh connection
    db_path = app.config["DATABASE_PATH"]
    from quantumshield.storage.repositories import AssetRepository
    repo = AssetRepository(db_path)
    asset = repo.get_by_id(asset_id)
    assert asset is not None
    assert asset.name == "Persistent Asset"
