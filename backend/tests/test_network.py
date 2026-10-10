"""
Automated Unit and Integration Tests for Stage 3: Network MTU & Middlebox Verification.
Verifies verification profiles, SSRF & authorization protections, 3 test execution modes,
accurate diagnostic classifications, and evidence-based remediation recommendations.
"""

import pytest


def test_create_valid_network_profile(client):
    """Verify creating a valid network verification profile."""
    res = client.post(
        "/api/v1/network/profiles",
        json={
            "name": "lab-standard-mtu",
            "target_host": "127.0.0.1",
            "target_port": 443,
            "environment": "local_lab",
            "test_profile": "standard_mtu",
            "test_mode": "simulation",
            "expected_mtu": 1500,
        },
    )
    assert res.status_code == 201
    profile = res.get_json()["profile"]
    assert profile["name"] == "lab-standard-mtu"
    assert profile["test_mode"] == "simulation"
    assert profile["expected_mtu"] == 1500


def test_reject_unauthorized_external_target(client):
    """External target verification must be rejected without explicit authorization."""
    res = client.post(
        "/api/v1/network/profiles",
        json={
            "name": "unauthorized-external",
            "target_host": "scanme.nmap.org",
            "target_port": 443,
            "test_mode": "authorised_endpoint",
            "authorized_by_operator": False,
        },
    )
    assert res.status_code == 400
    assert "authorization is required" in res.get_json()["error"].lower()


def test_reject_ssrf_cloud_metadata_target(client):
    """Reject attempts to probe cloud metadata endpoints."""
    res = client.post(
        "/api/v1/network/profiles",
        json={
            "name": "ssrf-probe",
            "target_host": "169.254.169.254",
            "target_port": 80,
            "test_mode": "authorised_endpoint",
            "authorized_by_operator": True,
        },
    )
    assert res.status_code == 400
    assert "prohibited cloud metadata" in res.get_json()["error"].lower()


def test_mode_1_simulation_execution(client):
    """Verify Mode 1 deterministic simulation with oversized handshake (> 1.5 KB)."""
    res_prof = client.post(
        "/api/v1/network/profiles",
        json={
            "name": "sim-oversized-handshake",
            "test_profile": "standard_mtu",
            "test_mode": "simulation",
            "expected_mtu": 1500,
        },
    )
    profile_id = res_prof.get_json()["profile"]["id"]

    res_run = client.post(f"/api/v1/network/profiles/{profile_id}/run", json={})
    assert res_run.status_code == 200
    result = res_run.get_json()["result"]
    assert result["test_mode"] == "simulation"
    assert result["is_simulated"] is True
    assert result["diagnostic_classification"] == "SIMULATED"
    assert result["packet_size_estimate_bytes"] > 1500
    assert len(result["remediation_recommendations"]) >= 1
    assert "TCP segmentation" in result["diagnostic_finding"]


def test_mode_1_reduced_mtu_fragmentation_drop_simulation(client):
    """Verify Mode 1 simulation correctly flags packet drop under reduced MTU."""
    res_prof = client.post(
        "/api/v1/network/profiles",
        json={
            "name": "sim-reduced-mtu",
            "test_profile": "fragmentation_sensitive",
            "test_mode": "simulation",
            "expected_mtu": 1280,  # IPv6 minimum MTU / reduced tunnel
        },
    )
    profile_id = res_prof.get_json()["profile"]["id"]

    res_run = client.post(f"/api/v1/network/profiles/{profile_id}/run", json={})
    assert res_run.status_code == 200
    result = res_run.get_json()["result"]
    assert result["handshake_success"] is False
    assert result["diagnostic_classification"] == "FAIL"
    assert "Path MTU" in result["observed_error"]
    assert any("ICMP" in r for r in result["remediation_recommendations"])


def test_mode_2_local_loopback_connection_test(client):
    """
    Verify Mode 2 loopback test measures actual connection and does NOT
    falsely accuse a firewall when port is closed.
    """
    res_prof = client.post(
        "/api/v1/network/profiles",
        json={
            "name": "loopback-test",
            "target_host": "127.0.0.1",
            "target_port": 54321,  # Unused port
            "test_mode": "local_loopback",
        },
    )
    profile_id = res_prof.get_json()["profile"]["id"]

    res_run = client.post(f"/api/v1/network/profiles/{profile_id}/run", json={})
    assert res_run.status_code == 200
    result = res_run.get_json()["result"]
    assert result["test_mode"] == "local_loopback"
    assert result["is_simulated"] is False
    # Must report connection refused honestly without claiming a firewall caused it
    assert result["diagnostic_classification"] == "NOT_SUPPORTED"
    assert "Connection refused" in result["diagnostic_finding"]


def test_query_results_and_audit_trail(client):
    """Verify querying historical results and audit event recording."""
    res_prof = client.post(
        "/api/v1/network/profiles",
        json={
            "name": "audit-net-profile",
            "test_mode": "simulation",
        },
    )
    profile_id = res_prof.get_json()["profile"]["id"]
    client.post(f"/api/v1/network/profiles/{profile_id}/run", json={})

    # Query results endpoint
    res_results = client.get(f"/api/v1/network/results?profile_id={profile_id}")
    assert res_results.status_code == 200
    assert len(res_results.get_json()["results"]) >= 1

    # Verify audit event
    res_audit = client.get(f"/api/v1/audit/events?entity_id={profile_id}")
    assert res_audit.status_code == 200
    events = res_audit.get_json()["events"]
    assert any(e["action"] == "execute_verification" for e in events)
