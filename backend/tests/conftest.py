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


@pytest.fixture
def app():
    """Create test application instance."""
    app_inst = create_app(config_object=TestingConfig)
    yield app_inst


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()
