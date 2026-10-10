"""
SQLite Database Storage Layer for QuantumShield.
Handles connection management, parameterised execution, and schema initialisation.
"""

import sqlite3
from pathlib import Path
from typing import Union


def get_db_connection(db_path: Union[str, Path]) -> sqlite3.Connection:
    """
    Open an SQLite connection with row mapping and foreign keys enabled.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Union[str, Path]) -> None:
    """
    Initialise or migrate the SQLite database schema safely.
    Creates tables and indexes IF NOT EXISTS without dropping existing data.
    """
    conn = get_db_connection(db_path)
    with conn:
        # Assets Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                environment TEXT NOT NULL,
                hostname TEXT,
                ip_address TEXT,
                owner TEXT,
                description TEXT,
                criticality TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT chk_asset_type CHECK (
                    asset_type IN ('server', 'website', 'application', 'certificate', 'database', 'other')
                ),
                CONSTRAINT chk_environment CHECK (
                    environment IN ('development', 'testing', 'staging', 'production')
                ),
                CONSTRAINT chk_criticality CHECK (
                    criticality IN ('low', 'medium', 'high', 'critical')
                ),
                CONSTRAINT chk_status CHECK (
                    status IN ('active', 'inactive', 'under_review')
                )
            );
        """)

        # Indexes for fast search and filtering
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_name ON assets (name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets (hostname);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_type ON assets (asset_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_environment ON assets (environment);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_criticality ON assets (criticality);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_status ON assets (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_updated_at ON assets (updated_at);")

    conn.close()
