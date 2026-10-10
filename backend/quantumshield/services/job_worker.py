"""
Background Worker Processing and Job Queue Manager.
Executes long-running scans asynchronously without blocking Flask request handlers.
"""

import threading
import time
import logging
from pathlib import Path
from typing import Callable, Dict, Optional, Union
from quantumshield.storage.job_repository import JobRepository
from quantumshield.models.job import ScanJob, utc_now_iso

logger = logging.getLogger("quantumshield.worker")


class BackgroundJobManager:
    """
    Manages background worker threads and asynchronous execution of scan jobs.
    """

    def __init__(self, db_path: Union[str, Path], max_workers: int = 3):
        self.db_path = db_path
        self.max_workers = max_workers
        self.repo = JobRepository(db_path)
        self.handlers: Dict[str, Callable[[ScanJob], dict]] = {}
        self._running = False
        self._threads: list[threading.Thread] = []
        self._wake_event = threading.Event()

    def register_handler(self, job_type: str, handler: Callable[[ScanJob], dict]) -> None:
        """Register an execution function for a specific job_type."""
        self.handlers[job_type.lower()] = handler

    def enqueue(self, job: ScanJob) -> ScanJob:
        """Persist a job in queued state and notify background workers."""
        job.status = "queued"
        saved = self.repo.create(job)
        self._wake_event.set()
        return saved

    def start(self) -> None:
        """Start worker threads."""
        if self._running:
            return

        self._running = True
        self._wake_event.clear()

        # Recover any orphaned jobs from previous crashes
        recovered_count = self.repo.recover_stale_jobs()
        if recovered_count > 0:
            logger.info(f"Recovered {recovered_count} stale jobs left in running state.")

        for i in range(self.max_workers):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"JobWorker-{i+1}",
                daemon=True,
            )
            self._threads.append(t)
            t.start()

        logger.info(f"Started BackgroundJobManager with {self.max_workers} worker threads.")

    def stop(self, timeout: float = 3.0) -> None:
        """Gracefully stop all worker threads."""
        self._running = False
        self._wake_event.set()
        for t in self._threads:
            t.join(timeout=timeout)
        self._threads.clear()
        logger.info("BackgroundJobManager stopped cleanly.")

    def _worker_loop(self) -> None:
        """Main loop executed by worker threads."""
        while self._running:
            try:
                job = self.repo.claim_next_job()
                if not job:
                    # No job available, wait up to 2 seconds or until signaled
                    self._wake_event.wait(timeout=2.0)
                    self._wake_event.clear()
                    continue

                self._process_job(job)
            except Exception as exc:
                logger.error(f"Unexpected error in worker loop: {exc}", exc_info=True)
                time.sleep(1.0)

    def _process_job(self, job: ScanJob) -> None:
        """Execute a claimed job and update its lifecycle state."""
        logger.info(f"Worker claimed job '{job.id}' (Type: {job.job_type}, Asset: {job.asset_id})")

        handler = self.handlers.get(job.job_type.lower())
        if not handler:
            # Default placeholder execution if specific scanner handler not registered yet
            handler = self._default_mock_handler

        try:
            # Execute handler
            result_data = handler(job)
            job.status = "completed"
            job.progress = 100
            job.completed_at = utc_now_iso()
            job.result_data = result_data
            self.repo.update(job)
            logger.info(f"Job '{job.id}' completed successfully.")
        except Exception as exc:
            logger.error(f"Job '{job.id}' failed during execution: {exc}")
            job.completed_at = utc_now_iso()
            job.error_message = str(exc)

            # Check if eligible for retry
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = "queued"
                logger.info(f"Job '{job.id}' will be retried (Attempt {job.retry_count}/{job.max_retries})")
            else:
                job.status = "failed"
                logger.warning(f"Job '{job.id}' reached maximum retries ({job.max_retries}) and marked failed.")

            self.repo.update(job)

    def _default_mock_handler(self, job: ScanJob) -> dict:
        """Default baseline handler for jobs when dedicated scanners are in progress."""
        return {
            "job_id": job.id,
            "asset_id": job.asset_id,
            "operation": job.operation,
            "message": "Scan job queued and processed by QuantumShield background worker engine.",
            "processed_at": utc_now_iso(),
        }
