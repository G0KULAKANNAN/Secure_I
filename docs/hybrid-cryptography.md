# Hybrid Post-Quantum Cryptography in Staging

## 1. Overview & Architectural Principle

Hybrid key exchange pairs a classical key agreement algorithm (such as **X25519** or **NIST P-256**) with a NIST-standardized Post-Quantum Key Encapsulation Mechanism (**ML-KEM-768**, FIPS 203).

$$\text{Shared Secret} = \text{KDF}(\text{Classical Secret} \parallel \text{PQC Secret})$$

This defense-in-depth model guarantees:
1. **Classical Security Hedge**: The connection remains at least as secure as classical cryptography, even if unforeseen mathematical vulnerabilities emerge in lattice cryptography.
2. **Post-Quantum Security**: Active passive eavesdroppers attempting Store Now, Decrypt Later (SNDL) cannot decrypt the recorded ciphertext without breaking the post-quantum component.

---

## 2. Capability Registry & Classification

QuantumShield distinguishes between four levels of cryptographic capability:
1. **Supported by Library**: The algorithm is implemented in cryptographic code (e.g. liboqs, AWS-LC).
2. **Enabled by TLS Implementation**: The runtime TLS stack (OpenSSL/BoringSSL) has configured the hybrid group in `SSL_CTX`.
3. **Negotiated in Connection**: Both client and server successfully exchange key shares and agree on the hybrid group during the TLS 1.3 handshake.
4. **Verified in Test**: Automated interoperability tests demonstrate that both classical-only and hybrid clients connect successfully without connection drop or performance degradation.

---

## 3. Staging Migration Workflow

To prevent disruption to legacy clients or operating system stacks, hybrid configurations follow a strict five-state staging lifecycle:

```
[PLANNED] ──► [CONFIGURED] ──► [TESTING] ──► [VERIFIED] ──► [APPROVED]
                                    │
                                    └──► [FAILED]
```

- **Environment Restriction**: Hybrid profiles are strictly scoped to `staging`. Automatic production deployment is prohibited by policy.
- **Explicit Approval**: Activation requires authenticated operator approval recorded in the immutable audit trail.
- **Safe Rollback**: A single rollback operation reverts configuration to the previous baseline and disables active rollout immediately.
- **Simulation Transparency**: When the host Python runtime uses standard OpenSSL lacking the OQS provider, tests are executed in deterministic simulation mode and tagged:
  `SIMULATED — NO REAL HYBRID TLS CAPABILITY IN PYTHON SSL`.

---

## 4. REST API Reference

- `GET /api/v1/hybrid/capabilities`: Inspect local host OpenSSL provider status and registry of supported hybrid combinations.
- `GET /api/v1/hybrid/profiles`: List all configured staging profiles.
- `POST /api/v1/hybrid/profiles`: Create a new hybrid staging profile.
- `POST /api/v1/hybrid/profiles/<id>/test`: Run interoperability test (real TLS or simulated).
- `POST /api/v1/hybrid/profiles/<id>/approve`: Gate approval for verified profiles.
- `POST /api/v1/hybrid/profiles/<id>/rollback`: Safely restore previous configuration.
- `GET /api/v1/audit/events`: Query immutable audit history.
