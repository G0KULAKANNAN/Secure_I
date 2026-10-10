"""
Finding Repository for SQLite Persistence, Deduplication, and Risk Scoring.
Supports prioritized queries, Monday Morning queue generation, and auditable assessments.
"""

from pathlib import Path
import json
from typing import List, Optional, Tuple, Union, Dict, Any
from quantumshield.storage.database import get_db_connection
from quantumshield.models.finding import Finding, utc_now_iso
from quantumshield.storage.audit_repository import AuditRepository


class FindingRepository:
    """Repository handling findings persistence, fingerprint deduplication, and risk prioritization."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path
        self.audit_repo = AuditRepository(db_path)

    def save_finding(self, finding: Finding) -> Finding:
        """
        Insert or update a cryptographic finding using deterministic fingerprint deduplication.
        """
        now = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "SELECT id, created_at, remediation_status, data_sensitivity, exposure, "
                    "confidentiality_lifetime, risk_score, risk_category, assigned_owner, "
                    "target_remediation_date FROM findings WHERE fingerprint = ?;",
                    (finding.fingerprint,),
                )
                existing = cursor.fetchone()
                if existing:
                    # Preserve existing manual risk assessment and assignment if newly scanned item doesn't have it
                    data_sensitivity = finding.data_sensitivity if finding.data_sensitivity is not None else existing["data_sensitivity"]
                    exposure = finding.exposure if finding.exposure is not None else existing["exposure"]
                    lifetime = finding.confidentiality_lifetime if finding.confidentiality_lifetime is not None else existing["confidentiality_lifetime"]
                    risk_score = finding.risk_score if finding.risk_score is not None else existing["risk_score"]
                    risk_cat = finding.risk_category if finding.risk_category != "Needs Assessment" else existing["risk_category"]
                    owner = finding.assigned_owner if finding.assigned_owner else existing["assigned_owner"]
                    due_date = finding.target_remediation_date if finding.target_remediation_date else existing["target_remediation_date"]

                    conn.execute(
                        """
                        UPDATE findings SET
                            scan_run_id = COALESCE(?, scan_run_id),
                            job_id = COALESCE(?, job_id),
                            updated_at = ?,
                            evidence = ?,
                            title = ?,
                            description = ?,
                            severity = ?,
                            detection_category = ?,
                            data_sensitivity = ?,
                            exposure = ?,
                            confidentiality_lifetime = ?,
                            risk_score = ?,
                            risk_category = ?,
                            model_version = ?,
                            score_rationale = ?,
                            recommended_action = ?,
                            migration_approach = ?,
                            queue_group = ?,
                            assigned_owner = ?,
                            target_remediation_date = ?
                        WHERE fingerprint = ?;
                        """,
                        (
                            finding.scan_run_id,
                            finding.job_id,
                            now,
                            finding.evidence,
                            finding.title,
                            finding.description,
                            finding.severity,
                            finding.detection_category,
                            data_sensitivity,
                            exposure,
                            lifetime,
                            risk_score,
                            risk_cat,
                            finding.model_version,
                            finding.score_rationale,
                            finding.recommended_action,
                            finding.migration_approach,
                            finding.queue_group,
                            owner,
                            due_date,
                            finding.fingerprint,
                        ),
                    )
                    finding.id = existing["id"]
                    finding.created_at = existing["created_at"]
                    finding.updated_at = now
                    finding.remediation_status = existing["remediation_status"]
                    finding.data_sensitivity = data_sensitivity
                    finding.exposure = exposure
                    finding.confidentiality_lifetime = lifetime
                    finding.risk_score = risk_score
                    finding.risk_category = risk_cat
                    finding.assigned_owner = owner
                    finding.target_remediation_date = due_date
                else:
                    finding.created_at = now
                    finding.updated_at = now
                    conn.execute(
                        """
                        INSERT INTO findings (
                            id, asset_id, scan_run_id, job_id, scanner_type,
                            algorithm, cryptographic_primitive, quantum_vulnerable,
                            recommended_pqc, rule_id, title, description,
                            severity, evidence, file_path, line_number,
                            confidence, remediation_status, fingerprint,
                            detection_category, data_sensitivity, exposure,
                            confidentiality_lifetime, risk_score, risk_category,
                            model_version, score_rationale, recommended_action,
                            migration_approach, queue_group, queue_rank,
                            assigned_owner, target_remediation_date, assessment_status,
                            assessed_at, assessed_by, created_at, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?, ?
                        );
                        """,
                        (
                            finding.id,
                            finding.asset_id,
                            finding.scan_run_id,
                            finding.job_id,
                            finding.scanner_type,
                            finding.algorithm,
                            finding.cryptographic_primitive,
                            1 if finding.quantum_vulnerable else 0,
                            finding.recommended_pqc,
                            finding.rule_id,
                            finding.title,
                            finding.description,
                            finding.severity,
                            finding.evidence,
                            finding.file_path,
                            finding.line_number,
                            finding.confidence,
                            finding.remediation_status,
                            finding.fingerprint,
                            finding.detection_category,
                            finding.data_sensitivity,
                            finding.exposure,
                            finding.confidentiality_lifetime,
                            finding.risk_score,
                            finding.risk_category,
                            finding.model_version,
                            finding.score_rationale,
                            finding.recommended_action,
                            finding.migration_approach,
                            finding.queue_group,
                            finding.queue_rank,
                            finding.assigned_owner,
                            finding.target_remediation_date,
                            finding.assessment_status,
                            finding.assessed_at,
                            finding.assessed_by,
                            finding.created_at,
                            finding.updated_at,
                        ),
                    )
        finally:
            conn.close()

        return finding

    def get_by_id(self, finding_id: str) -> Optional[Finding]:
        """Retrieve finding by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.execute("SELECT * FROM findings WHERE id = ?;", (finding_id,))
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return None
        return Finding.from_dict(dict(row))

    def list_findings(
        self,
        asset_id: Optional[str] = None,
        scan_run_id: Optional[str] = None,
        severity: Optional[str] = None,
        scanner_type: Optional[str] = None,
        status: Optional[str] = None,
        risk_category: Optional[str] = None,
        algorithm: Optional[str] = None,
        assigned_owner: Optional[str] = None,
        queue_group: Optional[str] = None,
        sort_by: str = "risk_score",
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Finding], int]:
        """List findings with rich filtering, risk prioritization, and pagination."""
        conditions = []
        params = []

        if asset_id and asset_id.strip():
            conditions.append("asset_id = ?")
            params.append(asset_id.strip())

        if scan_run_id and scan_run_id.strip():
            conditions.append("scan_run_id = ?")
            params.append(scan_run_id.strip())

        if severity and severity.strip() and severity.lower() != "all":
            conditions.append("severity = ?")
            params.append(severity.strip().lower())

        if scanner_type and scanner_type.strip() and scanner_type.lower() != "all":
            conditions.append("scanner_type = ?")
            params.append(scanner_type.strip().lower())

        if status and status.strip() and status.lower() != "all":
            conditions.append("remediation_status = ?")
            params.append(status.strip().lower())

        if risk_category and risk_category.strip() and risk_category.lower() != "all":
            conditions.append("LOWER(risk_category) = LOWER(?)")
            params.append(risk_category.strip())

        if algorithm and algorithm.strip() and algorithm.lower() != "all":
            conditions.append("algorithm LIKE ?")
            params.append(f"%{algorithm.strip()}%")

        if assigned_owner and assigned_owner.strip() and assigned_owner.lower() != "all":
            if assigned_owner.lower() == "unassigned":
                conditions.append("(assigned_owner IS NULL OR assigned_owner = '')")
            else:
                conditions.append("LOWER(assigned_owner) = LOWER(?)")
                params.append(assigned_owner.strip())

        if queue_group and queue_group.strip() and queue_group.lower() != "all":
            conditions.append("queue_group = ?")
            params.append(queue_group.strip().lower())

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Ordering: Sort by risk_score desc by default (assessed scores first, then unassessed)
        direction = "ASC" if order.lower() == "asc" else "DESC"
        if sort_by == "risk_score":
            order_clause = f"ORDER BY (risk_score IS NULL) ASC, risk_score {direction}, created_at DESC"
        elif sort_by == "created_at":
            order_clause = f"ORDER BY created_at {direction}"
        elif sort_by == "severity":
            order_clause = f"ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END {direction}, created_at DESC"
        else:
            order_clause = f"ORDER BY (risk_score IS NULL) ASC, risk_score {direction}, created_at DESC"

        conn = get_db_connection(self.db_path)
        try:
            count_query = f"SELECT COUNT(*) AS total FROM findings {where_clause};"
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["total"]

            data_query = f"""
                SELECT * FROM findings
                {where_clause}
                {order_clause}
                LIMIT ? OFFSET ?;
            """
            query_params = list(params) + [max(1, limit), max(0, offset)]
            cursor = conn.execute(data_query, query_params)
            rows = cursor.fetchall()
        finally:
            conn.close()

        findings = [Finding.from_dict(dict(r)) for r in rows]
        return findings, total

    def update_assessment(
        self,
        finding_id: str,
        sensitivity: Optional[int],
        exposure: Optional[int],
        lifetime: Optional[int],
        assigned_owner: Optional[str] = None,
        target_remediation_date: Optional[str] = None,
        remediation_status: Optional[str] = None,
        operator: str = "security_lead",
    ) -> Optional[Finding]:
        """
        Update risk factors, recalculate explainable score, and record audit event.
        """
        finding = self.get_by_id(finding_id)
        if not finding:
            return None

        from quantumshield.risk.engine import RiskEngine
        engine = RiskEngine(self.db_path)
        updated_finding = engine.assess_finding(
            finding,
            sensitivity_override=sensitivity,
            exposure_override=exposure,
            lifetime_override=lifetime,
        )

        now = utc_now_iso()
        updated_finding.updated_at = now
        updated_finding.assessed_at = now
        updated_finding.assessed_by = operator
        if assigned_owner is not None:
            updated_finding.assigned_owner = assigned_owner
        if target_remediation_date is not None:
            updated_finding.target_remediation_date = target_remediation_date
        if remediation_status is not None:
            updated_finding.remediation_status = remediation_status.lower()

        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE findings SET
                        data_sensitivity = ?,
                        exposure = ?,
                        confidentiality_lifetime = ?,
                        risk_score = ?,
                        risk_category = ?,
                        model_version = ?,
                        score_rationale = ?,
                        recommended_action = ?,
                        migration_approach = ?,
                        queue_group = ?,
                        assigned_owner = ?,
                        target_remediation_date = ?,
                        remediation_status = ?,
                        assessment_status = ?,
                        assessed_at = ?,
                        assessed_by = ?,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (
                        updated_finding.data_sensitivity,
                        updated_finding.exposure,
                        updated_finding.confidentiality_lifetime,
                        updated_finding.risk_score,
                        updated_finding.risk_category,
                        updated_finding.model_version,
                        updated_finding.score_rationale,
                        updated_finding.recommended_action,
                        updated_finding.migration_approach,
                        updated_finding.queue_group,
                        updated_finding.assigned_owner,
                        updated_finding.target_remediation_date,
                        updated_finding.remediation_status,
                        updated_finding.assessment_status,
                        updated_finding.assessed_at,
                        updated_finding.assessed_by,
                        now,
                        finding_id,
                    ),
                )
        finally:
            conn.close()

        # Record auditable event
        audit_details = json.dumps({
            "finding_id": finding_id,
            "rule_id": updated_finding.rule_id,
            "algorithm": updated_finding.algorithm,
            "sensitivity": sensitivity,
            "exposure": exposure,
            "lifetime": lifetime,
            "risk_score": updated_finding.risk_score,
            "risk_category": updated_finding.risk_category,
            "assigned_owner": updated_finding.assigned_owner,
            "target_date": updated_finding.target_remediation_date,
            "status": updated_finding.remediation_status,
        })
        self.audit_repo.record_event(
            entity_type="finding_risk_assessment",
            entity_id=finding_id,
            action="risk_score_recalculated",
            details_json=audit_details,
            operator=operator,
        )

        return updated_finding

    def update_status(self, finding_id: str, new_status: str) -> Optional[Finding]:
        """Update remediation status of a finding."""
        now = utc_now_iso()
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                cursor = conn.execute(
                    """
                    UPDATE findings SET
                        remediation_status = ?,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (new_status.lower(), now, finding_id),
                )
                affected = cursor.rowcount
        finally:
            conn.close()

        if affected == 0:
            return None
        return self.get_by_id(finding_id)

    def get_remediation_queue(self) -> Dict[str, Any]:
        """
        Generate Monday Morning Remediation Queue grouped into 4 actionable priority tiers
        plus a Needs Assessment bucket.
        """
        findings, _ = self.list_findings(limit=500, sort_by="risk_score", order="desc")

        tiers = {
            "immediate_investigation": [],
            "high_priority_migration": [],
            "scheduled_remediation": [],
            "monitoring_reassessment": [],
            "needs_assessment": [],
        }

        rank = 1
        for f in findings:
            item = {
                "priority_rank": rank,
                "finding_id": f.id,
                "title": f.title,
                "asset_id": f.asset_id,
                "algorithm": f.algorithm,
                "cryptographic_primitive": f.cryptographic_primitive,
                "detection_category": f.detection_category,
                "risk_score": f.risk_score,
                "risk_category": f.risk_category,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "why_now": f.score_rationale or "Requires technical investigation.",
                "first_concrete_action": f.recommended_action or "Review cryptographic usage.",
                "required_validation": f.migration_approach or "Verify environment compatibility.",
                "assigned_owner": f.assigned_owner,
                "target_remediation_date": f.target_remediation_date,
                "remediation_status": f.remediation_status,
                "factors": {
                    "sensitivity": f.data_sensitivity,
                    "exposure": f.exposure,
                    "lifetime": f.confidentiality_lifetime,
                },
            }

            # Map to queue tier
            grp = f.queue_group or ("needs_assessment" if f.risk_score is None else "scheduled_remediation")
            if grp not in tiers:
                grp = "scheduled_remediation"
            tiers[grp].append(item)
            rank += 1

        return {
            "total_items": len(findings),
            "tiers": {
                "immediate_investigation": {
                    "title": "Immediate Investigation (Critical / Active Broken Crypto)",
                    "count": len(tiers["immediate_investigation"]),
                    "items": tiers["immediate_investigation"],
                },
                "high_priority_migration": {
                    "title": "High-Priority Migration Planning (SNDL Exposure / FIPS 203 Target)",
                    "count": len(tiers["high_priority_migration"]),
                    "items": tiers["high_priority_migration"],
                },
                "scheduled_remediation": {
                    "title": "Scheduled Remediation (Moderate Risk / Digital Signatures)",
                    "count": len(tiers["scheduled_remediation"]),
                    "items": tiers["scheduled_remediation"],
                },
                "monitoring_reassessment": {
                    "title": "Monitoring or Reassessment (Low Risk / Approved PQC)",
                    "count": len(tiers["monitoring_reassessment"]),
                    "items": tiers["monitoring_reassessment"],
                },
                "needs_assessment": {
                    "title": "Needs Assessment (Missing Factors)",
                    "count": len(tiers["needs_assessment"]),
                    "items": tiers["needs_assessment"],
                },
            },
        }

    def get_stats(self, asset_id: Optional[str] = None) -> Dict[str, Any]:
        """Return counts of findings grouped by severity, risk category, and overdue tasks."""
        conn = get_db_connection(self.db_path)
        where_clause = "WHERE asset_id = ?" if asset_id else ""
        params = [asset_id] if asset_id else []

        try:
            query = f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low,
                    SUM(CASE WHEN quantum_vulnerable = 1 THEN 1 ELSE 0 END) as quantum_vulnerable,
                    SUM(CASE WHEN LOWER(risk_category) = 'critical' THEN 1 ELSE 0 END) as risk_critical,
                    SUM(CASE WHEN LOWER(risk_category) = 'high' THEN 1 ELSE 0 END) as risk_high,
                    SUM(CASE WHEN LOWER(risk_category) = 'moderate' THEN 1 ELSE 0 END) as risk_moderate,
                    SUM(CASE WHEN LOWER(risk_category) = 'low' THEN 1 ELSE 0 END) as risk_low,
                    SUM(CASE WHEN risk_score IS NULL OR LOWER(risk_category) = 'needs assessment' THEN 1 ELSE 0 END) as needs_assessment,
                    SUM(CASE WHEN target_remediation_date IS NOT NULL AND target_remediation_date < DATE('now') AND remediation_status NOT IN ('remediated', 'accepted_risk') THEN 1 ELSE 0 END) as overdue_remediations
                FROM findings {where_clause};
            """
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
        finally:
            conn.close()

        return {
            "total": row["total"] or 0,
            "total_findings": row["total"] or 0,
            "critical": row["critical"] or 0,
            "high": row["high"] or 0,
            "medium": row["medium"] or 0,
            "low": row["low"] or 0,
            "quantum_vulnerable": row["quantum_vulnerable"] or 0,
            "risk_critical": row["risk_critical"] or 0,
            "risk_high": row["risk_high"] or 0,
            "risk_moderate": row["risk_moderate"] or 0,
            "risk_low": row["risk_low"] or 0,
            "needs_assessment": row["needs_assessment"] or 0,
            "overdue_remediations": row["overdue_remediations"] or 0,
        }
