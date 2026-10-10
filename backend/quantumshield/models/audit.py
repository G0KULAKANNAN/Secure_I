"""
Audit Domain Model for immutable change tracking and security governance.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import uuid
from typing import Dict, Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AuditEvent:
    id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    action: str = ""
    operator: str = "local_operator"
    details_json: Optional[str] = "{}"
    timestamp: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"aud_{uuid.uuid4().hex[:12]}"
        if not self.timestamp:
            self.timestamp = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        details = {}
        if self.details_json:
            try:
                details = json.loads(self.details_json)
            except Exception:
                details = {"raw": self.details_json}
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "operator": self.operator,
            "details": details,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        details = data.get("details_json")
        if details is None and "details" in data:
            details = json.dumps(data["details"])
        return cls(
            id=data.get("id", ""),
            entity_type=data.get("entity_type", ""),
            entity_id=data.get("entity_id", ""),
            action=data.get("action", ""),
            operator=data.get("operator", "local_operator"),
            details_json=details or "{}",
            timestamp=data.get("timestamp", ""),
        )
