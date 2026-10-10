"""
Comprehensive tests for scan orchestration, scanner execution, and findings persistence.
"""

import io
import pytest
from quantumshield.storage.repositories import AssetRepository
from quantumshield.models.asset import Asset


def create_sample_asset(client, name="Test Production Server", hostname="scanme.nmap.org"):
    """Helper to register an asset."""
    res = client.post(
        "/api/v1/assets",
        json={
            "name": name,
            "asset_type": "server",
            "environment": "production",
            "hostname": hostname,
            "criticality": "high",
        },
    )
    assert res.status_code == 201
    return res.get_json()["asset"]


def test_source_code_scan_string(client):
    """Test static scanner detecting classical RSA and ECDH patterns in pasted source code."""
    code_snippet = '''
import rsa
from cryptography.hazmat.primitives.asymmetric import ec

def generate_keys():
    (pubkey, privkey) = rsa.newkeys(2048)
    ec_key = ec.generate_private_key(ec.SECP256R1())
    return pubkey, ec_key
'''
    res = client.post(
        "/api/v1/scanners/source",
        json={
            "source_content": code_snippet,
            "file_name": "crypto_service.py",
        },
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "job_id" in data
    assert len(data["findings"]) >= 2
    
    # Check that findings contain RSA and EC detections
    algorithms = [f["algorithm"] for f in data["findings"]]
    assert any("RSA" in a for a in algorithms)
    assert any("EC" in a for a in algorithms)


def test_source_code_scan_file_upload(client):
    """Test static scanner via multipart file upload."""
    content = b"""
import ssl
ctx = ssl.create_default_context()
# Using classical Diffie-Hellman
ctx.set_ciphers('DHE-RSA-AES128-SHA')
"""
    data = {
        "file": (io.BytesIO(content), "ssl_config.py"),
    }
    res = client.post(
        "/api/v1/scanners/source",
        data=data,
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    res_data = res.get_json()
    assert res_data["status"] == "ok"
    assert len(res_data["findings"]) >= 1


def test_source_code_scan_no_payload_rejected(client):
    """Reject empty source scan request."""
    res = client.post("/api/v1/scanners/source", json={})
    assert res.status_code == 400


def test_live_server_scan_requires_authorization(client):
    """Test that TLS scan fails if user does not confirm authorization."""
    res = client.post(
        "/api/v1/scanners/tls",
        json={
            "hostname": "example.com",
            "port": 443,
            "authorized": False,
        },
    )
    assert res.status_code == 400
    assert "authorization" in res.get_json()["error"].lower()


def test_live_server_scan_rejects_empty_hostname(client):
    """Test that TLS scan fails without hostname."""
    res = client.post(
        "/api/v1/scanners/tls",
        json={
            "hostname": "",
            "port": 443,
            "authorized": True,
        },
    )
    assert res.status_code == 400


def test_certificate_scanner_direct_upload(client):
    """Test certificate scanner rejects private keys and handles certs."""
    # Test private key rejection
    fake_privkey = b"-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAz...\n-----END RSA PRIVATE KEY-----"
    res = client.post(
        "/api/v1/scanners/certificate",
        data={"file": (io.BytesIO(fake_privkey), "priv.pem")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    assert "private key" in res.get_json()["error"].lower()


def test_scan_orchestration_flow(client):
    """Test full scan orchestration flow via /api/v1/scans."""
    asset = create_sample_asset(client, name="Orchestrated Web Node", hostname="api.internal.local")
    
    # Enqueue scan run
    res = client.post(
        "/api/v1/scans",
        json={
            "asset_id": asset["id"],
            "scanner_types": ["static_scan"],
        },
    )
    assert res.status_code == 201
    run = res.get_json()["scan_run"]
    assert run["asset_id"] == asset["id"]
    assert run["status"] == "queued"

    # List scans
    res_list = client.get("/api/v1/scans")
    assert res_list.status_code == 200
    assert res_list.get_json()["total"] >= 1


def test_scan_duplicate_active_protection(client):
    """Test that requesting two simultaneous scans on the same asset returns 409 Conflict."""
    asset = create_sample_asset(client, name="Conflict Asset", hostname="conflict.local")
    
    res1 = client.post(
        "/api/v1/scans",
        json={
            "asset_id": asset["id"],
            "scanner_types": ["static_scan"],
        },
    )
    assert res1.status_code == 201

    # Immediate second request should be 409 Conflict
    res2 = client.post(
        "/api/v1/scans",
        json={
            "asset_id": asset["id"],
            "scanner_types": ["static_scan"],
        },
    )
    assert res2.status_code == 409


def test_list_and_filter_findings(client):
    """Test findings listing, stats, and status patching."""
    # Create findings by performing a static scan
    snippet = "from Crypto.PublicKey import RSA\nkey = RSA.generate(2048)"
    client.post(
        "/api/v1/scanners/source",
        json={"source_content": snippet, "file_name": "app.py"},
    )

    # Fetch findings
    res = client.get("/api/v1/findings")
    assert res.status_code == 200
    findings = res.get_json()["findings"]
    assert len(findings) >= 1
    
    finding_id = findings[0]["id"]
    
    # Get finding by ID
    res_single = client.get(f"/api/v1/findings/{finding_id}")
    assert res_single.status_code == 200
    assert res_single.get_json()["finding"]["id"] == finding_id

    # Update status
    res_patch = client.patch(
        f"/api/v1/findings/{finding_id}",
        json={"remediation_status": "verified_usage"},
    )
    assert res_patch.status_code == 200
    assert res_patch.get_json()["finding"]["remediation_status"] == "verified_usage"

    # Get finding stats
    res_stats = client.get("/api/v1/findings/stats")
    assert res_stats.status_code == 200
    stats = res_stats.get_json()["stats"]
    assert "total_findings" in stats
    assert stats["total_findings"] >= 1


def test_migration_guidance_endpoints(client):
    """Test global migration guidance and asset-specific plan endpoints."""
    res_global = client.get("/api/v1/migration")
    assert res_global.status_code == 200
    summary = res_global.get_json()["migration_summary"]
    assert "fips_standards" in summary
    assert len(summary["fips_standards"]) == 3

    asset = create_sample_asset(client, name="Migration Target", hostname="pqc.internal")
    res_plan = client.get(f"/api/v1/migration/assets/{asset['id']}")
    assert res_plan.status_code == 200
    plan = res_plan.get_json()["migration_plan"]
    assert plan["asset_id"] == asset["id"]
    assert "migration_phases" in plan
    assert "testing_checklist" in plan
