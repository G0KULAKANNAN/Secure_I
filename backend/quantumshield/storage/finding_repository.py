"""
Finding Repository for SQLite Persistence and Deduplication.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union, Dict, Any
from quantumshield.storage.database import get_db_connection
from quantumshield.models.finding import Finding, utc_now_iso


class FindingRepository:
    """Repository handling findings persistence, fingerprint deduplication, and status updates."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    def save_finding(self, finding: Finding) -> Finding:
        """
        Insert or update a cryptographic finding using deterministic fingerprint deduplication.
        """
        now = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                # Check for existing finding with same fingerprint
                cursor = conn.execute(
                    "SELECT id, created_at, remediation_status FROM findings WHERE fingerprint = ?;",
                    (finding.fingerprint,),
                )
                existing = cursor.fetchone()
                if existing:
                    # Update updated_at and scan trace
                    conn.execute(
                        """
                        UPDATE findings SET
                            scan_run_id = COALESCE(?, scan_run_id),
                            job_id = COALESCE(?, job_id),
                            updated_at = ?,
                            evidence = ?,
                            title = ?,
                            description = ?,
                            severity = ?
                        WHERE fingerprint = ?;
                        """,
                        (
                            finding.scan_run_id,
                            finding.job_id,
                            now,
                            finding.evidence,
                            finding.title,
                            finding.description,
                            finding.severity,
                            finding.fingerprint,
                        ),
                    )
                    finding.id = existing["id"]
                    finding.created_at = existing["created_at"]
                    finding.updated_at = now
                    finding.remediation_status = existing["remediation_status"]
                else:
                    finding.created_at = now
                    finding.updated_at = now
                    conn.execute(
                        """
                        INSERT INTO findings (
                            id, asset_id, scan_run_id, job_id, scanner_type,
                            algorithm, cryptographic_primitive, quantum_vulnerable,
                            recommended_pqc, rule_id, title, description,
                            severity, evidence, file_path, line_number,
                            confidence, remediation_status, fingerprint,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            finding.id,
                            finding.asset_id,
                            finding.scan_run_id,
                            finding.job_id,
                            finding.scanner_type,
                            finding.algorithm,
                            finding.cryptographic_primitive,
                            1 if finding.quantum_vulnerable else 0,
                            finding.recommended_pqc,
                            finding.rule_id,
                            finding.title,
                            finding.description,
                            finding.severity,
                            finding.evidence,
                            finding.file_path,
                            finding.line_number,
                            finding.confidence,
                            finding.remediation_status,
                            finding.fingerprint,
                            finding.created_at,
                            finding.updated_at,
                        ),
                    )
        finally:
            conn.close()

        return finding

    def get_by_id(self, finding_id: str) -> Optional[Finding]:
        """Retrieve finding by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM findings WHERE id = ?;", (finding_id,))
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return None
        return Finding.from_dict(dict(row))

    def list_findings(
        self,
        asset_id: Optional[str] = None,
        scan_run_id: Optional[str] = None,
        severity: Optional[str] = None,
        scanner_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Finding], int]:
        """List findings with filtering and pagination."""
        conditions = []
        params = []

        if asset_id and asset_id.strip():
            conditions.append("asset_id = ?")
            params.append(asset_id.strip())

        if scan_run_id and scan_run_id.strip():
            conditions.append("scan_run_id = ?")
            params.append(scan_run_id.strip())

        if severity and severity.strip():
            conditions.append("severity = ?")
            params.append(severity.strip().lower())

        if scanner_type and scanner_type.strip():
            conditions.append("scanner_type = ?")
            params.append(scanner_type.strip().lower())

        if status and status.strip():
            conditions.append("remediation_status = ?")
            params.append(status.strip().lower())

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        conn = get_db_connection(self.db_path)
        try:
            count_query = f"SELECT COUNT(*) AS total FROM findings {where_clause};"
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["total"]

            data_query = f"""
                SELECT * FROM findings
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?;
            """
            query_params = list(params) + [max(1, limit), max(0, offset)]
            cursor = conn.execute(data_query, query_params)
            rows = cursor.fetchall()
        finally:
            conn.close()

        findings = [Finding.from_dict(dict(r)) for r in rows]
        return findings, total

    def update_status(self, finding_id: str, new_status: str) -> Optional[Finding]:
        """Update remediation status of a finding."""
        now = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE findings SET
                        remediation_status = ?,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (new_status.lower(), now, finding_id),
                )
                affected = cursor.rowcount
        finally:
            conn.close()

        if affected == 0:
            return None
        return self.get_by_id(finding_id)

    def get_stats(self, asset_id: Optional[str] = None) -> Dict[str, Any]:
        """Return counts of findings grouped by severity and quantum vulnerability."""
        conn = get_db_connection(self.db_path)
        where_clause = "WHERE asset_id = ?" if asset_id else ""
        params = [asset_id] if asset_id else []

        try:
            query = f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low,
                    SUM(CASE WHEN quantum_vulnerable = 1 THEN 1 ELSE 0 END) as quantum_vulnerable
                FROM findings {where_clause};
            """
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
        finally:
            conn.close()

        return {
            "total": row["total"] or 0,
            "total_findings": row["total"] or 0,
            "critical": row["critical"] or 0,
            "high": row["high"] or 0,
            "medium": row["medium"] or 0,
            "low": row["low"] or 0,
            "quantum_vulnerable": row["quantum_vulnerable"] or 0,
        }
