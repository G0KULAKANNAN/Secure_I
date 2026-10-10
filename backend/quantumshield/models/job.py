"""
Scan Job Data Model and Lifecycle State Definitions.
Milestone 1: Persistent Background Job Processing Engine.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import uuid
from typing import Optional, Dict, Any, Union, Set
from quantumshield.core.exceptions import ValidationError


VALID_JOB_STATUSES: Set[str] = {
    "pending",
    "queued",
    "running",
    "completed",
    "partially_completed",
    "failed",
    "cancel_requested",
    "cancelled",
}

VALID_JOB_TYPES: Set[str] = {
    "health_check",
    "asset_validation",
    "certificate_scan",
    "tls_scan",
    "static_scan",
    "system_scan",
    "full_orchestrated_scan",
    "change_detection",
}

# Lifecycle State Machine Transition Rules
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "pending": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"completed", "partially_completed", "failed", "cancel_requested"},
    "cancel_requested": {"cancelled", "failed"},
    "failed": {"queued"},
    "cancelled": {"queued"},
    "completed": set(),
    "partially_completed": set(),
}


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def calculate_backoff(attempt_count: int, base_seconds: int = 5, max_seconds: int = 300) -> int:
    """
    Calculate exponential backoff in seconds for retries:
    base * (2 ** (attempt_count - 1)), capped at max_seconds.
    """
    if attempt_count <= 0:
        return base_seconds
    delay = base_seconds * (2 ** (attempt_count - 1))
    return min(max_seconds, delay)


@dataclass(init=False)
class ScanJob:
    id: str
    job_type: str
    asset_id: Optional[str]
    operation: str
    status: str
    priority: int
    payload_json: Optional[Union[Dict[str, Any], str]]
    result_json: Optional[Union[Dict[str, Any], str]]
    progress: int
    attempt_count: int
    max_attempts: int
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
    updated_at: str
    next_retry_at: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    scan_run_id: Optional[str]

    def __init__(
        self,
        id: str = "",
        job_type: str = "health_check",
        asset_id: Optional[str] = None,
        operation: str = "execute",
        status: str = "pending",
        priority: int = 5,
        payload_json: Optional[Union[Dict[str, Any], str]] = None,
        result_json: Optional[Union[Dict[str, Any], str]] = None,
        progress: int = 0,
        attempt_count: Optional[int] = None,
        max_attempts: Optional[int] = None,
        created_at: str = "",
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
        updated_at: str = "",
        next_retry_at: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        scan_run_id: Optional[str] = None,
        # Legacy aliases
        retry_count: Optional[int] = None,
        max_retries: Optional[int] = None,
        completed_at: Optional[str] = None,
        result_data: Optional[Union[Dict[str, Any], str]] = None,
        payload: Optional[Union[Dict[str, Any], str]] = None,
        **kwargs,
    ):
        self.id = id if id else f"job_{uuid.uuid4().hex[:12]}"
        self.job_type = job_type
        self.asset_id = asset_id.strip() if asset_id and str(asset_id).strip() else None
        self.operation = operation
        self.status = status
        self.priority = int(priority)

        # Payload resolution and parsing
        effective_payload = payload_json if payload_json is not None else payload
        if isinstance(effective_payload, str) and effective_payload:
            try:
                effective_payload = json.loads(effective_payload)
            except Exception:
                pass
        self.payload_json = effective_payload

        # Result resolution and parsing
        effective_result = result_json if result_json is not None else result_data
        if isinstance(effective_result, str) and effective_result:
            try:
                effective_result = json.loads(effective_result)
            except Exception:
                pass
        self.result_json = effective_result

        self.progress = int(progress)
        self.attempt_count = int(attempt_count if attempt_count is not None else (retry_count or 0))
        self.max_attempts = int(max_attempts if max_attempts is not None else (max_retries or 3))

        now = utc_now_iso()
        self.created_at = created_at or now
        self.started_at = started_at
        self.finished_at = finished_at or completed_at
        self.updated_at = updated_at or self.created_at
        self.next_retry_at = next_retry_at
        self.error_code = error_code
        self.error_message = error_message
        self.scan_run_id = scan_run_id

    # Backward compatibility properties
    @property
    def retry_count(self) -> int:
        return self.attempt_count

    @retry_count.setter
    def retry_count(self, value: int):
        self.attempt_count = value

    @property
    def max_retries(self) -> int:
        return self.max_attempts

    @max_retries.setter
    def max_retries(self, value: int):
        self.max_attempts = value

    @property
    def completed_at(self) -> Optional[str]:
        return self.finished_at

    @completed_at.setter
    def completed_at(self, value: Optional[str]):
        self.finished_at = value

    @property
    def result_data(self) -> Optional[Union[Dict[str, Any], str]]:
        return self.result_json

    @result_data.setter
    def result_data(self, value: Optional[Union[Dict[str, Any], str]]):
        self.result_json = value

    def can_transition_to(self, target_status: str) -> bool:
        """Verify whether transition from current status to target_status is valid."""
        target = target_status.lower()
        allowed = ALLOWED_TRANSITIONS.get(self.status.lower(), set())
        return target in allowed

    def validate(self) -> None:
        """Validate job fields against schema rules."""
        if not self.job_type or self.job_type.lower() not in VALID_JOB_TYPES:
            raise ValidationError(
                f"Invalid job_type '{self.job_type}'. Must be one of: {', '.join(sorted(VALID_JOB_TYPES))}"
            )

        if not self.status or self.status.lower() not in VALID_JOB_STATUSES:
            raise ValidationError(
                f"Invalid status '{self.status}'. Must be one of: {', '.join(sorted(VALID_JOB_STATUSES))}"
            )

        if not (1 <= self.priority <= 10):
            raise ValidationError("Priority must be an integer between 1 and 10.")

        if not (0 <= self.progress <= 100):
            raise ValidationError("Progress must be an integer between 0 and 100.")

        if self.attempt_count < 0:
            raise ValidationError("Attempt count cannot be negative.")

        if self.max_attempts < 1:
            raise ValidationError("Max attempts must be at least 1.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert job instance to JSON-serializable dictionary."""
        def parse_json(val):
            if isinstance(val, str) and val:
                try:
                    return json.loads(val)
                except Exception:
                    return val
            return val

        parsed_payload = parse_json(self.payload_json)
        parsed_result = parse_json(self.result_json)

        return {
            "id": self.id,
            "job_type": self.job_type.lower(),
            "asset_id": self.asset_id.strip() if self.asset_id else None,
            "operation": self.operation.strip() if self.operation else "execute",
            "status": self.status.lower(),
            "priority": self.priority,
            "payload_json": parsed_payload,
            "result_json": parsed_result,
            "progress": self.progress,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "updated_at": self.updated_at,
            "next_retry_at": self.next_retry_at,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "scan_run_id": self.scan_run_id,
            # Legacy fields for backward compatibility
            "retry_count": self.attempt_count,
            "max_retries": self.max_attempts,
            "completed_at": self.finished_at,
            "result_data": parsed_result,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanJob":
        """Instantiate ScanJob from dictionary data."""
        # Handle payload
        raw_payload = data.get("payload_json") or data.get("payload")
        # Handle result
        raw_result = data.get("result_json") or data.get("result_data")

        # Handle attempt count (attempt_count or retry_count)
        attempt_count = data.get("attempt_count")
        if attempt_count is None:
            attempt_count = data.get("retry_count", 0)

        # Handle max attempts (max_attempts or max_retries)
        max_attempts = data.get("max_attempts")
        if max_attempts is None:
            max_attempts = data.get("max_retries", 3)

        # Handle finished_at / completed_at
        finished_at = data.get("finished_at") or data.get("completed_at")

        asset_id = data.get("asset_id")
        if asset_id is not None:
            asset_id = str(asset_id).strip()
            if not asset_id:
                asset_id = None

        return cls(
            id=data.get("id", ""),
            job_type=data.get("job_type", "health_check"),
            asset_id=asset_id,
            operation=data.get("operation", "execute"),
            status=data.get("status", "pending"),
            priority=int(data.get("priority", 5)),
            payload_json=raw_payload,
            result_json=raw_result,
            progress=int(data.get("progress", 0)),
            attempt_count=int(attempt_count),
            max_attempts=int(max_attempts),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at"),
            finished_at=finished_at,
            updated_at=data.get("updated_at", ""),
            next_retry_at=data.get("next_retry_at"),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            scan_run_id=data.get("scan_run_id"),
        )
