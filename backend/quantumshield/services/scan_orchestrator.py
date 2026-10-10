"""
Automated Scan Orchestration Engine.
Coordinates cryptographic discovery scanners through the background job system,
normalizes findings, tracks scan runs, and records historical audit traces.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from quantumshield.storage.repositories import AssetRepository
from quantumshield.storage.scan_repository import ScanRepository
from quantumshield.storage.job_repository import JobRepository
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.models.scan_run import ScanRun, utc_now_iso
from quantumshield.models.job import ScanJob
from quantumshield.models.finding import Finding
from quantumshield.core.exceptions import ValidationError, NotFoundError, ConflictError

logger = logging.getLogger("quantumshield.orchestrator")

SUPPORTED_SCANNERS = {
    "certificate_scan",
    "static_scan",
    "tls_scan",
    "system_scan",
}


class ScanOrchestrator:
    """Service coordinating end-to-end security scans over authorized assets."""

    def __init__(self, db_path: Union[str, Path], job_manager=None):
        self.db_path = db_path
        self.job_manager = job_manager
        self.asset_repo = AssetRepository(db_path)
        self.scan_repo = ScanRepository(db_path)
        self.job_repo = JobRepository(db_path)
        self.finding_repo = FindingRepository(db_path)

    def validate_scan_scope(self, asset_id: str, scanner_types: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Validate target authorization, asset existence, and scanner support.
        """
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            return False, f"Target asset '{asset_id}' does not exist in inventory.", []

        if asset.status == "inactive":
            return False, f"Target asset '{asset_id}' is marked inactive. Scanning prohibited.", []

        if not scanner_types:
            return False, "At least one scanner type must be specified.", []

        unsupported = [s for s in scanner_types if s.lower() not in SUPPORTED_SCANNERS]
        if unsupported:
            return False, f"Unsupported scanner type(s): {', '.join(unsupported)}. Supported: {', '.join(SUPPORTED_SCANNERS)}", []

        # Determine applicability based on asset characteristics
        valid_scanners = [s.lower() for s in scanner_types]
        return True, "Scope and authorization validated.", valid_scanners

    def request_scan(
        self,
        asset_id: str,
        scanner_types: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> ScanRun:
        """
        Public entry point to request an orchestrated scan.
        Performs scope validation, duplicate protection, scan run creation, and job queuing.
        """
        is_valid, message, applicable_scanners = self.validate_scan_scope(asset_id, scanner_types)
        if not is_valid:
            if "does not exist" in message:
                raise NotFoundError(message)
            raise ValidationError(message)

        # Duplicate scan protection
        active_run = self.scan_repo.get_active_scan_run_for_asset(asset_id)
        if active_run:
            raise ConflictError(
                f"An active scan run '{active_run.id}' is already in progress ({active_run.status}) for this asset."
            )

        # Create scan run
        run = ScanRun(
            asset_id=asset_id,
            requested_scanners=applicable_scanners,
            status="queued",
            total_jobs=len(applicable_scanners),
        )
        self.scan_repo.create(run)

        # Schedule jobs
        self.schedule_scan_jobs(run.id, options=options)

        logger.info(f"Orchestrated scan run '{run.id}' enqueued with {len(applicable_scanners)} scanner jobs.")
        return run

    def schedule_scan_jobs(self, scan_run_id: str, options: Optional[Dict[str, Any]] = None) -> List[ScanJob]:
        """Create and enqueue background jobs for each applicable scanner."""
        run = self.scan_repo.get_by_id(scan_run_id)
        if not run:
            raise NotFoundError(f"Scan run '{scan_run_id}' not found.")

        jobs: List[ScanJob] = []
        for scanner_type in run.requested_scanners:
            job = ScanJob(
                job_type=scanner_type,
                asset_id=run.asset_id,
                operation=f"orchestrated_{scanner_type}",
                priority=6,
                scan_run_id=run.id,
                payload_json=options or {},
                status="queued",
            )
            if self.job_manager:
                saved = self.job_manager.enqueue(job)
            else:
                saved = self.job_repo.create(job)
            jobs.append(saved)

        run.total_jobs = len(jobs)
        self.scan_repo.update(run)
        return jobs

    def collect_scan_results(self, scan_run_id: str) -> ScanRun:
        """
        Inspect all child jobs, normalize & persist discovered findings, and update scan run status.
        """
        run = self.scan_repo.get_by_id(scan_run_id)
        if not run:
            raise NotFoundError(f"Scan run '{scan_run_id}' not found.")

        jobs = self.job_repo.list_by_scan_run(scan_run_id)
        total_findings_count = 0

        for job in jobs:
            if job.status == "completed" and job.result_json:
                res_data = job.result_json
                if isinstance(res_data, dict):
                    findings_list = res_data.get("findings", [])
                    for f_dict in findings_list:
                        finding = Finding(
                            asset_id=job.asset_id or run.asset_id,
                            scan_run_id=run.id,
                            job_id=job.id,
                            scanner_type=job.job_type,
                            algorithm=f_dict.get("algorithm", "Unknown"),
                            cryptographic_primitive=f_dict.get("cryptographic_primitive", "key_establishment"),
                            quantum_vulnerable=f_dict.get("quantum_vulnerable", True),
                            recommended_pqc=f_dict.get("recommended_pqc", "ML-KEM-768"),
                            rule_id=f_dict.get("rule_id", "GENERIC-RULE"),
                            title=f_dict.get("title", "Cryptographic Finding"),
                            description=f_dict.get("description", ""),
                            severity=f_dict.get("severity", "medium"),
                            evidence=f_dict.get("evidence", ""),
                            file_path=f_dict.get("file_path"),
                            line_number=f_dict.get("line_number"),
                            confidence=f_dict.get("confidence", "high"),
                            remediation_status=f_dict.get("remediation_status", "potential_exposure"),
                            detection_category=f_dict.get("detection_category", "Confirmed cryptographic API usage"),
                            data_sensitivity=f_dict.get("data_sensitivity"),
                            exposure=f_dict.get("exposure"),
                            confidentiality_lifetime=f_dict.get("confidentiality_lifetime"),
                            risk_score=f_dict.get("risk_score"),
                            risk_category=f_dict.get("risk_category", "Needs Assessment"),
                            score_rationale=f_dict.get("score_rationale", ""),
                            recommended_action=f_dict.get("recommended_action", ""),
                            migration_approach=f_dict.get("migration_approach", ""),
                            queue_group=f_dict.get("queue_group", "needs_assessment"),
                        )
                        self.finding_repo.save_finding(finding)
                        total_findings_count += 1

        run.update_from_jobs(jobs)
        if run.status in ("completed", "partially_completed"):
            run.result_summary = {
                "scanned_jobs": len(jobs),
                "findings_discovered": total_findings_count,
                "synced_at": utc_now_iso(),
            }

        self.scan_repo.update(run)
        return run

    def get_scan_run_status(self, scan_run_id: str) -> ScanRun:
        """Retrieve latest synchronized state for a scan run."""
        return self.collect_scan_results(scan_run_id)

    def cancel_scan_run(self, scan_run_id: str) -> ScanRun:
        """Cancel all child jobs for a scan run."""
        run = self.scan_repo.get_by_id(scan_run_id)
        if not run:
            raise NotFoundError(f"Scan run '{scan_run_id}' not found.")

        jobs = self.job_repo.list_by_scan_run(scan_run_id)
        for job in jobs:
            if job.status in ("pending", "queued", "running"):
                self.job_repo.request_cancellation(job.id)

        return self.collect_scan_results(scan_run_id)
