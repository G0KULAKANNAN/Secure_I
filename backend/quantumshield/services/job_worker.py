"""
Background Worker Processing and Job Queue Manager.
Executes long-running scans asynchronously without blocking Flask request handlers.
Milestone 1: Resilient background job engine with health monitoring, cooperative cancellation, and built-in safe handlers.
"""

import threading
import time
import logging
from pathlib import Path
from typing import Callable, Dict, Optional, Union, Any
from quantumshield.storage.job_repository import JobRepository
from quantumshield.storage.repositories import AssetRepository
from quantumshield.models.job import ScanJob, utc_now_iso

logger = logging.getLogger("quantumshield.worker")


class BackgroundJobManager:
    """
    Manages background worker threads and asynchronous execution of scan jobs.
    """

    def __init__(self, db_path: Union[str, Path], max_workers: int = 3, lease_seconds: int = 60):
        self.db_path = db_path
        self.max_workers = max_workers
        self.lease_seconds = lease_seconds
        self.repo = JobRepository(db_path)
        self.asset_repo = AssetRepository(db_path)
        self.handlers: Dict[str, Callable[[ScanJob, Callable[[], bool]], Any]] = {}
        self._running = False
        self._threads: list[threading.Thread] = []
        self._wake_event = threading.Event()
        self._lock = threading.Lock()
        self._start_time: Optional[float] = None

        # Metrics
        self._active_workers = 0
        self._processed_count = 0
        self._succeeded_count = 0
        self._failed_count = 0
        self._retried_count = 0

        # Register default safe handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register built-in safe execution handlers for milestone 1 & 2."""
        self.register_handler("health_check", self._handle_health_check)
        self.register_handler("asset_validation", self._handle_asset_validation)
        self.register_handler("certificate_scan", self._handle_certificate_scan)
        self.register_handler("static_scan", self._handle_static_scan)
        self.register_handler("tls_scan", self._handle_tls_scan)

    def register_handler(
        self, job_type: str, handler: Union[Callable[[ScanJob], Any], Callable[[ScanJob, Callable[[], bool]], Any]]
    ) -> None:
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
        self._start_time = time.time()
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

    def get_status(self) -> Dict[str, Any]:
        """Return runtime status and health metrics for the worker engine."""
        uptime = time.time() - self._start_time if self._start_time and self._running else 0.0

        # Query live queue depth from SQLite
        _, pending_count = self.repo.list_jobs(status="pending", limit=1)
        _, queued_count = self.repo.list_jobs(status="queued", limit=1)
        queue_depth = pending_count + queued_count

        return {
            "engine": "QuantumShield Background Job Worker",
            "status": "running" if self._running else "stopped",
            "uptime_seconds": round(uptime, 2),
            "max_workers": self.max_workers,
            "active_workers": self._active_workers,
            "queue_depth": queue_depth,
            "processed_count": self._processed_count,
            "succeeded_count": self._succeeded_count,
            "failed_count": self._failed_count,
            "retried_count": self._retried_count,
        }

    def _worker_loop(self) -> None:
        """Main loop executed by worker threads."""
        while self._running:
            try:
                # Recover any abandoned jobs whose lease expired
                self.repo.recover_abandoned_jobs(self.lease_seconds)

                job = self.repo.claim_next_job()
                if not job:
                    # No job available, wait up to 2 seconds or until signaled
                    self._wake_event.wait(timeout=2.0)
                    self._wake_event.clear()
                    continue

                with self._lock:
                    self._active_workers += 1

                try:
                    self._process_job(job)
                finally:
                    with self._lock:
                        self._active_workers = max(0, self._active_workers - 1)
                        self._processed_count += 1

            except Exception as exc:
                logger.error(f"Unexpected error in worker loop: {exc}", exc_info=True)
                time.sleep(1.0)

    def _is_job_cancelled(self, job_id: str) -> bool:
        """Check if job cancellation was requested."""
        fresh = self.repo.get_by_id(job_id)
        if not fresh:
            return True
        return fresh.status in ("cancel_requested", "cancelled")

    def _process_job(self, job: ScanJob) -> None:
        """Execute a claimed job and update its lifecycle state."""
        logger.info(f"Worker claimed job '{job.id}' (Type: {job.job_type}, Priority: {job.priority})")

        # Check for immediate cancellation before beginning
        if self._is_job_cancelled(job.id):
            job.status = "cancelled"
            job.finished_at = utc_now_iso()
            job.error_code = "CANCELLED"
            job.error_message = "Job cancelled before execution started."
            self.repo.update(job)
            return

        handler = self.handlers.get(job.job_type.lower())
        if not handler:
            # Reject unknown job type
            logger.error(f"Job '{job.id}' has unknown job_type '{job.job_type}'. Rejection recorded.")
            job.status = "failed"
            job.finished_at = utc_now_iso()
            job.error_code = "UNKNOWN_JOB_TYPE"
            job.error_message = f"Unsupported or unknown job type '{job.job_type}'. No handler registered."
            self.repo.update(job)
            with self._lock:
                self._failed_count += 1
            return

        try:
            # Prepare cancellation token
            cancel_token = lambda: self._is_job_cancelled(job.id)

            # Invoke handler
            import inspect
            sig = inspect.signature(handler)
            if len(sig.parameters) >= 2:
                result_data = handler(job, cancel_token)
            else:
                result_data = handler(job)

            # Check if cancellation was flagged during handler execution
            if self._is_job_cancelled(job.id):
                job.status = "cancelled"
                job.finished_at = utc_now_iso()
                job.error_code = "CANCELLED"
                job.error_message = "Job cancelled by user request during execution."
                self.repo.update(job)
                return

            job.status = "completed"
            job.progress = 100
            job.finished_at = utc_now_iso()
            job.result_json = result_data
            job.error_code = None
            job.error_message = None
            self.repo.update(job)

            # Automatically persist findings and sync scan run if linked
            self._sync_job_results_and_findings(job, result_data)

            with self._lock:
                self._succeeded_count += 1
            logger.info(f"Job '{job.id}' completed successfully.")

        except Exception as exc:
            logger.error(f"Job '{job.id}' failed during execution: {exc}")
            job.finished_at = utc_now_iso()
            job.error_code = getattr(exc, "code", "EXECUTION_ERROR")
            job.error_message = str(exc)

            # Check if eligible for retry
            if job.attempt_count < job.max_attempts:
                with self._lock:
                    self._retried_count += 1
                self.repo.retry(job.id)
                logger.info(f"Job '{job.id}' scheduled for retry (Attempt {job.attempt_count}/{job.max_attempts}).")
            else:
                job.status = "failed"
                with self._lock:
                    self._failed_count += 1
                self.repo.update(job)
                logger.warning(f"Job '{job.id}' reached maximum retries ({job.max_attempts}) and marked failed.")

    # -------------------------------------------------------------
    # Default Safe Handlers for Milestone 1
    # -------------------------------------------------------------
    def _handle_health_check(self, job: ScanJob, is_cancelled: Optional[Callable[[], bool]] = None) -> dict:
        """Safe handler verifying system health and dependencies."""
        job.progress = 25
        self.repo.update(job)

        # Check DB
        t0 = time.time()
        conn = self.repo.get_by_id(job.id)
        db_latency = (time.time() - t0) * 1000

        if is_cancelled and is_cancelled():
            return {"cancelled": True}

        job.progress = 75
        self.repo.update(job)

        storage_path = Path(self.db_path).resolve()
        is_writable = storage_path.parent.is_dir()

        return {
            "status": "healthy",
            "database": "connected",
            "database_latency_ms": round(db_latency, 2),
            "storage_path": str(storage_path),
            "storage_writable": is_writable,
            "checked_at": utc_now_iso(),
            "execution_mode": "persistent_worker",
        }

    def _handle_asset_validation(self, job: ScanJob, is_cancelled: Optional[Callable[[], bool]] = None) -> dict:
        """Safe handler validating asset parameters and network configuration."""
        if not job.asset_id:
            raise ValueError("Target asset_id is required for asset_validation job.")

        job.progress = 30
        self.repo.update(job)

        asset = self.asset_repo.get_by_id(job.asset_id)
        if not asset:
            raise ValueError(f"Target asset '{job.asset_id}' not found in database.")

        if is_cancelled and is_cancelled():
            return {"cancelled": True}

        job.progress = 80
        self.repo.update(job)

        return {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "asset_type": asset.asset_type,
            "environment": asset.environment,
            "criticality": asset.criticality,
            "hostname": asset.hostname,
            "ip_address": asset.ip_address,
            "validation_passed": True,
            "checks": {
                "record_exists": True,
                "valid_identifier": bool(asset.id),
                "environment_configured": bool(asset.environment),
                "criticality_rated": bool(asset.criticality),
            },
            "validated_at": utc_now_iso(),
        }

    def _sync_job_results_and_findings(self, job: ScanJob, result_data: Any) -> None:
        """Persist findings and synchronize parent scan run state."""
        try:
            if isinstance(result_data, dict) and "findings" in result_data:
                from quantumshield.storage.finding_repository import FindingRepository
                from quantumshield.models.finding import Finding
                finding_repo = FindingRepository(self.db_path)
                for f_dict in result_data.get("findings", []):
                    finding = Finding(
                        asset_id=job.asset_id or "",
                        scan_run_id=job.scan_run_id,
                        job_id=job.id,
                        scanner_type=job.job_type,
                        algorithm=f_dict.get("algorithm", "Unknown"),
                        cryptographic_primitive=f_dict.get("cryptographic_primitive", "key_establishment"),
                        quantum_vulnerable=f_dict.get("quantum_vulnerable", True),
                        recommended_pqc=f_dict.get("recommended_pqc", "ML-KEM-768"),
                        rule_id=f_dict.get("rule_id", "GENERIC-RULE"),
                        title=f_dict.get("title", "Finding"),
                        description=f_dict.get("description", ""),
                        severity=f_dict.get("severity", "medium"),
                        evidence=f_dict.get("evidence", ""),
                        file_path=f_dict.get("file_path"),
                        line_number=f_dict.get("line_number"),
                        confidence=f_dict.get("confidence", "high"),
                        remediation_status=f_dict.get("remediation_status", "potential_exposure"),
                    )
                    finding_repo.save_finding(finding)

            if job.scan_run_id:
                from quantumshield.storage.scan_repository import ScanRepository
                scan_repo = ScanRepository(self.db_path)
                run = scan_repo.get_by_id(job.scan_run_id)
                if run:
                    child_jobs = self.repo.list_by_scan_run(run.id)
                    run.update_from_jobs(child_jobs)
                    scan_repo.update(run)
        except Exception as exc:
            logger.error(f"Error syncing findings/scan run for job {job.id}: {exc}", exc_info=True)

    def _handle_certificate_scan(self, job: ScanJob, is_cancelled: Optional[Callable[[], bool]] = None) -> dict:
        """Execute real X.509 Certificate Scanner."""
        if not job.asset_id:
            raise ValueError("Target asset_id is required for certificate scan.")
        asset = self.asset_repo.get_by_id(job.asset_id)
        if not asset:
            raise ValueError(f"Asset '{job.asset_id}' not found.")

        job.progress = 30
        self.repo.update(job)

        from quantumshield.scanner.certificate_scanner import CertificateScanner
        scanner = CertificateScanner()
        payload = job.payload_json if isinstance(job.payload_json, dict) else {}
        result = scanner.scan(asset, payload)

        if is_cancelled and is_cancelled():
            return {"cancelled": True}

        if result.status == "failed" and result.error_message:
            raise RuntimeError(result.error_message)

        job.progress = 90
        self.repo.update(job)
        return result.to_dict()

    def _handle_static_scan(self, job: ScanJob, is_cancelled: Optional[Callable[[], bool]] = None) -> dict:
        """Execute real Static Cryptography Scanner."""
        if not job.asset_id:
            raise ValueError("Target asset_id is required for static scan.")
        asset = self.asset_repo.get_by_id(job.asset_id)
        if not asset:
            raise ValueError(f"Asset '{job.asset_id}' not found.")

        job.progress = 30
        self.repo.update(job)

        from quantumshield.scanner.static_scanner import StaticScanner
        scanner = StaticScanner()
        payload = job.payload_json if isinstance(job.payload_json, dict) else {}
        result = scanner.scan(asset, payload)

        if is_cancelled and is_cancelled():
            return {"cancelled": True}

        if result.status == "failed" and result.error_message:
            raise RuntimeError(result.error_message)

        job.progress = 90
        self.repo.update(job)
        return result.to_dict()

    def _handle_tls_scan(self, job: ScanJob, is_cancelled: Optional[Callable[[], bool]] = None) -> dict:
        """Execute real TLS Handshake Scanner."""
        if not job.asset_id:
            raise ValueError("Target asset_id is required for TLS scan.")
        asset = self.asset_repo.get_by_id(job.asset_id)
        if not asset:
            raise ValueError(f"Asset '{job.asset_id}' not found.")

        job.progress = 30
        self.repo.update(job)

        from quantumshield.scanner.tls_scanner import TlsScanner
        scanner = TlsScanner(allow_local_lab=True)
        payload = job.payload_json if isinstance(job.payload_json, dict) else {}
        result = scanner.scan(asset, payload)

        if is_cancelled and is_cancelled():
            return {"cancelled": True}

        if result.status == "failed" and result.error_message:
            raise RuntimeError(result.error_message)

        job.progress = 90
        self.repo.update(job)
        return result.to_dict()

