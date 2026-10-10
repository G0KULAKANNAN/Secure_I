"""
Cryptographic Pattern Rules and Contextual Classification Catalog.
Supports multi-language code analysis, configuration inspection, certificate recognition,
and classification into distinct evidence tiers.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


# Classification Categories
CAT_CONFIRMED_API = "Confirmed cryptographic API usage"
CAT_CONFIG_EVIDENCE = "Configuration-based evidence"
CAT_CERT_EVIDENCE = "Certificate-based evidence"
CAT_TEXTUAL_REF = "Textual reference only"
CAT_MANUAL_VALIDATION = "Needs manual validation"


def redact_secrets(text: str) -> str:
    """Mask sensitive tokens, private keys, passwords, and passphrases in evidence."""
    # Redact PEM private key content
    text = re.sub(
        r"-----BEGIN (?:[A-Z\s]+)?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z\s]+)?PRIVATE KEY-----",
        "-----BEGIN PRIVATE KEY-----\n[ENCRYPTED/PRIVATE KEY DATA REDACTED]\n-----END PRIVATE KEY-----",
        text,
        flags=re.IGNORECASE,
    )
    # Redact assignment-style credentials
    text = re.sub(
        r'((?:api_key|password|secret|token|private_key|auth_token|client_secret)\s*[:=]\s*["\'])[^"\']+(["\'])',
        r'\1[REDACTED]\2',
        text,
        flags=re.IGNORECASE,
    )
    # Redact raw hex/base64 keys
    text = re.sub(
        r'((?:secret|key|token)\s*=\s*b?["\'])[A-Fa-f0-9]{32,}(["\'])',
        r'\1[REDACTED_HEX_KEY]\2',
        text,
        flags=re.IGNORECASE,
    )
    return text[:250]


def is_comment_or_doc_line(line: str, ext: str) -> bool:
    """Determine if a code line is purely a comment or documentation."""
    s = line.strip()
    if not s:
        return True
    
    # Hash-style comments (#)
    if s.startswith("#"):
        return True
    
    # Slash-style comments (// or /* or *)
    if s.startswith("//") or s.startswith("/*") or s.startswith("*") or s.endswith("*/"):
        return True
    
    # Python docstrings (""" or ''')
    if s.startswith('"""') or s.startswith("'''") or s.endswith('"""') or s.endswith("'''"):
        return True
    
    # HTML / XML comments (<!--)
    if s.startswith("<!--") or s.endswith("-->"):
        return True
    
    # SQL / Ada / Lua comments (--)
    if s.startswith("--"):
        return True
    
    # Semicolon comments in .ini / .conf (;)
    if s.startswith(";"):
        return True
    
    return False


# Multi-Language Cryptographic Patterns
CRYPTO_RULES: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # 1. Classical RSA
    # -------------------------------------------------------------
    {
        "rule_id": "PQC-ALGO-RSA-1024",
        "algorithm": "RSA-1024",
        "primitive": "asymmetric_key_or_signature",
        "quantum_vulnerable": True,
        "severity": "critical",
        "title": "Legacy Broken RSA-1024 Detected",
        "description": "Detected reference to 1024-bit RSA. Cryptographically obsolete today by classical factorization standards and immediately broken by quantum computers.",
        "recommended_pqc": "ML-KEM-768 (Encryption) / ML-DSA-65 (Signatures)",
        "api_regex": re.compile(
            r'(?:rsa\.generate_private_key\([^)]*key_size\s*=\s*1024|'
            r'RSA\.generate\(\s*1024|'
            r'rsa\.newkeys\(\s*1024|'
            r'KeyPairGenerator\.getInstance\([^)]*RSA[^)]*\)[\s\S]{0,40}initialize\(\s*1024|'
            r'openssl\s+genrsa\s+1024|'
            r'RSACryptoServiceProvider\(\s*1024\b)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bRSA[-_\s]?1024\b', re.IGNORECASE),
    },
    {
        "rule_id": "PQC-ALGO-RSA-STANDARD",
        "algorithm": "RSA-2048/4096",
        "primitive": "asymmetric_key_or_signature",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Classical RSA Cryptography Detected",
        "description": "Detected classical RSA key generation or cipher operations. Shor's quantum algorithm factors RSA moduli in polynomial time.",
        "recommended_pqc": "ML-KEM-768 (Encryption) / ML-DSA-65 (Signatures)",
        "api_regex": re.compile(
            r'(?:rsa\.generate_private_key\s*\(|'
            r'RSA\.generate\s*\(|'
            r'rsa\.newkeys\s*\(|'
            r'KeyPairGenerator\.getInstance\s*\(\s*["\']RSA|'
            r'Cipher\.getInstance\s*\(\s*["\']RSA|'
            r'crypto/rsa|'
            r'RSACryptoServiceProvider|'
            r'openssl\s+genrsa|'
            r'PKCS1_OAEP|'
            r'PKCS1_v1_5|'
            r'from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+rsa)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bRSA[-_\s]?(?:2048|3072|4096)\b|\bRSA\b', re.IGNORECASE),
    },

    # -------------------------------------------------------------
    # 2. Elliptic Curve (ECC, ECDSA, ECDH)
    # -------------------------------------------------------------
    {
        "rule_id": "PQC-ALGO-ECDSA",
        "algorithm": "ECDSA",
        "primitive": "digital_signature",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Classical Elliptic Curve Digital Signature (ECDSA)",
        "description": "Detected ECDSA digital signature usage. Discrete logarithm operations are vulnerable to Shor's algorithm on a cryptographically relevant quantum computer.",
        "recommended_pqc": "ML-DSA-65 (FIPS 204) / SLH-DSA (FIPS 205)",
        "api_regex": re.compile(
            r'(?:ec\.generate_private_key\s*\(|'
            r'Signature\.getInstance\s*\(\s*["\'][^"\']*ECDSA|'
            r'crypto/ecdsa|'
            r'ECDsaCng|'
            r'ec\.ECDSA\s*\(|'
            r'from\s+cryptography\.hazmat\.primitives\.asymmetric\s+import\s+ec)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bECDSA\b|\bsecp256r1\b|\bsecp256k1\b|\bP-256\b|\bP-384\b', re.IGNORECASE),
    },
    {
        "rule_id": "PQC-ALGO-ECDH",
        "algorithm": "ECDH/Diffie-Hellman",
        "primitive": "key_establishment",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Classical ECDH / Diffie-Hellman Key Exchange",
        "description": "Detected classical ECDH or Diffie-Hellman key exchange. Ephemeral classical key exchange is susceptible to Store-Now-Decrypt-Later (SNDL) attacks.",
        "recommended_pqc": "ML-KEM-768 (FIPS 203)",
        "api_regex": re.compile(
            r'(?:KeyAgreement\.getInstance\s*\(\s*["\']ECDH|'
            r'ec\.ECDH\s*\(|'
            r'crypto/ecdh|'
            r'crypto/diffiehellman|'
            r'DHParameterSpec|'
            r'DiffieHellman|'
            r'ECDH_compute_key)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bECDH\b|\bDiffie[-_\s]?Hellman\b|\bECDHE\b|\bDHE\b', re.IGNORECASE),
    },
    {
        "rule_id": "PQC-ALGO-X25519",
        "algorithm": "X25519/X448",
        "primitive": "key_establishment",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Montgomery Curve Key Exchange (X25519 / X448)",
        "description": "Detected X25519/X448 modern classical key agreement. While secure classically, it remains vulnerable to Shor's algorithm.",
        "recommended_pqc": "X25519 + ML-KEM-768 (Hybrid FIPS 203)",
        "api_regex": re.compile(
            r'(?:x25519\.X25519PrivateKey|'
            r'x448\.X448PrivateKey|'
            r'crypto/ed25519|'
            r'crypto/curve25519|'
            r'KeyAgreement\.getInstance\s*\(\s*["\']X25519|'
            r'Curve25519)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bX25519\b|\bX448\b|\bCurve25519\b', re.IGNORECASE),
    },

    # -------------------------------------------------------------
    # 3. Legacy Classical Weak Ciphers (DES, 3DES, RC4)
    # -------------------------------------------------------------
    {
        "rule_id": "LEGACY-CIPHER-DES-RC4",
        "algorithm": "DES/3DES/RC4",
        "primitive": "symmetric_encryption",
        "quantum_vulnerable": False,
        "severity": "critical",
        "title": "Deprecated Legacy Symmetric Cipher (DES / RC4)",
        "description": "Detected reference to obsolete symmetric cipher (DES, 3DES, or RC4). Insecure against classical cryptanalysis today.",
        "recommended_pqc": "AES-256-GCM (Classical and Post-Quantum Safe)",
        "api_regex": re.compile(
            r'(?:DES\.new\s*\(|'
            r'DES3\.new\s*\(|'
            r'ARC4\.new\s*\(|'
            r'Cipher\.getInstance\s*\(\s*["\'](?:DES|DESede|RC4|ARCFOUR)|'
            r'TripleDES|'
            r'crypto/des|'
            r'crypto/rc4)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\b(?:DES|3DES|Triple[-_\s]?DES|RC4|ARCFOUR)\b', re.IGNORECASE),
    },

    # -------------------------------------------------------------
    # 4. Hash Functions: MD5 & SHA-1
    # -------------------------------------------------------------
    {
        "rule_id": "LEGACY-HASH-MD5",
        "algorithm": "MD5",
        "primitive": "cryptographic_hash",
        "quantum_vulnerable": False,
        "severity": "high",
        "title": "Collision-Vulnerable MD5 Hash Function",
        "description": "Detected MD5 digest usage. MD5 is broken for cryptographic integrity and collision resistance.",
        "recommended_pqc": "SHA-256 / SHA-384 / SHA-3",
        "api_regex": re.compile(
            r'(?:hashlib\.md5\s*\(|'
            r'MessageDigest\.getInstance\s*\(\s*["\']MD5|'
            r'crypto/md5|'
            r'MD5_Init|'
            r'MD5_Update)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bMD5\b', re.IGNORECASE),
    },
    {
        "rule_id": "LEGACY-HASH-SHA1",
        "algorithm": "SHA-1",
        "primitive": "cryptographic_hash",
        "quantum_vulnerable": False,
        "severity": "medium",
        "title": "Collision-Vulnerable SHA-1 Hash Function",
        "description": "Detected SHA-1 digest usage. SHA-1 has practical collision vulnerabilities and should be phased out of signatures and certificates.",
        "recommended_pqc": "SHA-256 (Classical & PQ Hash) / SHA-3",
        "api_regex": re.compile(
            r'(?:hashlib\.sha1\s*\(|'
            r'MessageDigest\.getInstance\s*\(\s*["\']SHA-?1|'
            r'crypto/sha1|'
            r'SHA1_Init)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bSHA[-_]?1\b', re.IGNORECASE),
    },

    # -------------------------------------------------------------
    # 5. Symmetric Ciphers: AES-128 & AES-256
    # -------------------------------------------------------------
    {
        "rule_id": "SYM-CIPHER-AES-128",
        "algorithm": "AES-128",
        "primitive": "symmetric_encryption",
        "quantum_vulnerable": False,
        "severity": "low",
        "title": "AES-128 Symmetric Cipher Usage",
        "description": "AES-128 provides 64-bit security against Grover's quantum search. While adequate for commercial data, high-security systems should migrate to AES-256.",
        "recommended_pqc": "AES-256-GCM (CNSA 2.0 Recommended)",
        "api_regex": re.compile(
            r'(?:AES\.new\([^)]*16\b|'
            r'Cipher\.getInstance\s*\(\s*["\']AES/(?:GCM|CBC|CTR)/[^"\']*\)[\s\S]{0,40}128|'
            r'aes-128-(?:gcm|cbc|ctr))',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bAES[-_]?128\b', re.IGNORECASE),
    },
    {
        "rule_id": "SYM-CIPHER-AES-256",
        "algorithm": "AES-256",
        "primitive": "symmetric_encryption",
        "quantum_vulnerable": False,
        "severity": "info",
        "title": "Post-Quantum Resilient AES-256 Usage",
        "description": "AES-256 retains 128-bit quantum security against Grover's algorithm, satisfying NIST and CNSA 2.0 post-quantum symmetric encryption standards.",
        "recommended_pqc": "AES-256-GCM (Already PQ Compliant)",
        "api_regex": re.compile(
            r'(?:AES\.new\([^)]*32\b|'
            r'Cipher\.getInstance\s*\(\s*["\']AES/(?:GCM|CBC|CTR)/[^"\']*\)[\s\S]{0,40}256|'
            r'aes-256-(?:gcm|cbc|ctr))',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bAES[-_]?256\b', re.IGNORECASE),
    },

    # -------------------------------------------------------------
    # 6. Approved Post-Quantum Cryptography (FIPS 203 / 204 / 205)
    # -------------------------------------------------------------
    {
        "rule_id": "PQC-APPROVED-ML-KEM",
        "algorithm": "ML-KEM (FIPS 203 / Kyber)",
        "primitive": "key_establishment",
        "quantum_vulnerable": False,
        "severity": "info",
        "title": "Approved Post-Quantum ML-KEM Implementation",
        "description": "Detected reference to NIST FIPS 203 ML-KEM (Module-Lattice Key Encapsulation Mechanism) or Kyber. Approved for post-quantum key establishment.",
        "recommended_pqc": "ML-KEM-768 (Active PQC Standard)",
        "api_regex": re.compile(
            r'(?:ML[-_]?KEM|Kyber512|Kyber768|Kyber1024|X25519MLKEM768|SecP256r1MLKEM768|oqs\.KeyExchange|liboqs)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bML[-_]?KEM[-_]?(?:512|768|1024)?\b|\bKyber\b', re.IGNORECASE),
    },
    {
        "rule_id": "PQC-APPROVED-ML-DSA",
        "algorithm": "ML-DSA (FIPS 204 / Dilithium)",
        "primitive": "digital_signature",
        "quantum_vulnerable": False,
        "severity": "info",
        "title": "Approved Post-Quantum ML-DSA Implementation",
        "description": "Detected reference to NIST FIPS 204 ML-DSA (Module-Lattice Digital Signature Algorithm) or Dilithium. Approved for post-quantum digital signatures.",
        "recommended_pqc": "ML-DSA-65 (Active PQC Standard)",
        "api_regex": re.compile(
            r'(?:ML[-_]?DSA|Dilithium2|Dilithium3|Dilithium5|SLH[-_]?DSA|SPHINCS\+|oqs\.Signature)',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bML[-_]?DSA[-_]?(?:44|65|87)?\b|\bDilithium\b|\bSLH[-_]?DSA\b', re.IGNORECASE),
    },

    # -------------------------------------------------------------
    # 7. Insecure Randomness for Cryptography
    # -------------------------------------------------------------
    {
        "rule_id": "INSECURE-RANDOM-PSEUDO",
        "algorithm": "Insecure-PRNG",
        "primitive": "random_number_generation",
        "quantum_vulnerable": False,
        "severity": "high",
        "title": "Non-Cryptographic PRNG in Security Context",
        "description": "Detected usage of pseudo-random generators (e.g. random.random, Math.random) for security-sensitive tokens or key material.",
        "recommended_pqc": "secrets / os.urandom / SecureRandom",
        "api_regex": re.compile(
            r'(?:random\.randint|random\.random\(\)|Math\.random\(\)|rand\(\)|new\s+Random\(\))',
            re.IGNORECASE,
        ),
        "text_regex": re.compile(r'\bPseudoRandom\b|\bweak\s+seed\b', re.IGNORECASE),
    },
]


# Configuration-Specific Pattern Rules (Nginx, Apache, OpenSSL, TLS configs)
CONFIG_RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "CONFIG-TLS-WEAK-VERSION",
        "algorithm": "TLSv1.0/1.1",
        "primitive": "protocol_version",
        "quantum_vulnerable": False,
        "severity": "high",
        "title": "Deprecated TLS Protocol Version Configured",
        "description": "Configuration allows TLS 1.0 or TLS 1.1. Insecure classically and incompatible with post-quantum extensions.",
        "recommended_pqc": "Enforce TLS 1.3 with Hybrid PQC Groups",
        "regex": re.compile(r'(?:ssl_protocols\s+[^;]*(?:TLSv1\.0|TLSv1\.1)|SSLProtocol\s+[^;]*(?:TLSv1|TLSv1\.1))', re.IGNORECASE),
    },
    {
        "rule_id": "CONFIG-RSA-CIPHERSUITE",
        "algorithm": "RSA Key Exchange Cipher Suite",
        "primitive": "key_establishment",
        "quantum_vulnerable": True,
        "severity": "high",
        "title": "Classical RSA/ECDHE Cipher Suite Configured",
        "description": "Configuration specifies classical RSA or ECDHE cipher suites without hybrid post-quantum key exchange support.",
        "recommended_pqc": "Add X25519MLKEM768 to ssl_ecdh_curve / TLS groups",
        "regex": re.compile(r'(?:ssl_ciphers\s+["\']?[^;]*(?:ECDHE-RSA|RSA-AES|DHE-RSA)|ssl_ecdh_curve\s+["\']?(?:prime256v1|secp384r1|auto))', re.IGNORECASE),
    },
    {
        "rule_id": "CONFIG-CERTIFICATE-PATH",
        "algorithm": "X.509 Certificate Reference",
        "primitive": "digital_signature",
        "quantum_vulnerable": True,
        "severity": "medium",
        "title": "Classical Public Certificate Configured",
        "description": "Configuration references an X.509 server certificate file. Must be audited for classical RSA or ECDSA key parameters.",
        "recommended_pqc": "Audit Certificate & Plan Hybrid/PQC Certificate Migration",
        "regex": re.compile(r'(?:ssl_certificate\s+[^;]+\.(?:crt|pem)|SSLCertificateFile\s+[^\n]+\.(?:crt|pem))', re.IGNORECASE),
    },
]


def classify_line_detection(
    line: str,
    file_path: str,
    rule: Dict[str, Any],
) -> Optional[Tuple[str, str, str]]:
    """
    Evaluate a matching line and return:
        (classification_category, confidence, snippet)
    or None if false alarm.
    """
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    is_config_file = ext in ("conf", "cfg", "ini", "yaml", "yml", "json", "toml", "xml", "properties")
    
    # 1. Check if line is purely comment
    if is_comment_or_doc_line(line, ext):
        # Matches in comments are strictly Textual references
        text_regex = rule.get("text_regex")
        if (text_regex and text_regex.search(line)) or (rule.get("api_regex") and rule["api_regex"].search(line)):
            return (CAT_TEXTUAL_REF, "low", redact_secrets(line.strip()))
        return None

    # 2. Check configuration file matches
    if is_config_file:
        return (CAT_CONFIG_EVIDENCE, "high", redact_secrets(line.strip()))

    # 3. Check Confirmed API regex
    api_regex = rule.get("api_regex")
    if api_regex and api_regex.search(line):
        return (CAT_CONFIRMED_API, "high", redact_secrets(line.strip()))

    # 4. Text regex in active code (e.g. variable naming, string literal)
    text_regex = rule.get("text_regex")
    if text_regex and text_regex.search(line):
        return (CAT_MANUAL_VALIDATION, "medium", redact_secrets(line.strip()))

    return None
