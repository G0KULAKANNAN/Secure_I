# QuantumShield Architecture Specification

## Overview

QuantumShield is a decoupled cybersecurity web application designed to identify cryptographic assets vulnerable to quantum attacks (Harvest Now, Decrypt Later) and prioritize Post-Quantum Cryptography (PQC) migration.

## Architectural Layers

1. **Presentation Layer (`frontend/`)**: React 18, TypeScript, Vite, Tailwind CSS with a deep midnight navy design system.
2. **API Layer (`backend/quantumshield/api/`)**: Versioned Flask REST API (`/api/v1/`).
3. **Core Services (`backend/quantumshield/services/`)**: Business logic orchestration.
4. **Scanners (`backend/quantumshield/scanner/`)**: X.509 certificate parser, static AST/regex source scanner, and TLS handshake inspector.
5. **Risk Engine (`backend/quantumshield/risk/`)**: Explainable scoring model with formula `R = 20 * (0.35C + 0.30S + 0.25L + 0.10E)`.
6. **PQC Engine (`backend/quantumshield/migration/`)**: NIST FIPS 203/204/205 mapping and dependency planner.
7. **Storage Layer (`backend/quantumshield/storage/`)**: Local SQLite persistence with parameterized SQL.
