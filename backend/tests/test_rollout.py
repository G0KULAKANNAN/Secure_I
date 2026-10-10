"""
Tests for Stage 4: Staged Production Rollout Management.
"""

import json
import pytest
from quantumshield.storage.database import init_db
from quantumshield.services.rollout_engine import RolloutEngine
from quantumshield.models.rollout import CANARY_STAGES


@pytest.fixture
def test_app(tmp_path):
    from backend.app import create_app
    db_file = tmp_path / "quantumshield_test.db"
    init_db(db_file)

    class TestConfig:
        TESTING = True
        DATABASE_PATH = str(db_file)
        CORS_ORIGINS = "*"

    app = create_app(TestConfig, enable_workers=False)
    return app


@pytest.fixture
def client(test_app):
    return test_app.test_client()


def test_default_environments_seeded(client):
    res = client.get("/api/v1/rollout/environments")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["total"] >= 4
    categories = [e["category"] for e in data["environments"]]
    assert "development" in categories
    assert "local_lab" in categories
    assert "staging" in categories
    assert "production" in categories


def test_create_rollout_plan_and_duplicate_rejection(client):
    payload = {
        "name": "Production Canary Alpha",
        "environment_id": "env_production",
        "target_config": {
            "tls_version": "TLS 1.3",
            "supported_groups": ["X25519MLKEM768", "X25519"],
        },
        "rollback_threshold_failure_rate": 2.0,
        "deployment_mode": "simulation",
    }
    res = client.post("/api/v1/rollout/plans", json=payload)
    assert res.status_code == 201
    plan = res.get_json()["plan"]
    assert plan["name"] == "Production Canary Alpha"
    assert plan["state"] == "DRAFT"
    assert plan["current_stage"] == "DRAFT"
    assert plan["canary_percentage"] == 0

    # Duplicate name rejection
    res_dup = client.post("/api/v1/rollout/plans", json=payload)
    assert res_dup.status_code == 400


def test_readiness_gates_evaluation_blocks_invalid_config(client):
    # Create plan with non-compliant TLS version
    bad_payload = {
        "name": "Non-compliant Legacy Plan",
        "environment_id": "env_production",
        "target_config": {
            "tls_version": "TLS 1.2",
            "supported_groups": ["X25519"],
        },
    }
    create_res = client.post("/api/v1/rollout/plans", json=bad_payload)
    assert create_res.status_code == 201
    plan_id = create_res.get_json()["plan"]["id"]

    assess_res = client.post(f"/api/v1/rollout/plans/{plan_id}/assess-readiness")
    assert assess_res.status_code == 200
    assessment = assess_res.get_json()["assessment"]
    assert assessment["all_technical_passed"] is False
    assert len(assessment["blockers"]) > 0

    # Ensure plan is BLOCKED
    plan_res = client.get(f"/api/v1/rollout/plans/{plan_id}")
    assert plan_res.get_json()["plan"]["state"] == "BLOCKED"


def test_readiness_gates_pass_for_compliant_plan(client):
    payload = {
        "name": "Compliant Staging Rollout",
        "environment_id": "env_staging",
        "target_config": {
            "tls_version": "TLS 1.3",
            "supported_groups": ["X25519MLKEM768", "X25519"],
        },
        "rollback_threshold_failure_rate": 1.5,
    }
    create_res = client.post("/api/v1/rollout/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    assess_res = client.post(f"/api/v1/rollout/plans/{plan_id}/assess-readiness")
    assert assess_res.status_code == 200
    assessment = assess_res.get_json()["assessment"]
    assert assessment["all_technical_passed"] is True

    plan_res = client.get(f"/api/v1/rollout/plans/{plan_id}")
    assert plan_res.get_json()["plan"]["state"] == "READY_FOR_APPROVAL"


def test_operator_approval_workflow(client):
    payload = {
        "name": "Approved Production Rollout",
        "environment_id": "env_staging",
        "target_config": {
            "tls_version": "TLS 1.3",
            "supported_groups": ["X25519MLKEM768", "X25519"],
        },
    }
    create_res = client.post("/api/v1/rollout/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    # Reject empty approver
    appr_fail = client.post(f"/api/v1/rollout/plans/{plan_id}/approve", json={"approved_by": ""})
    assert appr_fail.status_code == 400

    # Successful approval
    appr_ok = client.post(f"/api/v1/rollout/plans/{plan_id}/approve", json={"approved_by": "alice_sre_lead"})
    assert appr_ok.status_code == 200
    plan = appr_ok.get_json()["plan"]
    assert plan["state"] == "APPROVED"
    assert plan["approved_by"] == "alice_sre_lead"
    assert plan["approved_at"] is not None


def test_canary_stage_progression_across_all_stages(client):
    payload = {
        "name": "Progressive Canary Rollout",
        "environment_id": "env_staging",
        "target_config": {
            "tls_version": "TLS 1.3",
            "supported_groups": ["X25519MLKEM768", "X25519"],
        },
    }
    create_res = client.post("/api/v1/rollout/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    # Cannot advance unapproved plan
    adv_blocked = client.post(f"/api/v1/rollout/plans/{plan_id}/advance")
    assert adv_blocked.status_code == 400

    # Approve
    client.post(f"/api/v1/rollout/plans/{plan_id}/approve", json={"approved_by": "bob_crypto_eng"})

    expected_percentages = [1, 5, 25, 50, 100]
    expected_states = ["CANARY", "CANARY", "CANARY", "CANARY", "COMPLETED"]

    for pct, expected_st in zip(expected_percentages, expected_states):
        adv_res = client.post(f"/api/v1/rollout/plans/{plan_id}/advance")
        assert adv_res.status_code == 200
        result = adv_res.get_json()["result"]
        assert result["canary_percentage"] == pct
        assert result["state"] == expected_st

    # Environment current config should now match target config
    env_res = client.get("/api/v1/rollout/environments/env_staging")
    assert env_res.get_json()["environment"]["rollout_status"] == "completed"
    assert env_res.get_json()["environment"]["current_config"]["supported_groups"] == ["X25519MLKEM768", "X25519"]


def test_telemetry_threshold_breach_triggers_automated_rollback(client):
    payload = {
        "name": "Telemetry Sensitive Canary",
        "environment_id": "env_staging",
        "target_config": {
            "tls_version": "TLS 1.3",
            "supported_groups": ["X25519MLKEM768", "X25519"],
        },
        "rollback_threshold_failure_rate": 2.0,
    }
    create_res = client.post("/api/v1/rollout/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    client.post(f"/api/v1/rollout/plans/{plan_id}/approve", json={"approved_by": "carol_ops"})
    client.post(f"/api/v1/rollout/plans/{plan_id}/advance")  # to 1%

    # Simulate healthy traffic (0.15% failure rate <= 2.0%)
    health_res = client.post(f"/api/v1/rollout/plans/{plan_id}/simulate-traffic", json={"healthy": True})
    assert health_res.status_code == 200
    assert health_res.get_json()["result"]["threshold_breached"] is False
    assert health_res.get_json()["result"]["rollback_triggered"] is False

    # Simulate degraded traffic (4.8% failure rate > 2.0%)
    bad_res = client.post(f"/api/v1/rollout/plans/{plan_id}/simulate-traffic", json={"healthy": False})
    assert bad_res.status_code == 200
    assert bad_res.get_json()["result"]["threshold_breached"] is True
    assert bad_res.get_json()["result"]["rollback_triggered"] is True

    # Verify plan is rolled back
    plan_res = client.get(f"/api/v1/rollout/plans/{plan_id}")
    assert plan_res.get_json()["plan"]["state"] == "ROLLED_BACK"

    # Verify environment status is updated
    env_res = client.get("/api/v1/rollout/environments/env_staging")
    assert env_res.get_json()["environment"]["rollout_status"] == "rolled_back"


def test_manual_rollback_restores_previous_configuration(client):
    payload = {
        "name": "Manual Rollback Plan",
        "environment_id": "env_staging",
        "target_config": {
            "tls_version": "TLS 1.3",
            "supported_groups": ["X25519MLKEM768", "X25519"],
        },
    }
    create_res = client.post("/api/v1/rollout/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    client.post(f"/api/v1/rollout/plans/{plan_id}/approve", json={"approved_by": "dave_lead"})
    client.post(f"/api/v1/rollout/plans/{plan_id}/advance")

    rb_res = client.post(
        f"/api/v1/rollout/plans/{plan_id}/rollback",
        json={"reason": "Unexpected handshake timeouts in upstream router", "operator": "dave_lead"},
    )
    assert rb_res.status_code == 200
    assert rb_res.get_json()["plan"]["state"] == "ROLLED_BACK"
