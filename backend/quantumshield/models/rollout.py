"""
Stage 4 Data Models: Staged Production Rollout Management.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional


@dataclass
class DeploymentEnvironment:
    id: str
    name: str
    category: str  # 'development', 'local_lab', 'staging', 'production'
    managed_service: str
    owner: str
    current_config: Dict[str, Any]
    desired_config: Dict[str, Any]
    supported_tls_version: str = "TLS 1.3"
    supported_groups: List[str] = field(default_factory=list)
    client_compatibility_reqs: Optional[str] = None
    readiness_status: str = "not_ready"  # 'not_ready', 'ready_for_canary', 'ready', 'degraded'
    rollout_status: str = "idle"  # 'idle', 'in_progress', 'completed', 'rolled_back'
    rollback_config_ref: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "managed_service": self.managed_service,
            "owner": self.owner,
            "current_config": self.current_config,
            "desired_config": self.desired_config,
            "supported_tls_version": self.supported_tls_version,
            "supported_groups": self.supported_groups,
            "client_compatibility_reqs": self.client_compatibility_reqs,
            "readiness_status": self.readiness_status,
            "rollout_status": self.rollout_status,
            "rollback_config_ref": self.rollback_config_ref,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "DeploymentEnvironment":
        current_cfg = {}
        if row["current_config_json"]:
            try:
                current_cfg = json.loads(row["current_config_json"])
            except Exception:
                current_cfg = {}

        desired_cfg = {}
        if row["desired_config_json"]:
            try:
                desired_cfg = json.loads(row["desired_config_json"])
            except Exception:
                desired_cfg = {}

        groups = []
        if row["supported_groups_json"]:
            try:
                groups = json.loads(row["supported_groups_json"])
            except Exception:
                groups = []

        rollback_cfg = None
        if row["rollback_config_ref"]:
            try:
                rollback_cfg = json.loads(row["rollback_config_ref"])
            except Exception:
                rollback_cfg = None

        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            managed_service=row["managed_service"],
            owner=row["owner"],
            current_config=current_cfg,
            desired_config=desired_cfg,
            supported_tls_version=row["supported_tls_version"],
            supported_groups=groups,
            client_compatibility_reqs=row["client_compatibility_reqs"],
            readiness_status=row["readiness_status"],
            rollout_status=row["rollout_status"],
            rollback_config_ref=rollback_cfg,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


CANARY_STAGES = [
    {"stage": "STAGE_1_INTERNAL_1PCT", "name": "Stage 1: Internal Dogfooding", "percentage": 1},
    {"stage": "STAGE_2_CANARY_5PCT", "name": "Stage 2: Low-Risk Traffic Canary", "percentage": 5},
    {"stage": "STAGE_3_BROADER_25PCT", "name": "Stage 3: Broader Traffic Canary", "percentage": 25},
    {"stage": "STAGE_4_MAJORITY_50PCT", "name": "Stage 4: Majority Production Traffic", "percentage": 50},
    {"stage": "STAGE_5_FULL_HYBRID_100PCT", "name": "Stage 5: Full Hybrid Production", "percentage": 100},
]


@dataclass
class RolloutPlan:
    id: str
    name: str
    environment_id: str
    current_stage: str = "DRAFT"
    state: str = "DRAFT"
    # States: DRAFT, VALIDATING, READY_FOR_APPROVAL, APPROVED, CANARY, MONITORING, COMPLETED, BLOCKED, FAILED, ROLLBACK_PENDING, ROLLED_BACK, CANCELLED
    canary_percentage: int = 5
    previous_config: Optional[Dict[str, Any]] = None
    target_config: Dict[str, Any] = field(default_factory=dict)
    readiness_assessment: Optional[Dict[str, Any]] = None
    rollback_threshold_failure_rate: float = 2.0
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    last_advanced_at: Optional[str] = None
    deployment_mode: str = "simulation"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "environment_id": self.environment_id,
            "current_stage": self.current_stage,
            "state": self.state,
            "canary_percentage": self.canary_percentage,
            "previous_config": self.previous_config,
            "target_config": self.target_config,
            "readiness_assessment": self.readiness_assessment,
            "rollback_threshold_failure_rate": self.rollback_threshold_failure_rate,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "last_advanced_at": self.last_advanced_at,
            "deployment_mode": self.deployment_mode,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "RolloutPlan":
        prev_cfg = None
        if row["previous_config_json"]:
            try:
                prev_cfg = json.loads(row["previous_config_json"])
            except Exception:
                prev_cfg = None

        target_cfg = {}
        if row["target_config_json"]:
            try:
                target_cfg = json.loads(row["target_config_json"])
            except Exception:
                target_cfg = {}

        assessment = None
        if row["readiness_assessment_json"]:
            try:
                assessment = json.loads(row["readiness_assessment_json"])
            except Exception:
                assessment = None

        return cls(
            id=row["id"],
            name=row["name"],
            environment_id=row["environment_id"],
            current_stage=row["current_stage"],
            state=row["state"],
            canary_percentage=row["canary_percentage"],
            previous_config=prev_cfg,
            target_config=target_cfg,
            readiness_assessment=assessment,
            rollback_threshold_failure_rate=row["rollback_threshold_failure_rate"],
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            last_advanced_at=row["last_advanced_at"],
            deployment_mode=row["deployment_mode"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class TelemetryEvent:
    id: str
    rollout_id: str
    stage: str
    handshake_success_rate: float = 100.0
    handshake_failure_rate: float = 0.0
    average_latency_ms: float = 15.0
    timeout_rate: float = 0.0
    negotiated_tls_version: str = "TLS 1.3"
    negotiated_group: str = "X25519MLKEM768"
    error_categories: Optional[Dict[str, int]] = None
    is_simulated: bool = True
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rollout_id": self.rollout_id,
            "stage": self.stage,
            "handshake_success_rate": self.handshake_success_rate,
            "handshake_failure_rate": self.handshake_failure_rate,
            "average_latency_ms": self.average_latency_ms,
            "timeout_rate": self.timeout_rate,
            "negotiated_tls_version": self.negotiated_tls_version,
            "negotiated_group": self.negotiated_group,
            "error_categories": self.error_categories,
            "is_simulated": self.is_simulated,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> "TelemetryEvent":
        errs = None
        if row["error_categories_json"]:
            try:
                errs = json.loads(row["error_categories_json"])
            except Exception:
                errs = None

        return cls(
            id=row["id"],
            rollout_id=row["rollout_id"],
            stage=row["stage"],
            handshake_success_rate=row["handshake_success_rate"],
            handshake_failure_rate=row["handshake_failure_rate"],
            average_latency_ms=row["average_latency_ms"],
            timeout_rate=row["timeout_rate"],
            negotiated_tls_version=row["negotiated_tls_version"],
            negotiated_group=row["negotiated_group"],
            error_categories=errs,
            is_simulated=bool(row["is_simulated"]),
            recorded_at=row["recorded_at"],
        )
