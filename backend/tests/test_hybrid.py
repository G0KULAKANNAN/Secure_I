"""
Automated Unit and Integration Tests for Stage 2: Hybrid Cryptography in Staging.
Verifies capability registry, staging profile management, test simulation vs real TLS distinction,
approval gating, rollback workflows, and immutable audit logging.
"""

import pytest


def test_get_crypto_capabilities_and_host_provider(client):
    """Verify capabilities registry returns seeded standards and real host provider status."""
    res = client.get("/api/v1/hybrid/capabilities")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "host_provider" in data
    assert "openssl_version" in data["host_provider"]
    assert "supports_native_hybrid" in data["host_provider"]
    assert isinstance(data["capabilities"], list)
    assert len(data["capabilities"]) >= 3

    combinations = [c["hybrid_combination"] for c in data["capabilities"]]
    assert "X25519MLKEM768" in combinations
    assert "SecP256r1MLKEM768" in combinations


def test_create_valid_hybrid_staging_profile(client):
    """Verify creating a valid hybrid staging profile."""
    res = client.post(
        "/api/v1/hybrid/profiles",
        json={
            "profile_name": "staging-edge-hybrid",
            "classical_component": "X25519",
            "pqc_component": "ML-KEM-768",
            "operator": "security_engineer",
        },
    )
    assert res.status_code == 201
    profile = res.get_json()["profile"]
    assert profile["profile_name"] == "staging-edge-hybrid"
    assert profile["classical_component"] == "X25519"
    assert profile["pqc_component"] == "ML-KEM-768"
    assert profile["environment"] == "staging"
    assert profile["migration_state"] == "CONFIGURED"
    assert profile["rollout_status"] == "disabled"
    assert profile["automatic_production_prohibited"] is True


def test_reject_duplicate_profile_name(client):
    """Reject duplicate profile names with 409 Conflict."""
    client.post(
        "/api/v1/hybrid/profiles",
        json={"profile_name": "unique-profile"},
    )
    res2 = client.post(
        "/api/v1/hybrid/profiles",
        json={"profile_name": "unique-profile"},
    )
    assert res2.status_code == 409


def test_reject_unsupported_hybrid_components(client):
    """Reject invalid classical or PQC algorithm configurations."""
    # Invalid classical group
    res1 = client.post(
        "/api/v1/hybrid/profiles",
        json={
            "profile_name": "bad-classical",
            "classical_component": "RSA-512-INSECURE",
            "pqc_component": "ML-KEM-768",
        },
    )
    assert res1.status_code == 400
    assert "unsupported classical component" in res1.get_json()["error"].lower()

    # Invalid PQC algorithm
    res2 = client.post(
        "/api/v1/hybrid/profiles",
        json={
            "profile_name": "bad-pqc",
            "classical_component": "X25519",
            "pqc_component": "UNKNOWN-PQC-ALGO",
        },
    )
    assert res2.status_code == 400
    assert "unsupported pqc component" in res2.get_json()["error"].lower()


def test_real_tls_mode_reports_unsupported_on_standard_ssl(client):
    """
    When real_tls mode is requested and host OpenSSL lacks native hybrid support,
    must report limitation accurately without faking success or silently downgrading.
    """
    res_prof = client.post(
        "/api/v1/hybrid/profiles",
        json={"profile_name": "real-tls-eval"},
    )
    profile_id = res_prof.get_json()["profile"]["id"]

    res_test = client.post(
        f"/api/v1/hybrid/profiles/{profile_id}/test",
        json={"test_mode": "real_tls"},
    )
    assert res_test.status_code == 200
    run = res_test.get_json()["verification_run"]
    assert run["test_mode"] == "real_tls"
    assert run["status"] == "unsupported"
    assert run["is_simulated"] is False
    assert "lacks native" in run["negotiation_outcome"]


def test_simulated_interoperability_test_and_approval_workflow(client):
    """
    Verify complete staging workflow:
    CONFIGURED -> TESTING -> VERIFIED -> APPROVED -> ROLLBACK.
    """
    # 1. Create profile
    res_prof = client.post(
        "/api/v1/hybrid/profiles",
        json={"profile_name": "full-lifecycle-profile"},
    )
    profile_id = res_prof.get_json()["profile"]["id"]

    # 2. Cannot approve unverified profile
    res_bad_app = client.post(
        f"/api/v1/hybrid/profiles/{profile_id}/approve",
        json={"approved_by": "qa_lead"},
    )
    assert res_bad_app.status_code == 400
    assert "must be verified" in res_bad_app.get_json()["error"].lower()

    # 3. Execute simulation test
    res_test = client.post(
        f"/api/v1/hybrid/profiles/{profile_id}/test",
        json={"test_mode": "simulation"},
    )
    assert res_test.status_code == 200
    run = res_test.get_json()["verification_run"]
    assert run["status"] == "passed"
    assert run["is_simulated"] is True
    assert run["classical_client_compatible"] is True
    assert run["hybrid_client_compatible"] is True

    # Check profile state is now VERIFIED
    res_get = client.get(f"/api/v1/hybrid/profiles/{profile_id}")
    assert res_get.get_json()["profile"]["migration_state"] == "VERIFIED"

    # 4. Approve verified profile
    res_app = client.post(
        f"/api/v1/hybrid/profiles/{profile_id}/approve",
        json={"approved_by": "qa_lead"},
    )
    assert res_app.status_code == 200
    approved_prof = res_app.get_json()["profile"]
    assert approved_prof["migration_state"] == "APPROVED"
    assert approved_prof["rollout_status"] == "enabled"
    assert approved_prof["approved_by"] == "qa_lead"
    assert approved_prof["approved_at"] is not None

    # 5. Rollback restores previous configuration and disables rollout
    res_rb = client.post(
        f"/api/v1/hybrid/profiles/{profile_id}/rollback",
        json={"operator": "admin"},
    )
    assert res_rb.status_code == 200
    rolled_back = res_rb.get_json()["profile"]
    assert rolled_back["migration_state"] == "CONFIGURED"
    assert rolled_back["rollout_status"] == "disabled"
    assert rolled_back["approved_by"] is None

    # 6. Verify audit trail recorded all events
    res_aud = client.get(f"/api/v1/audit/events?entity_id={profile_id}")
    assert res_aud.status_code == 200
    events = res_aud.get_json()["events"]
    actions = [e["action"] for e in events]
    assert "create_profile" in actions
    assert "verify_interoperability" in actions
    assert "approve_profile" in actions
    assert "rollback_profile" in actions
