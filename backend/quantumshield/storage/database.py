"""
SQLite Database Storage Layer for QuantumShield.
Handles connection management, parameterised execution, and schema initialisation.
"""

import sqlite3
from pathlib import Path
from typing import Union


def get_db_connection(db_path: Union[str, Path]) -> sqlite3.Connection:
    """
    Open an SQLite connection with row mapping and foreign keys enabled.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Union[str, Path]) -> None:
    """
    Initialise or migrate the SQLite database schema safely.
    Creates tables and indexes IF NOT EXISTS without dropping existing data.
    """
    conn = get_db_connection(db_path)
    with conn:
        # Assets Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                environment TEXT NOT NULL,
                hostname TEXT,
                ip_address TEXT,
                owner TEXT,
                description TEXT,
                criticality TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT chk_asset_type CHECK (
                    asset_type IN ('server', 'website', 'application', 'certificate', 'database', 'other')
                ),
                CONSTRAINT chk_environment CHECK (
                    environment IN ('development', 'testing', 'staging', 'production')
                ),
                CONSTRAINT chk_criticality CHECK (
                    criticality IN ('low', 'medium', 'high', 'critical')
                ),
                CONSTRAINT chk_status CHECK (
                    status IN ('active', 'inactive', 'under_review')
                )
            );
        """)

        # Indexes for assets
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_name ON assets (name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets (hostname);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_type ON assets (asset_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_environment ON assets (environment);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_criticality ON assets (criticality);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_status ON assets (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_updated_at ON assets (updated_at);")

        # Scan Jobs Table (Automation & Background Processing)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                asset_id TEXT,
                operation TEXT NOT NULL DEFAULT 'execute',
                status TEXT NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 5,
                payload_json TEXT,
                result_json TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                updated_at TEXT NOT NULL,
                next_retry_at TEXT,
                error_code TEXT,
                error_message TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                CONSTRAINT chk_job_status CHECK (
                    status IN ('pending', 'queued', 'running', 'completed', 'partially_completed', 'failed', 'cancel_requested', 'cancelled')
                )
            );
        """)

        # Perform seamless migration if scan_jobs was created in an older schema
        _migrate_scan_jobs_table(conn)

        # Indexes for jobs
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_asset_id ON scan_jobs (asset_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_status ON scan_jobs (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_created_at ON scan_jobs (created_at);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_job_type ON scan_jobs (job_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_priority ON scan_jobs (priority);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_jobs_next_retry ON scan_jobs (next_retry_at);")

        # Scan Runs Table (Scan Orchestration)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_runs (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                requested_scanners TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                total_jobs INTEGER NOT NULL DEFAULT 0,
                completed_jobs INTEGER NOT NULL DEFAULT 0,
                failed_jobs INTEGER NOT NULL DEFAULT 0,
                cancelled_jobs INTEGER NOT NULL DEFAULT 0,
                result_summary TEXT,
                error_summary TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                CONSTRAINT chk_scan_run_status CHECK (
                    status IN ('queued', 'running', 'completed', 'partially_completed', 'failed', 'cancelled')
                )
            );
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_asset_id ON scan_runs (asset_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_status ON scan_runs (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scan_runs_created_at ON scan_runs (created_at);")

        # Unified Findings Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                scan_run_id TEXT,
                job_id TEXT,
                scanner_type TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                cryptographic_primitive TEXT NOT NULL DEFAULT 'key_establishment',
                quantum_vulnerable INTEGER NOT NULL DEFAULT 1,
                recommended_pqc TEXT NOT NULL DEFAULT 'ML-KEM-768',
                rule_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'high',
                evidence TEXT NOT NULL,
                file_path TEXT,
                line_number INTEGER,
                confidence TEXT NOT NULL DEFAULT 'high',
                remediation_status TEXT NOT NULL DEFAULT 'potential_exposure',
                fingerprint TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id) ON DELETE SET NULL,
                CONSTRAINT chk_finding_severity CHECK (
                    severity IN ('info', 'low', 'medium', 'high', 'critical')
                ),
                CONSTRAINT chk_finding_remediation CHECK (
                    remediation_status IN ('potential_exposure', 'verified_usage', 'needs_review', 'remediated', 'accepted_risk')
                )
            );
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_asset_id ON findings (asset_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings (severity);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_fingerprint ON findings (fingerprint);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_scanner_type ON findings (scanner_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_findings_scan_run_id ON findings (scan_run_id);")

        # -------------------------------------------------------------
        # Stage 2: Audit Trail & Hybrid Cryptography in Staging Tables
        # -------------------------------------------------------------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                operator TEXT NOT NULL DEFAULT 'local_operator',
                details_json TEXT,
                timestamp TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events (entity_type, entity_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events (timestamp);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crypto_capabilities (
                id TEXT PRIMARY KEY,
                classical_group TEXT NOT NULL,
                pqc_algorithm TEXT NOT NULL,
                hybrid_combination TEXT NOT NULL UNIQUE,
                standard_reference TEXT NOT NULL,
                implementation_provider TEXT NOT NULL,
                library_version TEXT NOT NULL,
                client_compatibility TEXT NOT NULL,
                server_compatibility TEXT NOT NULL,
                staging_test_status TEXT NOT NULL DEFAULT 'untested',
                negotiation_status TEXT NOT NULL DEFAULT 'untested',
                failure_reason TEXT,
                security_notes TEXT,
                last_verified_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_caps_hybrid ON crypto_capabilities (hybrid_combination);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS hybrid_profiles (
                id TEXT PRIMARY KEY,
                profile_name TEXT NOT NULL UNIQUE,
                classical_component TEXT NOT NULL,
                pqc_component TEXT NOT NULL,
                environment TEXT NOT NULL DEFAULT 'staging',
                rollout_status TEXT NOT NULL DEFAULT 'disabled',
                migration_state TEXT NOT NULL DEFAULT 'PLANNED',
                automatic_production_prohibited INTEGER NOT NULL DEFAULT 1,
                previous_config_json TEXT,
                proposed_config_json TEXT,
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT chk_hybrid_state CHECK (
                    migration_state IN ('PLANNED', 'CONFIGURED', 'TESTING', 'VERIFIED', 'FAILED', 'APPROVED')
                )
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hybrid_profiles_env ON hybrid_profiles (environment);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hybrid_profiles_state ON hybrid_profiles (migration_state);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS hybrid_verification_runs (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                test_mode TEXT NOT NULL DEFAULT 'simulation',
                status TEXT NOT NULL,
                negotiation_outcome TEXT NOT NULL,
                classical_client_compatible INTEGER NOT NULL DEFAULT 1,
                hybrid_client_compatible INTEGER NOT NULL DEFAULT 0,
                observed_tls_version TEXT,
                negotiated_group TEXT,
                error_details TEXT,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                is_simulated INTEGER NOT NULL DEFAULT 1,
                operator TEXT NOT NULL DEFAULT 'local_operator',
                created_at TEXT NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES hybrid_profiles(id) ON DELETE CASCADE
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hybrid_runs_profile ON hybrid_verification_runs (profile_id);")

        # -------------------------------------------------------------
        # Stage 3: Network MTU & Middlebox Verification Tables
        # -------------------------------------------------------------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS network_verification_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                target_host TEXT NOT NULL DEFAULT '127.0.0.1',
                target_port INTEGER NOT NULL DEFAULT 443,
                environment TEXT NOT NULL DEFAULT 'local_lab',
                test_profile TEXT NOT NULL DEFAULT 'standard_mtu',
                test_mode TEXT NOT NULL DEFAULT 'simulation',
                expected_mtu INTEGER NOT NULL DEFAULT 1500,
                connection_timeout REAL NOT NULL DEFAULT 5.0,
                handshake_timeout REAL NOT NULL DEFAULT 5.0,
                max_retries INTEGER NOT NULL DEFAULT 2,
                is_allowlisted INTEGER NOT NULL DEFAULT 0,
                authorized_by_operator INTEGER NOT NULL DEFAULT 0,
                operator_notes TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_net_profiles_env ON network_verification_profiles (environment);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS network_verification_results (
                id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                job_id TEXT,
                test_mode TEXT NOT NULL,
                target_endpoint TEXT NOT NULL,
                address_family TEXT NOT NULL DEFAULT 'IPv4',
                configured_mtu INTEGER,
                tls_version TEXT,
                negotiated_group TEXT,
                handshake_success INTEGER NOT NULL DEFAULT 1,
                diagnostic_classification TEXT NOT NULL,
                diagnostic_finding TEXT NOT NULL,
                observed_error TEXT,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                packet_size_estimate_bytes INTEGER,
                evidence_level TEXT NOT NULL DEFAULT 'connection_level',
                evidence_details_json TEXT,
                remediation_recommendations_json TEXT,
                confidence TEXT NOT NULL DEFAULT 'high',
                created_at TEXT NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES network_verification_profiles(id) ON DELETE CASCADE
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_net_results_profile ON network_verification_results (profile_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_net_results_class ON network_verification_results (diagnostic_classification);")

        # -------------------------------------------------------------
        # Stage 4: Staged Production Rollout Management Tables
        # -------------------------------------------------------------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deployment_environments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                managed_service TEXT NOT NULL,
                owner TEXT NOT NULL,
                current_config_json TEXT NOT NULL,
                desired_config_json TEXT NOT NULL,
                supported_tls_version TEXT NOT NULL DEFAULT 'TLS 1.3',
                supported_groups_json TEXT NOT NULL,
                client_compatibility_reqs TEXT,
                readiness_status TEXT NOT NULL DEFAULT 'not_ready',
                rollout_status TEXT NOT NULL DEFAULT 'idle',
                rollback_config_ref TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT chk_env_category CHECK (
                    category IN ('development', 'local_lab', 'staging', 'production')
                )
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_deploy_env_cat ON deployment_environments (category);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS rollout_plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                environment_id TEXT NOT NULL,
                current_stage TEXT NOT NULL DEFAULT 'DRAFT',
                state TEXT NOT NULL DEFAULT 'DRAFT',
                canary_percentage INTEGER NOT NULL DEFAULT 5,
                previous_config_json TEXT,
                target_config_json TEXT NOT NULL,
                readiness_assessment_json TEXT,
                rollback_threshold_failure_rate REAL NOT NULL DEFAULT 2.0,
                approved_by TEXT,
                approved_at TEXT,
                last_advanced_at TEXT,
                deployment_mode TEXT NOT NULL DEFAULT 'simulation',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (environment_id) REFERENCES deployment_environments(id) ON DELETE CASCADE,
                CONSTRAINT chk_rollout_state CHECK (
                    state IN ('DRAFT', 'VALIDATING', 'READY_FOR_APPROVAL', 'APPROVED', 'CANARY', 'MONITORING', 'COMPLETED', 'BLOCKED', 'FAILED', 'ROLLBACK_PENDING', 'ROLLED_BACK', 'CANCELLED')
                )
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rollout_plans_state ON rollout_plans (state);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rollout_plans_env ON rollout_plans (environment_id);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_events (
                id TEXT PRIMARY KEY,
                rollout_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                handshake_success_rate REAL NOT NULL DEFAULT 100.0,
                handshake_failure_rate REAL NOT NULL DEFAULT 0.0,
                average_latency_ms REAL NOT NULL DEFAULT 15.0,
                timeout_rate REAL NOT NULL DEFAULT 0.0,
                negotiated_tls_version TEXT DEFAULT 'TLS 1.3',
                negotiated_group TEXT DEFAULT 'X25519MLKEM768',
                error_categories_json TEXT,
                is_simulated INTEGER NOT NULL DEFAULT 1,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (rollout_id) REFERENCES rollout_plans(id) ON DELETE CASCADE
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_rollout ON telemetry_events (rollout_id);")

        # -------------------------------------------------------------
        # Stage 5: Classical Cryptography Decommissioning Tables
        # -------------------------------------------------------------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decommissioning_policies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                algorithm TEXT NOT NULL,
                primitive_category TEXT NOT NULL,
                status TEXT NOT NULL,
                conditions TEXT,
                enforcement_deadline TEXT,
                rationale TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT chk_policy_status CHECK (
                    status IN ('APPROVED', 'APPROVED_WITH_CONDITIONS', 'MIGRATION_REQUIRED', 'DEPRECATED', 'PROHIBITED_BY_CONFIGURED_POLICY', 'NEEDS_REVIEW')
                )
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_decom_pol_alg ON decommissioning_policies (algorithm);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_decom_pol_stat ON decommissioning_policies (status);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crypto_dependencies (
                id TEXT PRIMARY KEY,
                asset_id TEXT,
                service_name TEXT NOT NULL,
                primitive_category TEXT NOT NULL,
                current_algorithm TEXT NOT NULL,
                target_algorithm TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                policy_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE SET NULL,
                FOREIGN KEY (policy_id) REFERENCES decommissioning_policies(id) ON DELETE SET NULL,
                CONSTRAINT chk_dep_status CHECK (
                    status IN ('active', 'migrating', 'decommissioned', 'blocked')
                )
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crypto_dep_srv ON crypto_dependencies (service_name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crypto_dep_stat ON crypto_dependencies (status);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS decommissioning_plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                target_primitive TEXT NOT NULL,
                affected_services_json TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'DISCOVERED',
                readiness_assessment_json TEXT,
                approved_by TEXT,
                approved_at TEXT,
                decommissioned_at TEXT,
                rollback_instructions TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CONSTRAINT chk_decom_plan_state CHECK (
                    state IN ('DISCOVERED', 'MIGRATION_VERIFIED', 'READY_FOR_REVIEW', 'APPROVED', 'DECOMMISSIONING_PLANNED', 'COMPLETED', 'BLOCKED', 'ROLLED_BACK')
                )
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_decom_plan_state ON decommissioning_plans (state);")

        # Seed default environments for Stage 4
        _seed_default_environments(conn)

        # Seed default crypto capabilities if empty
        _seed_default_capabilities(conn)

        # Seed default decommissioning policies for Stage 5
        _seed_default_decommissioning_policies(conn)

    conn.close()


def _seed_default_environments(conn: sqlite3.Connection) -> None:
    """Seed default deployment environments for Stage 4."""
    cursor = conn.execute("SELECT COUNT(*) as count FROM deployment_environments;")
    if cursor.fetchone()["count"] == 0:
        import datetime
        import json
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        seeds = [
            (
                "env_dev",
                "Internal Development Cluster",
                "development",
                "Kube-Ingress-Dev",
                "devops-team@company.internal",
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519MLKEM768", "X25519"]}),
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519MLKEM768", "X25519"]}),
                "TLS 1.3",
                json.dumps(["X25519MLKEM768", "X25519"]),
                "Developer workstations, internal CI/CD runners",
                "ready",
                "completed",
                None,
                now,
                now,
            ),
            (
                "env_local_lab",
                "Local Cryptographic Testbed",
                "local_lab",
                "Envoy-Local",
                "secops-research@company.internal",
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519MLKEM768", "SecP256r1MLKEM768", "X25519"]}),
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519MLKEM768", "SecP256r1MLKEM768", "X25519"]}),
                "TLS 1.3",
                json.dumps(["X25519MLKEM768", "SecP256r1MLKEM768", "X25519"]),
                "Local test harnesses, integration runners",
                "ready",
                "completed",
                None,
                now,
                now,
            ),
            (
                "env_staging",
                "Staging Gateway",
                "staging",
                "Edge-Proxy-Staging",
                "cloud-infra@company.internal",
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519MLKEM768", "X25519"]}),
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519MLKEM768", "X25519"]}),
                "TLS 1.3",
                json.dumps(["X25519MLKEM768", "X25519"]),
                "Chrome 124+, Firefox 128+, internal microservices",
                "ready",
                "ready",
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519"]}),
                now,
                now,
            ),
            (
                "env_production",
                "Primary Edge API Gateway",
                "production",
                "Cloudflare / Envoy Hybrid",
                "sre-core@company.internal",
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519"]}),
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519MLKEM768", "X25519"]}),
                "TLS 1.3",
                json.dumps(["X25519"]),
                "Global external clients, mobile SDKs, partner APIs",
                "ready_for_canary",
                "idle",
                json.dumps({"tls_version": "TLS 1.3", "supported_groups": ["X25519"]}),
                now,
                now,
            ),
        ]
        conn.executemany("""
            INSERT INTO deployment_environments (
                id, name, category, managed_service, owner, current_config_json,
                desired_config_json, supported_tls_version, supported_groups_json,
                client_compatibility_reqs, readiness_status, rollout_status,
                rollback_config_ref, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, seeds)


def _seed_default_capabilities(conn: sqlite3.Connection) -> None:
    """Seed standard hybrid and classical capabilities for Stage 2."""
    cursor = conn.execute("SELECT COUNT(*) as count FROM crypto_capabilities;")
    if cursor.fetchone()["count"] == 0:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        seeds = [
            (
                "cap_x25519_mlkem768",
                "X25519",
                "ML-KEM-768",
                "X25519MLKEM768",
                "Draft IETF / NIST FIPS 203 (Security Cat 3)",
                "OpenSSL 3.x / liboqs / AWS-LC",
                "liboqs-0.10.0+ / oqsprovider",
                "Modern browsers (Chrome 124+, Firefox Nightly) and PQC-enabled clients",
                "TLS 1.3 servers with post-quantum key exchange extension",
                "ready_for_staging",
                "supported_by_lib",
                None,
                "Recommended hybrid standard for general TLS 1.3 key encapsulation.",
                None,
                now,
                now,
            ),
            (
                "cap_secp256r1_mlkem768",
                "NIST P-256",
                "ML-KEM-768",
                "SecP256r1MLKEM768",
                "Draft IETF / NIST FIPS 203",
                "OpenSSL 3.x / liboqs",
                "liboqs-0.10.0+",
                "Suite B and government hybrid transition clients",
                "TLS 1.3 servers with FIPS hybrid curves",
                "ready_for_staging",
                "supported_by_lib",
                None,
                "Hybrid combination compliant with NIST P-256 legacy policy mandates.",
                None,
                now,
                now,
            ),
            (
                "cap_x25519_mlkem1024",
                "X25519",
                "ML-KEM-1024",
                "X25519MLKEM1024",
                "Draft IETF / NIST FIPS 203 (Security Cat 5)",
                "OpenSSL 3.x / liboqs",
                "liboqs-0.10.0+",
                "High-security specialized clients",
                "High-assurance TLS 1.3 endpoints",
                "planned",
                "supported_by_lib",
                None,
                "Highest security category hybrid parameter set for high-value targets.",
                None,
                now,
                now,
            ),
        ]
        conn.executemany("""
            INSERT INTO crypto_capabilities (
                id, classical_group, pqc_algorithm, hybrid_combination, standard_reference,
                implementation_provider, library_version, client_compatibility, server_compatibility,
                staging_test_status, negotiation_status, failure_reason, security_notes,
                last_verified_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, seeds)


def _seed_default_decommissioning_policies(conn: sqlite3.Connection) -> None:
    """Seed standard decommissioning policies for Stage 5."""
    cursor = conn.execute("SELECT COUNT(*) as count FROM decommissioning_policies;")
    if cursor.fetchone()["count"] == 0:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        seeds = [
            (
                "pol_rsa_1024",
                "RSA-1024 Key Exchange Prohibition",
                "RSA-1024",
                "key_exchange",
                "PROHIBITED_BY_CONFIGURED_POLICY",
                "Immediate revocation. Factoring feasible with classical hardware.",
                "2024-01-01T00:00:00Z",
                "NIST SP 800-131A Rev 2 disallows RSA < 2048. Factoring vulnerabilities present.",
                now,
                now,
            ),
            (
                "pol_rsa_2048",
                "RSA-2048 Key Exchange Migration Mandate",
                "RSA-2048",
                "key_exchange",
                "MIGRATION_REQUIRED",
                "Phase out for TLS 1.3 hybrid key exchange by deadline.",
                "2030-12-31T23:59:59Z",
                "Vulnerable to Shor's algorithm on Cryptanalytically Relevant Quantum Computer (CRQC).",
                now,
                now,
            ),
            (
                "pol_dh_classical",
                "Finite Field Diffie-Hellman Deprecation",
                "Diffie-Hellman",
                "key_exchange",
                "DEPRECATED",
                "Allow only in legacy read/decrypt mode, no new handshakes permitted.",
                "2026-06-30T00:00:00Z",
                "Vulnerable to quantum discrete logarithm attacks; lack of perfect forward secrecy when misconfigured.",
                now,
                now,
            ),
            (
                "pol_ecdsa_p256",
                "ECDSA P-256 Digital Signature Transition",
                "ECDSA-P256",
                "digital_signature",
                "MIGRATION_REQUIRED",
                "Dual-stack signatures with ML-DSA-65 (FIPS 204) where supported.",
                "2033-12-31T23:59:59Z",
                "Elliptic curve discrete logarithm solvable in polynomial time by quantum adversary.",
                now,
                now,
            ),
            (
                "pol_sha1",
                "SHA-1 Hash Function Complete Prohibition",
                "SHA-1",
                "hashing",
                "PROHIBITED_BY_CONFIGURED_POLICY",
                "Zero tolerance across all certificates and checksums.",
                "2020-01-01T00:00:00Z",
                "Collision attacks demonstrated. Disallowed by all modern TLS trust stores.",
                now,
                now,
            ),
            (
                "pol_3des",
                "Triple DES (3DES) Symmetric Cipher Prohibition",
                "3DES",
                "symmetric_encryption",
                "PROHIBITED_BY_CONFIGURED_POLICY",
                "Immediate removal from cipher suites.",
                "2023-12-31T00:00:00Z",
                "Sweet32 collision attack vulnerability due to 64-bit block size. NIST deprecated.",
                now,
                now,
            ),
            (
                "pol_aes_128",
                "AES-128 Symmetric Encryption Conditional Use",
                "AES-128",
                "symmetric_encryption",
                "APPROVED_WITH_CONDITIONS",
                "Permitted for short-lived sessions; recommend AES-256 for long-term data at rest (Grover's algorithm resistance).",
                "2035-12-31T23:59:59Z",
                "Grover's algorithm halves effective symmetric key length to 64 bits. AES-256 recommended.",
                now,
                now,
            ),
            (
                "pol_aes_256",
                "AES-256 Symmetric Encryption Approved",
                "AES-256",
                "symmetric_encryption",
                "APPROVED",
                "Fully quantum-resistant symmetric cipher (128-bit quantum security strength).",
                None,
                "Retains 128 bits of security against Grover's algorithm quantum search.",
                now,
                now,
            ),
            (
                "pol_hybrid_mlkem768",
                "X25519MLKEM768 Hybrid Key Exchange Approved",
                "X25519MLKEM768",
                "key_exchange",
                "APPROVED",
                "Recommended standard for TLS 1.3 dual-layer post-quantum defense.",
                None,
                "Combines classical ECDH X25519 with lattice-based ML-KEM-768 (FIPS 203).",
                now,
                now,
            ),
            (
                "pol_mldsa_65",
                "ML-DSA-65 Post-Quantum Signature Approved",
                "ML-DSA-65",
                "digital_signature",
                "APPROVED",
                "Primary standard for quantum-safe digital signatures (FIPS 204).",
                None,
                "Lattice-based digital signature standard offering Category 3 quantum hardness.",
                now,
                now,
            ),
        ]
        conn.executemany("""
            INSERT INTO decommissioning_policies (
                id, name, algorithm, primitive_category, status,
                conditions, enforcement_deadline, rationale, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, seeds)


def _migrate_scan_jobs_table(conn: sqlite3.Connection) -> None:
    """
    Ensure scan_jobs has all required Milestone 1 columns and nullable asset_id.
    """
    cursor = conn.execute("PRAGMA table_info(scan_jobs);")
    columns = {row["name"]: dict(row) for row in cursor.fetchall()}

    # If table is newly created or empty with proper schema, check missing columns
    needed_columns = {
        "priority": "INTEGER NOT NULL DEFAULT 5",
        "payload_json": "TEXT",
        "result_json": "TEXT",
        "attempt_count": "INTEGER NOT NULL DEFAULT 0",
        "max_attempts": "INTEGER NOT NULL DEFAULT 3",
        "finished_at": "TEXT",
        "updated_at": "TEXT",
        "next_retry_at": "TEXT",
        "error_code": "TEXT",
        "scan_run_id": "TEXT",
    }

    for col_name, col_type in needed_columns.items():
        if col_name not in columns:
            conn.execute(f"ALTER TABLE scan_jobs ADD COLUMN {col_name} {col_type};")

    # If asset_id has NOT NULL constraint or status check constraint needs upgrading, migrate table safely
    asset_id_col = columns.get("asset_id", {})
    if asset_id_col.get("notnull") == 1:
        # Recreate table with nullable asset_id
        conn.execute("""
            CREATE TABLE scan_jobs_migration (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                asset_id TEXT,
                operation TEXT NOT NULL DEFAULT 'execute',
                status TEXT NOT NULL DEFAULT 'pending',
                priority INTEGER NOT NULL DEFAULT 5,
                payload_json TEXT,
                result_json TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                updated_at TEXT NOT NULL,
                next_retry_at TEXT,
                error_code TEXT,
                error_message TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                CONSTRAINT chk_job_status CHECK (
                    status IN ('pending', 'queued', 'running', 'completed', 'partially_completed', 'failed', 'cancel_requested', 'cancelled')
                )
            );
        """)

        # Copy data
        conn.execute("""
            INSERT INTO scan_jobs_migration (
                id, job_type, asset_id, operation, status, priority,
                progress, attempt_count, max_attempts, created_at, started_at,
                finished_at, updated_at, error_message, result_json
            )
            SELECT
                id, job_type, asset_id, operation, status,
                COALESCE(priority, 5), progress,
                COALESCE(retry_count, 0), COALESCE(max_retries, 3),
                created_at, started_at, completed_at,
                COALESCE(created_at, datetime('now')),
                error_message, result_data
            FROM scan_jobs;
        """)

        conn.execute("DROP TABLE scan_jobs;")
        conn.execute("ALTER TABLE scan_jobs_migration RENAME TO scan_jobs;")

    # Sync any updated_at that might be NULL
    conn.execute("UPDATE scan_jobs SET updated_at = created_at WHERE updated_at IS NULL;")
