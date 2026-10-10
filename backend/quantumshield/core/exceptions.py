"""
Application domain exceptions.
"""

class QuantumShieldError(Exception):
    """Base exception for QuantumShield application."""
    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self):
        rv = dict(self.payload)
        rv["error"] = self.message
        rv["status"] = "error"
        return rv


class ValidationError(QuantumShieldError):
    """Raised on invalid request input."""
    def __init__(self, message: str, payload: dict = None):
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(QuantumShieldError):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str, payload: dict = None):
        super().__init__(message, status_code=404, payload=payload)


class ConfigurationError(QuantumShieldError):
    """Raised when configuration is invalid."""
    def __init__(self, message: str, payload: dict = None):
        super().__init__(message, status_code=500, payload=payload)
