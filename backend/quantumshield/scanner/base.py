"""
Base Scanner Interface and Result Structures for QuantumShield.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from quantumshield.models.asset import Asset


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScanResult:
    """Standardized result returned by all QuantumShield scanners."""
    scanner_type: str
    asset_id: str
    scan_timestamp: str = ""
    status: str = "completed"  # completed, partially_completed, failed, cancelled, unavailable
    findings: List[Dict[str, Any]] = field(default_factory=list)
    evidence_references: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.scan_timestamp:
            self.scan_timestamp = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanner_type": self.scanner_type,
            "asset_id": self.asset_id,
            "scan_timestamp": self.scan_timestamp,
            "status": self.status,
            "findings": self.findings,
            "evidence_references": self.evidence_references,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class BaseScanner(ABC):
    """Abstract base class for all scanner implementations."""

    @property
    @abstractmethod
    def scanner_type(self) -> str:
        """Unique identifier string for scanner."""
        pass

    @abstractmethod
    def scan(self, asset: Asset, options: Optional[Dict[str, Any]] = None) -> ScanResult:
        """Execute non-destructive cryptographic inspection and return ScanResult."""
        pass
