"""
Audit Repository for immutable security audit trail in SQLite.
"""

from pathlib import Path
from typing import List, Optional, Union
from quantumshield.storage.database import get_db_connection
from quantumshield.models.audit import AuditEvent, utc_now_iso


class AuditRepository:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    def record_event(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        details_json: str = "{}",
        operator: str = "local_operator",
    ) -> AuditEvent:
        event = AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            operator=operator,
            details_json=details_json,
            timestamp=utc_now_iso(),
        )
        conn = get_db_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO audit_events (
                        id, entity_type, entity_id, action, operator, details_json, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        event.id,
                        event.entity_type,
                        event.entity_id,
                        event.action,
                        event.operator,
                        event.details_json,
                        event.timestamp,
                    ),
                )
        finally:
            conn.close()
        return event

    def list_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditEvent]:
        conn = get_db_connection(self.db_path)
        clauses = []
        params = []
        if entity_type:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if entity_id:
            clauses.append("entity_id = ?")
            params.append(entity_id)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM audit_events {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [AuditEvent.from_dict(dict(r)) for r in rows]
        finally:
            conn.close()
