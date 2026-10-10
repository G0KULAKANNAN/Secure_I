"""
Static Cryptography and Configuration Scanner.
Applies safe directory traversal, extension filtering, and non-destructive pattern matching
for classical asymmetric algorithms (RSA, ECC, ECDH, ECDSA) and weak cryptography.
Never executes scanned source code.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import re
import logging
from quantumshield.models.asset import Asset
from quantumshield.models.finding import compute_finding_fingerprint
from quantumshield.scanner.base import BaseScanner, ScanResult

logger = logging.getLogger("quantumshield.scanner.static")

ALLOWED_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".jsx", ".tsx",
    ".go", ".c", ".cpp", ".h", ".cs",
    ".yml", ".yaml", ".json", ".conf", ".ini", ".xml",
}

EXCLUDED_DIRECTORIES = {
    "node_modules", ".git", "__pycache__", "venv", ".env",
    "dist", "build", ".idea", ".vscode", "target", "vendor",
}

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
MAX_FILES_TO_SCAN = 300

# Pattern definitions for classical / quantum-vulnerable cryptography
CRYPTO_PATTERNS = [
    {
        "rule_id": "PQC-CODE-RSA",
        "algorithm": "RSA",
        "primitive": "asymmetric_encryption",
        "recommended_pqc": "ML-KEM-768 (Encryption) / ML-DSA-65 (Signatures)",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Classical RSA Cryptographic API Reference",
        "description": "Source code references classical RSA key generation or cipher operations. Quantum computers running Shor's algorithm can factor RSA moduli.",
        "regex": re.compile(
            r'(RSA\.generate|rsa\.generate_private_key|rsa\.newkeys|KeyPairGenerator\.getInstance\s*\(\s*["\']RSA|crypto/rsa|RSACryptoServiceProvider|Cipher\.getInstance\s*\(\s*["\']RSA|openssl\s+genrsa|DHE-RSA|ECDHE-RSA)',
            re.IGNORECASE,
        ),
    },
    {
        "rule_id": "PQC-CODE-ECC",
        "algorithm": "ECC/ECDSA",
        "primitive": "digital_signature",
        "recommended_pqc": "ML-DSA-65 (FIPS 204)",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Classical Elliptic Curve (ECC/ECDSA) API Reference",
        "description": "Source code references classical Elliptic Curve cryptography. Discrete logarithm operations are vulnerable to Shor's algorithm.",
        "regex": re.compile(
            r'(ec\.generate_private_key|ec\.SECP\d+|KeyPairGenerator\.getInstance\s*\(\s*["\']EC|crypto/ecdsa|ECDsaCng|openssl\s+ecparam|Signature\.getInstance\s*\(\s*["\'].*ECDSA|ECDHE-ECDSA)',
            re.IGNORECASE,
        ),
    },
    {
        "rule_id": "PQC-CODE-ECDH",
        "algorithm": "ECDH/Diffie-Hellman",
        "primitive": "key_establishment",
        "recommended_pqc": "ML-KEM-768 (FIPS 203)",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Classical Diffie-Hellman / ECDH Key Exchange Reference",
        "description": "Source code references Diffie-Hellman key exchange. Ephemeral classical key exchange is susceptible to Store-Now-Decrypt-Later (SNDL) attacks.",
        "regex": re.compile(
            r'(KeyAgreement\.getInstance\s*\(\s*["\']ECDH|crypto/ecdh|crypto/diffiehellman|DHParameterSpec|DiffieHellman|DHE-|ECDHE|set_ciphers)',
            re.IGNORECASE,
        ),
    },
    {
        "rule_id": "LEGACY-WEAK-CIPHER",
        "algorithm": "DES/RC4",
        "primitive": "symmetric_encryption",
        "recommended_pqc": "AES-256-GCM (Classical and Post-Quantum Safe)",
        "quantum_vulnerable": False,
        "severity": "critical",
        "title": "Obsolete Legacy Cipher (DES / RC4) Reference",
        "description": "Detected reference to deprecated cipher (DES or RC4). Vulnerable to practical classical cryptanalysis.",
        "regex": re.compile(
            r'(DES\.new|ARC4\.new|Cipher\.getInstance\s*\(\s*["\']DES)',
            re.IGNORECASE,
        ),
    },
]


class StaticScanner(BaseScanner):
    """Safe Static Cryptography and Configuration Scanner."""

    @property
    def scanner_type(self) -> str:
        return "static_scan"

    def scan(self, asset: Asset, options: Optional[Dict[str, Any]] = None) -> ScanResult:
        """
        Scan a source directory, single file, or raw content.
        Options can include:
            - target_directory: Path to folder to inspect
            - file_path: Path to single file
            - source_content: Raw source code string
            - file_name: Optional filename when passing raw content
        """
        options = options or {}
        target_dir = options.get("target_directory") or options.get("payload", {}).get("target_directory")
        single_file = options.get("file_path") or options.get("payload", {}).get("file_path")
        source_content = options.get("source_content") or options.get("payload", {}).get("source_content")
        file_name = options.get("file_name") or options.get("payload", {}).get("file_name") or "snippet.py"

        findings: List[Dict[str, Any]] = []
        files_scanned = 0

        # Case 1: Raw code content passed directly
        if source_content:
            file_findings = self._scan_text_content(source_content, file_name, asset.id)
            findings.extend(file_findings)
            files_scanned = 1

        # Case 2: Single file path provided
        elif single_file:
            path_obj = Path(single_file).resolve()
            if not path_obj.is_file():
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message=f"File not found: {single_file}",
                )
            file_findings = self._scan_single_file(path_obj, asset.id)
            findings.extend(file_findings)
            files_scanned = 1

        # Case 3: Directory path provided
        elif target_dir:
            dir_path = Path(target_dir).resolve()
            if not dir_path.is_dir():
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message=f"Directory not found: {target_dir}",
                )

            # Traverse directory safely
            for file_path in dir_path.rglob("*"):
                if files_scanned >= MAX_FILES_TO_SCAN:
                    break

                if not file_path.is_file():
                    continue

                # Exclude unwanted directories
                if any(part in EXCLUDED_DIRECTORIES for part in file_path.parts):
                    continue

                # Check extension
                if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                    continue

                # Check file size
                try:
                    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                        continue
                except OSError:
                    continue

                # Ensure path containment
                try:
                    file_path.relative_to(dir_path)
                except ValueError:
                    continue

                file_findings = self._scan_single_file(file_path, asset.id, base_dir=dir_path)
                findings.extend(file_findings)
                files_scanned += 1

        else:
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message="Static scanner requires a target_directory, file_path, or source_content.",
            )

        return ScanResult(
            scanner_type=self.scanner_type,
            asset_id=asset.id,
            status="completed",
            findings=findings,
            evidence_references=[{"files_scanned_count": files_scanned}],
            metadata={
                "files_scanned": files_scanned,
                "ruleset_version": "v1.2-static-pqc",
                "disclaimer": "Pattern matches are structural indicators requiring verification, not automated proof of active production execution.",
            },
        )

    def _scan_single_file(self, file_path: Path, asset_id: str, base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Read and inspect a single file on disk."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            logger.warning(f"Unable to read file {file_path}: {exc}")
            return []

        rel_path = str(file_path.relative_to(base_dir)) if base_dir else str(file_path.name)
        return self._scan_text_content(content, rel_path, asset_id)

    def _scan_text_content(self, text: str, display_path: str, asset_id: str) -> List[Dict[str, Any]]:
        """Scan line by line for cryptographic patterns."""
        findings: List[Dict[str, Any]] = []
        lines = text.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                # Skip pure comments
                continue

            for rule in CRYPTO_PATTERNS:
                if rule["regex"].search(line):
                    # Redact potential embedded keys/tokens in the line
                    sanitized_line = self._redact_secrets(stripped)
                    loc_id = f"{display_path}:{idx}"

                    finding = {
                        "rule_id": rule["rule_id"],
                        "title": rule["title"],
                        "description": rule["description"],
                        "algorithm": rule["algorithm"],
                        "cryptographic_primitive": rule["primitive"],
                        "quantum_vulnerable": rule["quantum_vulnerable"],
                        "recommended_pqc": rule["recommended_pqc"],
                        "severity": rule["severity"],
                        "evidence": f"File: {display_path} (Line {idx})\nCode: {sanitized_line}",
                        "confidence": "needs_review",  # Requirement: treat matches as indicators needing validation
                        "file_path": display_path,
                        "line_number": idx,
                        "fingerprint": compute_finding_fingerprint(asset_id, rule["rule_id"], loc_id),
                    }
                    findings.append(finding)
                    break  # One finding per line maximum

        return findings

    def _redact_secrets(self, text: str) -> str:
        """Mask potential API keys, passphrases, and tokens."""
        # Simple mask for high-entropy strings or key-like tokens
        text = re.sub(r'(api_key|password|secret|token)\s*=\s*["\'][^"\']+["\']', r'\1="[REDACTED]"', text, flags=re.IGNORECASE)
        return text[:180]  # Cap evidence snippet length
