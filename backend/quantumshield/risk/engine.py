"""
Explainable Risk Assessment Scoring Engine.
Implements the QuantumShield Project Risk-Prioritization Model for both individual findings
and aggregated inventory assets using transparent mathematical formulas.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from quantumshield.models.asset import Asset
from quantumshield.models.finding import Finding
from quantumshield.storage.repositories import AssetRepository
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.scan_repository import ScanRepository
from quantumshield.risk.recommendations import generate_finding_recommendation


# Configurable Model Metadata & Thresholds
MODEL_VERSION = "QS-PRIORITY-V1"
MODEL_DISCLAIMER = "QuantumShield Project Risk-Prioritization Model (Non-NIST / Operational Engineering Guidance)"

SCORE_THRESHOLDS = {
    "low": (0, 29),
    "moderate": (30, 49),
    "high": (50, 74),
    "critical": (75, 100),
}


def calculate_finding_risk_score(
    sensitivity: Optional[int],
    exposure: Optional[int],
    lifetime: Optional[int],
) -> Tuple[Optional[int], str, str]:
    """
    Calculate explainable risk score:
        Risk Score = round(((S + E + L) / 15) * 100)
    
    Returns:
        (score, category, rationale)
    If any factor is missing (None), returns (None, 'Needs Assessment', rationale).
    """
    if sensitivity is None or exposure is None or lifetime is None:
        missing = []
        if sensitivity is None:
            missing.append("Data Sensitivity (S: 1-5)")
        if exposure is None:
            missing.append("Exposure (E: 1-5)")
        if lifetime is None:
            missing.append("Confidentiality Lifetime (L: 1-5)")
        
        rationale = (
            f"Needs Assessment: Missing required factor(s) [{', '.join(missing)}]. "
            "QuantumShield does not invent business context. Please provide all three factors to calculate an explainable risk score."
        )
        return None, "Needs Assessment", rationale

    # Validate factor bounds 1 to 5
    try:
        s = max(1, min(5, int(sensitivity)))
        e = max(1, min(5, int(exposure)))
        l = max(1, min(5, int(lifetime)))
    except (ValueError, TypeError):
        return None, "Needs Assessment", "Invalid factor values. Each factor must be an integer from 1 to 5."

    # Formula: ((S + E + L) / 15) * 100
    raw_score = ((s + e + l) / 15.0) * 100.0
    score = int(round(raw_score))

    # Determine risk category
    if score >= SCORE_THRESHOLDS["critical"][0]:
        category = "Critical"
    elif score >= SCORE_THRESHOLDS["high"][0]:
        category = "High"
    elif score >= SCORE_THRESHOLDS["moderate"][0]:
        category = "Moderate"
    else:
        category = "Low"

    rationale = (
        f"Score {score}/100 ({category}) calculated using {MODEL_VERSION}: "
        f"round((({s} + {e} + {l}) / 15) * 100). "
        f"Factors: Data Sensitivity={s}/5, Exposure={e}/5, Confidentiality Lifetime={l}/5."
    )

    return score, category, rationale


class RiskEngine:
    """Deterministic, transparent risk evaluation engine."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path
        self.asset_repo = AssetRepository(db_path)
        self.finding_repo = FindingRepository(db_path)
        self.scan_repo = ScanRepository(db_path)

    # -------------------------------------------------------------
    # Finding-Level Explainable Risk Assessment
    # -------------------------------------------------------------
    def assess_finding(
        self,
        finding: Finding,
        sensitivity_override: Optional[int] = None,
        exposure_override: Optional[int] = None,
        lifetime_override: Optional[int] = None,
    ) -> Finding:
        """
        Evaluate explainable risk score, category, and purpose-specific recommendations
        for an individual finding.
        """
        s = sensitivity_override if sensitivity_override is not None else finding.data_sensitivity
        e = exposure_override if exposure_override is not None else finding.exposure
        l = lifetime_override if lifetime_override is not None else finding.confidentiality_lifetime

        score, category, rationale = calculate_finding_risk_score(s, e, l)

        finding.data_sensitivity = s
        finding.exposure = e
        finding.confidentiality_lifetime = l
        finding.risk_score = score
        finding.risk_category = category
        finding.score_rationale = rationale
        finding.model_version = MODEL_VERSION
        finding.assessment_status = "assessed" if score is not None else "needs_assessment"

        # Generate recommendation and queue grouping
        rec = generate_finding_recommendation(
            algorithm=finding.algorithm,
            primitive=finding.cryptographic_primitive,
            quantum_vulnerable=finding.quantum_vulnerable,
            risk_score=score,
            risk_category=category,
            sensitivity=s,
            exposure=e,
            lifetime=l,
            detection_category=finding.detection_category,
            file_path=finding.file_path,
        )

        finding.recommended_action = rec["recommended_action"]
        finding.migration_approach = rec["migration_approach"]
        finding.queue_group = rec["queue_group"]

        return finding

    # -------------------------------------------------------------
    # Asset-Level Explainable Risk Assessment (Preserved for compatibility)
    # -------------------------------------------------------------
    def assess_asset(self, asset_id: str) -> Dict[str, Any]:
        """Calculate explainable risk score for an asset."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found.")

        findings, total_findings = self.finding_repo.list_findings(asset_id=asset_id, limit=100)

        if total_findings == 0:
            return {
                "asset_id": asset.id,
                "asset_name": asset.name,
                "status": "needs_assessment",
                "risk_score": None,
                "risk_level": "Needs assessment",
                "formula": "R = 20 * (0.35C + 0.30S + 0.25L + 0.10E)",
                "explanation": "Asset has not yet undergone cryptographic scanning. Assessment required before assigning a risk rating.",
                "factors": {
                    "C": {"value": None, "weight": 0.35, "name": "Cryptographic Exposure", "detail": "Pending scan execution"},
                    "S": {"value": self._calculate_sensitivity(asset), "weight": 0.30, "name": "Data Sensitivity", "detail": f"Based on '{asset.criticality}' criticality"},
                    "L": {"value": self._calculate_lifetime(asset), "weight": 0.25, "name": "Confidentiality Lifetime", "detail": f"Based on '{asset.environment}' environment"},
                    "E": {"value": self._calculate_exposure(asset), "weight": 0.10, "name": "Internet Exposure", "detail": f"Based on '{asset.asset_type}' asset type"},
                },
                "findings_count": 0,
                "quantum_vulnerable_count": 0,
            }

        # 1. Cryptographic Exposure Factor C (1 to 5)
        c_val, c_detail = self._calculate_crypto_exposure(findings)

        # 2. Data Sensitivity Factor S (1 to 5)
        s_val = self._calculate_sensitivity(asset)
        s_detail = f"Derived from business criticality: {asset.criticality}"

        # 3. Confidentiality Lifetime Factor L (1 to 5)
        l_val = self._calculate_lifetime(asset)
        l_detail = f"Derived from operational environment: {asset.environment}"

        # 4. Internet Exposure Factor E (1 to 5)
        e_val = self._calculate_exposure(asset)
        e_detail = f"Derived from asset type ({asset.asset_type}) and networking"

        # Formula: R = 20 * (0.35C + 0.30S + 0.25L + 0.10E)
        raw_score = 20.0 * (0.35 * c_val + 0.30 * s_val + 0.25 * l_val + 0.10 * e_val)
        risk_score = round(min(100.0, max(0.0, raw_score)), 1)

        # Categorize
        if risk_score >= 80.0:
            risk_level = "Critical"
        elif risk_score >= 60.0:
            risk_level = "High"
        elif risk_score >= 40.0:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        qv_count = sum(1 for f in findings if f.quantum_vulnerable)
        explanation = (
            f"Assigned {risk_level} risk score of {risk_score}/100. "
            f"{c_detail}. {s_detail}. Confidentiality lifetime rated {l_val}/5. Exposure rated {e_val}/5."
        )

        return {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "status": "assessed",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "formula": "R = 20 * (0.35C + 0.30S + 0.25L + 0.10E)",
            "factors": {
                "C": {"value": c_val, "weight": 0.35, "name": "Cryptographic Exposure", "detail": c_detail},
                "S": {"value": s_val, "weight": 0.30, "name": "Data Sensitivity", "detail": s_detail},
                "L": {"value": l_val, "weight": 0.25, "name": "Confidentiality Lifetime", "detail": l_detail},
                "E": {"value": e_val, "weight": 0.10, "name": "Internet Exposure", "detail": e_detail},
            },
            "explanation": explanation,
            "findings_count": len(findings),
            "quantum_vulnerable_count": qv_count,
        }

    def assess_all_assets(self) -> List[Dict[str, Any]]:
        """Calculate risk scores for all inventory assets."""
        assets, _ = self.asset_repo.list_assets(limit=500)
        return [self.assess_asset(a.id) for a in assets]

    def _calculate_crypto_exposure(self, findings: List[Finding]) -> Tuple[int, str]:
        """Evaluate cryptographic exposure factor C (1 to 5)."""
        if not findings:
            return 1, "No cryptographic vulnerabilities detected (C=1)"

        has_critical = any(f.severity == "critical" or "1024" in f.algorithm for f in findings)
        if has_critical:
            return 5, "Legacy/broken classical cryptography detected (e.g. RSA < 2048, SHA1, DES) (C=5)"

        has_rsa_ecc = any(f.quantum_vulnerable for f in findings)
        if has_rsa_ecc:
            return 4, "Quantum-vulnerable asymmetric cryptography active (RSA-2048/ECC/ECDH) (C=4)"

        return 2, "Modern or hybrid cryptographic implementations detected (C=2)"

    def _calculate_sensitivity(self, asset: Asset) -> int:
        crit_map = {"critical": 5, "high": 4, "medium": 3, "low": 1}
        return crit_map.get(asset.criticality.lower(), 3)

    def _calculate_lifetime(self, asset: Asset) -> int:
        env_map = {"production": 5, "staging": 3, "testing": 2, "development": 1}
        return env_map.get(asset.environment.lower(), 3)

    def _calculate_exposure(self, asset: Asset) -> int:
        if asset.asset_type in ("website",) or (asset.hostname and not asset.hostname.endswith(".local")):
            return 5
        if asset.ip_address:
            return 4
        if asset.asset_type in ("server",):
            return 3
        return 1
