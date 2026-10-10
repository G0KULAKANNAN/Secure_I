"""
Job Repository for Persistent Background Job Processing in SQLite.
Milestone 1: Atomic queue claiming, cooperative cancellation, retry backoff, and lease recovery.
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
from typing import List, Optional, Tuple, Union
from quantumshield.storage.database import get_db_connection
from quantumshield.models.job import ScanJob, utc_now_iso, calculate_backoff


class JobRepository:
    """Repository handling persistence, transitions, and queue claiming for scan jobs."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    def create(self, job: ScanJob) -> ScanJob:
        """Insert a new scan job into SQLite."""
        job.validate()
        payload_str = json.dumps(job.payload_json) if isinstance(job.payload_json, (dict, list)) else job.payload_json
        result_str = json.dumps(job.result_json) if isinstance(job.result_json, (dict, list)) else job.result_json

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO scan_jobs (
                        id, job_type, asset_id, operation, status, priority,
                        payload_json, result_json, progress, attempt_count,
                        max_attempts, created_at, started_at, finished_at,
                        updated_at, next_retry_at, error_code, error_message, scan_run_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        job.id,
                        job.job_type.lower(),
                        job.asset_id,
                        job.operation.strip() if job.operation else "execute",
                        job.status.lower(),
                        job.priority,
                        payload_str,
                        result_str,
                        job.progress,
                        job.attempt_count,
                        job.max_attempts,
                        job.created_at,
                        job.started_at,
                        job.finished_at,
                        job.updated_at or job.created_at,
                        job.next_retry_at,
                        job.error_code,
                        job.error_message,
                        job.scan_run_id,
                    ),
                )
        finally:
            conn.close()
        return job

    def get_by_id(self, job_id: str) -> Optional[ScanJob]:
        """Fetch a single scan job by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM scan_jobs WHERE id = ?;", (job_id,))
            row = cursor.fetchone()
        finally:
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
        try:
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
        finally:
            conn.close()

        jobs = [ScanJob.from_dict(dict(r)) for r in rows]
        return jobs, total

    def update(self, job: ScanJob) -> Optional[ScanJob]:
        """Update job fields in SQLite."""
        job.validate()
        job.updated_at = utc_now_iso()
        payload_str = json.dumps(job.payload_json) if isinstance(job.payload_json, (dict, list)) else job.payload_json
        result_str = json.dumps(job.result_json) if isinstance(job.result_json, (dict, list)) else job.result_json

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE scan_jobs SET
                        job_type = ?,
                        asset_id = ?,
                        operation = ?,
                        status = ?,
                        priority = ?,
                        payload_json = ?,
                        result_json = ?,
                        progress = ?,
                        attempt_count = ?,
                        max_attempts = ?,
                        started_at = ?,
                        finished_at = ?,
                        updated_at = ?,
                        next_retry_at = ?,
                        error_code = ?,
                        error_message = ?,
                        scan_run_id = ?
                    WHERE id = ?;
                    """,
                    (
                        job.job_type.lower(),
                        job.asset_id,
                        job.operation.strip() if job.operation else "execute",
                        job.status.lower(),
                        job.priority,
                        payload_str,
                        result_str,
                        job.progress,
                        job.attempt_count,
                        job.max_attempts,
                        job.started_at,
                        job.finished_at,
                        job.updated_at,
                        job.next_retry_at,
                        job.error_code,
                        job.error_message,
                        job.scan_run_id,
                        job.id,
                    ),
                )
                affected = cursor.rowcount
        finally:
            conn.close()

        if affected == 0:
            return None
        return job

    def list_by_scan_run(self, scan_run_id: str) -> List[ScanJob]:
        """Fetch all child jobs belonging to a specific scan run."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT * FROM scan_jobs WHERE scan_run_id = ? ORDER BY created_at ASC;",
                (scan_run_id,),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()
        return [ScanJob.from_dict(dict(r)) for r in rows]

    def claim_next_job(self, worker_id: Optional[str] = None) -> Optional[ScanJob]:
        """
        Atomically claim the next eligible job (pending or queued) and transition to running.
        Honours priority (priority DESC) and FIFO order (created_at ASC).
        Respects retry backoff (next_retry_at IS NULL OR next_retry_at <= now).
        """
        now_iso = utc_now_iso()
        conn = get_db_connection(self.db_path)
        updated_row = None
        try:
            with conn:
                cursor = conn.execute(
                    """
                    SELECT id FROM scan_jobs
                    WHERE status IN ('pending', 'queued')
                      AND (next_retry_at IS NULL OR next_retry_at <= ?)
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1;
                    """,
                    (now_iso,),
                )
                row = cursor.fetchone()
                if row:
                    job_id = row["id"]
                    conn.execute(
                        """
                        UPDATE scan_jobs SET
                            status = 'running',
                            started_at = COALESCE(started_at, ?),
                            updated_at = ?,
                            progress = CASE WHEN progress < 10 THEN 10 ELSE progress END
                        WHERE id = ? AND status IN ('pending', 'queued');
                        """,
                        (now_iso, now_iso, job_id),
                    )
                    cursor = conn.execute("SELECT * FROM scan_jobs WHERE id = ?;", (job_id,))
                    updated_row = cursor.fetchone()
        finally:
            conn.close()

        if not updated_row:
            return None
        return ScanJob.from_dict(dict(updated_row))

    def request_cancellation(self, job_id: str) -> Optional[ScanJob]:
        """
        Request cancellation of a job.
        If pending or queued: immediately transition to 'cancelled'.
        If running: transition to 'cancel_requested' for cooperative cancellation by worker.
        """
        job = self.get_by_id(job_id)
        if not job:
            return None

        now_iso = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                if job.status in ("pending", "queued"):
                    conn.execute(
                        """
                        UPDATE scan_jobs SET
                            status = 'cancelled',
                            finished_at = ?,
                            updated_at = ?,
                            error_code = 'CANCELLED',
                            error_message = 'Job cancelled by user request.'
                        WHERE id = ? AND status IN ('pending', 'queued');
                        """,
                        (now_iso, now_iso, job_id),
                    )
                elif job.status == "running":
                    conn.execute(
                        """
                        UPDATE scan_jobs SET
                            status = 'cancel_requested',
                            updated_at = ?,
                            error_code = 'CANCEL_REQUESTED',
                            error_message = 'Cancellation requested by user.'
                        WHERE id = ? AND status = 'running';
                        """,
                        (now_iso, job_id),
                    )
                else:
                    return None
        finally:
            conn.close()

        return self.get_by_id(job_id)

    def cancel(self, job_id: str) -> bool:
        """Backward-compatible cancel method."""
        updated = self.request_cancellation(job_id)
        return updated is not None and updated.status in ("cancelled", "cancel_requested")

    def retry(self, job_id: str) -> Optional[ScanJob]:
        """
        Retry a failed or cancelled job if within max_attempts limit.
        Applies exponential backoff and sets next_retry_at.
        """
        job = self.get_by_id(job_id)
        if not job:
            return None

        if job.status not in ("failed", "cancelled"):
            return None

        if job.attempt_count >= job.max_attempts:
            return None

        job.attempt_count += 1
        delay_seconds = calculate_backoff(job.attempt_count)
        next_retry_dt = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        job.status = "queued"
        job.started_at = None
        job.finished_at = None
        job.error_code = None
        job.error_message = None
        job.progress = 0
        job.next_retry_at = next_retry_dt.isoformat()
        job.updated_at = utc_now_iso()

        return self.update(job)

    def recover_abandoned_jobs(self, lease_seconds: int = 60) -> int:
        """
        Identify jobs in 'running' state whose heartbeat lease expired (updated_at too old).
        Re-queues them if retries remain, or fails them if max attempts exceeded.
        """
        now = datetime.now(timezone.utc)
        threshold_dt = now - timedelta(seconds=lease_seconds)
        threshold_iso = threshold_dt.isoformat()
        now_iso = now.isoformat()

        conn = get_db_connection(self.db_path)
        recovered_count = 0
        try:
            with conn:
                cursor = conn.execute(
                    """
                    SELECT id, attempt_count, max_attempts FROM scan_jobs
                    WHERE status = 'running' AND updated_at < ?;
                    """,
                    (threshold_iso,),
                )
                abandoned = cursor.fetchall()
                for row in abandoned:
                    job_id = row["id"]
                    attempt_count = row["attempt_count"]
                    max_attempts = row["max_attempts"]

                    if attempt_count < max_attempts:
                        conn.execute(
                            """
                            UPDATE scan_jobs SET
                                status = 'queued',
                                attempt_count = attempt_count + 1,
                                updated_at = ?,
                                next_retry_at = ?,
                                error_code = 'LEASE_EXPIRED',
                                error_message = 'Worker heartbeat lease expired; re-queued for execution.'
                            WHERE id = ?;
                            """,
                            (now_iso, now_iso, job_id),
                        )
                    else:
                        conn.execute(
                            """
                            UPDATE scan_jobs SET
                                status = 'failed',
                                finished_at = ?,
                                updated_at = ?,
                                error_code = 'LEASE_EXPIRED',
                                error_message = 'Worker heartbeat lease expired and max attempts reached.'
                            WHERE id = ?;
                            """,
                            (now_iso, now_iso, job_id),
                        )
                    recovered_count += 1
        finally:
            conn.close()

        return recovered_count

    def recover_stale_jobs(self) -> int:
        """
        Immediate recovery for jobs left in 'running' state after an unexpected process crash.
        """
        now_iso = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE scan_jobs SET
                        status = 'failed',
                        finished_at = ?,
                        updated_at = ?,
                        error_code = 'WORKER_CRASH',
                        error_message = 'Job aborted due to unexpected worker or server restart.'
                    WHERE status = 'running';
                    """,
                    (now_iso, now_iso),
                )
                affected = cursor.rowcount
        finally:
            conn.close()

        return affected
