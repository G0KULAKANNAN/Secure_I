"""
Hybrid Cryptography Domain Models for Staging Evaluation and Migration Governance.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import uuid
from typing import Dict, Any, Optional
from quantumshield.core.exceptions import ValidationError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


VALID_HYBRID_STATES = {"PLANNED", "CONFIGURED", "TESTING", "VERIFIED", "FAILED", "APPROVED"}
VALID_CLASSICAL_GROUPS = {"X25519", "NIST P-256", "NIST P-384", "FFDHE-2048", "FFDHE-3072"}
VALID_PQC_ALGORITHMS = {"ML-KEM-768", "ML-KEM-1024", "Kyber-768", "Kyber-1024"}


@dataclass
class CryptoCapability:
    id: str = ""
    classical_group: str = "X25519"
    pqc_algorithm: str = "ML-KEM-768"
    hybrid_combination: str = "X25519MLKEM768"
    standard_reference: str = "Draft IETF / NIST FIPS 203"
    implementation_provider: str = "OpenSSL 3.x / liboqs"
    library_version: str = "liboqs-0.10.0+"
    client_compatibility: str = ""
    server_compatibility: str = ""
    staging_test_status: str = "untested"
    negotiation_status: str = "untested"  # supported_by_lib, enabled_by_impl, negotiated_in_conn, verified_in_test
    failure_reason: Optional[str] = None
    security_notes: Optional[str] = None
    last_verified_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"cap_{uuid.uuid4().hex[:12]}"
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "classical_group": self.classical_group,
            "pqc_algorithm": self.pqc_algorithm,
            "hybrid_combination": self.hybrid_combination,
            "standard_reference": self.standard_reference,
            "implementation_provider": self.implementation_provider,
            "library_version": self.library_version,
            "client_compatibility": self.client_compatibility,
            "server_compatibility": self.server_compatibility,
            "staging_test_status": self.staging_test_status,
            "negotiation_status": self.negotiation_status,
            "failure_reason": self.failure_reason,
            "security_notes": self.security_notes,
            "last_verified_at": self.last_verified_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CryptoCapability":
        return cls(
            id=data.get("id", ""),
            classical_group=data.get("classical_group", "X25519"),
            pqc_algorithm=data.get("pqc_algorithm", "ML-KEM-768"),
            hybrid_combination=data.get("hybrid_combination", "X25519MLKEM768"),
            standard_reference=data.get("standard_reference", "Draft IETF"),
            implementation_provider=data.get("implementation_provider", "liboqs"),
            library_version=data.get("library_version", "1.0.0"),
            client_compatibility=data.get("client_compatibility", ""),
            server_compatibility=data.get("server_compatibility", ""),
            staging_test_status=data.get("staging_test_status", "untested"),
            negotiation_status=data.get("negotiation_status", "untested"),
            failure_reason=data.get("failure_reason"),
            security_notes=data.get("security_notes"),
            last_verified_at=data.get("last_verified_at"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class HybridProfile:
    id: str = ""
    profile_name: str = ""
    classical_component: str = "X25519"
    pqc_component: str = "ML-KEM-768"
    environment: str = "staging"
    rollout_status: str = "disabled"
    migration_state: str = "PLANNED"
    automatic_production_prohibited: bool = True
    previous_config_json: Optional[str] = "{}"
    proposed_config_json: Optional[str] = "{}"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"hyp_{uuid.uuid4().hex[:12]}"
        now = utc_now_iso()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = self.created_at

    def validate(self) -> None:
        if not self.profile_name or not self.profile_name.strip():
            raise ValidationError("Profile name is required and cannot be empty.")
        if self.environment != "staging":
            raise ValidationError("Hybrid profiles can only be configured for the 'staging' environment.")
        if self.migration_state not in VALID_HYBRID_STATES:
            raise ValidationError(f"Invalid migration_state '{self.migration_state}'. Must be one of: {', '.join(sorted(VALID_HYBRID_STATES))}")
        if self.classical_component not in VALID_CLASSICAL_GROUPS:
            raise ValidationError(f"Unsupported classical component '{self.classical_component}'. Must be one of: {', '.join(sorted(VALID_CLASSICAL_GROUPS))}")
        if self.pqc_component not in VALID_PQC_ALGORITHMS:
            raise ValidationError(f"Unsupported PQC component '{self.pqc_component}'. Must be one of: {', '.join(sorted(VALID_PQC_ALGORITHMS))}")

    def to_dict(self) -> Dict[str, Any]:
        prev_conf = {}
        prop_conf = {}
        if self.previous_config_json:
            try:
                prev_conf = json.loads(self.previous_config_json)
            except Exception:
                pass
        if self.proposed_config_json:
            try:
                prop_conf = json.loads(self.proposed_config_json)
            except Exception:
                pass

        return {
            "id": self.id,
            "profile_name": self.profile_name,
            "classical_component": self.classical_component,
            "pqc_component": self.pqc_component,
            "hybrid_combination": f"{self.classical_component}+{self.pqc_component}",
            "environment": self.environment,
            "rollout_status": self.rollout_status,
            "migration_state": self.migration_state,
            "automatic_production_prohibited": bool(self.automatic_production_prohibited),
            "previous_config": prev_conf,
            "proposed_config": prop_conf,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HybridProfile":
        prev = data.get("previous_config_json")
        if prev is None and "previous_config" in data:
            prev = json.dumps(data["previous_config"])
        prop = data.get("proposed_config_json")
        if prop is None and "proposed_config" in data:
            prop = json.dumps(data["proposed_config"])

        return cls(
            id=data.get("id", ""),
            profile_name=data.get("profile_name", ""),
            classical_component=data.get("classical_component", "X25519"),
            pqc_component=data.get("pqc_component", "ML-KEM-768"),
            environment=data.get("environment", "staging"),
            rollout_status=data.get("rollout_status", "disabled"),
            migration_state=data.get("migration_state", "PLANNED"),
            automatic_production_prohibited=bool(data.get("automatic_production_prohibited", True)),
            previous_config_json=prev or "{}",
            proposed_config_json=prop or "{}",
            approved_by=data.get("approved_by"),
            approved_at=data.get("approved_at"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class HybridVerificationRun:
    id: str = ""
    profile_id: str = ""
    test_mode: str = "simulation"  # real_tls, simulation
    status: str = "passed"         # passed, failed, unsupported
    negotiation_outcome: str = ""
    classical_client_compatible: bool = True
    hybrid_client_compatible: bool = False
    observed_tls_version: Optional[str] = "TLS 1.3"
    negotiated_group: Optional[str] = None
    error_details: Optional[str] = None
    duration_ms: int = 0
    is_simulated: bool = True
    operator: str = "local_operator"
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"vrf_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "test_mode": self.test_mode,
            "status": self.status,
            "negotiation_outcome": self.negotiation_outcome,
            "classical_client_compatible": bool(self.classical_client_compatible),
            "hybrid_client_compatible": bool(self.hybrid_client_compatible),
            "observed_tls_version": self.observed_tls_version,
            "negotiated_group": self.negotiated_group,
            "error_details": self.error_details,
            "duration_ms": self.duration_ms,
            "is_simulated": bool(self.is_simulated),
            "simulation_label": "SIMULATED — NO REAL HYBRID TLS CAPABILITY IN PYTHON SSL" if self.is_simulated else "REAL TLS NEGOTIATION",
            "operator": self.operator,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HybridVerificationRun":
        return cls(
            id=data.get("id", ""),
            profile_id=data.get("profile_id", ""),
            test_mode=data.get("test_mode", "simulation"),
            status=data.get("status", "passed"),
            negotiation_outcome=data.get("negotiation_outcome", ""),
            classical_client_compatible=bool(data.get("classical_client_compatible", True)),
            hybrid_client_compatible=bool(data.get("hybrid_client_compatible", False)),
            observed_tls_version=data.get("observed_tls_version"),
            negotiated_group=data.get("negotiated_group"),
            error_details=data.get("error_details"),
            duration_ms=int(data.get("duration_ms", 0)),
            is_simulated=bool(data.get("is_simulated", True)),
            operator=data.get("operator", "local_operator"),
            created_at=data.get("created_at", ""),
        )
