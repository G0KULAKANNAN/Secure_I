"""
Rollout Repository for environments, rollout plans, and telemetry.
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import json
from datetime import datetime, timezone

from quantumshield.storage.database import get_db_connection
from quantumshield.models.rollout import (
    DeploymentEnvironment,
    RolloutPlan,
    TelemetryEvent,
)


class RolloutRepository:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    # --- Deployment Environments ---
    def list_environments(self) -> List[DeploymentEnvironment]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM deployment_environments ORDER BY category ASC, name ASC;")
            rows = cursor.fetchall()
            return [DeploymentEnvironment.from_row(r) for r in rows]
        finally:
            conn.close()

    def get_environment(self, env_id: str) -> Optional[DeploymentEnvironment]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM deployment_environments WHERE id = ?;", (env_id,))
            row = cursor.fetchone()
            return DeploymentEnvironment.from_row(row) if row else None
        finally:
            conn.close()

    def update_environment(self, env_id: str, updates: Dict[str, Any]) -> Optional[DeploymentEnvironment]:
        conn = get_db_connection(self.db_path)
        try:
            now = datetime.now(timezone.utc).isoformat()
            set_clauses = ["updated_at = ?"]
            params: List[Any] = [now]

            for key, val in updates.items():
                if key in ("current_config", "desired_config", "supported_groups", "rollback_config_ref"):
                    col_name = f"{key}_json" if key != "rollback_config_ref" else "rollback_config_ref"
                    set_clauses.append(f"{col_name} = ?")
                    params.append(json.dumps(val) if val is not None else None)
                elif key in ("name", "category", "managed_service", "owner", "supported_tls_version",
                             "client_compatibility_reqs", "readiness_status", "rollout_status"):
                    set_clauses.append(f"{key} = ?")
                    params.append(val)

            params.append(env_id)
            with conn:
                conn.execute(
                    f"UPDATE deployment_environments SET {', '.join(set_clauses)} WHERE id = ?;",
                    params,
                )
            return self.get_environment(env_id)
        finally:
            conn.close()

    # --- Rollout Plans ---
    def create_rollout_plan(self, plan: RolloutPlan) -> RolloutPlan:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO rollout_plans (
                        id, name, environment_id, current_stage, state,
                        canary_percentage, previous_config_json, target_config_json,
                        readiness_assessment_json, rollback_threshold_failure_rate,
                        approved_by, approved_at, last_advanced_at, deployment_mode,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        plan.id,
                        plan.name,
                        plan.environment_id,
                        plan.current_stage,
                        plan.state,
                        plan.canary_percentage,
                        json.dumps(plan.previous_config) if plan.previous_config is not None else None,
                        json.dumps(plan.target_config),
                        json.dumps(plan.readiness_assessment) if plan.readiness_assessment is not None else None,
                        plan.rollback_threshold_failure_rate,
                        plan.approved_by,
                        plan.approved_at,
                        plan.last_advanced_at,
                        plan.deployment_mode,
                        plan.created_at,
                        plan.updated_at,
                    ),
                )
            return plan
        finally:
            conn.close()

    def get_rollout_plan(self, plan_id: str) -> Optional[RolloutPlan]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM rollout_plans WHERE id = ?;", (plan_id,))
            row = cursor.fetchone()
            return RolloutPlan.from_row(row) if row else None
        finally:
            conn.close()

    def get_rollout_plan_by_name(self, name: str) -> Optional[RolloutPlan]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM rollout_plans WHERE name = ?;", (name,))
            row = cursor.fetchone()
            return RolloutPlan.from_row(row) if row else None
        finally:
            conn.close()

    def list_rollout_plans(
        self, environment_id: Optional[str] = None, state: Optional[str] = None
    ) -> List[RolloutPlan]:
        conn = get_db_connection(self.db_path)
        try:
            sql = "SELECT * FROM rollout_plans WHERE 1=1"
            params: List[Any] = []
            if environment_id:
                sql += " AND environment_id = ?"
                params.append(environment_id)
            if state:
                sql += " AND state = ?"
                params.append(state)
            sql += " ORDER BY created_at DESC;"

            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [RolloutPlan.from_row(r) for r in rows]
        finally:
            conn.close()

    def update_rollout_plan(self, plan_id: str, updates: Dict[str, Any]) -> Optional[RolloutPlan]:
        conn = get_db_connection(self.db_path)
        try:
            now = datetime.now(timezone.utc).isoformat()
            set_clauses = ["updated_at = ?"]
            params: List[Any] = [now]

            for key, val in updates.items():
                if key in ("previous_config", "target_config", "readiness_assessment"):
                    set_clauses.append(f"{key}_json = ?")
                    params.append(json.dumps(val) if val is not None else None)
                elif key in (
                    "current_stage", "state", "canary_percentage",
                    "rollback_threshold_failure_rate", "approved_by",
                    "approved_at", "last_advanced_at", "deployment_mode"
                ):
                    set_clauses.append(f"{key} = ?")
                    params.append(val)

            params.append(plan_id)
            with conn:
                conn.execute(
                    f"UPDATE rollout_plans SET {', '.join(set_clauses)} WHERE id = ?;",
                    params,
                )
            return self.get_rollout_plan(plan_id)
        finally:
            conn.close()

    # --- Telemetry Events ---
    def record_telemetry(self, telemetry: TelemetryEvent) -> TelemetryEvent:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO telemetry_events (
                        id, rollout_id, stage, handshake_success_rate,
                        handshake_failure_rate, average_latency_ms, timeout_rate,
                        negotiated_tls_version, negotiated_group, error_categories_json,
                        is_simulated, recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        telemetry.id,
                        telemetry.rollout_id,
                        telemetry.stage,
                        telemetry.handshake_success_rate,
                        telemetry.handshake_failure_rate,
                        telemetry.average_latency_ms,
                        telemetry.timeout_rate,
                        telemetry.negotiated_tls_version,
                        telemetry.negotiated_group,
                        json.dumps(telemetry.error_categories) if telemetry.error_categories else None,
                        1 if telemetry.is_simulated else 0,
                        telemetry.recorded_at,
                    ),
                )
            return telemetry
        finally:
            conn.close()

    def get_telemetry_for_rollout(self, rollout_id: str, limit: int = 50) -> List[TelemetryEvent]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT * FROM telemetry_events
                WHERE rollout_id = ?
                ORDER BY recorded_at DESC
                LIMIT ?;
                """,
                (rollout_id, limit),
            )
            rows = cursor.fetchall()
            return [TelemetryEvent.from_row(r) for r in rows]
        finally:
            conn.close()
