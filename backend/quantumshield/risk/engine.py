"""
Explainable Risk Assessment Scoring Engine.
Calculates deterministic cryptographic exposure priority using transparent mathematical weighting:
    R = 20 * (0.35C + 0.30S + 0.25L + 0.10E)
Unscanned assets receive 'Needs assessment' rather than artificially low risk.
"""

from typing import Dict, Any, List, Optional, Tuple
from quantumshield.models.asset import Asset
from quantumshield.models.finding import Finding
from quantumshield.storage.repositories import AssetRepository
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.scan_repository import ScanRepository


class RiskEngine:
    """Deterministic, transparent risk evaluation engine."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.asset_repo = AssetRepository(db_path)
        self.finding_repo = FindingRepository(db_path)
        self.scan_repo = ScanRepository(db_path)

    def assess_asset(self, asset_id: str) -> Dict[str, Any]:
        """Calculate explainable risk score for an asset."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found.")

        # Check if asset has been scanned
        scan_runs, total_runs = self.scan_repo.list_scan_runs(asset_id=asset_id, status="completed", limit=1)
        findings, total_findings = self.finding_repo.list_findings(asset_id=asset_id, limit=100)

        if total_runs == 0 and total_findings == 0:
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
        from typing import Tuple
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
