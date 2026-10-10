"""
Pytest configuration and test fixtures.
"""

import sys
from pathlib import Path

# Ensure backend directory is in Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from app import create_app
from config import TestingConfig
from quantumshield.storage.database import init_db


@pytest.fixture
def app(tmp_path):
    """Create test application instance with an isolated temporary SQLite database."""
    test_db = tmp_path / "test_quantumshield.db"

    class IsolatedTestingConfig(TestingConfig):
        DATABASE_PATH = test_db

    init_db(test_db)
    app_inst = create_app(config_object=IsolatedTestingConfig)
    yield app_inst

    # Cleanup test db
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()
