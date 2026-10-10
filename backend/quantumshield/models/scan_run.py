"""
Scan Run Domain Model and Lifecycle Calculations.
Represents an orchestrated scan run over an authorized asset coordinating multiple scanner jobs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import uuid
from typing import Optional, List, Dict, Any, Union
from quantumshield.models.job import ScanJob


VALID_SCAN_RUN_STATUSES = {
    "queued",
    "running",
    "completed",
    "partially_completed",
    "failed",
    "cancelled",
}


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScanRun:
    id: str = ""
    asset_id: str = ""
    requested_scanners: List[str] = field(default_factory=list)
    status: str = "queued"
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    result_summary: Optional[Union[Dict[str, Any], str]] = None
    error_summary: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"run_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = utc_now_iso()
        if isinstance(self.requested_scanners, str):
            try:
                self.requested_scanners = json.loads(self.requested_scanners)
            except Exception:
                self.requested_scanners = [self.requested_scanners]

    @property
    def progress_percentage(self) -> int:
        """Calculate real progress percentage from completed jobs."""
        if self.total_jobs <= 0:
            return 100 if self.status in ("completed", "failed", "partially_completed") else 0
        finished = self.completed_jobs + self.failed_jobs + self.cancelled_jobs
        return min(100, int((finished / self.total_jobs) * 100))

    def update_from_jobs(self, jobs: List[ScanJob]) -> None:
        """Update scan run counters, timestamps, and status based on child jobs."""
        self.total_jobs = len(jobs)
        self.completed_jobs = sum(1 for j in jobs if j.status == "completed")
        self.failed_jobs = sum(1 for j in jobs if j.status == "failed")
        self.cancelled_jobs = sum(1 for j in jobs if j.status in ("cancelled", "cancel_requested"))

        running_jobs = sum(1 for j in jobs if j.status == "running")
        queued_jobs = sum(1 for j in jobs if j.status in ("queued", "pending"))

        # Started at timestamp
        if not self.started_at:
            started_times = [j.started_at for j in jobs if j.started_at]
            if started_times:
                self.started_at = min(started_times)

        # Status resolution
        if queued_jobs == self.total_jobs and self.total_jobs > 0:
            self.status = "queued"
        elif running_jobs > 0 or queued_jobs > 0:
            self.status = "running"
        elif self.completed_jobs == self.total_jobs and self.total_jobs > 0:
            self.status = "completed"
            if not self.completed_at:
                self.completed_at = utc_now_iso()
        elif self.completed_jobs > 0 and (self.failed_jobs > 0 or self.cancelled_jobs > 0):
            self.status = "partially_completed"
            if not self.completed_at:
                self.completed_at = utc_now_iso()
        elif self.cancelled_jobs == self.total_jobs and self.total_jobs > 0:
            self.status = "cancelled"
            if not self.completed_at:
                self.completed_at = utc_now_iso()
        elif self.failed_jobs == self.total_jobs and self.total_jobs > 0:
            self.status = "failed"
            if not self.completed_at:
                self.completed_at = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        summary = self.result_summary
        if isinstance(summary, str) and summary:
            try:
                summary = json.loads(summary)
            except Exception:
                pass

        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "requested_scanners": self.requested_scanners,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_jobs": self.total_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "cancelled_jobs": self.cancelled_jobs,
            "progress_percentage": self.progress_percentage,
            "result_summary": summary,
            "error_summary": self.error_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanRun":
        """Instantiate ScanRun from dictionary data."""
        raw_scanners = data.get("requested_scanners", [])
        if isinstance(raw_scanners, str):
            try:
                raw_scanners = json.loads(raw_scanners)
            except Exception:
                raw_scanners = [raw_scanners]

        raw_summary = data.get("result_summary")
        if isinstance(raw_summary, str) and raw_summary:
            try:
                raw_summary = json.loads(raw_summary)
            except Exception:
                pass

        return cls(
            id=data.get("id", ""),
            asset_id=data.get("asset_id", ""),
            requested_scanners=raw_scanners,
            status=data.get("status", "queued"),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            total_jobs=int(data.get("total_jobs", 0)),
            completed_jobs=int(data.get("completed_jobs", 0)),
            failed_jobs=int(data.get("failed_jobs", 0)),
            cancelled_jobs=int(data.get("cancelled_jobs", 0)),
            result_summary=raw_summary,
            error_summary=data.get("error_summary"),
        )
