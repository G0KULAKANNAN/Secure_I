"""
NIST Post-Quantum Cryptography (PQC) Migration and Remediation Engine.
Maps detected classical cryptographic mechanisms to official NIST PQC standards:
- FIPS 203 (ML-KEM / Kyber) for Key Establishment & Encryption.
- FIPS 204 (ML-DSA / Dilithium) and FIPS 205 (SLH-DSA / SPHINCS+) for Digital Signatures.
Never recommends ML-KEM for digital signatures.
Provides operational testing checklists and non-destructive migration roadmaps.
"""

from typing import Dict, Any, List
from quantumshield.storage.finding_repository import FindingRepository
from quantumshield.storage.repositories import AssetRepository


class MigrationEngine:
    """Generates standard-aligned PQC migration plans and test checklists."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.finding_repo = FindingRepository(db_path)
        self.asset_repo = AssetRepository(db_path)

    def get_asset_plan(self, asset_id: str) -> Dict[str, Any]:
        """Generate tailored PQC migration plan for a single asset."""
        asset = self.asset_repo.get_by_id(asset_id)
        if not asset:
            raise ValueError(f"Asset '{asset_id}' not found.")

        findings, _ = self.finding_repo.list_findings(asset_id=asset_id, limit=200)
        qv_findings = [f for f in findings if f.quantum_vulnerable]

        recommendations: List[Dict[str, Any]] = []

        # 1. Analyze Key Establishment Primitives
        kex_findings = [f for f in qv_findings if f.cryptographic_primitive in ("key_establishment", "asymmetric_encryption")]
        if kex_findings:
            recommendations.append({
                "primitive_category": "Key Establishment & Encapsulation",
                "current_algorithms": list({f.algorithm for f in kex_findings}),
                "target_pqc_standard": "ML-KEM (Kyber)",
                "nist_standard": "FIPS 203",
                "recommended_parameter_set": "ML-KEM-768 (NIST Security Category 3) or ML-KEM-1024",
                "purpose": "General Encryption and Shared Secret Establishment across network sessions and data storage.",
                "compatibility_note": (
                    "FIPS 203 ML-KEM is strictly an encapsulation mechanism. It CANNOT be used for digital signatures or identity certificates. "
                    "Deploy in hybrid mode (e.g. X25519 + ML-KEM-768) during transition."
                ),
                "affected_findings_count": len(kex_findings),
            })

        # 2. Analyze Digital Signature Primitives
        sig_findings = [f for f in qv_findings if f.cryptographic_primitive in ("digital_signature", "authentication")]
        if sig_findings:
            recommendations.append({
                "primitive_category": "Digital Signatures & Authentication",
                "current_algorithms": list({f.algorithm for f in sig_findings}),
                "target_pqc_standard": "ML-DSA (Dilithium) / SLH-DSA (SPHINCS+)",
                "nist_standard": "FIPS 204 (ML-DSA) & FIPS 205 (SLH-DSA)",
                "recommended_parameter_set": "ML-DSA-65 (Primary) or SLH-DSA-128s (Stateless Hash Fallback)",
                "purpose": "Identity authentication, X.509 certificate validation, code signing, and API token signing.",
                "compatibility_note": (
                    "ML-DSA signatures (3.3 KB) and public keys (1.9 KB) are significantly larger than RSA/ECDSA. "
                    "Ensure MTU limits, database certificate storage columns, and handshake buffers accommodate larger payloads. "
                    "Do NOT use ML-KEM as a direct replacement for digital signatures."
                ),
                "affected_findings_count": len(sig_findings),
            })

        # 3. Step-by-Step Migration Phases
        phases = [
            {
                "phase": "Phase 1: Cryptographic Inventory & Bill of Materials (CBOM)",
                "description": "Maintain automated inventory of all public keys, certificates, libraries, and cipher suites.",
                "status": "In Progress" if qv_findings else "Complete",
            },
            {
                "phase": "Phase 2: Hybrid Cryptography in Testing",
                "description": "Enable dual-mode classical + PQC algorithms (e.g. X25519 + ML-KEM-768) in staging without disrupting legacy clients.",
                "status": "Planned",
            },
            {
                "phase": "Phase 3: Buffer & Bandwidth Verification",
                "description": "Test packet fragmentation, TLS handshake latency, and PKI certificate chain storage.",
                "status": "Planned",
            },
            {
                "phase": "Phase 4: Staged Production Rollout",
                "description": "Deploy PQC-enabled endpoints and services with active monitoring and automated rollback capabilities.",
                "status": "Planned",
            },
            {
                "phase": "Phase 5: Classical Decommissioning",
                "description": "Disable legacy RSA and ECC cipher suites once global client ecosystem supports NIST PQC standards.",
                "status": "Planned",
            },
        ]

        # 4. Operational Testing Checklist
        testing_checklist = [
            {"item": "Verify network middleboxes and firewalls do not drop larger TLS ClientHello packets (> 1.5 KB)", "verified": False},
            {"item": "Ensure cryptographic library (OpenSSL 3.3+, BouncyCastle, liboqs) supports FIPS 203/204", "verified": False},
            {"item": "Validate that TLS session resumption and ticket caching function correctly with PQC hybrids", "verified": False},
            {"item": "Benchmark CPU overhead of lattice polynomial multiplication on target server architecture", "verified": False},
            {"item": "Confirm certificate authority (CA) root supports ML-DSA certificate chains", "verified": False},
        ]

        return {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "environment": asset.environment,
            "criticality": asset.criticality,
            "quantum_vulnerable_findings_count": len(qv_findings),
            "recommendations": recommendations,
            "migration_phases": phases,
            "testing_checklist": testing_checklist,
            "safety_policy": "QuantumShield provides defensive guidance and testing specifications. It never modifies production systems or keys automatically.",
        }

    def get_global_summary(self) -> Dict[str, Any]:
        """Aggregate migration targets across all assets."""
        assets, _ = self.asset_repo.list_assets(limit=500)
        total_assets = len(assets)
        vulnerable_assets = 0
        ml_kem_candidates = 0
        ml_dsa_candidates = 0

        for a in assets:
            findings, _ = self.finding_repo.list_findings(asset_id=a.id, limit=100)
            qv = [f for f in findings if f.quantum_vulnerable]
            if qv:
                vulnerable_assets += 1
            if any(f.cryptographic_primitive in ("key_establishment", "asymmetric_encryption") for f in qv):
                ml_kem_candidates += 1
            if any(f.cryptographic_primitive in ("digital_signature", "authentication") for f in qv):
                ml_dsa_candidates += 1

        return {
            "total_assets": total_assets,
            "vulnerable_assets": vulnerable_assets,
            "ml_kem_target_assets": ml_kem_candidates,
            "ml_dsa_target_assets": ml_dsa_candidates,
            "fips_standards": [
                {"name": "FIPS 203", "title": "ML-KEM (Module-Lattice Key Encapsulation)", "status": "Final NIST Standard (Aug 2024)"},
                {"name": "FIPS 204", "title": "ML-DSA (Module-Lattice Digital Signatures)", "status": "Final NIST Standard (Aug 2024)"},
                {"name": "FIPS 205", "title": "SLH-DSA (Stateless Hash-Based Signatures)", "status": "Final NIST Standard (Aug 2024)"},
            ],
        }
