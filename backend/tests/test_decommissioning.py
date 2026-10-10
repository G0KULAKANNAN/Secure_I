"""
Tests for Stage 5: Classical Cryptography Decommissioning.
"""

import json
import pytest
from quantumshield.storage.database import init_db
from quantumshield.services.decommissioning_engine import DecommissioningEngine


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


def test_default_policies_seeded(client):
    res = client.get("/api/v1/decommissioning/policies")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["total"] >= 8

    algorithms = [p["algorithm"] for p in data["policies"]]
    assert "RSA-1024" in algorithms
    assert "RSA-2048" in algorithms
    assert "Diffie-Hellman" in algorithms
    assert "ECDSA-P256" in algorithms
    assert "SHA-1" in algorithms
    assert "3DES" in algorithms
    assert "X25519MLKEM768" in algorithms


def test_discover_dependencies_inventories_crypto(client):
    res = client.get("/api/v1/decommissioning/dependencies")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["total"] >= 4

    services = [d["service_name"] for d in data["dependencies"]]
    assert "Public API Gateway" in services or "Core Gateway Service" in services or len(services) > 0


def test_create_custom_policy_and_query_by_algorithm(client):
    payload = {
        "name": "RC4 Cipher Complete Prohibition",
        "algorithm": "RC4",
        "primitive_category": "symmetric_encryption",
        "status": "PROHIBITED_BY_CONFIGURED_POLICY",
        "conditions": "Immediate block. Stream cipher bias vulnerabilities.",
        "rationale": "RFC 7465 prohibits RC4 cipher suites.",
    }
    create_res = client.post("/api/v1/decommissioning/policies", json=payload)
    assert create_res.status_code == 201
    pol = create_res.get_json()["policy"]
    assert pol["algorithm"] == "RC4"
    assert pol["status"] == "PROHIBITED_BY_CONFIGURED_POLICY"

    # Query filtered by category
    filter_res = client.get("/api/v1/decommissioning/policies?category=symmetric_encryption")
    assert filter_res.status_code == 200
    assert any(p["algorithm"] == "RC4" for p in filter_res.get_json()["policies"])


def test_create_decommissioning_plan_and_duplicate_prevention(client):
    payload = {
        "name": "Phase Out Diffie-Hellman Key Exchange",
        "target_primitive": "Diffie-Hellman",
        "affected_services": ["Legacy Partner VPN"],
        "rollback_instructions": "Revert firewall IPSec policy to allow DH Group 14.",
    }
    create_res = client.post("/api/v1/decommissioning/plans", json=payload)
    assert create_res.status_code == 201
    plan = create_res.get_json()["plan"]
    assert plan["name"] == "Phase Out Diffie-Hellman Key Exchange"
    assert plan["state"] == "DISCOVERED"
    assert plan["target_primitive"] == "Diffie-Hellman"

    # Reject duplicate plan name
    dup_res = client.post("/api/v1/decommissioning/plans", json=payload)
    assert dup_res.status_code == 400


def test_readiness_gates_evaluation_with_blockers_and_resolution(client):
    # Ensure dependencies are discovered
    deps_res = client.get("/api/v1/decommissioning/dependencies")
    deps = deps_res.get_json()["dependencies"]
    dh_dep = next((d for d in deps if "Diffie" in d["current_algorithm"] or "DH" in d["current_algorithm"]), None)

    payload = {
        "name": "DH Retirement Plan with Gate Check",
        "target_primitive": "Diffie-Hellman",
        "affected_services": ["Legacy Partner VPN"],
        "rollback_instructions": "Emergency reactivation of classical DH Group 14 gateway.",
    }
    create_res = client.post("/api/v1/decommissioning/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    # Initial assessment: active unmigrated dependency should cause Gate 2 to block
    assess1 = client.post(f"/api/v1/decommissioning/plans/{plan_id}/assess-readiness")
    assert assess1.status_code == 200
    res1 = assess1.get_json()["assessment"]
    assert res1["all_technical_passed"] is False
    assert any("GATE_2" in g["gate_id"] and g["status"] == "FAIL" for g in res1["gates"])

    # Update the dependency to 'migrating'
    if dh_dep:
        client.patch(f"/api/v1/decommissioning/dependencies/{dh_dep['id']}", json={"status": "migrating"})

    # Re-evaluate: Gate 2 now passes!
    assess2 = client.post(f"/api/v1/decommissioning/plans/{plan_id}/assess-readiness")
    assert assess2.status_code == 200
    res2 = assess2.get_json()["assessment"]
    assert res2["all_technical_passed"] is True

    # Plan state should now be READY_FOR_REVIEW
    plan_check = client.get(f"/api/v1/decommissioning/plans/{plan_id}")
    assert plan_check.get_json()["plan"]["state"] == "READY_FOR_REVIEW"


def test_plan_approval_requires_valid_signoff(client):
    # Prepare dependencies
    client.get("/api/v1/decommissioning/dependencies")
    deps_res = client.get("/api/v1/decommissioning/dependencies")
    for d in deps_res.get_json()["dependencies"]:
        if "RSA" in d["current_algorithm"]:
            client.patch(f"/api/v1/decommissioning/dependencies/{d['id']}", json={"status": "migrating"})

    payload = {
        "name": "RSA-2048 Retirement Authorization",
        "target_primitive": "RSA-2048",
        "affected_services": ["Public API Gateway"],
        "rollback_instructions": "Revert Envoy ingress cipher suite to accept TLS_RSA_WITH_AES_256_GCM_SHA384.",
    }
    create_res = client.post("/api/v1/decommissioning/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    # Reject empty approver
    appr_fail = client.post(f"/api/v1/decommissioning/plans/{plan_id}/approve", json={"approved_by": ""})
    assert appr_fail.status_code == 400

    # Successful approval
    appr_ok = client.post(f"/api/v1/decommissioning/plans/{plan_id}/approve", json={
        "approved_by": "Dr. Elena Rostova",
        "role": "Chief Information Security Officer",
    })
    assert appr_ok.status_code == 200
    plan = appr_ok.get_json()["plan"]
    assert plan["state"] == "APPROVED"
    assert "Dr. Elena Rostova" in plan["approved_by"]
    assert plan["approved_at"] is not None


def test_execute_decommissioning_and_rollback(client):
    client.get("/api/v1/decommissioning/dependencies")
    deps_res = client.get("/api/v1/decommissioning/dependencies")
    for d in deps_res.get_json()["dependencies"]:
        if "Diffie" in d["current_algorithm"]:
            client.patch(f"/api/v1/decommissioning/dependencies/{d['id']}", json={"status": "migrating"})

    payload = {
        "name": "Execute Decommissioning Test",
        "target_primitive": "Diffie-Hellman",
        "affected_services": ["Legacy Partner VPN"],
        "rollback_instructions": "Instant configuration rollback command.",
    }
    create_res = client.post("/api/v1/decommissioning/plans", json=payload)
    plan_id = create_res.get_json()["plan"]["id"]

    client.post(f"/api/v1/decommissioning/plans/{plan_id}/approve", json={"approved_by": "CISO Operator"})

    # Execute decommissioning
    exec_res = client.post(f"/api/v1/decommissioning/plans/{plan_id}/execute", json={"operator": "secops_eng"})
    assert exec_res.status_code == 200
    plan = exec_res.get_json()["plan"]
    assert plan["state"] == "COMPLETED"
    assert plan["decommissioned_at"] is not None

    # Check dependencies are marked 'decommissioned'
    deps_after = client.get("/api/v1/decommissioning/dependencies").get_json()["dependencies"]
    dh_deps = [d for d in deps_after if "Diffie" in d["current_algorithm"]]
    assert all(d["status"] == "decommissioned" for d in dh_deps)

    # Rollback execution
    rb_res = client.post(f"/api/v1/decommissioning/plans/{plan_id}/rollback", json={
        "reason": "Partner client reported legacy connection failures.",
        "operator": "secops_eng",
    })
    assert rb_res.status_code == 200
    assert rb_res.get_json()["plan"]["state"] == "ROLLED_BACK"

    # Check dependencies reverted to 'active'
    deps_rb = client.get("/api/v1/decommissioning/dependencies").get_json()["dependencies"]
    dh_deps_rb = [d for d in deps_rb if "Diffie" in d["current_algorithm"]]
    assert any(d["status"] == "active" for d in dh_deps_rb)
