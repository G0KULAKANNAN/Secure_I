# Security Policy — QuantumShield

## Reporting Security Issues

Security is paramount to QuantumShield. If you discover a security vulnerability, please report it responsibly:

- **Email**: `security@quantumshield.local` or open a private security advisory on GitHub.
- **Scope**:
  - Scanning safety bypasses (e.g., SSRF protections, loopback restrictions).
  - Secret leakage or failure in redaction formatters.
  - Path traversal or symlink escapes during source code scanning.
  - Remote code execution vulnerabilities.

Please do not disclose security issues publicly until a remediation has been validated and released.

## Defensive Design Principles

1. **Explicit Authorisation**: Scanning external endpoints requires explicit authorization flags. Arbitrary IP range scanning is strictly prohibited.
2. **Zero Credential Persistence**: Private keys, passwords, and API tokens are redacted before evidence is stored.
3. **No Exploitation**: QuantumShield is strictly a defensive exposure discovery and migration prioritization platform.
