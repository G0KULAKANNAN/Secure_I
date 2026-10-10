"""
Hybrid Repository for capabilities registry, staging profiles, and verification runs.
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Tuple
import json
from quantumshield.storage.database import get_db_connection
from quantumshield.models.hybrid import (
    CryptoCapability,
    HybridProfile,
    HybridVerificationRun,
    utc_now_iso,
)


class HybridRepository:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    # --- Capabilities Registry ---
    def list_capabilities(self) -> List[CryptoCapability]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM crypto_capabilities ORDER BY hybrid_combination ASC;")
            rows = cursor.fetchall()
            return [CryptoCapability.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()

    def get_capability_by_combination(self, combination: str) -> Optional[CryptoCapability]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT * FROM crypto_capabilities WHERE hybrid_combination = ?;",
                (combination,),
            )
            row = cursor.fetchone()
            return CryptoCapability.from_dict(dict(row)) if row else None
        finally:
            conn.close()

    # --- Hybrid Profiles ---
    def create_profile(self, profile: HybridProfile) -> HybridProfile:
        profile.validate()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO hybrid_profiles (
                        id, profile_name, classical_component, pqc_component,
                        environment, rollout_status, migration_state, automatic_production_prohibited,
                        previous_config_json, proposed_config_json, approved_by, approved_at,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        profile.id,
                        profile.profile_name,
                        profile.classical_component,
                        profile.pqc_component,
                        profile.environment,
                        profile.rollout_status,
                        profile.migration_state,
                        1 if profile.automatic_production_prohibited else 0,
                        profile.previous_config_json,
                        profile.proposed_config_json,
                        profile.approved_by,
                        profile.approved_at,
                        profile.created_at,
                        profile.updated_at,
                    ),
                )
        finally:
            conn.close()
        return profile

    def get_profile_by_id(self, profile_id: str) -> Optional[HybridProfile]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM hybrid_profiles WHERE id = ?;", (profile_id,))
            row = cursor.fetchone()
            return HybridProfile.from_dict(dict(row)) if row else None
        finally:
            conn.close()

    def get_profile_by_name(self, name: str) -> Optional[HybridProfile]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM hybrid_profiles WHERE profile_name = ?;", (name,))
            row = cursor.fetchone()
            return HybridProfile.from_dict(dict(row)) if row else None
        finally:
            conn.close()

    def list_profiles(self) -> List[HybridProfile]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM hybrid_profiles ORDER BY created_at DESC;")
            rows = cursor.fetchall()
            return [HybridProfile.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()

    def update_profile(self, profile: HybridProfile) -> HybridProfile:
        profile.validate()
        profile.updated_at = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE hybrid_profiles SET
                        profile_name = ?,
                        classical_component = ?,
                        pqc_component = ?,
                        rollout_status = ?,
                        migration_state = ?,
                        previous_config_json = ?,
                        proposed_config_json = ?,
                        approved_by = ?,
                        approved_at = ?,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (
                        profile.profile_name,
                        profile.classical_component,
                        profile.pqc_component,
                        profile.rollout_status,
                        profile.migration_state,
                        profile.previous_config_json,
                        profile.proposed_config_json,
                        profile.approved_by,
                        profile.approved_at,
                        profile.updated_at,
                        profile.id,
                    ),
                )
        finally:
            conn.close()
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute("DELETE FROM hybrid_profiles WHERE id = ?;", (profile_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    # --- Verification Runs ---
    def save_verification_run(self, run: HybridVerificationRun) -> HybridVerificationRun:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO hybrid_verification_runs (
                        id, profile_id, test_mode, status, negotiation_outcome,
                        classical_client_compatible, hybrid_client_compatible,
                        observed_tls_version, negotiated_group, error_details,
                        duration_ms, is_simulated, operator, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        run.id,
                        run.profile_id,
                        run.test_mode,
                        run.status,
                        run.negotiation_outcome,
                        1 if run.classical_client_compatible else 0,
                        1 if run.hybrid_client_compatible else 0,
                        run.observed_tls_version,
                        run.negotiated_group,
                        run.error_details,
                        run.duration_ms,
                        1 if run.is_simulated else 0,
                        run.operator,
                        run.created_at,
                    ),
                )
        finally:
            conn.close()
        return run

    def list_runs_for_profile(self, profile_id: str, limit: int = 20) -> List[HybridVerificationRun]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT * FROM hybrid_verification_runs WHERE profile_id = ? ORDER BY created_at DESC LIMIT ?;",
                (profile_id, limit),
            )
            rows = cursor.fetchall()
            return [HybridVerificationRun.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()
