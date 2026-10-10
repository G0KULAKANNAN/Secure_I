# Controlled Classical Cryptography Decommissioning

## 1. Objective & Scope

As post-quantum cryptographic primitives (e.g., ML-KEM-768 for key exchange and ML-DSA-65 for signatures) are validated and staged in production, legacy classical primitives must be systematically retired.

Premature or uncoordinated decommissioning risks service outages, broken external client integrations, and partner API failures. Conversely, delayed decommissioning leaves organizations vulnerable to **"Harvest Now, Decrypt Later" (HNDL)** quantum adversaries.

QuantumShield implements a controlled, auditable, and rollback-safe retirement pipeline to guarantee zero unplanned downtime during algorithmic sunsetting.

---

## 2. Policy Governance Framework

QuantumShield categorizes all cryptographic algorithms into six standardized policy states:

| Policy Status | Meaning & Operational Constraint | Examples |
| :--- | :--- | :--- |
| **`APPROVED`** | Fully validated for long-term production use. Meets NIST post-quantum or high-security classical standards. | ML-KEM-768, X25519MLKEM768, ML-DSA-65, AES-256 |
| **`APPROVED_WITH_CONDITIONS`** | Permitted for specific legacy workloads or short-lived ephemeral sessions. | AES-128 (64-bit quantum strength under Grover's algorithm) |
| **`MIGRATION_REQUIRED`** | Active in production, but flagged with a mandatory migration deadline. | RSA-2048, ECDSA-P256 |
| **`DEPRECATED`** | Prohibited for new sessions or handshakes; permitted only for historical decryption / verification. | Diffie-Hellman Group 14 |
| **`PROHIBITED_BY_CONFIGURED_POLICY`** | Zero-tolerance prohibition across all environments and cipher suites. | RSA-1024, SHA-1, 3DES, RC4 |
| **`NEEDS_REVIEW`** | Unrecognized algorithm requiring cryptanalysis and policy classification. | Custom / proprietary algorithms |

---

## 3. Cryptographic Dependency Inventory

Decommissioning cannot treat a system as a monolith. A single service may use multiple independent primitives:
1. **Key Exchange (KEM / ECDH)**: Protects session confidentiality against future CRQCs.
2. **Digital Signatures (DSA / ECDSA)**: Protects identity authentication and integrity.
3. **Symmetric Encryption (AES)**: Protects bulk payload data.
4. **Hashing (SHA-2 / SHA-3)**: Protects message digest integrity.

QuantumShield catalogs dependencies per service and primitive, tracking each from `active` to `migrating` to `decommissioned`.

---

## 4. The 10-Point Decommissioning Readiness Gate

Before any classical primitive is deactivated, the 10-point gate verifies operational safety:

1. **Quantum-Safe Replacement Identified**: Replacement algorithm mapped and validated against NIST FIPS standards.
2. **Dependent Services Migrated & Verified**: All services marked as `migrating` or verified on hybrid paths.
3. **Fallback Compatibility Paths Defined**: Documented failover routes established.
4. **Staging Regressions Verified**: Interoperability test passes in the Staging Hybrid Lab.
5. **Zero Legacy Traffic Telemetry**: Handshake telemetry confirms zero active client traffic relying on the primitive.
6. **Certificate Compliance & Trust Chains**: Certificate authorities and dual-stack credentials validated.
7. **Rollback Playbook Documented**: Step-by-step instructions recorded for immediate recovery within SLA.
8. **Security Policy Active**: Deprecation or prohibition rule enforced in database.
9. **Technical Service Owner Sign-off**: Designated service engineering lead approves retirement.
10. **Executive & CISO Authorization**: Formal executive sign-off required for permanent primitive decommission.

---

## 5. Decommissioning Lifecycle & Rollback Playbook

```
DISCOVERED ──> MIGRATION_VERIFIED ──> READY_FOR_REVIEW ──> APPROVED ──> COMPLETED
     │                                     │                  │             │
     └─────────────────────────────── BLOCKED ────────────────┴──────> ROLLED_BACK
```

- **Execution**: Setting a plan to `COMPLETED` automatically updates all matching dependent services to `decommissioned` and logs an immutable audit event (`CLASSICAL_PRIMITIVE_DECOMMISSIONED`).
- **Rollback Guarantee**: In the event of unforeseen downstream client failures, the operator triggers `Rollback Decommissioning`, which instantly restores dependent services to `active` and records the reason in the audit trail.
