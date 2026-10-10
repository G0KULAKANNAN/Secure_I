"""
Authorised TLS Handshake and Cipher Suite Scanner.
Performs non-destructive network handshake probing against approved endpoints with SSRF guards.
Identifies classical key-exchange mechanisms vulnerable to Store-Now-Decrypt-Later (SNDL) quantum threats.
"""

import socket
import ssl
import ipaddress
import logging
from typing import Optional, Dict, Any, List
from quantumshield.models.asset import Asset
from quantumshield.models.finding import compute_finding_fingerprint
from quantumshield.scanner.base import BaseScanner, ScanResult

logger = logging.getLogger("quantumshield.scanner.tls")

ALLOWED_TLS_PORTS = {443, 8443, 9443}


class TlsScanner(BaseScanner):
    """Controlled TLS Configuration and Handshake Scanner."""

    def __init__(self, allow_local_lab: bool = True):
        self.allow_local_lab = allow_local_lab

    @property
    def scanner_type(self) -> str:
        return "tls_scan"

    def scan(self, asset: Asset, options: Optional[Dict[str, Any]] = None) -> ScanResult:
        """
        Probe authorized target hostname or IP address.
        """
        options = options or {}
        target_host = asset.hostname or asset.ip_address
        if not target_host:
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message="Asset must have a valid hostname or IP address configured for TLS scanning.",
            )

        port = int(options.get("port") or 443)
        if port not in ALLOWED_TLS_PORTS:
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message=f"Port {port} is not in the approved TLS port allowlist ({ALLOWED_TLS_PORTS}).",
            )

        # 1. Resolve host and perform SSRF validation
        try:
            resolved_ip = socket.gethostbyname(target_host)
            ip_obj = ipaddress.ip_address(resolved_ip)
        except Exception as exc:
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message=f"DNS resolution failed for '{target_host}': {str(exc)}",
            )

        # SSRF checks
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            if not self.allow_local_lab:
                return ScanResult(
                    scanner_type=self.scanner_type,
                    asset_id=asset.id,
                    status="failed",
                    error_message=f"SSRF Protection: Access to private/loopback IP {resolved_ip} is prohibited in production mode.",
                )

        # 2. Execute TLS Handshake
        findings: List[Dict[str, Any]] = []
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # Discovery mode allows inspecting internal endpoints

            with socket.create_connection((target_host, port), timeout=4.0) as sock:
                with context.wrap_socket(sock, server_hostname=target_host if asset.hostname else None) as ssock:
                    tls_version = ssock.version()
                    cipher_info = ssock.cipher()
                    cipher_name, proto_version, secret_bits = cipher_info if cipher_info else ("Unknown", "Unknown", 0)

                    # 3. Analyze negotiated cipher
                    is_pqc_hybrid = "KYBER" in cipher_name.upper() or "MLKEM" in cipher_name.upper()
                    if not is_pqc_hybrid:
                        # Classical key exchange identified
                        finding = {
                            "rule_id": "PQC-TLS-CLASSICAL-KEX",
                            "title": f"Classical Key Exchange in TLS Handshake ({cipher_name})",
                            "description": (
                                f"Endpoint '{target_host}:{port}' negotiated {tls_version} with cipher suite '{cipher_name}'. "
                                "Classical key exchange (ECDHE / DHE / RSA) is vulnerable to Store-Now-Decrypt-Later (SNDL) attacks. "
                                "Adversaries can record encrypted network sessions today and decrypt them once a CRQC becomes available."
                            ),
                            "algorithm": cipher_name,
                            "cryptographic_primitive": "key_establishment",
                            "quantum_vulnerable": True,
                            "recommended_pqc": "ML-KEM-768 Hybrid (X25519 + ML-KEM-768)",
                            "severity": "high",
                            "evidence": f"Endpoint: {target_host}:{port}\nTLS Version: {tls_version}\nCipher: {cipher_name}\nBits: {secret_bits}",
                            "confidence": "high",
                            "file_path": f"{target_host}:{port}",
                            "line_number": 0,
                            "fingerprint": compute_finding_fingerprint(asset.id, "PQC-TLS-CLASSICAL-KEX", f"{target_host}:{port}"),
                        }
                        findings.append(finding)

                    return ScanResult(
                        scanner_type=self.scanner_type,
                        asset_id=asset.id,
                        status="completed",
                        findings=findings,
                        evidence_references=[{
                            "endpoint": f"{target_host}:{port}",
                            "tls_version": tls_version,
                            "cipher": cipher_name,
                        }],
                        metadata={
                            "endpoint": f"{target_host}:{port}",
                            "resolved_ip": resolved_ip,
                            "tls_version": tls_version,
                            "cipher_suite": cipher_name,
                            "bits": secret_bits,
                        },
                    )

        except (socket.timeout, TimeoutError):
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message=f"Connection timed out while probing '{target_host}:{port}'. Target may be offline or filtered by firewall.",
            )
        except ConnectionRefusedError:
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message=f"Connection refused by '{target_host}:{port}'. Service is not listening on this port.",
            )
        except Exception as exc:
            return ScanResult(
                scanner_type=self.scanner_type,
                asset_id=asset.id,
                status="failed",
                error_message=f"TLS handshake probe failed: {str(exc)}",
            )
