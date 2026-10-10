"""
Asset Data Model and Validation.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import uuid
import re
from typing import Optional, Dict, Any
from quantumshield.core.exceptions import ValidationError


VALID_ASSET_TYPES = {"server", "website", "application", "certificate", "database", "other"}
VALID_ENVIRONMENTS = {"development", "testing", "staging", "production"}
VALID_CRITICALITY = {"low", "medium", "high", "critical"}
VALID_STATUSES = {"active", "inactive", "under_review"}


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Asset:
    id: str = ""
    name: str = ""
    asset_type: str = "other"
    environment: str = "production"
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    criticality: str = "medium"
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"ast_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = utc_now_iso()
        if not self.updated_at:
            self.updated_at = self.created_at

    def validate(self) -> None:
        """Validate asset fields against security and business rules."""
        if not self.name or not self.name.strip():
            raise ValidationError("Asset name is required and cannot be empty.")
        if len(self.name.strip()) > 255:
            raise ValidationError("Asset name cannot exceed 255 characters.")

        if self.asset_type.lower() not in VALID_ASSET_TYPES:
            raise ValidationError(
                f"Invalid asset_type '{self.asset_type}'. Must be one of: {', '.join(sorted(VALID_ASSET_TYPES))}"
            )

        if self.environment.lower() not in VALID_ENVIRONMENTS:
            raise ValidationError(
                f"Invalid environment '{self.environment}'. Must be one of: {', '.join(sorted(VALID_ENVIRONMENTS))}"
            )

        if self.criticality.lower() not in VALID_CRITICALITY:
            raise ValidationError(
                f"Invalid criticality '{self.criticality}'. Must be one of: {', '.join(sorted(VALID_CRITICALITY))}"
            )

        if self.status.lower() not in VALID_STATUSES:
            raise ValidationError(
                f"Invalid status '{self.status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )

        if self.hostname and len(self.hostname.strip()) > 255:
            raise ValidationError("Hostname cannot exceed 255 characters.")

        if self.ip_address and self.ip_address.strip():
            clean_ip = self.ip_address.strip()
            if len(clean_ip) > 45:
                raise ValidationError("IP address cannot exceed 45 characters.")
            import ipaddress
            try:
                ipaddress.ip_address(clean_ip)
            except ValueError:
                raise ValidationError(f"Invalid IP address format '{clean_ip}'. Must be a valid IPv4 or IPv6 address.")

        if self.owner and len(self.owner.strip()) > 255:
            raise ValidationError("Owner cannot exceed 255 characters.")

        if self.description and len(self.description.strip()) > 2000:
            raise ValidationError("Description cannot exceed 2000 characters.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert asset instance to serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name.strip(),
            "asset_type": self.asset_type.lower(),
            "environment": self.environment.lower(),
            "hostname": self.hostname.strip() if self.hostname else None,
            "ip_address": self.ip_address.strip() if self.ip_address else None,
            "owner": self.owner.strip() if self.owner else None,
            "description": self.description.strip() if self.description else None,
            "criticality": self.criticality.lower(),
            "status": self.status.lower(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Asset":
        """Instantiate Asset from dictionary data."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            asset_type=data.get("asset_type", "server"),
            environment=data.get("environment", "development"),
            hostname=data.get("hostname"),
            ip_address=data.get("ip_address"),
            owner=data.get("owner"),
            description=data.get("description"),
            criticality=data.get("criticality", "medium"),
            status=data.get("status", "active"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
