"""
Finding Domain Model and Stable Fingerprinting.
Represents a cryptographic vulnerability or observation with sanitized evidence and PQC recommendations.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import uuid
from typing import Optional, Dict, Any


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def compute_finding_fingerprint(asset_id: str, rule_id: str, location: str) -> str:
    """Generate deterministic SHA-256 fingerprint for deduplication."""
    raw = f"{asset_id.strip()}:{rule_id.strip()}:{location.strip()}".lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


@dataclass
class Finding:
    id: str = ""
    asset_id: str = ""
    scan_run_id: Optional[str] = None
    job_id: Optional[str] = None
    scanner_type: str = "certificate_scan"
    algorithm: str = "RSA-2048"
    cryptographic_primitive: str = "digital_signature"
    quantum_vulnerable: bool = True
    recommended_pqc: str = "ML-DSA-65"
    rule_id: str = "CRYPTO-RSA-2048"
    title: str = "Quantum-Vulnerable RSA Key Detected"
    description: str = ""
    severity: str = "high"
    evidence: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    confidence: str = "high"
    remediation_status: str = "potential_exposure"
    fingerprint: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"fnd_{uuid.uuid4().hex[:12]}"
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.fingerprint:
            loc = self.file_path or self.evidence or "default"
            self.fingerprint = compute_finding_fingerprint(self.asset_id, self.rule_id, loc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to serializable dictionary."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "scan_run_id": self.scan_run_id,
            "job_id": self.job_id,
            "scanner_type": self.scanner_type,
            "algorithm": self.algorithm,
            "cryptographic_primitive": self.cryptographic_primitive,
            "quantum_vulnerable": bool(self.quantum_vulnerable),
            "recommended_pqc": self.recommended_pqc,
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "evidence": self.evidence,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "remediation_status": self.remediation_status,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Finding":
        """Instantiate Finding from dictionary data."""
        return cls(
            id=data.get("id", ""),
            asset_id=data.get("asset_id", ""),
            scan_run_id=data.get("scan_run_id"),
            job_id=data.get("job_id"),
            scanner_type=data.get("scanner_type", "certificate_scan"),
            algorithm=data.get("algorithm", "Unknown"),
            cryptographic_primitive=data.get("cryptographic_primitive", "key_establishment"),
            quantum_vulnerable=bool(data.get("quantum_vulnerable", True)),
            recommended_pqc=data.get("recommended_pqc", "ML-KEM-768"),
            rule_id=data.get("rule_id", "GENERIC-CRYPTO"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            severity=data.get("severity", "medium"),
            evidence=data.get("evidence", ""),
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            confidence=data.get("confidence", "high"),
            remediation_status=data.get("remediation_status", "potential_exposure"),
            fingerprint=data.get("fingerprint", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
