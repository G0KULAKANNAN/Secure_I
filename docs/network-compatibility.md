# Post-Quantum Network MTU & Middlebox Verification

## 1. Problem Statement: Enlarged Handshake Payloads

Post-quantum algorithms require significantly larger key shares and public keys than classical elliptic curve cryptography:

| Mechanism | Classical (X25519) | Post-Quantum (ML-KEM-768) | Hybrid (X25519 + ML-KEM-768) |
| :--- | :--- | :--- | :--- |
| **ClientHello Key Share** | 32 bytes | 1,184 bytes | ~1,216 bytes |
| **ServerHello Key Share** | 32 bytes | 1,088 bytes | ~1,120 bytes |
| **Total Handshake Overhead** | < 1.0 KB | ~2.5 KB | ~3.0 KB – 3.5 KB |

Because typical Internet and datacenter Ethernet interfaces configure a **Maximum Transmission Unit (MTU)** of 1,500 bytes, TLS handshake records containing PQC key shares exceed single packet limits.

---

## 2. Packet Fragmentation Realities

> [!IMPORTANT]
> **Key Engineering Distinction**:
> A TLS record larger than 1.5 KB does **not** necessarily result in an IP packet larger than 1.5 KB.
> Standard TCP stacks perform **TCP Segmentation** at the transport layer into multiple Maximum Segment Size (MSS) frames (typically 1,460 bytes).
>
> However, network issues arise when:
> 1. Middleboxes (firewalls, deep packet inspection, load balancers) expect the complete `ClientHello` within a single initial TCP packet and fail to reassemble multi-segment handshakes.
> 2. Path MTU (PMTU) blackholes drop fragmented IP packets or block ICMP Fragmentation Needed messages (Type 3, Code 4).
> 3. Enterprise SSL inspection gateways reject unknown post-quantum named group extensions.

---

## 3. Verification Framework Execution Modes

QuantumShield provides 3 strictly controlled modes:

### Mode 1: Local Simulation (`SIMULATED`)
- Evaluates scenarios deterministically without external network traffic.
- Models standard MTU TCP segmentation, tunnel fragmentation drops, and middlebox reassembly.
- Display label: `SIMULATED — NO REAL NETWORK TEST PERFORMED`.

### Mode 2: Local Loopback (`127.0.0.1`)
- Measures actual local socket connections and TCP stack buffer behavior.
- Does not falsely blame middleboxes when local ports are not listening.

### Mode 3: Authorised Endpoint Verification
- Connects exclusively to allowlisted, authorized endpoints.
- Strict 5.0-second timeout, SSRF protection blocking cloud metadata (`169.254.169.254`), and passive handshake analysis only.

---

## 4. Diagnostic Classifications

- `PASS`: Full handshake completed within timeout parameters.
- `FAIL`: Handshake dropped (fragmentation drop or connection reset).
- `INCONCLUSIVE`: Handshake timed out without definitive evidence attributing failure to a middlebox vs network latency.
- `SIMULATED`: Deterministic simulated scenario.
- `NOT_SUPPORTED`: Port closed or protocol unsupported.

QuantumShield never claims a firewall or middlebox caused a failure without verifiable evidence.
