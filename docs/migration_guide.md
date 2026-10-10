# NIST PQC Migration Guide

## Standardized Algorithm Targets

- **FIPS 203 (ML-KEM)**: Module-Lattice-Based Key-Encapsulation Mechanism for asymmetric key establishment and encryption.
- **FIPS 204 (ML-DSA)**: Module-Lattice-Based Digital Signature Algorithm for general digital signature operations.
- **FIPS 205 (SLH-DSA)**: Stateless Hash-Based Digital Signature Algorithm for alternative/backup digital signatures.

## Hybrid Migration Strategy
Organizations should implement hybrid key exchange (e.g., X25519 + ML-KEM-768) during transition periods to maintain classical compliance while providing defense against future quantum decryption.
