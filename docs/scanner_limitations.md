# Scanner Limitations & Evidence Interpretation

1. **Static Analysis Limitations**: Pattern and AST matching cannot determine whether a detected cryptographic library is actively executed in production code paths.
2. **Cipher Suite Inference**: Observing a cipher suite in a TLS handshake indicates server support, but does not prove exclusive usage for all historical client connections.
3. **Not a Proof of Compromise**: The presence of RSA-2048 or ECC-P256 is an indicator of future quantum risk under Shor's algorithm, not an ongoing compromise or active breach.
