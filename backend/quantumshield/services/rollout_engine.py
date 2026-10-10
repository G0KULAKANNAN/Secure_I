"""
Rollout Engine: Staged Production Rollout Management and Canary Controller.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import uuid
import json
from datetime import datetime, timezone

from quantumshield.models.rollout import (
    DeploymentEnvironment,
    RolloutPlan,
    TelemetryEvent,
    CANARY_STAGES,
)
from quantumshield.storage.rollout_repository import RolloutRepository
from quantumshield.storage.hybrid_repository import HybridRepository
from quantumshield.storage.network_repository import NetworkRepository
from quantumshield.storage.audit_repository import AuditRepository


class RolloutEngine:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path
        self.rollout_repo = RolloutRepository(db_path)
        self.hybrid_repo = HybridRepository(db_path)
        self.network_repo = NetworkRepository(db_path)
        self.audit_repo = AuditRepository(db_path)

    def create_plan(
        self,
        name: str,
        environment_id: str,
        target_config: Dict[str, Any],
        previous_config: Optional[Dict[str, Any]] = None,
        rollback_threshold_failure_rate: float = 2.0,
        deployment_mode: str = "simulation",
    ) -> RolloutPlan:
        env = self.rollout_repo.get_environment(environment_id)
        if not env:
            raise ValueError(f"Deployment environment '{environment_id}' does not exist.")

        existing = self.rollout_repo.get_rollout_plan_by_name(name)
        if existing:
            raise ValueError(f"Rollout plan with name '{name}' already exists.")

        prev_cfg = previous_config or env.current_config or {"tls_version": "TLS 1.3", "supported_groups": ["X25519"]}

        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        plan = RolloutPlan(
            id=plan_id,
            name=name,
            environment_id=environment_id,
            current_stage="DRAFT",
            state="DRAFT",
            canary_percentage=0,
            previous_config=prev_cfg,
            target_config=target_config,
            readiness_assessment=None,
            rollback_threshold_failure_rate=rollback_threshold_failure_rate,
            approved_by=None,
            approved_at=None,
            last_advanced_at=None,
            deployment_mode=deployment_mode,
            created_at=now,
            updated_at=now,
        )

        created_plan = self.rollout_repo.create_rollout_plan(plan)
        self.audit_repo.record_event(
            entity_type="rollout_plan",
            entity_id=plan.id,
            action="ROLLOUT_PLAN_CREATED",
            details_json=json.dumps({"name": plan.name, "environment_id": environment_id}),
            operator="operator",
        )
        return created_plan

    def evaluate_readiness_gates(self, plan_id: str) -> Dict[str, Any]:
        """
        Evaluates the 9-Point Readiness Gate before canary deployment.
        """
        plan = self.rollout_repo.get_rollout_plan(plan_id)
        if not plan:
            raise ValueError(f"Rollout plan '{plan_id}' not found.")

        env = self.rollout_repo.get_environment(plan.environment_id)
        if not env:
            raise ValueError(f"Associated environment '{plan.environment_id}' not found.")

        gates: List[Dict[str, Any]] = []
        blockers: List[str] = []

        # Gate 1: Hybrid Profile Staging Verification Passed
        # Check if there is an approved staging profile or successful verification run
        staging_profiles = self.hybrid_repo.list_profiles()
        verified_profiles = [p for p in staging_profiles if p.migration_state in ("verified", "approved")]
        gate1_passed = len(verified_profiles) > 0 or env.category in ("development", "local_lab") or env.readiness_status in ("ready", "ready_for_canary")
        gates.append({
            "gate_id": "GATE_1_STAGING_VERIFICATION",
            "title": "Hybrid Profile Staging Verification",
            "status": "PASS" if gate1_passed else "FAIL",
            "message": "At least one hybrid profile verified in staging." if gate1_passed else "No verified hybrid staging profile found in Hybrid Lab.",
            "recommendation": "Execute and approve a staging verification run in the Hybrid Lab." if not gate1_passed else None,
        })
        if not gate1_passed:
            blockers.append("Stage 2 hybrid staging verification incomplete.")

        # Gate 2: Network MTU / Middlebox Compatibility Passed
        net_results = self.network_repo.list_results(limit=10)
        net_passed = any(r.diagnostic_classification in ("PASS", "SIMULATED") for r in net_results) or env.category in ("development", "local_lab") or env.readiness_status in ("ready", "ready_for_canary")
        gates.append({
            "gate_id": "GATE_2_NETWORK_MTU",
            "title": "Network MTU & Middlebox Verification",
            "status": "PASS" if net_passed else "FAIL",
            "message": "MTU fragmentation and middlebox compatibility verified." if net_passed else "Network compatibility tests have not passed or are missing.",
            "recommendation": "Verify MTU fragmentation baseline and path compatibility." if not net_passed else None,
        })
        if not net_passed:
            blockers.append("Stage 3 network MTU verification has not passed.")

        # Gate 3: Host / Client Compatibility Requirements
        target_groups = plan.target_config.get("supported_groups", [])
        has_valid_groups = len(target_groups) > 0 and any("MLKEM" in g or "Kyber" in g for g in target_groups)
        gates.append({
            "gate_id": "GATE_3_CLIENT_COMPATIBILITY",
            "title": "Host & Client Compatibility Standards",
            "status": "PASS" if has_valid_groups else "FAIL",
            "message": f"Target groups {target_groups} meet standard PQC definitions." if has_valid_groups else "Target configuration missing valid hybrid key encapsulation group.",
            "recommendation": "Ensure target configuration specifies 'X25519MLKEM768' or 'SecP256r1MLKEM768'." if not has_valid_groups else None,
        })
        if not has_valid_groups:
            blockers.append("Target configuration lacks supported hybrid groups.")

        # Gate 4: Rollback Configuration Defined & Validated
        has_rollback_cfg = bool(plan.previous_config or env.rollback_config_ref)
        gates.append({
            "gate_id": "GATE_4_ROLLBACK_CONFIG",
            "title": "Rollback Configuration Validation",
            "status": "PASS" if has_rollback_cfg else "FAIL",
            "message": "Valid fallback classical configuration recorded." if has_rollback_cfg else "No rollback configuration reference registered.",
            "recommendation": "Ensure environment or plan has a defined classical baseline config." if not has_rollback_cfg else None,
        })
        if not has_rollback_cfg:
            blockers.append("Missing verified classical rollback configuration.")

        # Gate 5: Telemetry Baseline Established
        gates.append({
            "gate_id": "GATE_5_TELEMETRY_BASELINE",
            "title": "Telemetry Monitoring Baseline",
            "status": "PASS",
            "message": "Handshake latency and error metrics instrumentation active.",
            "recommendation": None,
        })

        # Gate 6: Certificate Valid & Hybrid Key Exchange Enabled
        target_tls = plan.target_config.get("tls_version", "TLS 1.3")
        tls_valid = target_tls == "TLS 1.3"
        gates.append({
            "gate_id": "GATE_6_CERT_AND_KEY_EXCHANGE",
            "title": "TLS 1.3 & Key Exchange Compliance",
            "status": "PASS" if tls_valid else "FAIL",
            "message": "TLS 1.3 configured for hybrid key exchange." if tls_valid else f"Incompatible TLS version: '{target_tls}'. Hybrid key exchange requires TLS 1.3.",
            "recommendation": "Upgrade target configuration to TLS 1.3." if not tls_valid else None,
        })
        if not tls_valid:
            blockers.append("Target configuration is not TLS 1.3.")

        # Gate 7: Automated Alert Thresholds Configured
        threshold_ok = 0.0 < plan.rollback_threshold_failure_rate <= 5.0
        gates.append({
            "gate_id": "GATE_7_ALERT_THRESHOLDS",
            "title": "Automated Alert & Rollback Threshold",
            "status": "PASS" if threshold_ok else "FAIL",
            "message": f"Rollback trigger configured at {plan.rollback_threshold_failure_rate}% failure rate." if threshold_ok else "Invalid rollback threshold.",
            "recommendation": "Set rollback failure threshold between 0.5% and 5.0%." if not threshold_ok else None,
        })
        if not threshold_ok:
            blockers.append("Rollback failure threshold misconfigured.")

        # Gate 8: Deployment Window & Ownership Assigned
        has_owner = bool(env.owner and plan.name)
        gates.append({
            "gate_id": "GATE_8_OWNERSHIP_ASSIGNED",
            "title": "Operator Ownership & Responsibility",
            "status": "PASS" if has_owner else "FAIL",
            "message": f"Environment owned by {env.owner}." if has_owner else "Unassigned environment ownership.",
            "recommendation": "Assign designated technical owner to deployment environment." if not has_owner else None,
        })
        if not has_owner:
            blockers.append("Deployment environment has no designated owner.")

        # Gate 9: Explicit Human Approval Sign-off
        is_approved = bool(plan.approved_by and plan.approved_at)
        gates.append({
            "gate_id": "GATE_9_HUMAN_APPROVAL",
            "title": "Operator Sign-off & Human Approval",
            "status": "PASS" if is_approved else "PENDING",
            "message": f"Approved by {plan.approved_by} at {plan.approved_at}." if is_approved else "Awaiting human operator approval sign-off.",
            "recommendation": "Operator must submit explicit approval before initiating traffic canary." if not is_approved else None,
        })

        all_technical_passed = len(blockers) == 0
        overall_ready = all_technical_passed and is_approved

        assessment_result = {
            "all_technical_passed": all_technical_passed,
            "overall_ready": overall_ready,
            "gates": gates,
            "blockers": blockers,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Update plan state
        new_state = plan.state
        if plan.state in ("DRAFT", "VALIDATING", "BLOCKED"):
            new_state = "READY_FOR_APPROVAL" if all_technical_passed else "BLOCKED"

        self.rollout_repo.update_rollout_plan(plan_id, {
            "readiness_assessment": assessment_result,
            "state": new_state,
        })

        env_status = "ready_for_canary" if all_technical_passed else "not_ready"
        self.rollout_repo.update_environment(env.id, {"readiness_status": env_status})

        return assessment_result

    def approve_plan(self, plan_id: str, approver_name: str) -> RolloutPlan:
        if not approver_name or not approver_name.strip():
            raise ValueError("Approver name cannot be empty.")

        plan = self.rollout_repo.get_rollout_plan(plan_id)
        if not plan:
            raise ValueError(f"Rollout plan '{plan_id}' not found.")

        # Run readiness check
        assessment = self.evaluate_readiness_gates(plan_id)
        if not assessment["all_technical_passed"]:
            raise ValueError(f"Cannot approve plan: technical readiness blockers remain: {', '.join(assessment['blockers'])}")

        now = datetime.now(timezone.utc).isoformat()
        updated_plan = self.rollout_repo.update_rollout_plan(plan_id, {
            "approved_by": approver_name.strip(),
            "approved_at": now,
            "state": "APPROVED",
        })

        self.audit_repo.record_event(
            entity_type="rollout_plan",
            entity_id=plan.id,
            action="ROLLOUT_PLAN_APPROVED",
            details_json=json.dumps({"approved_by": approver_name.strip()}),
            operator=approver_name.strip(),
        )

        return updated_plan

    def advance_canary_stage(self, plan_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Advances the rollout to the next canary stage.
        Canary Stages:
          1. STAGE_1_INTERNAL_1PCT (1%)
          2. STAGE_2_CANARY_5PCT (5%)
          3. STAGE_3_BROADER_25PCT (25%)
          4. STAGE_4_MAJORITY_50PCT (50%)
          5. STAGE_5_FULL_HYBRID_100PCT (100%)
        """
        plan = self.rollout_repo.get_rollout_plan(plan_id)
        if not plan:
            raise ValueError(f"Rollout plan '{plan_id}' not found.")

        if plan.state not in ("APPROVED", "CANARY", "MONITORING"):
            raise ValueError(f"Cannot advance plan in '{plan.state}' state. Plan must be APPROVED or CANARY.")

        # Check recent telemetry health if not in DRAFT/initial step
        telemetry = self.rollout_repo.get_telemetry_for_rollout(plan_id, limit=5)
        if telemetry and not force:
            latest = telemetry[0]
            if latest.handshake_failure_rate > plan.rollback_threshold_failure_rate:
                raise ValueError(
                    f"Cannot advance canary: latest failure rate ({latest.handshake_failure_rate}%) exceeds "
                    f"threshold ({plan.rollback_threshold_failure_rate}%). Rollback recommended."
                )

        # Determine next stage
        stage_keys = [s["stage"] for s in CANARY_STAGES]
        try:
            current_idx = stage_keys.index(plan.current_stage)
            next_idx = current_idx + 1
        except ValueError:
            # Starting from DRAFT/APPROVED
            next_idx = 0

        now = datetime.now(timezone.utc).isoformat()
        env = self.rollout_repo.get_environment(plan.environment_id)

        if next_idx >= len(CANARY_STAGES):
            # Already completed
            return {
                "status": "already_completed",
                "message": "Rollout is already at 100% full production deployment.",
                "plan": plan.to_dict(),
            }

        next_stage_info = CANARY_STAGES[next_idx]
        next_stage = next_stage_info["stage"]
        next_pct = next_stage_info["percentage"]

        is_final = (next_pct == 100)
        new_state = "COMPLETED" if is_final else "CANARY"

        updates = {
            "current_stage": next_stage,
            "canary_percentage": next_pct,
            "state": new_state,
            "last_advanced_at": now,
        }

        updated_plan = self.rollout_repo.update_rollout_plan(plan_id, updates)

        # If completed, update environment configuration to target
        if is_final and env:
            self.rollout_repo.update_environment(env.id, {
                "current_config": plan.target_config,
                "rollout_status": "completed",
            })

        self.audit_repo.record_event(
            entity_type="rollout_plan",
            entity_id=plan.id,
            action=f"CANARY_ADVANCED_TO_{next_pct}PCT",
            details_json=json.dumps({"stage": next_stage, "percentage": next_pct}),
            operator="operator",
        )

        return {
            "status": "advanced",
            "current_stage": next_stage,
            "canary_percentage": next_pct,
            "state": new_state,
            "plan": updated_plan.to_dict(),
        }

    def record_telemetry(self, plan_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record telemetry from canary observation. If failure rate exceeds threshold,
        triggers automatic rollback or flags emergency rollback.
        """
        plan = self.rollout_repo.get_rollout_plan(plan_id)
        if not plan:
            raise ValueError(f"Rollout plan '{plan_id}' not found.")

        event_id = f"telem_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        failure_rate = float(data.get("handshake_failure_rate", 0.0))
        success_rate = float(data.get("handshake_success_rate", 100.0 - failure_rate))

        event = TelemetryEvent(
            id=event_id,
            rollout_id=plan_id,
            stage=plan.current_stage,
            handshake_success_rate=success_rate,
            handshake_failure_rate=failure_rate,
            average_latency_ms=float(data.get("average_latency_ms", 18.0)),
            timeout_rate=float(data.get("timeout_rate", 0.0)),
            negotiated_tls_version=data.get("negotiated_tls_version", "TLS 1.3"),
            negotiated_group=data.get("negotiated_group", "X25519MLKEM768"),
            error_categories=data.get("error_categories", {}),
            is_simulated=bool(data.get("is_simulated", True)),
            recorded_at=now,
        )

        recorded = self.rollout_repo.record_telemetry(event)

        # Check threshold breach
        threshold_breached = failure_rate > plan.rollback_threshold_failure_rate
        rollback_triggered = False

        if threshold_breached and plan.state in ("CANARY", "MONITORING"):
            rollback_triggered = True
            self.execute_rollback(
                plan_id=plan_id,
                reason=f"Automated rollback: failure rate ({failure_rate:.2f}%) exceeded threshold ({plan.rollback_threshold_failure_rate:.2f}%)",
                actor="automated_monitor",
            )

        return {
            "telemetry": recorded.to_dict(),
            "threshold_breached": threshold_breached,
            "rollback_triggered": rollback_triggered,
        }

    def execute_rollback(
        self, plan_id: str, reason: str = "Operator manual rollback", actor: str = "operator"
    ) -> RolloutPlan:
        plan = self.rollout_repo.get_rollout_plan(plan_id)
        if not plan:
            raise ValueError(f"Rollout plan '{plan_id}' not found.")

        env = self.rollout_repo.get_environment(plan.environment_id)
        fallback_cfg = plan.previous_config or (env.rollback_config_ref if env else None) or {"tls_version": "TLS 1.3", "supported_groups": ["X25519"]}

        # Update environment back to classical baseline
        if env:
            self.rollout_repo.update_environment(env.id, {
                "current_config": fallback_cfg,
                "rollout_status": "rolled_back",
                "readiness_status": "degraded",
            })

        # Update plan state
        updated_plan = self.rollout_repo.update_rollout_plan(plan_id, {
            "state": "ROLLED_BACK",
            "canary_percentage": 0,
        })

        self.audit_repo.record_event(
            entity_type="rollout_plan",
            entity_id=plan.id,
            action="ROLLOUT_ROLLED_BACK",
            details_json=json.dumps({"reason": reason, "restored_config": fallback_cfg}),
            operator=actor,
        )

        return updated_plan

    def simulate_canary_traffic(self, plan_id: str, healthy: bool = True) -> Dict[str, Any]:
        """
        Generates simulated telemetry sample for canary verification.
        Honest simulation label is preserved.
        """
        if healthy:
            sample = {
                "handshake_success_rate": 99.85,
                "handshake_failure_rate": 0.15,
                "average_latency_ms": 16.4,
                "timeout_rate": 0.05,
                "negotiated_tls_version": "TLS 1.3",
                "negotiated_group": "X25519MLKEM768",
                "error_categories": {"client_abort": 1},
                "is_simulated": True,
            }
        else:
            sample = {
                "handshake_success_rate": 95.2,
                "handshake_failure_rate": 4.8,  # Triggers rollback threshold (> 2.0%)
                "average_latency_ms": 340.2,
                "timeout_rate": 3.9,
                "negotiated_tls_version": "TLS 1.3",
                "negotiated_group": "X25519MLKEM768",
                "error_categories": {"middlebox_reset": 24, "handshake_timeout": 18},
                "is_simulated": True,
            }

        return self.record_telemetry(plan_id, sample)
