"""
Decommissioning Repository for policies, cryptographic dependencies, and decommissioning plans.
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import json
from datetime import datetime, timezone

from quantumshield.storage.database import get_db_connection
from quantumshield.models.decommissioning import (
    DecommissioningPolicy,
    CryptoDependency,
    DecommissioningPlan,
)


class DecommissioningRepository:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    # --- Policies ---
    def list_policies(
        self, status: Optional[str] = None, category: Optional[str] = None
    ) -> List[DecommissioningPolicy]:
        conn = get_db_connection(self.db_path)
        try:
            sql = "SELECT * FROM decommissioning_policies WHERE 1=1"
            params: List[Any] = []
            if status:
                sql += " AND status = ?"
                params.append(status)
            if category:
                sql += " AND primitive_category = ?"
                params.append(category)
            sql += " ORDER BY primitive_category ASC, name ASC;"

            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [DecommissioningPolicy.from_row(r) for r in rows]
        finally:
            conn.close()

    def get_policy(self, policy_id: str) -> Optional[DecommissioningPolicy]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM decommissioning_policies WHERE id = ?;", (policy_id,))
            row = cursor.fetchone()
            return DecommissioningPolicy.from_row(row) if row else None
        finally:
            conn.close()

    def get_policy_by_algorithm(self, algorithm: str) -> Optional[DecommissioningPolicy]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT * FROM decommissioning_policies WHERE LOWER(algorithm) = LOWER(?);",
                (algorithm.strip(),),
            )
            row = cursor.fetchone()
            return DecommissioningPolicy.from_row(row) if row else None
        finally:
            conn.close()

    def create_policy(self, policy: DecommissioningPolicy) -> DecommissioningPolicy:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO decommissioning_policies (
                        id, name, algorithm, primitive_category, status,
                        conditions, enforcement_deadline, rationale, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        policy.id,
                        policy.name,
                        policy.algorithm,
                        policy.primitive_category,
                        policy.status,
                        policy.conditions,
                        policy.enforcement_deadline,
                        policy.rationale,
                        policy.created_at,
                        policy.updated_at,
                    ),
                )
            return policy
        finally:
            conn.close()

    # --- Crypto Dependencies ---
    def list_dependencies(
        self,
        status: Optional[str] = None,
        primitive_category: Optional[str] = None,
        service_name: Optional[str] = None,
    ) -> List[CryptoDependency]:
        conn = get_db_connection(self.db_path)
        try:
            sql = "SELECT * FROM crypto_dependencies WHERE 1=1"
            params: List[Any] = []
            if status:
                sql += " AND status = ?"
                params.append(status)
            if primitive_category:
                sql += " AND primitive_category = ?"
                params.append(primitive_category)
            if service_name:
                sql += " AND service_name = ?"
                params.append(service_name)
            sql += " ORDER BY service_name ASC, primitive_category ASC;"

            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [CryptoDependency.from_row(r) for r in rows]
        finally:
            conn.close()

    def get_dependency(self, dep_id: str) -> Optional[CryptoDependency]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM crypto_dependencies WHERE id = ?;", (dep_id,))
            row = cursor.fetchone()
            return CryptoDependency.from_row(row) if row else None
        finally:
            conn.close()

    def create_dependency(self, dep: CryptoDependency) -> CryptoDependency:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO crypto_dependencies (
                        id, asset_id, service_name, primitive_category,
                        current_algorithm, target_algorithm, status, policy_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        dep.id,
                        dep.asset_id,
                        dep.service_name,
                        dep.primitive_category,
                        dep.current_algorithm,
                        dep.target_algorithm,
                        dep.status,
                        dep.policy_id,
                        dep.created_at,
                        dep.updated_at,
                    ),
                )
            return dep
        finally:
            conn.close()

    def update_dependency(self, dep_id: str, updates: Dict[str, Any]) -> Optional[CryptoDependency]:
        conn = get_db_connection(self.db_path)
        try:
            now = datetime.now(timezone.utc).isoformat()
            set_clauses = ["updated_at = ?"]
            params: List[Any] = [now]

            for key, val in updates.items():
                if key in ("asset_id", "service_name", "primitive_category", "current_algorithm",
                           "target_algorithm", "status", "policy_id"):
                    set_clauses.append(f"{key} = ?")
                    params.append(val)

            params.append(dep_id)
            with conn:
                conn.execute(
                    f"UPDATE crypto_dependencies SET {', '.join(set_clauses)} WHERE id = ?;",
                    params,
                )
            return self.get_dependency(dep_id)
        finally:
            conn.close()

    # --- Decommissioning Plans ---
    def list_plans(self, state: Optional[str] = None) -> List[DecommissioningPlan]:
        conn = get_db_connection(self.db_path)
        try:
            sql = "SELECT * FROM decommissioning_plans WHERE 1=1"
            params: List[Any] = []
            if state:
                sql += " AND state = ?"
                params.append(state)
            sql += " ORDER BY created_at DESC;"

            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [DecommissioningPlan.from_row(r) for r in rows]
        finally:
            conn.close()

    def get_plan(self, plan_id: str) -> Optional[DecommissioningPlan]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM decommissioning_plans WHERE id = ?;", (plan_id,))
            row = cursor.fetchone()
            return DecommissioningPlan.from_row(row) if row else None
        finally:
            conn.close()

    def get_plan_by_name(self, name: str) -> Optional[DecommissioningPlan]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM decommissioning_plans WHERE name = ?;", (name,))
            row = cursor.fetchone()
            return DecommissioningPlan.from_row(row) if row else None
        finally:
            conn.close()

    def create_plan(self, plan: DecommissioningPlan) -> DecommissioningPlan:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO decommissioning_plans (
                        id, name, target_primitive, affected_services_json,
                        state, readiness_assessment_json, approved_by,
                        approved_at, decommissioned_at, rollback_instructions,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        plan.id,
                        plan.name,
                        plan.target_primitive,
                        json.dumps(plan.affected_services),
                        plan.state,
                        json.dumps(plan.readiness_assessment) if plan.readiness_assessment else None,
                        plan.approved_by,
                        plan.approved_at,
                        plan.decommissioned_at,
                        plan.rollback_instructions,
                        plan.created_at,
                        plan.updated_at,
                    ),
                )
            return plan
        finally:
            conn.close()

    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Optional[DecommissioningPlan]:
        conn = get_db_connection(self.db_path)
        try:
            now = datetime.now(timezone.utc).isoformat()
            set_clauses = ["updated_at = ?"]
            params: List[Any] = [now]

            for key, val in updates.items():
                if key == "affected_services":
                    set_clauses.append("affected_services_json = ?")
                    params.append(json.dumps(val))
                elif key == "readiness_assessment":
                    set_clauses.append("readiness_assessment_json = ?")
                    params.append(json.dumps(val) if val is not None else None)
                elif key in ("name", "target_primitive", "state", "approved_by",
                             "approved_at", "decommissioned_at", "rollback_instructions"):
                    set_clauses.append(f"{key} = ?")
                    params.append(val)

            params.append(plan_id)
            with conn:
                conn.execute(
                    f"UPDATE decommissioning_plans SET {', '.join(set_clauses)} WHERE id = ?;",
                    params,
                )
            return self.get_plan(plan_id)
        finally:
            conn.close()
