"""
Real X.509 Certificate Cryptography Scanner.
Parses public certificates using Python cryptography library, extracts algorithms,
detects Shor's algorithm quantum vulnerabilities, and maps NIST PQC recommendations.
Never requires or processes private keys.
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timezone
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, dsa
from quantumshield.models.asset import Asset
from quantumshield.models.finding import compute_finding_fingerprint
from quantumshield.scanner.base import BaseScanner, ScanResult

logger = logging.getLogger("quantumshield.scanner.certificate")


class CertificateScanner(BaseScanner):
    """Scanner for X.509 public certificates."""

    @property
    def scanner_type(self) -> str:
        return "certificate_scan"

    def scan(self, asset: Asset, options: Optional[Dict[str, Any]] = None) -> ScanResult:
        """
        Scan a public certificate provided in options or referenced in asset metadata.
        Options can include:
            - certificate_data: PEM string or raw DER bytes
            - file_path: Path to certificate file on local disk
        """
        options = options or {}
        cert_data = options.get("certificate_data") or options.get("payload", {}).get("certificate_data")
        file_path = options.get("file_path") or options.get("payload", {}).get("file_path")

        # 1. Security Check: Reject any private keys
        if cert_data:
            text_to_check = cert_data.decode("utf-8", errors="ignore") if isinstance(cert_data, bytes) else str(cert_data)
            if "PRIVATE KEY" in text_to_check.upper():
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message="Security Policy Violation: Private key detected. QuantumShield strictly rejects private keys and only accepts public certificates.",
                )

        # 2. Load certificate data
        raw_bytes: Optional[bytes] = None
        if cert_data:
            if isinstance(cert_data, str):
                raw_bytes = cert_data.encode("utf-8")
            elif isinstance(cert_data, bytes):
                raw_bytes = cert_data
        elif file_path:
            from pathlib import Path
            p = Path(file_path).resolve()
            if not p.is_file():
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message=f"Certificate file not found at: {file_path}",
                )
            raw_bytes = p.read_bytes()
            if b"PRIVATE KEY" in raw_bytes.upper():
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message="Security Policy Violation: Private key found in file. QuantumShield strictly prohibits private key inspection.",
                )
        else:
            # Check if asset has certificate in description or hostname
            if asset.asset_type != "certificate" and not asset.hostname:
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message="No certificate file or data provided for scanning.",
                )
            # Default fallback when no certificate data is attached
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message="Asset requires certificate data (PEM/DER) to perform certificate inspection.",
            )

        # 3. Parse X.509 Certificate
        cert = None
        is_pem = True
        try:
            cert = x509.load_pem_x509_certificate(raw_bytes)
        except Exception:
            try:
                cert = x509.load_der_x509_certificate(raw_bytes)
                is_pem = False
            except Exception as exc:
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message=f"Invalid X.509 certificate format (neither valid PEM nor DER): {str(exc)}",
                )

        # 4. Extract Certificate Metadata
        try:
            subject = cert.subject.rfc4514_string()
            issuer = cert.issuer.rfc4514_string()
            serial_hex = f"{cert.serial_number:X}"
            not_before = cert.not_valid_before_utc.isoformat()
            not_after = cert.not_valid_after_utc.isoformat()
            validity_days = (cert.not_valid_after_utc - cert.not_valid_before_utc).days
            sig_algo = getattr(cert.signature_algorithm_oid, "_name", str(cert.signature_algorithm_oid))

            public_key = cert.public_key()
            findings: List[Dict[str, Any]] = []

            # 5. Cryptographic Evaluation
            if isinstance(public_key, rsa.RSAPublicKey):
                key_size = public_key.key_size
                algo_name = f"RSA-{key_size}"
                is_quantum_vulnerable = True

                severity = "critical" if key_size < 2048 else "high"
                finding_dict = {
                    "rule_id": f"PQC-CERT-RSA-{key_size}",
                    "title": f"Quantum-Vulnerable {algo_name} Certificate Public Key",
                    "description": (
                        f"The certificate utilizes {algo_name} public key encryption/signature mechanism. "
                        "RSA is vulnerable to polynomial-time factorization via Shor's algorithm on Cryptographically "
                        "Relevant Quantum Computers (CRQCs). NIST recommends migrating to FIPS 204 ML-DSA for digital "
                        "signatures or FIPS 203 ML-KEM for key establishment."
                    ),
                    "algorithm": algo_name,
                    "cryptographic_primitive": "digital_signature",
                    "quantum_vulnerable": is_quantum_vulnerable,
                    "recommended_pqc": "ML-DSA-65 (FIPS 204)",
                    "severity": severity,
                    "evidence": f"Subject: {subject}\nIssuer: {issuer}\nSerial: {serial_hex}\nAlgorithm: {algo_name}\nSignature: {sig_algo}",
                    "confidence": "high",
                    "file_path": file_path or "inline_certificate.pem",
                    "line_number": 1,
                    "fingerprint": compute_finding_fingerprint(asset.id, f"PQC-CERT-RSA-{key_size}", serial_hex),
                }
                findings.append(finding_dict)

            elif isinstance(public_key, ec.EllipticCurvePublicKey):
                curve_name = public_key.curve.name
                algo_name = f"ECDSA-{curve_name}"
                finding_dict = {
                    "rule_id": f"PQC-CERT-ECC-{curve_name}",
                    "title": f"Quantum-Vulnerable {algo_name} Certificate Public Key",
                    "description": (
                        f"The certificate utilizes Elliptic Curve Cryptography ({curve_name}). "
                        "ECC discrete logarithms can be broken in polynomial time by Shor's algorithm. "
                        "NIST recommends migration to ML-DSA (FIPS 204) or SLH-DSA (FIPS 205)."
                    ),
                    "algorithm": algo_name,
                    "cryptographic_primitive": "digital_signature",
                    "quantum_vulnerable": True,
                    "recommended_pqc": "ML-DSA-65 (FIPS 204)",
                    "severity": "high",
                    "evidence": f"Subject: {subject}\nIssuer: {issuer}\nSerial: {serial_hex}\nCurve: {curve_name}\nSignature: {sig_algo}",
                    "confidence": "high",
                    "file_path": file_path or "inline_certificate.pem",
                    "line_number": 1,
                    "fingerprint": compute_finding_fingerprint(asset.id, f"PQC-CERT-ECC-{curve_name}", serial_hex),
                }
                findings.append(finding_dict)

            elif isinstance(public_key, ed25519.Ed25519PublicKey):
                algo_name = "Ed25519"
                finding_dict = {
                    "rule_id": "PQC-CERT-ED25519",
                    "title": "Quantum-Vulnerable Ed25519 Certificate Public Key",
                    "description": (
                        "The certificate utilizes Ed25519. Classical Edwards curve cryptography is vulnerable to Shor's algorithm. "
                        "NIST recommends migration to ML-DSA (FIPS 204)."
                    ),
                    "algorithm": algo_name,
                    "cryptographic_primitive": "digital_signature",
                    "quantum_vulnerable": True,
                    "recommended_pqc": "ML-DSA-65 (FIPS 204)",
                    "severity": "high",
                    "evidence": f"Subject: {subject}\nIssuer: {issuer}\nSerial: {serial_hex}\nSignature: {sig_algo}",
                    "confidence": "high",
                    "file_path": file_path or "inline_certificate.pem",
                    "line_number": 1,
                    "fingerprint": compute_finding_fingerprint(asset.id, "PQC-CERT-ED25519", serial_hex),
                }
                findings.append(finding_dict)

            # Check weak signature hash (SHA-1 / MD5)
            if "sha1" in sig_algo.lower() or "md5" in sig_algo.lower():
                findings.append({
                    "rule_id": "LEGACY-WEAK-SIG-HASH",
                    "title": f"Weak Classical Signature Algorithm ({sig_algo})",
                    "description": f"The certificate signature employs weak hashing ({sig_algo}), vulnerable to collision attacks.",
                    "algorithm": sig_algo,
                    "cryptographic_primitive": "hash",
                    "quantum_vulnerable": False,
                    "recommended_pqc": "SHA-256 / SHA-384 / SHAKE-256",
                    "severity": "critical",
                    "evidence": f"Certificate signature algorithm: {sig_algo}",
                    "confidence": "high",
                    "file_path": file_path or "inline_certificate.pem",
                    "line_number": 1,
                    "fingerprint": compute_finding_fingerprint(asset.id, "LEGACY-WEAK-SIG-HASH", serial_hex),
                })

            metadata = {
                "subject": subject,
                "issuer": issuer,
                "serial_number": serial_hex,
                "not_before": not_before,
                "not_after": not_after,
                "validity_days": validity_days,
                "signature_algorithm": sig_algo,
                "format": "PEM" if is_pem else "DER",
                "ruleset_version": "v1.2-nist-pqc",
            }

            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="completed",
                findings=findings,
                evidence_references=[{
                    "type": "x509_certificate_metadata",
                    "serial": serial_hex,
                    "subject": subject,
                }],
                metadata=metadata,
            )

        except Exception as exc:
            logger.error(f"Error analyzing certificate: {exc}", exc_info=True)
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message=f"Error inspecting certificate metadata: {str(exc)}",
            )
