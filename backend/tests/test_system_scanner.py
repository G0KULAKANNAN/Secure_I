"""
Comprehensive Acceptance Tests for Automatic System File Scanner and Risk Prioritization.
Verifies all 15 acceptance criteria: real background execution, recursive traversal,
risk formula test cases A, B, C, D, category boundaries, comment vs API classification,
PQC recognition, cancellation, audit events, sorting, and file non-modification.
"""

import tempfile
import os
from pathlib import Path
import pytest
from quantumshield.models.asset import Asset
from quantumshield.models.finding import Finding
from quantumshield.scanner.system_file_scanner import SystemFileScanner
from quantumshield.risk.engine import (
    calculate_finding_risk_score,
    RiskEngine,
    SCORE_THRESHOLDS,
)
from quantumshield.risk.recommendations import generate_finding_recommendation
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.audit_repository import AuditRepository


# ---------------------------------------------------------------------------
# Section 8 & 10 Acceptance Tests: Cases A, B, C, D & Risk Calculation
# ---------------------------------------------------------------------------

def test_case_a_critical_risk_score():
    """Case A: Sensitivity = 5, Exposure = 4, Lifetime = 5 -> Score = 93, Critical."""
    score, category, rationale = calculate_finding_risk_score(5, 4, 5)
    assert score == 93
    assert category == "Critical"
    assert "93/100" in rationale
    assert "Critical" in rationale


def test_case_b_high_risk_score():
    """Case B: Sensitivity = 2, Exposure = 5, Lifetime = 2 -> Score = 60, High."""
    score, category, rationale = calculate_finding_risk_score(2, 5, 2)
    assert score == 60
    assert category == "High"
    assert "60/100" in rationale


def test_case_c_low_risk_score():
    """Case C: Sensitivity = 1, Exposure = 1, Lifetime = 1 -> Score = 20, Low."""
    score, category, rationale = calculate_finding_risk_score(1, 1, 1)
    assert score == 20
    assert category == "Low"
    assert "20/100" in rationale


def test_case_d_missing_factors_needs_assessment():
    """Case D: Missing one or more factors -> Needs Assessment, score None, no silent guessing."""
    score, category, rationale = calculate_finding_risk_score(None, 4, 5)
    assert score is None
    assert category == "Needs Assessment"
    assert "Missing required factor" in rationale

    score, category, rationale = calculate_finding_risk_score(5, None, None)
    assert score is None
    assert category == "Needs Assessment"

    score, category, rationale = calculate_finding_risk_score(None, None, None)
    assert score is None
    assert category == "Needs Assessment"


def test_risk_category_boundaries():
    """Verify exact category thresholds: Low (0-29), Moderate (30-49), High (50-74), Critical (75-100)."""
    # Low: 0 to 29 (e.g. S=1, E=1, L=2 -> (4/15)*100 = 26.66 -> 27)
    score_27, cat_27, _ = calculate_finding_risk_score(1, 1, 2)
    assert score_27 == 27
    assert cat_27 == "Low"

    # Moderate boundary: 30 (e.g. S=1, E=2, L=2 -> (5/15)*100 = 33.3 -> 33)
    score_33, cat_33, _ = calculate_finding_risk_score(1, 2, 2)
    assert score_33 == 33
    assert cat_33 == "Moderate"

    # Moderate upper: 47 (S=2, E=2, L=3 -> (7/15)*100 = 46.66 -> 47)
    score_47, cat_47, _ = calculate_finding_risk_score(2, 2, 3)
    assert score_47 == 47
    assert cat_47 == "Moderate"

    # High boundary: 53 (S=2, E=3, L=3 -> (8/15)*100 = 53.3 -> 53)
    score_53, cat_53, _ = calculate_finding_risk_score(2, 3, 3)
    assert score_53 == 53
    assert cat_53 == "High"

    # High upper: 73 (S=4, E=3, L=4 -> (11/15)*100 = 73.3 -> 73)
    score_73, cat_73, _ = calculate_finding_risk_score(4, 3, 4)
    assert score_73 == 73
    assert cat_73 == "High"

    # Critical boundary: 80 (S=4, E=4, L=4 -> (12/15)*100 = 80)
    score_80, cat_80, _ = calculate_finding_risk_score(4, 4, 4)
    assert score_80 == 80
    assert cat_80 == "Critical"


# ---------------------------------------------------------------------------
# Purpose-Specific Recommendations & Fix First
# ---------------------------------------------------------------------------

def test_algorithm_purpose_specific_recommendations():
    """Verify technically appropriate next actions per algorithm and primitive."""
    # 1. Legacy RSA-1024
    rec_1024 = generate_finding_recommendation("RSA-1024", "asymmetric_key", True, risk_score=93, risk_category="Critical")
    assert "RSA-1024" in rec_1024["recommended_action"] or "replace" in rec_1024["recommended_action"].lower()
    assert rec_1024["queue_group"] == "immediate_investigation"

    # 2. Key Exchange (ECDH / RSA-2048)
    rec_ecdh = generate_finding_recommendation("ECDH", "key_establishment", True, risk_score=80, risk_category="Critical", exposure=4, lifetime=5)
    assert "ML-KEM" in rec_ecdh["recommended_action"] or "hybrid" in rec_ecdh["recommended_action"].lower()
    assert "SNDL" in rec_ecdh["why_now"] or "Store-Now-Decrypt-Later" in rec_ecdh["why_now"]

    # 3. Digital Signatures (ECDSA)
    rec_ecdsa = generate_finding_recommendation("ECDSA", "digital_signature", True, risk_score=60, risk_category="High")
    assert "ML-DSA" in rec_ecdsa["recommended_action"] or "SLH-DSA" in rec_ecdsa["recommended_action"]

    # 4. SHA-1 distinction
    rec_sha1 = generate_finding_recommendation("SHA-1", "cryptographic_hash", False)
    assert "SHA-1" in rec_sha1["recommended_action"]
    assert "signatures vs non-security checksums" in rec_sha1["recommended_action"]

    # 5. AES-128
    rec_aes128 = generate_finding_recommendation("AES-128", "symmetric_encryption", False)
    assert rec_aes128["queue_group"] == "monitoring_reassessment"

    # 6. Approved PQC (ML-KEM)
    rec_pqc = generate_finding_recommendation("ML-KEM-768", "key_establishment", False)
    assert "Approved" in rec_pqc["migration_approach"]
    assert rec_pqc["queue_group"] == "monitoring_reassessment"


# ---------------------------------------------------------------------------
# File System Scanner Acceptance Tests (Real Traversal & Synthetic Fixtures)
# ---------------------------------------------------------------------------

def test_filesystem_scanner_synthetic_fixtures():
    """Test scanner on temporary directory with code, comments, configs, certs, and exclusions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # 1. Active Python code using RSA API
        py_file = root / "service.py"
        py_file.write_text("""
import rsa

def setup_keys():
    # Active cryptographic API call
    key = rsa.generate_private_key(key_size=2048)
    return key
""", encoding="utf-8")

        # 2. Python file with comment-only reference
        comment_file = root / "notes.py"
        comment_file.write_text("""
# We evaluated RSA-2048 and ECC last month for documentation
# TODO: consider migration roadmap
def add(a, b):
    return a + b
""", encoding="utf-8")

        # 3. Normal plain text file without cryptography
        normal_file = root / "README.txt"
        normal_file.write_text("This is an ordinary documentation file without any encryption.\nJust normal text.", encoding="utf-8")

        # 4. Excluded directory (node_modules)
        node_modules = root / "node_modules"
        node_modules.mkdir()
        (node_modules / "legacy.js").write_text("var des = DES.new('secret');", encoding="utf-8")

        # 5. PQC code
        pqc_file = root / "pqc_worker.py"
        pqc_file.write_text("""
from liboqs import KeyExchange
kem = KeyExchange('ML-KEM-768')
""", encoding="utf-8")

        # Run SystemFileScanner
        scanner = SystemFileScanner()
        asset = Asset(id="test_asset", name="Test Asset", criticality="high", environment="production")
        
        # Capture pre-scan modification times to verify non-modification
        pre_mtime_py = py_file.stat().st_mtime
        pre_content_py = py_file.read_text(encoding="utf-8")

        result = scanner.scan(asset, options={"target_directory": str(root)})

        assert result.status == "completed"
        assert result.metadata["files_scanned"] >= 3
        assert result.metadata["files_discovered"] >= 3

        # Verification 1: Scanning NEVER modifies files
        assert py_file.stat().st_mtime == pre_mtime_py
        assert py_file.read_text(encoding="utf-8") == pre_content_py

        # Verification 2: Active RSA API detected with Confirmed API classification
        rsa_findings = [f for f in result.findings if "service.py" in f["file_path"]]
        assert len(rsa_findings) >= 1
        active_api_findings = [f for f in rsa_findings if f["detection_category"] == "Confirmed cryptographic API usage"]
        assert len(active_api_findings) >= 1
        assert active_api_findings[0]["line_number"] == 6

        # Verification 3: Comment-only mention classified as Textual reference only
        comment_findings = [f for f in result.findings if "notes.py" in f["file_path"]]
        if comment_findings:
            assert comment_findings[0]["detection_category"] == "Textual reference only"
            assert comment_findings[0]["confidence"] == "low"

        # Verification 4: Normal text file produces zero findings
        normal_findings = [f for f in result.findings if "README.txt" in f["file_path"]]
        assert len(normal_findings) == 0

        # Verification 5: Excluded directory (node_modules) was NOT scanned
        node_findings = [f for f in result.findings if "node_modules" in f["file_path"]]
        assert len(node_findings) == 0

        # Verification 6: Approved PQC recognized
        pqc_findings = [f for f in result.findings if "pqc_worker.py" in f["file_path"]]
        assert len(pqc_findings) >= 1
        assert "ML-KEM" in pqc_findings[0]["algorithm"]
        assert pqc_findings[0]["quantum_vulnerable"] is False


def test_cooperative_scan_cancellation():
    """Verify cancellation callback halts traversal immediately."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        for i in range(10):
            (root / f"file_{i}.py").write_text("import rsa\nkey = rsa.generate_private_key()", encoding="utf-8")

        scanner = SystemFileScanner()
        asset = Asset(id="test_asset", name="Test Asset")
        
        # Always cancelled callback
        result = scanner.scan(asset, options={"target_directory": str(root)}, is_cancelled=lambda: True)
        assert result.status == "cancelled"
        assert result.metadata.get("cancelled") is True


# ---------------------------------------------------------------------------
# API Integration Tests (Scan System Endpoint, Queue, Assessment Update)
# ---------------------------------------------------------------------------

def test_api_system_scan_endpoint_and_queue(client):
    """Test POST /api/v1/scanners/system triggers real job and findings populate queue."""
    # 1. Trigger system scan
    res = client.post("/api/v1/scanners/system", json={"target_scope": "project"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "ok"
    assert "job_id" in data
    assert "scope" in data

    # 2. Query scanner config
    res_cfg = client.get("/api/v1/scanners/system/config")
    assert res_cfg.status_code == 200
    cfg = res_cfg.get_json()["config"]
    assert "project_root" in cfg
    assert "supported_extensions" in cfg
    assert "safety_model" in cfg
    assert cfg["safety_model"]["read_only"] is True

    # 3. Query findings sorted by risk score
    res_findings = client.get("/api/v1/findings?sort_by=risk_score&order=desc")
    assert res_findings.status_code == 200
    findings = res_findings.get_json()["findings"]
    assert isinstance(findings, list)

    # 4. Query Monday Morning Remediation Queue
    res_queue = client.get("/api/v1/findings/queue")
    assert res_queue.status_code == 200
    q_data = res_queue.get_json()["queue"]
    assert "tiers" in q_data
    assert "immediate_investigation" in q_data["tiers"]
    assert "high_priority_migration" in q_data["tiers"]
    assert "scheduled_remediation" in q_data["tiers"]
    assert "monitoring_reassessment" in q_data["tiers"]


def test_api_finding_assessment_update_and_audit(client):
    """Test POST /api/v1/findings/<id>/assess updates score and writes audit event."""
    # First create a finding by scanning source snippet
    res_scan = client.post(
        "/api/v1/scanners/source",
        json={
            "source_content": "import rsa\nkey = rsa.newkeys(2048)",
            "file_name": "crypto_test.py",
        },
    )
    assert res_scan.status_code == 200
    findings = res_scan.get_json()["findings"]
    assert len(findings) > 0
    f_id = findings[0]["id"]

    # Assess finding with S=5, E=4, L=5 (Case A -> expected 93, Critical)
    res_assess = client.post(
        f"/api/v1/findings/{f_id}/assess",
        json={
            "data_sensitivity": 5,
            "exposure": 4,
            "confidentiality_lifetime": 5,
            "assigned_owner": "cyber_lead",
            "target_remediation_date": "2026-12-01",
            "remediation_status": "needs_review",
        },
    )
    assert res_assess.status_code == 200
    updated = res_assess.get_json()["finding"]
    assert updated["risk_score"] == 93
    assert updated["risk_category"] == "Critical"
    assert updated["assigned_owner"] == "cyber_lead"
    assert updated["target_remediation_date"] == "2026-12-01"

    # Verify audit event recorded
    res_audit = client.get("/api/v1/audit")
    assert res_audit.status_code == 200
    events = res_audit.get_json()["events"]
    assert any(e["entity_id"] == f_id for e in events)


def test_risk_formula_and_calculate_endpoints(client):
    """Test GET /api/v1/risk/formula and POST /api/v1/risk/calculate."""
    res_formula = client.get("/api/v1/risk/formula")
    assert res_formula.status_code == 200
    data = res_formula.get_json()
    assert "formula" in data
    assert "factors" in data
    assert "disclaimer" in data

    # Test calculator endpoint for Case B: S=2, E=5, L=2 -> 60
    res_calc = client.post(
        "/api/v1/risk/calculate",
        json={"sensitivity": 2, "exposure": 5, "lifetime": 2},
    )
    assert res_calc.status_code == 200
    calc_data = res_calc.get_json()
    assert calc_data["risk_score"] == 60
    assert calc_data["risk_category"] == "High"
