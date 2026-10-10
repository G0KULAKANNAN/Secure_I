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
                asset_id TEXT,
                operation TEXT NOT NULL DEFAULT 'execute',
                status TEXT NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 5,
                payload_json TEXT,
                result_json TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                updated_at TEXT NOT NULL,
                next_retry_at TEXT,
                error_code TEXT,
                error_message TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                CONSTRAINT chk_job_status CHECK (
                    status IN ('pending', 'queued', 'running', 'completed', 'partially_completed', 'failed', 'cancel_requested', 'cancelled')
                )
            );
        """)

        # Perform seamless migration if scan_jobs was created in an older schema
        _migrate_scan_jobs_table(conn)

        # Indexes for jobs
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_asset_id ON scan_jobs (asset_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_status ON scan_jobs (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_created_at ON scan_jobs (created_at);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_job_type ON scan_jobs (job_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_priority ON scan_jobs (priority);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_next_retry ON scan_jobs (next_retry_at);")

        # Scan Runs Table (Scan Orchestration)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_runs (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                requested_scanners TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                total_jobs INTEGER NOT NULL DEFAULT 0,
                completed_jobs INTEGER NOT NULL DEFAULT 0,
                failed_jobs INTEGER NOT NULL DEFAULT 0,
                cancelled_jobs INTEGER NOT NULL DEFAULT 0,
                result_summary TEXT,
                error_summary TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                CONSTRAINT chk_scan_run_status CHECK (
                    status IN ('queued', 'running', 'completed', 'partially_completed', 'failed', 'cancelled')
                )
            );
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_asset_id ON scan_runs (asset_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_status ON scan_runs (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_created_at ON scan_runs (created_at);")

        # Unified Findings Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                scan_run_id TEXT,
                job_id TEXT,
                scanner_type TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                cryptographic_primitive TEXT NOT NULL DEFAULT 'key_establishment',
                quantum_vulnerable INTEGER NOT NULL DEFAULT 1,
                recommended_pqc TEXT NOT NULL DEFAULT 'ML-KEM-768',
                rule_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'high',
                evidence TEXT NOT NULL,
                file_path TEXT,
                line_number INTEGER,
                confidence TEXT NOT NULL DEFAULT 'high',
                remediation_status TEXT NOT NULL DEFAULT 'potential_exposure',
                fingerprint TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id) ON DELETE SET NULL,
                CONSTRAINT chk_finding_severity CHECK (
                    severity IN ('info', 'low', 'medium', 'high', 'critical')
                ),
                CONSTRAINT chk_finding_remediation CHECK (
                    remediation_status IN ('potential_exposure', 'verified_usage', 'needs_review', 'remediated', 'accepted_risk')
                )
            );
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_asset_id ON findings (asset_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings (severity);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_fingerprint ON findings (fingerprint);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_scanner_type ON findings (scanner_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_scan_run_id ON findings (scan_run_id);")

    conn.close()


def _migrate_scan_jobs_table(conn: sqlite3.Connection) -> None:
    """
    Ensure scan_jobs has all required Milestone 1 columns and nullable asset_id.
    """
    cursor = conn.execute("PRAGMA table_info(scan_jobs);")
    columns = {row["name"]: dict(row) for row in cursor.fetchall()}

    # If table is newly created or empty with proper schema, check missing columns
    needed_columns = {
        "priority": "INTEGER NOT NULL DEFAULT 5",
        "payload_json": "TEXT",
        "result_json": "TEXT",
        "attempt_count": "INTEGER NOT NULL DEFAULT 0",
        "max_attempts": "INTEGER NOT NULL DEFAULT 3",
        "finished_at": "TEXT",
        "updated_at": "TEXT",
        "next_retry_at": "TEXT",
        "error_code": "TEXT",
        "scan_run_id": "TEXT",
    }

    for col_name, col_type in needed_columns.items():
        if col_name not in columns:
            conn.execute(f"ALTER TABLE scan_jobs ADD COLUMN {col_name} {col_type};")

    # If asset_id has NOT NULL constraint or status check constraint needs upgrading, migrate table safely
    asset_id_col = columns.get("asset_id", {})
    if asset_id_col.get("notnull") == 1:
        # Recreate table with nullable asset_id
        conn.execute("""
            CREATE TABLE scan_jobs_migration (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                asset_id TEXT,
                operation TEXT NOT NULL DEFAULT 'execute',
                status TEXT NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 5,
                payload_json TEXT,
                result_json TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                updated_at TEXT NOT NULL,
                next_retry_at TEXT,
                error_code TEXT,
                error_message TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                CONSTRAINT chk_job_status CHECK (
                    status IN ('pending', 'queued', 'running', 'completed', 'partially_completed', 'failed', 'cancel_requested', 'cancelled')
                )
            );
        """)

        # Copy data
        conn.execute("""
            INSERT INTO scan_jobs_migration (
                id, job_type, asset_id, operation, status, priority,
                progress, attempt_count, max_attempts, created_at, started_at,
                finished_at, updated_at, error_message, result_json
            )
            SELECT
                id, job_type, asset_id, operation, status,
                COALESCE(priority, 5), progress,
                COALESCE(retry_count, 0), COALESCE(max_retries, 3),
                created_at, started_at, completed_at,
                COALESCE(created_at, datetime('now')),
                error_message, result_data
            FROM scan_jobs;
        """)

        conn.execute("DROP TABLE scan_jobs;")
        conn.execute("ALTER TABLE scan_jobs_migration RENAME TO scan_jobs;")

    # Sync any updated_at that might be NULL
    conn.execute("UPDATE scan_jobs SET updated_at = created_at WHERE updated_at IS NULL;")
