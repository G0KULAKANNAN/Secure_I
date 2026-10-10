"""
Automatic System File Scanner.
Recursively inspects authorized project and system files for cryptographic usage,
weak configurations, certificates, and API patterns with safety bounds,
secret redaction, streaming reads, and live telemetry tracking.
"""

from pathlib import Path
import os
import re
import logging
from typing import Optional, Dict, Any, List, Set, Callable
from quantumshield.models.asset import Asset
from quantumshield.models.finding import compute_finding_fingerprint
from quantumshield.scanner.base import BaseScanner, ScanResult
from quantumshield.scanner.rules import (
    CRYPTO_RULES,
    CONFIG_RULES,
    classify_line_detection,
    redact_secrets,
    CAT_CONFIRMED_API,
    CAT_CONFIG_EVIDENCE,
    CAT_CERT_EVIDENCE,
    CAT_TEXTUAL_REF,
    CAT_MANUAL_VALIDATION,
)
from quantumshield.risk.engine import calculate_finding_risk_score
from quantumshield.risk.recommendations import generate_finding_recommendation

logger = logging.getLogger("quantumshield.scanner.system_file")

# Default Safety Bounds
DEFAULT_MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_MAX_FILES_TO_SCAN = 1500

DEFAULT_EXCLUDED_DIRS: Set[str] = {
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "target",
    "vendor",
    ".pytest_cache",
    ".gemini",
    "coverage",
    ".next",
    ".nuxt",
}

DEFAULT_SUPPORTED_EXTENSIONS: Set[str] = {
    # Source Code
    ".py", ".java", ".js", ".jsx", ".ts", ".tsx",
    ".c", ".h", ".cpp", ".hpp", ".go", ".cs", ".php", ".rb",
    # Configurations
    ".conf", ".cfg", ".ini", ".yaml", ".yml", ".json", ".toml", ".xml", ".properties",
    # Certificates & Key metadata
    ".pem", ".crt", ".cer", ".der", ".p7b",
}


class SystemFileScanner(BaseScanner):
    """Real filesystem scanner with safety guards and multi-tier cryptographic classification."""

    @property
    def scanner_type(self) -> str:
        return "system_scan"

    def scan(
        self,
        asset: Asset,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> ScanResult:
        """
        Execute real recursive scan on configured, authorized scope.
        """
        options = options or {}
        payload = options.get("payload", {}) if "payload" in options else options

        # Determine scan root(s)
        target_dir_str = payload.get("target_directory") or payload.get("directory")
        if not target_dir_str:
            # Default to current project root: e:\Secure_I or directory containing backend
            current_file_dir = Path(__file__).resolve().parent
            project_root = current_file_dir.parent.parent.parent  # e:\Secure_I
            target_dirs = [project_root]
        elif isinstance(target_dir_str, list):
            target_dirs = [Path(d).resolve() for d in target_dir_str]
        else:
            target_dirs = [Path(target_dir_str).resolve()]

        max_file_size = int(payload.get("max_file_size_bytes") or DEFAULT_MAX_FILE_SIZE_BYTES)
        max_files = int(payload.get("max_files") or DEFAULT_MAX_FILES_TO_SCAN)
        
        custom_extensions = payload.get("include_extensions")
        if custom_extensions and isinstance(custom_extensions, list):
            allowed_exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in custom_extensions}
        else:
            allowed_exts = DEFAULT_SUPPORTED_EXTENSIONS

        custom_excludes = payload.get("exclude_directories")
        if custom_excludes and isinstance(custom_excludes, list):
            excluded_dirs = set(custom_excludes) | {".git", "node_modules", "__pycache__"}
        else:
            excluded_dirs = DEFAULT_EXCLUDED_DIRS

        findings: List[Dict[str, Any]] = []
        files_discovered = 0
        files_scanned = 0
        files_skipped = 0
        files_errored = 0
        skipped_details: List[Dict[str, str]] = []
        error_details: List[Dict[str, str]] = []

        # Derive initial risk context from asset if available (without inventing business context)
        asset_sensitivity = None
        asset_exposure = None
        asset_lifetime = None
        if asset.criticality:
            crit_map = {"critical": 5, "high": 4, "medium": 3, "low": 1}
            asset_sensitivity = crit_map.get(asset.criticality.lower())
        if asset.environment:
            env_map = {"production": 5, "staging": 3, "testing": 2, "development": 1}
            asset_lifetime = env_map.get(asset.environment.lower())
            asset_exposure = 4 if asset.environment.lower() == "production" else 2

        for root_dir in target_dirs:
            if not root_dir.exists() or not root_dir.is_dir():
                error_details.append({"path": str(root_dir), "reason": "Directory does not exist or is not a directory."})
                files_errored += 1
                continue

            for dirpath, dirnames, filenames in os.walk(str(root_dir), followlinks=False):
                # Cooperative cancellation check
                if is_cancelled and is_cancelled():
                    logger.info("System file scan cancelled by operator.")
                    return ScanResult(
                        scanner_type=self.scanner_type,
                        asset_id=asset.id,
                        status="cancelled",
                        findings=findings,
                        metadata={
                            "files_discovered": files_discovered,
                            "files_scanned": files_scanned,
                            "files_skipped": files_skipped,
                            "files_errored": files_errored,
                            "cancelled": True,
                        },
                    )

                # Prune excluded directories in-place
                dirnames[:] = [d for d in dirnames if d not in excluded_dirs and not d.startswith(".")]

                current_p = Path(dirpath)

                for fname in filenames:
                    files_discovered += 1
                    file_p = current_p / fname
                    ext = file_p.suffix.lower()

                    # 1. Extension filter
                    if ext not in allowed_exts:
                        files_skipped += 1
                        continue

                    # 2. File size and accessibility filter
                    try:
                        stat = file_p.stat()
                        if stat.st_size > max_file_size:
                            files_skipped += 1
                            skipped_details.append({"path": str(file_p), "reason": f"File size ({stat.st_size} bytes) exceeds limit ({max_file_size} bytes)."})
                            continue
                        if stat.st_size == 0:
                            files_skipped += 1
                            continue
                    except (OSError, PermissionError) as exc:
                        files_errored += 1
                        error_details.append({"path": str(file_p), "reason": f"Permission or OS error: {exc}"})
                        continue

                    if files_scanned >= max_files:
                        break

                    # 3. Inspect single file
                    try:
                        rel_path = str(file_p.relative_to(root_dir))
                    except ValueError:
                        rel_path = file_p.name

                    try:
                        file_findings = self._inspect_file(
                            file_p=file_p,
                            rel_path=rel_path,
                            asset_id=asset.id,
                            sensitivity=asset_sensitivity,
                            exposure=asset_exposure,
                            lifetime=asset_lifetime,
                        )
                        findings.extend(file_findings)
                        files_scanned += 1
                    except Exception as exc:
                        files_errored += 1
                        error_details.append({"path": str(file_p), "reason": f"Scan error: {exc}"})

                    # Progress update callback
                    if progress_callback and files_scanned % 20 == 0:
                        progress_callback({
                            "files_discovered": files_discovered,
                            "files_scanned": files_scanned,
                            "files_skipped": files_skipped,
                            "files_errored": files_errored,
                            "findings_count": len(findings),
                        })

                if files_scanned >= max_files:
                    break

        # Final progress callback
        if progress_callback:
            progress_callback({
                "files_discovered": files_discovered,
                "files_scanned": files_scanned,
                "files_skipped": files_skipped,
                "files_errored": files_errored,
                "findings_count": len(findings),
            })

        return ScanResult(
            scanner_type=self.scanner_type,
            asset_id=asset.id,
            status="completed",
            findings=findings,
            evidence_references=[{"files_scanned": files_scanned}],
            metadata={
                "files_discovered": files_discovered,
                "files_scanned": files_scanned,
                "files_skipped": files_skipped,
                "files_errored": files_errored,
                "findings_count": len(findings),
                "skipped_summary": skipped_details[:10],
                "error_summary": error_details[:10],
                "scan_scope": [str(d) for d in target_dirs],
            },
        )

    def _inspect_file(
        self,
        file_p: Path,
        rel_path: str,
        asset_id: str,
        sensitivity: Optional[int],
        exposure: Optional[int],
        lifetime: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Stream line-by-line inspection of code, configuration, or certificate files."""
        findings: List[Dict[str, Any]] = []
        ext = file_p.suffix.lower()

        # Handle X.509 Certificate files (.pem, .crt, .cer)
        if ext in (".pem", ".crt", ".cer"):
            cert_findings = self._inspect_certificate_file(file_p, rel_path, asset_id, sensitivity, exposure, lifetime)
            if cert_findings:
                return cert_findings

        # Stream text lines
        try:
            with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, start=1):
                    line_findings = self._inspect_line(
                        line=line,
                        line_idx=line_idx,
                        rel_path=rel_path,
                        ext=ext,
                        asset_id=asset_id,
                        sensitivity=sensitivity,
                        exposure=exposure,
                        lifetime=lifetime,
                    )
                    findings.extend(line_findings)
        except Exception as exc:
            logger.debug(f"Streaming error on {file_p}: {exc}")

        return findings

    def _inspect_line(
        self,
        line: str,
        line_idx: int,
        rel_path: str,
        ext: str,
        asset_id: str,
        sensitivity: Optional[int],
        exposure: Optional[int],
        lifetime: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Check line against cryptographic and configuration patterns."""
        line_findings: List[Dict[str, Any]] = []
        stripped = line.strip()
        if not stripped:
            return line_findings

        # 1. Private Key Detection (Zero-content disclosure guard)
        if "BEGIN" in stripped and "PRIVATE KEY" in stripped:
            loc_id = f"{rel_path}:{line_idx}"
            finding_dict = self._build_finding_dict(
                rule_id="SEC-PRIVATE-KEY-FILE",
                title="Cryptographic Private Key File Located",
                description="Detected private key material in filesystem. Private key contents are redacted and never stored.",
                algorithm="Private Key Artifact",
                primitive="private_key_material",
                quantum_vulnerable=True,
                recommended_pqc="Ensure private keys are protected with HSM / encrypted storage",
                severity="high",
                classification=CAT_CERT_EVIDENCE,
                confidence="high",
                evidence=f"File: {rel_path} (Line {line_idx})\nPattern: [ENCRYPTED/PRIVATE KEY HEADER REDACTED]",
                file_path=rel_path,
                line_number=line_idx,
                asset_id=asset_id,
                loc_id=loc_id,
                sensitivity=sensitivity,
                exposure=exposure,
                lifetime=lifetime,
            )
            line_findings.append(finding_dict)
            return line_findings

        # 2. Configuration file rules
        if ext in (".conf", ".cfg", ".ini", ".yaml", ".yml", ".json", ".toml", ".xml", ".properties"):
            for cfg_rule in CONFIG_RULES:
                if cfg_rule["regex"].search(line):
                    loc_id = f"{rel_path}:{line_idx}"
                    snippet = redact_secrets(stripped)
                    finding_dict = self._build_finding_dict(
                        rule_id=cfg_rule["rule_id"],
                        title=cfg_rule["title"],
                        description=cfg_rule["description"],
                        algorithm=cfg_rule["algorithm"],
                        primitive=cfg_rule["primitive"],
                        quantum_vulnerable=cfg_rule["quantum_vulnerable"],
                        recommended_pqc=cfg_rule["recommended_pqc"],
                        severity=cfg_rule["severity"],
                        classification=CAT_CONFIG_EVIDENCE,
                        confidence="high",
                        evidence=f"File: {rel_path} (Line {line_idx})\nConfig: {snippet}",
                        file_path=rel_path,
                        line_number=line_idx,
                        asset_id=asset_id,
                        loc_id=loc_id,
                        sensitivity=sensitivity,
                        exposure=exposure,
                        lifetime=lifetime,
                    )
                    line_findings.append(finding_dict)
                    return line_findings

        # 3. Multi-Language Cryptographic API and Pattern Rules
        for rule in CRYPTO_RULES:
            match_info = classify_line_detection(line, rel_path, rule)
            if match_info:
                cat, conf, snippet = match_info
                loc_id = f"{rel_path}:{line_idx}"
                finding_dict = self._build_finding_dict(
                    rule_id=rule["rule_id"],
                    title=rule["title"],
                    description=rule["description"],
                    algorithm=rule["algorithm"],
                    primitive=rule["primitive"],
                    quantum_vulnerable=rule["quantum_vulnerable"],
                    recommended_pqc=rule["recommended_pqc"],
                    severity=rule["severity"],
                    classification=cat,
                    confidence=conf,
                    evidence=f"File: {rel_path} (Line {line_idx})\nEvidence: {snippet}",
                    file_path=rel_path,
                    line_number=line_idx,
                    asset_id=asset_id,
                    loc_id=loc_id,
                    sensitivity=sensitivity,
                    exposure=exposure,
                    lifetime=lifetime,
                )
                line_findings.append(finding_dict)
                break  # Max 1 finding per line

        return line_findings

    def _inspect_certificate_file(
        self,
        file_p: Path,
        rel_path: str,
        asset_id: str,
        sensitivity: Optional[int],
        exposure: Optional[int],
        lifetime: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Inspect public certificate files without exposing private keys."""
        findings = []
        try:
            content = file_p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        # Check for public certificate header
        if "BEGIN CERTIFICATE" in content:
            from cryptography import x509
            try:
                cert = x509.load_pem_x509_certificate(content.encode("utf-8"))
                pub_key = cert.public_key()
                pub_type = type(pub_key).__name__
                
                algo = "RSA-2048"
                if "RSA" in pub_type:
                    key_size = getattr(pub_key, "key_size", 2048)
                    algo = f"RSA-{key_size}"
                elif "EllipticCurve" in pub_type:
                    curve = getattr(pub_key.curve, "name", "secp256r1")
                    algo = f"ECDSA ({curve})"
                elif "Ed25519" in pub_type:
                    algo = "Ed25519"

                subject = cert.subject.rfc4514_string()
                loc_id = f"{rel_path}:cert"

                finding_dict = self._build_finding_dict(
                    rule_id="PQC-CERT-PUBLIC-KEY",
                    title=f"X.509 Certificate with Classical {algo} Key",
                    description=f"Public certificate uses quantum-vulnerable {algo} public key. Subject: {subject}",
                    algorithm=algo,
                    primitive="digital_signature",
                    quantum_vulnerable=True,
                    recommended_pqc="ML-DSA-65 (FIPS 204) / SLH-DSA (FIPS 205)",
                    severity="high" if "1024" not in algo else "critical",
                    classification=CAT_CERT_EVIDENCE,
                    confidence="high",
                    evidence=f"File: {rel_path}\nSubject: {subject}\nAlgorithm: {algo}",
                    file_path=rel_path,
                    line_number=1,
                    asset_id=asset_id,
                    loc_id=loc_id,
                    sensitivity=sensitivity,
                    exposure=exposure,
                    lifetime=lifetime,
                )
                findings.append(finding_dict)
            except Exception as exc:
                logger.debug(f"Unable to parse PEM cert {file_p}: {exc}")

        return findings

    def _build_finding_dict(
        self,
        rule_id: str,
        title: str,
        description: str,
        algorithm: str,
        primitive: str,
        quantum_vulnerable: bool,
        recommended_pqc: str,
        severity: str,
        classification: str,
        confidence: str,
        evidence: str,
        file_path: str,
        line_number: int,
        asset_id: str,
        loc_id: str,
        sensitivity: Optional[int],
        exposure: Optional[int],
        lifetime: Optional[int],
    ) -> Dict[str, Any]:
        """Construct full finding dictionary with risk score and actionable guidance."""
        score, category, rationale = calculate_finding_risk_score(sensitivity, exposure, lifetime)
        rec = generate_finding_recommendation(
            algorithm=algorithm,
            primitive=primitive,
            quantum_vulnerable=quantum_vulnerable,
            risk_score=score,
            risk_category=category,
            sensitivity=sensitivity,
            exposure=exposure,
            lifetime=lifetime,
            detection_category=classification,
            file_path=file_path,
        )

        return {
            "rule_id": rule_id,
            "title": title,
            "description": description,
            "algorithm": algorithm,
            "cryptographic_primitive": primitive,
            "quantum_vulnerable": quantum_vulnerable,
            "recommended_pqc": recommended_pqc,
            "severity": severity,
            "detection_category": classification,
            "confidence": confidence,
            "evidence": evidence,
            "file_path": file_path,
            "line_number": line_number,
            "fingerprint": compute_finding_fingerprint(asset_id, rule_id, loc_id),
            "data_sensitivity": sensitivity,
            "exposure": exposure,
            "confidentiality_lifetime": lifetime,
            "risk_score": score,
            "risk_category": category,
            "score_rationale": rationale,
            "recommended_action": rec["recommended_action"],
            "migration_approach": rec["migration_approach"],
            "queue_group": rec["queue_group"],
            "remediation_status": "potential_exposure",
        }
