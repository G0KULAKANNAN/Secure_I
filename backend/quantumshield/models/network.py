"""
Network MTU and Middlebox Verification Domain Models.
Supports local simulations, local loopback integration testing, and authorised endpoint evaluation.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import uuid
from typing import Dict, Any, Optional, List
from quantumshield.core.exceptions import ValidationError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


VALID_TEST_MODES = {"simulation", "local_loopback", "authorised_endpoint"}
VALID_TEST_PROFILES = {"standard_mtu", "fragmentation_sensitive", "large_handshake_probe", "middlebox_probe"}
VALID_DIAGNOSTIC_CLASSIFICATIONS = {"PASS", "FAIL", "INCONCLUSIVE", "SIMULATED", "NOT_SUPPORTED"}


@dataclass
class NetworkProfile:
    id: str = ""
    name: str = ""
    target_host: str = "127.0.0.1"
    target_port: int = 443
    environment: str = "local_lab"
    test_profile: str = "standard_mtu"
    test_mode: str = "simulation"
    expected_mtu: int = 1500
    connection_timeout: float = 5.0
    handshake_timeout: float = 5.0
    max_retries: int = 2
    is_allowlisted: bool = False
    authorized_by_operator: bool = False
    operator_notes: Optional[str] = None
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"net_{uuid.uuid4().hex[:12]}"
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = self.created_at

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Profile name is required.")
        if self.test_mode not in VALID_TEST_MODES:
            raise ValidationError(f"Invalid test_mode '{self.test_mode}'. Must be one of: {', '.join(sorted(VALID_TEST_MODES))}")
        if self.test_profile not in VALID_TEST_PROFILES:
            raise ValidationError(f"Invalid test_profile '{self.test_profile}'. Must be one of: {', '.join(sorted(VALID_TEST_PROFILES))}")
        if self.target_port < 1 or self.target_port > 65535:
            raise ValidationError("Target port must be between 1 and 65535.")
        if self.expected_mtu < 576 or self.expected_mtu > 9000:
            raise ValidationError("Expected MTU must be between 576 and 9000.")

        # Security check: External network mode requires explicit authorization
        if self.test_mode == "authorised_endpoint":
            if not self.authorized_by_operator:
                raise ValidationError("Explicit operator authorization is required before connecting to external endpoints.")
            # SSRF check: Disallow cloud metadata addresses
            host = self.target_host.lower().strip()
            if host in ("169.254.169.254", "metadata.google.internal", "instance-data"):
                raise ValidationError("SSRF Security Violation: Prohibited cloud metadata endpoint target.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_host": self.target_host,
            "target_port": self.target_port,
            "environment": self.environment,
            "test_profile": self.test_profile,
            "test_mode": self.test_mode,
            "expected_mtu": self.expected_mtu,
            "connection_timeout": self.connection_timeout,
            "handshake_timeout": self.handshake_timeout,
            "max_retries": self.max_retries,
            "is_allowlisted": bool(self.is_allowlisted),
            "authorized_by_operator": bool(self.authorized_by_operator),
            "operator_notes": self.operator_notes,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetworkProfile":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            target_host=data.get("target_host", "127.0.0.1"),
            target_port=int(data.get("target_port", 443)),
            environment=data.get("environment", "local_lab"),
            test_profile=data.get("test_profile", "standard_mtu"),
            test_mode=data.get("test_mode", "simulation"),
            expected_mtu=int(data.get("expected_mtu", 1500)),
            connection_timeout=float(data.get("connection_timeout", 5.0)),
            handshake_timeout=float(data.get("handshake_timeout", 5.0)),
            max_retries=int(data.get("max_retries", 2)),
            is_allowlisted=bool(data.get("is_allowlisted", False)),
            authorized_by_operator=bool(data.get("authorized_by_operator", False)),
            operator_notes=data.get("operator_notes"),
            status=data.get("status", "active"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class NetworkVerificationResult:
    id: str = ""
    profile_id: str = ""
    job_id: Optional[str] = None
    test_mode: str = "simulation"
    target_endpoint: str = "127.0.0.1:443"
    address_family: str = "IPv4"
    configured_mtu: Optional[int] = 1500
    tls_version: Optional[str] = "TLS 1.3"
    negotiated_group: Optional[str] = "X25519"
    handshake_success: bool = True
    diagnostic_classification: str = "PASS"  # PASS, FAIL, INCONCLUSIVE, SIMULATED, NOT_SUPPORTED
    diagnostic_finding: str = ""
    observed_error: Optional[str] = None
    duration_ms: int = 0
    retry_count: int = 0
    packet_size_estimate_bytes: Optional[int] = 1420
    evidence_level: str = "connection_level"  # connection_level, measured, simulated
    evidence_details_json: Optional[str] = "{}"
    remediation_recommendations_json: Optional[str] = "[]"
    confidence: str = "high"
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"nvr_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        ev_details = {}
        if self.evidence_details_json:
            try:
                ev_details = json.loads(self.evidence_details_json)
            except Exception:
                pass

        recs = []
        if self.remediation_recommendations_json:
            try:
                recs = json.loads(self.remediation_recommendations_json)
            except Exception:
                pass

        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "job_id": self.job_id,
            "test_mode": self.test_mode,
            "target_endpoint": self.target_endpoint,
            "address_family": self.address_family,
            "configured_mtu": self.configured_mtu,
            "tls_version": self.tls_version,
            "negotiated_group": self.negotiated_group,
            "handshake_success": bool(self.handshake_success),
            "diagnostic_classification": self.diagnostic_classification,
            "diagnostic_finding": self.diagnostic_finding,
            "observed_error": self.observed_error,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "packet_size_estimate_bytes": self.packet_size_estimate_bytes,
            "evidence_level": self.evidence_level,
            "evidence_details": ev_details,
            "remediation_recommendations": recs,
            "confidence": self.confidence,
            "is_simulated": self.test_mode == "simulation" or self.evidence_level == "simulated",
            "simulation_label": "SIMULATED — NO REAL NETWORK TEST PERFORMED" if (self.test_mode == "simulation" or self.evidence_level == "simulated") else "MEASURED NETWORK TEST",
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetworkVerificationResult":
        ev = data.get("evidence_details_json")
        if ev is None and "evidence_details" in data:
            ev = json.dumps(data["evidence_details"])
        recs = data.get("remediation_recommendations_json")
        if recs is None and "remediation_recommendations" in data:
            recs = json.dumps(data["remediation_recommendations"])

        return cls(
            id=data.get("id", ""),
            profile_id=data.get("profile_id", ""),
            job_id=data.get("job_id"),
            test_mode=data.get("test_mode", "simulation"),
            target_endpoint=data.get("target_endpoint", "127.0.0.1:443"),
            address_family=data.get("address_family", "IPv4"),
            configured_mtu=data.get("configured_mtu"),
            tls_version=data.get("tls_version"),
            negotiated_group=data.get("negotiated_group"),
            handshake_success=bool(data.get("handshake_success", True)),
            diagnostic_classification=data.get("diagnostic_classification", "PASS"),
            diagnostic_finding=data.get("diagnostic_finding", ""),
            observed_error=data.get("observed_error"),
            duration_ms=int(data.get("duration_ms", 0)),
            retry_count=int(data.get("retry_count", 0)),
            packet_size_estimate_bytes=data.get("packet_size_estimate_bytes"),
            evidence_level=data.get("evidence_level", "connection_level"),
            evidence_details_json=ev or "{}",
            remediation_recommendations_json=recs or "[]",
            confidence=data.get("confidence", "high"),
            created_at=data.get("created_at", ""),
        )
