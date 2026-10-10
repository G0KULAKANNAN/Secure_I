"""
Tests for health check and version API endpoints.
"""

def test_health_endpoint(client):
    """Test GET /api/v1/health returns 200 OK and valid health metadata."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "QuantumShield API"
    assert "version" in data
    assert "environment" in data


def test_version_endpoint(client):
    """Test GET /api/v1/version returns version metadata and disclaimer."""
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["api_version"] == "v1"
    assert "disclaimer" in data
    assert "not proof of compromise" in data["disclaimer"]


def test_404_not_found(client):
    """Test accessing unknown endpoint returns structured 404 JSON."""
    response = client.get("/api/v1/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.get_json()
    assert data["status"] == "error"
    assert data["code"] == 404
