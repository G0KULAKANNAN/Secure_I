# QuantumShield Platform Security Model

## 1. Threat Model & Post-Quantum Context

### 1.1 "Harvest Now, Decrypt Later" (HNDL)
Adversaries with long-term intelligence mandates are currently recording encrypted TLS communications traversing public backbones. While modern classical algorithms like ECDH (X25519) and RSA cannot be broken today, a future **Cryptanalytically Relevant Quantum Computer (CRQC)** executing Shor's algorithm will solve discrete logarithm and integer factorization problems in polynomial time.

QuantumShield facilitates proactive migration to **NIST FIPS 203 (ML-KEM)**, **FIPS 204 (ML-DSA)**, and **FIPS 205 (SLH-DSA)** to eliminate HNDL exposure.

---

## 2. Safe Probing & Network Guardrails

### 2.1 Default Local Loopback
All active network verification probes default to local loopback addresses (`127.0.0.1` / `::1`).

### 2.2 Strict External Network Controls
External network inspection requires:
1. Pre-registration of the host in the Asset Inventory.
2. Explicit boolean allowlisting (`is_allowlisted = True`).
3. Explicit operator authorization (`authorized_by_operator = True`).
4. Hard-capped socket timeouts (5.0 seconds).
5. **SSRF Guard**: Strict blocking of cloud metadata IP ranges (`169.254.169.254`), link-local ranges, and unroutable addresses.

### 2.3 Non-Destructive Passive Inspection
QuantumShield only initiates standard TLS handshakes. It never attempts exploit injections, denial-of-service stress tests, or unauthorized configuration changes on remote hosts.

---

## 3. Simulation Transparency & Cryptographic Honesty

> [!IMPORTANT]
> **No Fake Security**:
> Standard Python distributions (including Python 3.13 on Windows) use host OpenSSL libraries that do not bundle `oqsprovider` or native draft IETF hybrid groups (`X25519MLKEM768`).
>
> When real TLS connections fail to negotiate a hybrid group due to local runtime limitations, QuantumShield **honestly reports the limitation**:
> - Status: `unsupported` / `SIMULATED`
> - Display Label: `SIMULATED — NO REAL HYBRID TLS CAPABILITY IN PYTHON SSL`
>
> QuantumShield never masks cryptographic limitations or creates fake successful handshakes.

---

## 4. SQLite Storage Integrity & Auditability

1. **Persistent SQLite**: Uses WAL mode (`PRAGMA journal_mode = WAL`) and enforced foreign keys (`PRAGMA foreign_keys = ON`).
2. **Zero Mock Data**: All metrics, capabilities, findings, jobs, canary plans, and policies reflect persistent SQLite state.
3. **Immutable Audit Trail**: All governance actions (readiness evaluations, canary advancements, rollbacks, policy overrides, and primitive retirements) write append-only records to `audit_events`.
4. **Idempotent Upgrades**: All schema migrations use safe `CREATE TABLE IF NOT EXISTS` and table introspection to protect existing user inventory across version updates.
