"""
Remediation Recommendation and Action Priority Generator.
Answers: "What should the security team fix first, and why?"
Generates technically sound, primitive-specific migration guidance.
"""

from typing import Dict, Any, Optional, Tuple


def generate_finding_recommendation(
    algorithm: str,
    primitive: str,
    quantum_vulnerable: bool,
    risk_score: Optional[int] = None,
    risk_category: str = "Needs Assessment",
    sensitivity: Optional[int] = None,
    exposure: Optional[int] = None,
    lifetime: Optional[int] = None,
    detection_category: str = "Confirmed cryptographic API usage",
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate technically appropriate next action, migration approach,
    rationale, and queue priority grouping.
    """
    algo_upper = (algorithm or "").upper()
    prim_lower = (primitive or "").lower()
    
    # Defaults
    recommended_action = "Review cryptographic usage and align with NIST PQC migration timeline."
    migration_approach = "PQC Migration Review"
    why_now = "Requires assessment against organizational cryptography standards."
    required_validation = "Verify target environment and client compatibility."
    queue_group = "needs_assessment"

    # 1. Approved PQC usage (ML-KEM, ML-DSA, SLH-DSA, Kyber, Dilithium)
    if "ML-KEM" in algo_upper or "KYBER" in algo_upper:
        recommended_action = "Maintain active monitoring of FIPS 203 ML-KEM parameter sets and verify library updates."
        migration_approach = "NIST FIPS 203 ML-KEM (Approved Standard)"
        why_now = "PQC key encapsulation already active. Ensure implementation adheres to final FIPS 203 standard."
        required_validation = "Verify interoperability across client TLS implementations."
        queue_group = "monitoring_reassessment"
        return {
            "recommended_action": recommended_action,
            "migration_approach": migration_approach,
            "why_now": why_now,
            "required_validation": required_validation,
            "queue_group": queue_group,
        }

    if "ML-DSA" in algo_upper or "DILITHIUM" in algo_upper or "SLH-DSA" in algo_upper:
        recommended_action = "Maintain active monitoring of FIPS 204/205 signature parameters and certificate chains."
        migration_approach = "NIST FIPS 204 ML-DSA / FIPS 205 SLH-DSA (Approved Standard)"
        why_now = "PQC digital signatures already active. Ensure client trust stores support quantum-safe verification."
        required_validation = "Validate root of trust and CA hierarchy compatibility."
        queue_group = "monitoring_reassessment"
        return {
            "recommended_action": recommended_action,
            "migration_approach": migration_approach,
            "why_now": why_now,
            "required_validation": required_validation,
            "queue_group": queue_group,
        }

    # 2. Legacy / Broken Classical Cryptography (RSA-1024, DES, RC4) - Immediate Priority!
    if "1024" in algo_upper or "DES" in algo_upper or "RC4" in algo_upper or "MD5" in algo_upper:
        if "1024" in algo_upper:
            recommended_action = "Immediately investigate and replace RSA-1024 keys with modern asymmetric algorithms (minimum RSA-3072) or transition directly to ML-DSA/ML-KEM."
            migration_approach = "Immediate Classical Hardening & PQC Migration"
            why_now = "RSA-1024 is vulnerable to classical factorization attacks today, posing immediate pre-quantum security risk."
            required_validation = "Check key generation routines and replace deprecated keypairs."
        elif "DES" in algo_upper or "RC4" in algo_upper:
            recommended_action = "Decommission obsolete cipher (DES/RC4) immediately and replace with AES-256-GCM."
            migration_approach = "Symmetric Cipher Replacement (AES-256-GCM)"
            why_now = "Legacy ciphers have known practical cryptanalytic breaks and fail basic compliance mandates."
            required_validation = "Audit cipher configuration and test decryption compatibility."
        else: # MD5
            recommended_action = "Replace MD5 with SHA-256 or SHA-3 for all integrity and signature operations."
            migration_approach = "Cryptographic Hash Upgrade (SHA-256 / SHA-3)"
            why_now = "MD5 has practical collision attacks that allow attacker certificate or file forging."
            required_validation = "Confirm hash digest consumers support 256-bit digests."

        queue_group = "immediate_investigation"
        return {
            "recommended_action": recommended_action,
            "migration_approach": migration_approach,
            "why_now": why_now,
            "required_validation": required_validation,
            "queue_group": queue_group,
        }

    # 3. SHA-1 - Purpose-specific analysis
    if "SHA-1" in algo_upper or "SHA1" in algo_upper:
        recommended_action = "Identify whether SHA-1 is used for cryptographic signatures vs non-security checksums. If used in signatures/HMAC, replace with SHA-256."
        migration_approach = "Hash Upgrade (SHA-256 / SHA-3)"
        why_now = "SHA-1 is deprecated by NIST; signatures using SHA-1 are susceptible to collision attacks."
        required_validation = "Determine if usage is in digital signatures, certificate chains, or legacy git/checksums."
        queue_group = "scheduled_remediation"
        return {
            "recommended_action": recommended_action,
            "migration_approach": migration_approach,
            "why_now": why_now,
            "required_validation": required_validation,
            "queue_group": queue_group,
        }

    # 4. AES-128 - Nuanced assessment (not automatically critical)
    if "AES-128" in algo_upper:
        recommended_action = "Assess data classification against CNSA 2.0 policy. Retain AES-128 if sufficient or upgrade to AES-256 for maximum post-quantum margin."
        migration_approach = "Symmetric Review (AES-256 Upgrade Optional)"
        why_now = "AES-128 provides 64-bit post-quantum security via Grover's algorithm; adequate for commercial data, but high-assurance requires AES-256."
        required_validation = "Evaluate storage and wire performance impact of 256-bit key size."
        queue_group = "monitoring_reassessment"
        return {
            "recommended_action": recommended_action,
            "migration_approach": migration_approach,
            "why_now": why_now,
            "required_validation": required_validation,
            "queue_group": queue_group,
        }

    # 5. Key Establishment (RSA / ECC / ECDH / X25519) - Store-Now-Decrypt-Later (SNDL) Exposure
    if any(k in prim_lower for k in ["key_establishment", "key_exchange", "asymmetric_encryption"]) or "ECDH" in algo_upper or "X25519" in algo_upper:
        # Check exposure and lifetime
        is_high_exposure = (exposure is not None and exposure >= 4)
        is_long_lifetime = (lifetime is not None and lifetime >= 3)

        if is_high_exposure or is_long_lifetime or risk_category == "Critical":
            recommended_action = "Prioritize compatibility assessment and configure a dual-algorithm hybrid PQC key exchange (e.g. X25519 + ML-KEM-768) in staging."
            migration_approach = "Hybrid PQC Key Exchange (FIPS 203 ML-KEM-768)"
            why_now = "High exposure with long confidentiality lifetime creates immediate Store-Now-Decrypt-Later (SNDL) vulnerability."
            required_validation = "Verify client TLS 1.3 support for draft hybrid key exchange groups."
            queue_group = "high_priority_migration" if risk_category != "Critical" else "immediate_investigation"
        else:
            recommended_action = "Plan transition to hybrid key exchange (X25519 + ML-KEM-768) for key establishment and TLS sessions."
            migration_approach = "Hybrid PQC Key Exchange (FIPS 203 ML-KEM-768)"
            why_now = "Classical asymmetric key agreement will be solvable by Shor's algorithm on CRQC arrival."
            required_validation = "Benchmark handshake latency and packet size impacts."
            queue_group = "scheduled_remediation" if risk_category != "Needs Assessment" else "needs_assessment"

        return {
            "recommended_action": recommended_action,
            "migration_approach": migration_approach,
            "why_now": why_now,
            "required_validation": required_validation,
            "queue_group": queue_group,
        }

    # 6. Digital Signatures (ECDSA / RSA Signatures)
    if any(s in prim_lower for s in ["signature", "digital_signature"]) or "ECDSA" in algo_upper:
        recommended_action = "Assess client trust store compatibility and plan migration to NIST FIPS 204 ML-DSA or FIPS 205 SLH-DSA for digital signatures."
        migration_approach = "Post-Quantum Digital Signatures (FIPS 204 ML-DSA / FIPS 205 SLH-DSA)"
        why_now = "Digital signatures verify authenticity; quantum computers can forge signatures, but cannot retroactively decrypt past traffic."
        required_validation = "Verify certificate size (~2.4 KB) support across middleboxes and legacy TLS clients."
        queue_group = "high_priority_migration" if (exposure and exposure >= 4) else "scheduled_remediation"
        if risk_category == "Needs Assessment":
            queue_group = "needs_assessment"

        return {
            "recommended_action": recommended_action,
            "migration_approach": migration_approach,
            "why_now": why_now,
            "required_validation": required_validation,
            "queue_group": queue_group,
        }

    # 7. Fallback based on risk category
    if risk_category == "Critical":
        queue_group = "immediate_investigation"
        why_now = "Finding carries a Critical risk rating; investigate immediately to mitigate operational exposure."
    elif risk_category == "High":
        queue_group = "high_priority_migration"
        why_now = "High-priority finding; schedule migration planning in the upcoming sprint."
    elif risk_category == "Moderate":
        queue_group = "scheduled_remediation"
        why_now = "Moderate priority; include in regular quarterly cryptographic maintenance."
    elif risk_category == "Low":
        queue_group = "monitoring_reassessment"
        why_now = "Low priority; maintain monitoring during standard review cycles."
    else:
        queue_group = "needs_assessment"
        why_now = "Pending risk assessment inputs to determine remediation priority."

    return {
        "recommended_action": recommended_action,
        "migration_approach": migration_approach,
        "why_now": why_now,
        "required_validation": required_validation,
        "queue_group": queue_group,
    }
