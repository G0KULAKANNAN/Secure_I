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

        # Indexes for assets
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_name ON assets (name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets (hostname);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_type ON assets (asset_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_environment ON assets (environment);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_criticality ON assets (criticality);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_status ON assets (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_updated_at ON assets (updated_at);")

        # Scan Jobs Table (Automation & Background Processing)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                error_message TEXT,
                result_data TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                CONSTRAINT chk_job_status CHECK (
                    status IN ('pending', 'queued', 'running', 'completed', 'partially_completed', 'failed', 'cancelled')
                )
            );
        """)

        # Indexes for jobs
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_asset_id ON scan_jobs (asset_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_status ON scan_jobs (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_created_at ON scan_jobs (created_at);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_job_type ON scan_jobs (job_type);")

    conn.close()
