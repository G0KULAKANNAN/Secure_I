# QuantumShield Risk Model & Scoring Specification

## Mathematical Formula

Priority Score \( R \) is determined deterministically on a scale of 20 to 100:

$$R = 20 \times (0.35C + 0.30S + 0.25L + 0.10E)$$

Where:
- **C** (Cryptographic Exposure, 1–5): Vulnerability of the detected algorithm to quantum algorithms (e.g. Shor's algorithm breaking RSA/ECC vs Grover's quadratic impact on AES).
- **S** (Data Sensitivity, 1–5): Criticality of protected information (e.g., public data = 1, master secrets / financial records = 5).
- **L** (Confidentiality Lifetime, 1–5): Required secrecy duration (e.g., ephemeral = 1, >10 years = 5).
- **E** (Internet Exposure, 1–5): Network accessibility (internal air-gapped = 1, public internet facing = 5).

## Disclaimer
The priority score reflects relative urgency for migration planning and does **not** predict quantum computer breakthrough timelines or indicate confirmed system compromise.
