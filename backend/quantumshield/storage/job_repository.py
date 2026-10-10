"""
Job Repository for Persistent Background Job Processing in SQLite.
"""

from pathlib import Path
import json
from typing import List, Optional, Tuple, Union
from quantumshield.storage.database import get_db_connection
from quantumshield.models.job import ScanJob, utc_now_iso


class JobRepository:
    """Repository handling persistence, transitions, and queue claiming for scan jobs."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    def create(self, job: ScanJob) -> ScanJob:
        """Insert a new scan job into SQLite."""
        job.validate()
        result_str = None
        if job.result_data:
            result_str = job.result_data if isinstance(job.result_data, str) else json.dumps(job.result_data)

        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute(
                """
                INSERT INTO scan_jobs (
                    id, job_type, asset_id, operation, status,
                    created_at, started_at, completed_at, progress,
                    retry_count, max_retries, error_message, result_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    job.id,
                    job.job_type.lower(),
                    job.asset_id.strip(),
                    job.operation.strip(),
                    job.status.lower(),
                    job.created_at,
                    job.started_at,
                    job.completed_at,
                    job.progress,
                    job.retry_count,
                    job.max_retries,
                    job.error_message,
                    result_str,
                ),
            )
        conn.close()
        return job

    def get_by_id(self, job_id: str) -> Optional[ScanJob]:
        """Fetch a single scan job by ID."""
        conn = get_db_connection(self.db_path)
        cursor = conn.execute("SELECT * FROM scan_jobs WHERE id = ?;", (job_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return ScanJob.from_dict(dict(row))

    def list_jobs(
        self,
        asset_id: Optional[str] = None,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ScanJob], int]:
        """List jobs with filtering and pagination."""
        conditions = []
        params = []

        if asset_id and asset_id.strip():
            conditions.append("asset_id = ?")
            params.append(asset_id.strip())

        if status and status.strip():
            conditions.append("status = ?")
            params.append(status.strip().lower())

        if job_type and job_type.strip():
            conditions.append("job_type = ?")
            params.append(job_type.strip().lower())

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        conn = get_db_connection(self.db_path)

        # Count total matching rows
        count_query = f"SELECT COUNT(*) AS total FROM scan_jobs {where_clause};"
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()["total"]

        # Fetch paginated rows ordered by created_at descending
        data_query = f"""
            SELECT * FROM scan_jobs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?;
        """
        query_params = list(params) + [max(1, limit), max(0, offset)]
        cursor = conn.execute(data_query, query_params)
        rows = cursor.fetchall()
        conn.close()

        jobs = [ScanJob.from_dict(dict(r)) for r in rows]
        return jobs, total

    def update(self, job: ScanJob) -> Optional[ScanJob]:
        """Update job fields in SQLite."""
        job.validate()
        result_str = None
        if job.result_data:
            result_str = job.result_data if isinstance(job.result_data, str) else json.dumps(job.result_data)

        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute(
                """
                UPDATE scan_jobs SET
                    job_type = ?,
                    asset_id = ?,
                    operation = ?,
                    status = ?,
                    started_at = ?,
                    completed_at = ?,
                    progress = ?,
                    retry_count = ?,
                    max_retries = ?,
                    error_message = ?,
                    result_data = ?
                WHERE id = ?;
                """,
                (
                    job.job_type.lower(),
                    job.asset_id.strip(),
                    job.operation.strip(),
                    job.status.lower(),
                    job.started_at,
                    job.completed_at,
                    job.progress,
                    job.retry_count,
                    job.max_retries,
                    job.error_message,
                    result_str,
                    job.id,
                ),
            )
            affected = cursor.rowcount
        conn.close()

        if affected == 0:
            return None
        return job

    def claim_next_job(self) -> Optional[ScanJob]:
        """
        Atomically claim the next eligible job (pending or queued) and transition to running.
        Ensures thread-safe claiming in SQLite.
        """
        conn = get_db_connection(self.db_path)
        updated_row = None
        try:
            with conn:
                cursor = conn.execute(
                    """
                    SELECT id FROM scan_jobs
                    WHERE status IN ('pending', 'queued')
                    ORDER BY created_at ASC
                    LIMIT 1;
                    """
                )
                row = cursor.fetchone()
                if row:
                    job_id = row["id"]
                    now_iso = utc_now_iso()
                    conn.execute(
                        """
                        UPDATE scan_jobs SET
                            status = 'running',
                            started_at = ?,
                            progress = 10
                        WHERE id = ? AND status IN ('pending', 'queued');
                        """,
                        (now_iso, job_id),
                    )
                    cursor = conn.execute("SELECT * FROM scan_jobs WHERE id = ?;", (job_id,))
                    updated_row = cursor.fetchone()
        finally:
            conn.close()

        if not updated_row:
            return None
        return ScanJob.from_dict(dict(updated_row))

    def cancel(self, job_id: str) -> bool:
        """Cancel a pending, queued, or running job."""
        now_iso = utc_now_iso()
        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute(
                """
                UPDATE scan_jobs SET
                    status = 'cancelled',
                    completed_at = ?,
                    error_message = 'Job cancelled by user request.'
                WHERE id = ? AND status IN ('pending', 'queued', 'running');
                """,
                (now_iso, job_id),
            )
            affected = cursor.rowcount
        conn.close()
        return affected > 0

    def retry(self, job_id: str) -> Optional[ScanJob]:
        """
        Retry a failed or cancelled job if within max_retries limit.
        """
        job = self.get_by_id(job_id)
        if not job:
            return None

        if job.retry_count >= job.max_retries:
            return None

        job.retry_count += 1
        job.status = "queued"
        job.started_at = None
        job.completed_at = None
        job.error_message = None
        job.progress = 0
        return self.update(job)

    def recover_stale_jobs(self) -> int:
        """
        Find any jobs that were left in 'running' state (due to unexpected process termination)
        and mark them as failed with recovery notice or re-queue them.
        """
        now_iso = utc_now_iso()
        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute(
                """
                UPDATE scan_jobs SET
                    status = 'failed',
                    completed_at = ?,
                    error_message = 'Job aborted due to unexpected worker or server restart.'
                WHERE status = 'running';
                """,
                (now_iso,),
            )
            affected = cursor.rowcount
        conn.close()
        return affected
