"""
Health check and application version API routes.
"""

import platform
import time
from flask import Blueprint, jsonify, current_app
from quantumshield import __version__

health_bp = Blueprint("health", __name__, url_prefix="/api/v1")
START_TIME = time.time()


@health_bp.route("/health", methods=["GET"])
def get_health():
    """
    Check API service status, environment mode, and uptime.
    """
    uptime_seconds = round(time.time() - START_TIME, 2)
    return jsonify({
        "status": "ok",
        "service": "QuantumShield API",
        "version": __version__,
        "environment": current_app.config.get("ENV", "development"),
        "uptime_seconds": uptime_seconds,
        "python_version": platform.python_version(),
    }), 200


@health_bp.route("/version", methods=["GET"])
def get_version():
    """
    Get application version metadata.
    """
    return jsonify({
        "status": "ok",
        "name": "QuantumShield — Cryptographic Exposure Intelligence Platform",
        "version": __version__,
        "api_version": "v1",
        "disclaimer": (
            "Potential quantum vulnerability detection is not proof of compromise. "
            "Prioritisation scores do not predict when a quantum computer will break a cryptographic system."
        ),
    }), 200
