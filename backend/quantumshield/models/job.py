"""
Scan Job Data Model and Lifecycle State Definitions.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import uuid
from typing import Optional, Dict, Any, Union
from quantumshield.core.exceptions import ValidationError


VALID_JOB_STATUSES = {
    "pending",
    "queued",
    "running",
    "completed",
    "partially_completed",
    "failed",
    "cancelled",
}

VALID_JOB_TYPES = {
    "certificate_scan",
    "tls_scan",
    "static_scan",
    "full_orchestrated_scan",
    "change_detection",
}


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScanJob:
    id: str
    job_type: str
    asset_id: str
    operation: str
    status: str = "pending"
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result_data: Optional[Union[Dict[str, Any], str]] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"job_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = utc_now_iso()

    def validate(self) -> None:
        """Validate job fields against schema rules."""
        if not self.asset_id or not self.asset_id.strip():
            raise ValidationError("Target asset_id is required for a scan job.")

        if self.job_type.lower() not in VALID_JOB_TYPES:
            raise ValidationError(
                f"Invalid job_type '{self.job_type}'. Must be one of: {', '.join(sorted(VALID_JOB_TYPES))}"
            )

        if self.status.lower() not in VALID_JOB_STATUSES:
            raise ValidationError(
                f"Invalid status '{self.status}'. Must be one of: {', '.join(sorted(VALID_JOB_STATUSES))}"
            )

        if not self.operation or not self.operation.strip():
            raise ValidationError("Job operation name is required.")

        if not (0 <= self.progress <= 100):
            raise ValidationError("Progress must be an integer between 0 and 100.")

        if self.retry_count < 0:
            raise ValidationError("Retry count cannot be negative.")

        if self.max_retries < 0:
            raise ValidationError("Max retries cannot be negative.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert job instance to JSON-serializable dictionary."""
        parsed_result = self.result_data
        if isinstance(self.result_data, str) and self.result_data:
            try:
                parsed_result = json.loads(self.result_data)
            except Exception:
                parsed_result = self.result_data

        return {
            "id": self.id,
            "job_type": self.job_type.lower(),
            "asset_id": self.asset_id.strip(),
            "operation": self.operation.strip(),
            "status": self.status.lower(),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "result_data": parsed_result,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanJob":
        """Instantiate ScanJob from dictionary data."""
        raw_result = data.get("result_data")
        parsed_result = raw_result
        if isinstance(raw_result, str) and raw_result:
            try:
                parsed_result = json.loads(raw_result)
            except Exception:
                parsed_result = raw_result

        return cls(
            id=data.get("id", ""),
            job_type=data.get("job_type", "full_orchestrated_scan"),
            asset_id=data.get("asset_id", ""),
            operation=data.get("operation", "run_scan"),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            progress=int(data.get("progress", 0)),
            retry_count=int(data.get("retry_count", 0)),
            max_retries=int(data.get("max_retries", 3)),
            error_message=data.get("error_message"),
            result_data=parsed_result,
        )
