"""
Flask Application Factory for QuantumShield Backend API.
"""

import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from flask import Flask, jsonify
from config import get_config
from quantumshield.extensions import cors
from quantumshield.core.exceptions import QuantumShieldError
from quantumshield.storage.database import init_db
from quantumshield.api.health import health_bp
from quantumshield.api.assets import assets_bp


def create_app(config_object=None):
    """
    Construct and configure the Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    if config_object is None:
        config_object = get_config()

    app.config.from_object(config_object)

    # Initialise SQLite Database
    db_path = app.config.get("DATABASE_PATH")
    if db_path:
        init_db(db_path)

    # Initialize extensions
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Register Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(assets_bp)

    # Global Exception Handlers
    @app.errorhandler(QuantumShieldError)
    def handle_quantumshield_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            "status": "error",
            "error": "Resource not found",
            "code": 404
        }), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({
            "status": "error",
            "error": "An unexpected internal server error occurred",
            "code": 500
        }), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=app.config.get("DEBUG", True))
