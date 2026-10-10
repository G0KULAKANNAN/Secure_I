"""
Tests for SQLite Database Initialisation and Constraints.
"""

from pathlib import Path
from quantumshield.storage.database import init_db, get_db_connection


def test_init_db_creates_tables_and_indexes(tmp_path):
    """Test init_db creates assets table and required indexes."""
    db_file = tmp_path / "test.db"
    init_db(db_file)

    conn = get_db_connection(db_file)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets';")
    table = cursor.fetchone()
    assert table is not None
    assert table["name"] == "assets"

    # Verify indexes
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='assets';")
    indexes = {row["name"] for row in cursor.fetchall()}
    assert "idx_assets_name" in indexes
    assert "idx_assets_type" in indexes
    assert "idx_assets_environment" in indexes
    assert "idx_assets_criticality" in indexes
    assert "idx_assets_status" in indexes
    conn.close()


def test_init_db_idempotent_preserves_data(tmp_path):
    """Test re-running init_db preserves existing records without error."""
    db_file = tmp_path / "test.db"
    init_db(db_file)

    # Insert a dummy record
    conn = get_db_connection(db_file)
    conn.execute("""
        INSERT INTO assets (id, name, asset_type, environment, created_at, updated_at)
        VALUES ('ast_001', 'Test Server', 'server', 'production', '2026-10-10T00:00:00Z', '2026-10-10T00:00:00Z');
    """)
    conn.commit()
    conn.close()

    # Re-run init_db
    init_db(db_file)

    conn = get_db_connection(db_file)
    cursor = conn.execute("SELECT COUNT(*) AS cnt FROM assets;")
    count = cursor.fetchone()["cnt"]
    conn.close()

    assert count == 1
