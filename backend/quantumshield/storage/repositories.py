"""
Data Access Repositories for QuantumShield Storage Layer.
Uses parameterised queries to prevent SQL injection and ensure reliable persistence.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union
from quantumshield.storage.database import get_db_connection
from quantumshield.models.asset import Asset, utc_now_iso


class AssetRepository:
    """Repository handling CRUD and query operations for assets in SQLite."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path

    def create(self, asset: Asset) -> Asset:
        """Insert a new asset record into SQLite."""
        asset.validate()
        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute(
                """
                INSERT INTO assets (
                    id, name, asset_type, environment, hostname,
                    ip_address, owner, description, criticality, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    asset.id,
                    asset.name.strip(),
                    asset.asset_type.lower(),
                    asset.environment.lower(),
                    asset.hostname.strip() if asset.hostname else None,
                    asset.ip_address.strip() if asset.ip_address else None,
                    asset.owner.strip() if asset.owner else None,
                    asset.description.strip() if asset.description else None,
                    asset.criticality.lower(),
                    asset.status.lower(),
                    asset.created_at,
                    asset.updated_at,
                ),
            )
        conn.close()
        return asset

    def get_by_id(self, asset_id: str) -> Optional[Asset]:
        """Retrieve a single asset by unique identifier."""
        conn = get_db_connection(self.db_path)
        cursor = conn.execute("SELECT * FROM assets WHERE id = ?;", (asset_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return Asset.from_dict(dict(row))

    def list_assets(
        self,
        search: Optional[str] = None,
        asset_type: Optional[str] = None,
        environment: Optional[str] = None,
        criticality: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Asset], int]:
        """
        List assets with parameterised search, filtering, and pagination.
        Returns a tuple of (assets_list, total_count).
        """
        conditions = []
        params = []

        if search and search.strip():
            clean_search = f"%{search.strip()}%"
            conditions.append("(name LIKE ? OR hostname LIKE ? OR description LIKE ?)")
            params.extend([clean_search, clean_search, clean_search])

        if asset_type and asset_type.strip():
            conditions.append("asset_type = ?")
            params.append(asset_type.strip().lower())

        if environment and environment.strip():
            conditions.append("environment = ?")
            params.append(environment.strip().lower())

        if criticality and criticality.strip():
            conditions.append("criticality = ?")
            params.append(criticality.strip().lower())

        if status and status.strip():
            conditions.append("status = ?")
            params.append(status.strip().lower())

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        conn = get_db_connection(self.db_path)

        # Count total matching rows
        count_query = f"SELECT COUNT(*) AS total FROM assets {where_clause};"
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()["total"]

        # Fetch paginated rows ordered by updated_at descending
        data_query = f"""
            SELECT * FROM assets
            {where_clause}
            ORDER BY updated_at DESC, created_at DESC
            LIMIT ? OFFSET ?;
        """
        query_params = list(params) + [max(1, limit), max(0, offset)]
        cursor = conn.execute(data_query, query_params)
        rows = cursor.fetchall()
        conn.close()

        assets = [Asset.from_dict(dict(r)) for r in rows]
        return assets, total

    def update(self, asset: Asset) -> Optional[Asset]:
        """Update an existing asset in SQLite."""
        asset.updated_at = utc_now_iso()
        asset.validate()

        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute(
                """
                UPDATE assets SET
                    name = ?,
                    asset_type = ?,
                    environment = ?,
                    hostname = ?,
                    ip_address = ?,
                    owner = ?,
                    description = ?,
                    criticality = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ?;
                """,
                (
                    asset.name.strip(),
                    asset.asset_type.lower(),
                    asset.environment.lower(),
                    asset.hostname.strip() if asset.hostname else None,
                    asset.ip_address.strip() if asset.ip_address else None,
                    asset.owner.strip() if asset.owner else None,
                    asset.description.strip() if asset.description else None,
                    asset.criticality.lower(),
                    asset.status.lower(),
                    asset.updated_at,
                    asset.id,
                ),
            )
            affected = cursor.rowcount
        conn.close()

        if affected == 0:
            return None

        return asset

    def delete(self, asset_id: str) -> bool:
        """Delete an asset record by ID."""
        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute("DELETE FROM assets WHERE id = ?;", (asset_id,))
            affected = cursor.rowcount
        conn.close()
        return affected > 0
