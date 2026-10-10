"""
Domain constants, error codes, and enum values.
"""

# Risk Scoring Weight Constants (R = 20 * (0.35C + 0.30S + 0.25L + 0.10E))
WEIGHT_CRYPTO_EXPOSURE = 0.35
WEIGHT_DATA_SENSITIVITY = 0.30
WEIGHT_CONFIDENTIALITY_LIFETIME = 0.25
WEIGHT_EXPOSURE = 0.10

# Valid Enum Values
VALID_ENVIRONMENTS = {"development", "testing", "production"}
VALID_CRITICALITY_LEVELS = {"low", "medium", "high", "critical"}
VALID_FINDING_STATUSES = {
    "potential_exposure",
    "verified_usage",
    "needs_review",
    "insufficient_evidence",
    "remediated",
    "accepted_risk",
}
VALID_MIGRATION_STATUSES = {
    "not_started",
    "assessment",
    "testing",
    "approved",
    "completed",
}
