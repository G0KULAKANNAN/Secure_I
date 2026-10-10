"""
Stage 5 Data Models: Classical Cryptography Decommissioning.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional


@dataclass
class DecommissioningPolicy:
    id: str
    name: str
    algorithm: str
    primitive_category: str  # 'key_exchange', 'digital_signature', 'symmetric_encryption', 'hashing'
    status: str  # 'APPROVED', 'APPROVED_WITH_CONDITIONS', 'MIGRATION_REQUIRED', 'DEPRECATED', 'PROHIBITED_BY_CONFIGURED_POLICY', 'NEEDS_REVIEW'
    conditions: Optional[str] = None
    enforcement_deadline: Optional[str] = None
    rationale: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "algorithm": self.algorithm,
            "primitive_category": self.primitive_category,
            "status": self.status,
            "conditions": self.conditions,
            "enforcement_deadline": self.enforcement_deadline,
            "rationale": self.rationale,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "DecommissioningPolicy":
        return cls(
            id=row["id"],
            name=row["name"],
            algorithm=row["algorithm"],
            primitive_category=row["primitive_category"],
            status=row["status"],
            conditions=row["conditions"],
            enforcement_deadline=row["enforcement_deadline"],
            rationale=row["rationale"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class CryptoDependency:
    id: str
    asset_id: Optional[str]
    service_name: str
    primitive_category: str
    current_algorithm: str
    target_algorithm: str
    status: str = "active"  # 'active', 'migrating', 'decommissioned', 'blocked'
    policy_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "service_name": self.service_name,
            "primitive_category": self.primitive_category,
            "current_algorithm": self.current_algorithm,
            "target_algorithm": self.target_algorithm,
            "status": self.status,
            "policy_id": self.policy_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "CryptoDependency":
        return cls(
            id=row["id"],
            asset_id=row["asset_id"],
            service_name=row["service_name"],
            primitive_category=row["primitive_category"],
            current_algorithm=row["current_algorithm"],
            target_algorithm=row["target_algorithm"],
            status=row["status"],
            policy_id=row["policy_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


DECOMMISSIONING_STATES = [
    "DISCOVERED",
    "MIGRATION_VERIFIED",
    "READY_FOR_REVIEW",
    "APPROVED",
    "DECOMMISSIONING_PLANNED",
    "COMPLETED",
    "BLOCKED",
    "ROLLED_BACK",
]


@dataclass
class DecommissioningPlan:
    id: str
    name: str
    target_primitive: str
    affected_services: List[str] = field(default_factory=list)
    state: str = "DISCOVERED"
    readiness_assessment: Optional[Dict[str, Any]] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    decommissioned_at: Optional[str] = None
    rollback_instructions: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_primitive": self.target_primitive,
            "affected_services": self.affected_services,
            "state": self.state,
            "readiness_assessment": self.readiness_assessment,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "decommissioned_at": self.decommissioned_at,
            "rollback_instructions": self.rollback_instructions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "DecommissioningPlan":
        services = []
        if row["affected_services_json"]:
            try:
                services = json.loads(row["affected_services_json"])
            except Exception:
                services = []

        assessment = None
        if row["readiness_assessment_json"]:
            try:
                assessment = json.loads(row["readiness_assessment_json"])
            except Exception:
                assessment = None

        return cls(
            id=row["id"],
            name=row["name"],
            target_primitive=row["target_primitive"],
            affected_services=services,
            state=row["state"],
            readiness_assessment=assessment,
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            decommissioned_at=row["decommissioned_at"],
            rollback_instructions=row["rollback_instructions"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
