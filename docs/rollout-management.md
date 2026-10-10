# Staged Production Rollout Management

## 1. Overview

Deploying hybrid Post-Quantum Cryptography (PQC) into production environments introduces operational risks, including client incompatibility, packet fragmentation drops, and latency increases.

QuantumShield manages this risk through a controlled **5-Stage Canary Progression**, a **9-Point Pre-Deployment Readiness Gate**, and **Automated Emergency Rollback** triggered by real-time telemetry threshold breaches.

---

## 2. 5-Stage Canary Progression

QuantumShield coordinates traffic exposure incrementally across five distinct canary stages:

| Stage | Name | Traffic Exposure | Description |
| :--- | :--- | :--- | :--- |
| **Stage 1** | Internal Dogfooding | **1%** | Internal employee traffic, synthetic monitoring probes, CI/CD runners. |
| **Stage 2** | Low-Risk Traffic Canary | **5%** | Non-critical endpoints, regional background workloads, opt-in clients. |
| **Stage 3** | Broader Traffic Canary | **25%** | General public traffic across diverse operating systems and mobile SDKs. |
| **Stage 4** | Majority Production Traffic | **50%** | Mainstream customer traffic, mission-critical API endpoints. |
| **Stage 5** | Full Hybrid Production | **100%** | Dual classical + post-quantum hybrid negotiation active across all endpoints. |

---

## 3. The 9-Point Pre-Deployment Readiness Gate

Before any rollout plan can transition from `DRAFT` to `APPROVED` or advance traffic, the 9-point readiness gate evaluates system health:

1. **Gate 1: Hybrid Profile Staging Verification**: Validates that the hybrid key exchange profile (`X25519MLKEM768`) was verified and approved in the Staging Hybrid Lab.
2. **Gate 2: Network MTU & Middlebox Verification**: Validates that network paths have completed MTU fragmentation and middlebox traversal checks.
3. **Gate 3: Host & Client Compatibility**: Verifies that client compatibility requirements are documented and supported.
4. **Gate 4: Rollback Configuration Validation**: Confirms that a known-good classical fallback configuration (e.g., pure X25519) is persisted and valid.
5. **Gate 5: Telemetry Monitoring Baseline**: Confirms active monitoring hooks for handshake success, latency, and timeout rates.
6. **Gate 6: TLS 1.3 & Key Exchange Compliance**: Verifies that endpoints negotiate TLS 1.3 with draft/FIPS-compliant hybrid groups.
7. **Gate 7: Automated Alert & Rollback Threshold**: Verifies that the automated rollback threshold is configured within safety bounds (e.g. failure rate $\le 2.0\%$).
8. **Gate 8: Operator Ownership & Responsibility**: Confirms designated technical owner assigned to the environment.
9. **Gate 9: Human Sign-Off & Approval**: Enforces explicit human operator review before initiating live canary routing.

---

## 4. Telemetry Monitoring & Automated Rollback

During each canary stage, telemetry samples are ingested or simulated:

- **Metrics Evaluated**:
  - `handshake_success_rate`: Percentage of successfully negotiated TLS 1.3 sessions.
  - `handshake_failure_rate`: Rate of failed handshakes (middlebox resets, client aborts, group negotiation errors).
  - `average_latency_ms`: Duration of full TLS key exchange and connection establishment.
  - `timeout_rate`: Percentage of TCP/TLS timeouts.
- **Rollback Safeguard**:
  - If `handshake_failure_rate > rollback_threshold_failure_rate` (default $2.0\%$), the controller triggers an **immediate automated rollback**.
  - The deployment environment is automatically reverted to the classical configuration reference (`previous_config`), the plan state is set to `ROLLED_BACK`, and an immutable security event is written to `audit_events`.

---

## 5. Simulation Transparency

> [!NOTE]
> QuantumShield explicitly notes that without cloud IAM credentials or direct load-balancer administrative sockets, production proxy transitions and telemetry data are managed in simulation mode. All simulated telemetry displays the badge: `is_simulated = true`.
