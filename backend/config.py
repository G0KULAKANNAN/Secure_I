"""
QuantumShield Central Configuration Management.
"""

import os
from pathlib import Path
from typing import List


BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base Configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "quantumshield-default-dev-secret-key-change-me")
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = False
    TESTING = False

    # Database
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "quantumshield.db"))

    # CORS
    CORS_ORIGINS: List[str] = os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")

    # Scanner Limits
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10 MB
    NETWORK_TIMEOUT_SECONDS = int(os.environ.get("NETWORK_TIMEOUT_SECONDS", 30))
    MAX_DIRECTORY_DEPTH = 10
    ALLOWED_EXTENSIONS = {".py", ".java", ".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".pem", ".crt", ".cer"}


class DevelopmentConfig(Config):
    """Development Configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing Configuration."""
    TESTING = True
    DATABASE_PATH = BASE_DIR / "test_quantumshield.db"


class ProductionConfig(Config):
    """Production Configuration."""
    DEBUG = False
    TESTING = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    env_name = os.environ.get("FLASK_ENV", "development").lower()
    return config_by_name.get(env_name, DevelopmentConfig)
