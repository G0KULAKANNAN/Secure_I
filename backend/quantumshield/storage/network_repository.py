"""
Network Repository for profiles and verification results persistence.
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from quantumshield.storage.database import get_db_connection
from quantumshield.models.network import (
    NetworkProfile,
    NetworkVerificationResult,
    utc_now_iso,
)


class NetworkRepository:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    # --- Verification Profiles ---
    def create_profile(self, profile: NetworkProfile) -> NetworkProfile:
        profile.validate()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO network_verification_profiles (
                        id, name, target_host, target_port, environment,
                        test_profile, test_mode, expected_mtu, connection_timeout,
                        handshake_timeout, max_retries, is_allowlisted, authorized_by_operator,
                        operator_notes, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        profile.id,
                        profile.name,
                        profile.target_host,
                        profile.target_port,
                        profile.environment,
                        profile.test_profile,
                        profile.test_mode,
                        profile.expected_mtu,
                        profile.connection_timeout,
                        profile.handshake_timeout,
                        profile.max_retries,
                        1 if profile.is_allowlisted else 0,
                        1 if profile.authorized_by_operator else 0,
                        profile.operator_notes,
                        profile.status,
                        profile.created_at,
                        profile.updated_at,
                    ),
                )
        finally:
            conn.close()
        return profile

    def get_profile_by_id(self, profile_id: str) -> Optional[NetworkProfile]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM network_verification_profiles WHERE id = ?;", (profile_id,))
            row = cursor.fetchone()
            return NetworkProfile.from_dict(dict(row)) if row else None
        finally:
            conn.close()

    def get_profile_by_name(self, name: str) -> Optional[NetworkProfile]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM network_verification_profiles WHERE name = ?;", (name,))
            row = cursor.fetchone()
            return NetworkProfile.from_dict(dict(row)) if row else None
        finally:
            conn.close()

    def list_profiles(self) -> List[NetworkProfile]:
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM network_verification_profiles ORDER BY created_at DESC;")
            rows = cursor.fetchall()
            return [NetworkProfile.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()

    def update_profile(self, profile: NetworkProfile) -> NetworkProfile:
        profile.validate()
        profile.updated_at = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE network_verification_profiles SET
                        name = ?,
                        target_host = ?,
                        target_port = ?,
                        environment = ?,
                        test_profile = ?,
                        test_mode = ?,
                        expected_mtu = ?,
                        connection_timeout = ?,
                        handshake_timeout = ?,
                        max_retries = ?,
                        is_allowlisted = ?,
                        authorized_by_operator = ?,
                        operator_notes = ?,
                        status = ?,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (
                        profile.name,
                        profile.target_host,
                        profile.target_port,
                        profile.environment,
                        profile.test_profile,
                        profile.test_mode,
                        profile.expected_mtu,
                        profile.connection_timeout,
                        profile.handshake_timeout,
                        profile.max_retries,
                        1 if profile.is_allowlisted else 0,
                        1 if profile.authorized_by_operator else 0,
                        profile.operator_notes,
                        profile.status,
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
                cursor = conn.execute("DELETE FROM network_verification_profiles WHERE id = ?;", (profile_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    # --- Verification Results ---
    def save_result(self, result: NetworkVerificationResult) -> NetworkVerificationResult:
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO network_verification_results (
                        id, profile_id, job_id, test_mode, target_endpoint,
                        address_family, configured_mtu, tls_version, negotiated_group,
                        handshake_success, diagnostic_classification, diagnostic_finding,
                        observed_error, duration_ms, retry_count, packet_size_estimate_bytes,
                        evidence_level, evidence_details_json, remediation_recommendations_json,
                        confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        result.id,
                        result.profile_id,
                        result.job_id,
                        result.test_mode,
                        result.target_endpoint,
                        result.address_family,
                        result.configured_mtu,
                        result.tls_version,
                        result.negotiated_group,
                        1 if result.handshake_success else 0,
                        result.diagnostic_classification,
                        result.diagnostic_finding,
                        result.observed_error,
                        result.duration_ms,
                        result.retry_count,
                        result.packet_size_estimate_bytes,
                        result.evidence_level,
                        result.evidence_details_json,
                        result.remediation_recommendations_json,
                        result.confidence,
                        result.created_at,
                    ),
                )
        finally:
            conn.close()
        return result

    def list_results(
        self,
        profile_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[NetworkVerificationResult]:
        conn = get_db_connection(self.db_path)
        clauses = []
        params = []
        if profile_id:
            clauses.append("profile_id = ?")
            params.append(profile_id)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM network_verification_results {where} ORDER BY created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [NetworkVerificationResult.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()
