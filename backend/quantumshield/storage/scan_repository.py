"""
Scan Run Repository for SQLite Persistence.
Manages orchestrated scan runs and historical run traces.
"""

from pathlib import Path
import json
from typing import List, Optional, Tuple, Union
from quantumshield.storage.database import get_db_connection
from quantumshield.models.scan_run import ScanRun, utc_now_iso


class ScanRepository:
    """Repository managing scan runs in SQLite."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    def create(self, run: ScanRun) -> ScanRun:
        """Insert a new scan run record."""
        scanners_str = json.dumps(run.requested_scanners)
        summary_str = json.dumps(run.result_summary) if run.result_summary else None

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO scan_runs (
                        id, asset_id, requested_scanners, status,
                        created_at, started_at, completed_at,
                        total_jobs, completed_jobs, failed_jobs, cancelled_jobs,
                        result_summary, error_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        run.id,
                        run.asset_id,
                        scanners_str,
                        run.status,
                        run.created_at,
                        run.started_at,
                        run.completed_at,
                        run.total_jobs,
                        run.completed_jobs,
                        run.failed_jobs,
                        run.cancelled_jobs,
                        summary_str,
                        run.error_summary,
                    ),
                )
        finally:
            conn.close()
        return run

    def get_by_id(self, scan_run_id: str) -> Optional[ScanRun]:
        """Retrieve a scan run by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM scan_runs WHERE id = ?;", (scan_run_id,))
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return None
        return ScanRun.from_dict(dict(row))

    def list_scan_runs(
        self,
        asset_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ScanRun], int]:
        """List scan runs with filtering and pagination."""
        conditions = []
        params = []

        if asset_id and asset_id.strip():
            conditions.append("asset_id = ?")
            params.append(asset_id.strip())

        if status and status.strip():
            conditions.append("status = ?")
            params.append(status.strip().lower())

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        conn = get_db_connection(self.db_path)
        try:
            count_query = f"SELECT COUNT(*) AS total FROM scan_runs {where_clause};"
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["total"]

            data_query = f"""
                SELECT * FROM scan_runs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?;
            """
            query_params = list(params) + [max(1, limit), max(0, offset)]
            cursor = conn.execute(data_query, query_params)
            rows = cursor.fetchall()
        finally:
            conn.close()

        runs = [ScanRun.from_dict(dict(r)) for r in rows]
        return runs, total

    def update(self, run: ScanRun) -> Optional[ScanRun]:
        """Update scan run record in SQLite."""
        scanners_str = json.dumps(run.requested_scanners)
        summary_str = json.dumps(run.result_summary) if run.result_summary else None

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE scan_runs SET
                        status = ?,
                        started_at = ?,
                        completed_at = ?,
                        total_jobs = ?,
                        completed_jobs = ?,
                        failed_jobs = ?,
                        cancelled_jobs = ?,
                        result_summary = ?,
                        error_summary = ?
                    WHERE id = ?;
                    """,
                    (
                        run.status,
                        run.started_at,
                        run.completed_at,
                        run.total_jobs,
                        run.completed_jobs,
                        run.failed_jobs,
                        run.cancelled_jobs,
                        summary_str,
                        run.error_summary,
                        run.id,
                    ),
                )
                affected = cursor.rowcount
        finally:
            conn.close()

        if affected == 0:
            return None
        return run

    def get_active_scan_run_for_asset(self, asset_id: str) -> Optional[ScanRun]:
        """Check if an active scan run is already in progress for this asset."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT * FROM scan_runs
                WHERE asset_id = ? AND status IN ('queued', 'running')
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (asset_id,),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return None
        return ScanRun.from_dict(dict(row))
