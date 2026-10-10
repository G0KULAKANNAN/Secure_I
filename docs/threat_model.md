# QuantumShield Threat Model

## Threat Landscape: Harvest Now, Decrypt Later (HNDL)

Nation-state and advanced adversaries currently intercept and archive encrypted network traffic and encrypted backups. While asymmetric encryption (RSA, ECC) protects this data today, adversaries intend to decrypt it when cryptographically relevant quantum computers become operational.

## Scanner Trust Boundaries & Protections

1. **SSRF & DNS Rebinding**: TLS scanner validates resolved IP addresses, rejecting RFC 1918 private IPs, loopback, and link-local ranges by default.
2. **Credential Sanitization**: Private keys (`-----BEGIN PRIVATE KEY-----`) and passwords are automatically redacted from logs and scan excerpts.
3. **Symlink Escape Mitigation**: File traversal rejects directory traversal outside user-selected paths.
