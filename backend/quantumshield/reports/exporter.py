"""
Audit Reports and Data Export Engine.
Generates compliant, sanitized CSV reports from actual SQLite findings and scan runs.
Enforces CSV formula injection mitigations.
"""

import io
import csv
from typing import List, Optional, Any
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.repositories import AssetRepository
from quantumshield.models.finding import Finding


def sanitize_csv_cell(value: Any) -> str:
    """Neutralize potential CSV formula injection characters (=, +, -, @, tab, CR)."""
    if value is None:
        return ""
    text = str(value).strip()
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{text}"
    return text


class ReportExporter:
    """Exports actual findings and assets to sanitized CSV format."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.finding_repo = FindingRepository(db_path)
        self.asset_repo = AssetRepository(db_path)

    def export_findings_csv(self, asset_id: Optional[str] = None) -> str:
        """Generate a complete CSV document containing real database findings."""
        findings, _ = self.finding_repo.list_findings(asset_id=asset_id, limit=2000)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        headers = [
            "Finding ID",
            "Asset ID",
            "Scanner Type",
            "Algorithm",
            "Cryptographic Primitive",
            "Quantum Vulnerable",
            "Recommended NIST PQC",
            "Rule ID",
            "Title",
            "Severity",
            "Confidence",
            "Remediation Status",
            "Target Location",
            "Line Number",
            "First Seen (UTC)",
            "Last Seen (UTC)",
            "Evidence Excerpt",
        ]
        writer.writerow(headers)

        for f in findings:
            row = [
                sanitize_csv_cell(f.id),
                sanitize_csv_cell(f.asset_id),
                sanitize_csv_cell(f.scanner_type),
                sanitize_csv_cell(f.algorithm),
                sanitize_csv_cell(f.cryptographic_primitive),
                sanitize_csv_cell("YES" if f.quantum_vulnerable else "NO"),
                sanitize_csv_cell(f.recommended_pqc),
                sanitize_csv_cell(f.rule_id),
                sanitize_csv_cell(f.title),
                sanitize_csv_cell(f.severity.upper()),
                sanitize_csv_cell(f.confidence),
                sanitize_csv_cell(f.remediation_status),
                sanitize_csv_cell(f.file_path or "N/A"),
                sanitize_csv_cell(f.line_number or "N/A"),
                sanitize_csv_cell(f.first_seen),
                sanitize_csv_cell(f.last_seen),
                sanitize_csv_cell(f.evidence.replace("\n", " | ") if f.evidence else ""),
            ]
            writer.writerow(row)

        return output.getvalue()
