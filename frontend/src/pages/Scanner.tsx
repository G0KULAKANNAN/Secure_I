import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Code,
  Globe,
  Upload,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
  ShieldCheck,
  ArrowRight,
  Info,
  Loader2,
  KeyRound,
  FileCode,
} from 'lucide-react';
import { scanSourceCode, scanLiveServer } from '../api/scans';
import { Finding } from '../types';

export const Scanner: React.FC = () => {
  // Source Code Scanner State
  const [sourceMode, setSourceMode] = useState<'upload' | 'paste'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceCodeText, setSourceCodeText] = useState<string>('');
  const [fileNameInput, setFileNameInput] = useState<string>('sample_service.py');
  const [sourceScanning, setSourceScanning] = useState<boolean>(false);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [sourceSuccess, setSourceSuccess] = useState<boolean>(false);
  const [sourceFindings, setSourceFindings] = useState<Finding[]>([]);
  const [dragOver, setDragOver] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Live Server Scanner State
  const [hostname, setHostname] = useState<string>('');
  const [port, setPort] = useState<number>(443);
  const [authorized, setAuthorized] = useState<boolean>(false);
  const [serverScanning, setServerScanning] = useState<boolean>(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [serverSuccess, setServerSuccess] = useState<boolean>(false);
  const [serverFindings, setServerFindings] = useState<Finding[]>([]);
  const [tlsMetadata, setTlsMetadata] = useState<Record<string, any> | null>(null);

  // Handlers for Source Code Scan
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setSourceError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setSourceError(null);
    }
  };

  const handleRunSourceScan = async () => {
    setSourceError(null);
    setSourceSuccess(false);

    if (sourceMode === 'upload' && !selectedFile) {
      setSourceError('Please select a file to scan.');
      return;
    }
    if (sourceMode === 'paste' && !sourceCodeText.trim()) {
      setSourceError('Please paste source code content to scan.');
      return;
    }

    setSourceScanning(true);
    try {
      const res = await scanSourceCode({
        file: sourceMode === 'upload' && selectedFile ? selectedFile : undefined,
        source_content: sourceMode === 'paste' ? sourceCodeText : undefined,
        file_name: sourceMode === 'upload' && selectedFile ? selectedFile.name : fileNameInput,
      });

      setSourceFindings(res.findings || []);
      setSourceSuccess(true);
    } catch (err: any) {
      setSourceError(err.message || 'Failed to scan source code.');
    } finally {
      setSourceScanning(false);
    }
  };

  // Handlers for Live Server Scan
  const handleRunServerScan = async () => {
    setServerError(null);
    setServerSuccess(false);
    setTlsMetadata(null);

    if (!hostname.trim()) {
      setServerError('Please provide a target hostname or IP address.');
      return;
    }
    if (!authorized) {
      setServerError('You must confirm that you are authorized to scan this target.');
      return;
    }

    setServerScanning(true);
    try {
      const res = await scanLiveServer({
        hostname: hostname.trim(),
        port: port || 443,
        authorized: true,
      });

      setServerFindings(res.findings || []);
      setTlsMetadata(res.scan_result?.metadata || null);
      setServerSuccess(true);
    } catch (err: any) {
      setServerError(err.message || 'Failed to inspect server TLS handshake.');
    } finally {
      setServerScanning(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="border-b border-navy-750 pb-5">
        <h1 className="text-2xl font-bold text-white tracking-tight">Quantum Security Scanner</h1>
        <p className="text-sm text-gray-400 mt-1">
          Scan application code, configurations, and live network servers to discover quantum-vulnerable cryptography (RSA, ECC, classical Diffie-Hellman) and plan NIST PQC migration.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* ========================================================================= */}
        {/* CARD 1: Scan Source Code & Configurations */}
        {/* ========================================================================= */}
        <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-navy-750">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <FileCode className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">1. Scan Source Code</h2>
                <p className="text-xs text-gray-400">Inspect code and configuration files for classical algorithms</p>
              </div>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-navy-950 text-cyan-300 border border-navy-800">
              Safe Static
            </span>
          </div>

          {/* Mode Switcher (Upload vs Paste) */}
          <div className="flex rounded-lg bg-navy-950 p-1 border border-navy-800">
            <button
              type="button"
              onClick={() => { setSourceMode('upload'); setSourceError(null); }}
              className={`flex-1 py-1.5 px-3 text-xs font-medium rounded-md transition ${
                sourceMode === 'upload'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Upload File
            </button>
            <button
              type="button"
              onClick={() => { setSourceMode('paste'); setSourceError(null); }}
              className={`flex-1 py-1.5 px-3 text-xs font-medium rounded-md transition ${
                sourceMode === 'paste'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Paste Code Snippet
            </button>
          </div>

          {sourceMode === 'upload' ? (
            /* File Upload Dropzone */
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
                dragOver
                  ? 'border-cyan-400 bg-cyan-500/10'
                  : selectedFile
                  ? 'border-emerald-500/50 bg-emerald-500/5'
                  : 'border-navy-700 hover:border-cyan-500/40 bg-navy-900/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept=".py,.java,.js,.ts,.tsx,.go,.c,.cpp,.cs,.yml,.yaml,.conf,.pem,.crt"
              />
              <Upload className={`w-8 h-8 mx-auto mb-2 ${selectedFile ? 'text-emerald-400' : 'text-gray-400'}`} />
              {selectedFile ? (
                <div>
                  <p className="text-sm font-semibold text-emerald-300 font-mono">{selectedFile.name}</p>
                  <p className="text-xs text-gray-400 mt-1">{(selectedFile.size / 1024).toFixed(1)} KB — Click to choose different file</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium text-gray-200">Drag & drop source or config file here</p>
                  <p className="text-xs text-gray-400 mt-1">Supports Python, Java, JS/TS, Go, C/C++, YAML, Conf, PEM certificates (Max 2MB)</p>
                </div>
              )}
            </div>
          ) : (
            /* Code Paste Area */
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <label className="text-xs text-gray-400">File Name / Context:</label>
                <input
                  type="text"
                  value={fileNameInput}
                  onChange={(e) => setFileNameInput(e.target.value)}
                  className="flex-1 bg-navy-950 border border-navy-750 rounded px-2.5 py-1 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
                  placeholder="e.g. auth_service.py or nginx.conf"
                />
              </div>
              <textarea
                rows={7}
                value={sourceCodeText}
                onChange={(e) => setSourceCodeText(e.target.value)}
                placeholder="// Paste cryptographic code, key generation, or TLS cipher configuration..."
                className="w-full bg-navy-950 border border-navy-750 rounded-xl p-3 text-xs text-gray-200 font-mono focus:border-cyan-500 focus:outline-none leading-relaxed resize-y"
              />
            </div>
          )}

          {sourceError && (
            <div className="flex items-center space-x-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{sourceError}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-gray-400 flex items-center space-x-1">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              <span>Non-executing static analysis</span>
            </span>

            <button
              type="button"
              disabled={sourceScanning}
              onClick={handleRunSourceScan}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-navy-950 font-semibold text-xs tracking-wide transition shadow-lg shadow-cyan-500/20"
            >
              {sourceScanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Scanning Code...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Scan Files</span>
                </>
              )}
            </button>
          </div>

          {/* Results Display */}
          {sourceSuccess && (
            <div className="mt-4 pt-4 border-t border-navy-750 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white uppercase tracking-wider">
                  Scan Results ({sourceFindings.length} {sourceFindings.length === 1 ? 'Finding' : 'Findings'})
                </span>
                <Link to="/findings" className="text-xs text-cyan-400 hover:underline inline-flex items-center space-x-1">
                  <span>View All in Findings</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {sourceFindings.length === 0 ? (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center space-x-3 text-xs text-emerald-300">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
                  <span>No quantum-vulnerable cryptographic patterns detected in this file.</span>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-navy-750">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-navy-950 text-gray-400 font-mono text-[11px] border-b border-navy-750">
                      <tr>
                        <th className="py-2.5 px-3">File : Line</th>
                        <th className="py-2.5 px-3">Detected Algorithm</th>
                        <th className="py-2.5 px-3">Evidence</th>
                        <th className="py-2.5 px-3">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-750/60 bg-navy-900/60 font-mono text-[11px]">
                      {sourceFindings.map((f, idx) => (
                        <tr key={idx} className="hover:bg-navy-800/50">
                          <td className="py-2.5 px-3 text-gray-300">
                            {f.file_path || 'snippet'}:{f.line_number || 1}
                          </td>
                          <td className="py-2.5 px-3 font-semibold text-amber-300">
                            {f.algorithm}
                          </td>
                          <td className="py-2.5 px-3 text-gray-400 truncate max-w-[180px]" title={f.evidence}>
                            {f.evidence}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-300 border border-amber-500/20">
                              Needs verification
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ========================================================================= */}
        {/* CARD 2: Scan Live Server (TLS Handshake) */}
        {/* ========================================================================= */}
        <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-navy-750">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
                <Globe className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">2. Scan Live Server</h2>
                <p className="text-xs text-gray-400">Live TLS handshake inspection on authorized hosts</p>
              </div>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-navy-950 text-violet-300 border border-navy-800">
              Live TLS
            </span>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2 space-y-1">
                <label className="text-xs text-gray-300 font-medium">Hostname or IP Address</label>
                <input
                  type="text"
                  value={hostname}
                  onChange={(e) => { setHostname(e.target.value); setServerError(null); }}
                  placeholder="e.g. scanme.nmap.org or example.com"
                  className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-gray-500 font-mono focus:border-violet-500 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-gray-300 font-medium">Port</label>
                <input
                  type="number"
                  value={port}
                  onChange={(e) => setPort(parseInt(e.target.value, 10) || 443)}
                  className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3.5 py-2.5 text-xs text-white font-mono focus:border-violet-500 focus:outline-none"
                  placeholder="443"
                />
              </div>
            </div>

            {/* Authorisation Confirmation Checkbox */}
            <div className="p-3.5 rounded-xl bg-navy-950/80 border border-navy-800 flex items-start space-x-3">
              <input
                id="auth-checkbox"
                type="checkbox"
                checked={authorized}
                onChange={(e) => { setAuthorized(e.target.checked); setServerError(null); }}
                className="mt-1 h-4 w-4 rounded border-navy-700 bg-navy-900 text-violet-500 focus:ring-violet-500 focus:ring-offset-navy-950"
              />
              <label htmlFor="auth-checkbox" className="text-xs text-gray-300 leading-relaxed cursor-pointer select-none">
                I confirm that I own or have written authorization to perform non-destructive TLS inspection on this server.
              </label>
            </div>
          </div>

          {serverError && (
            <div className="flex items-center space-x-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              <span>{serverError}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-gray-400 flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-violet-400" />
              <span>SSRF protected & passive handshake only</span>
            </span>

            <button
              type="button"
              disabled={serverScanning || !authorized || !hostname.trim()}
              onClick={handleRunServerScan}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white font-semibold text-xs tracking-wide transition shadow-lg shadow-violet-600/20"
            >
              {serverScanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Connecting & Inspecting...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Scan Server</span>
                </>
              )}
            </button>
          </div>

          {/* Results Display */}
          {serverSuccess && (
            <div className="mt-4 pt-4 border-t border-navy-750 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white uppercase tracking-wider">
                  Handshake Diagnostics
                </span>
                <Link to="/findings" className="text-xs text-violet-400 hover:underline inline-flex items-center space-x-1">
                  <span>View in Findings</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Handshake Details Card */}
              {tlsMetadata && (
                <div className="rounded-xl bg-navy-950 p-4 border border-navy-800 space-y-2.5 text-xs font-mono">
                  <div className="flex justify-between items-center pb-2 border-b border-navy-800">
                    <span className="text-gray-400">Target:</span>
                    <span className="text-white font-semibold">{hostname}:{port}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">TLS Protocol:</span>
                    <span className="text-cyan-300 font-semibold">{tlsMetadata.tls_version || 'TLS 1.3 / 1.2'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Cipher Suite:</span>
                    <span className="text-amber-300 truncate max-w-[220px]" title={tlsMetadata.cipher_suite}>
                      {tlsMetadata.cipher_suite || 'Standard Cipher Suite'}
                    </span>
                  </div>
                  {tlsMetadata.cert_public_key_algorithm && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Certificate Key:</span>
                      <span className="text-rose-400 font-semibold">
                        {tlsMetadata.cert_public_key_algorithm} ({tlsMetadata.cert_key_size || 2048} bits)
                      </span>
                    </div>
                  )}
                  {tlsMetadata.quantum_vulnerable && (
                    <div className="pt-2 border-t border-navy-800 text-[11px] text-rose-300 font-sans leading-relaxed">
                      ⚠️ <strong>Vulnerability:</strong> Classical key exchange & RSA/ECC certificates are susceptible to Harvest Now, Decrypt Later (HNDL). Migrate to NIST FIPS 203 (ML-KEM) hybrid key exchange.
                    </div>
                  )}
                </div>
              )}

              {serverFindings.length > 0 && (
                <div className="overflow-x-auto rounded-xl border border-navy-750">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-navy-950 text-gray-400 font-mono text-[11px] border-b border-navy-750">
                      <tr>
                        <th className="py-2.5 px-3">Algorithm</th>
                        <th className="py-2.5 px-3">Evidence</th>
                        <th className="py-2.5 px-3">Recommended PQC</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-750/60 bg-navy-900/60 font-mono text-[11px]">
                      {serverFindings.map((f, idx) => (
                        <tr key={idx} className="hover:bg-navy-800/50">
                          <td className="py-2.5 px-3 font-semibold text-rose-400">
                            {f.algorithm}
                          </td>
                          <td className="py-2.5 px-3 text-gray-400 truncate max-w-[180px]" title={f.evidence}>
                            {f.evidence}
                          </td>
                          <td className="py-2.5 px-3 text-cyan-300">
                            {f.recommended_pqc}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Guidance Link Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-navy-850 via-navy-800 to-navy-850 border border-navy-750 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <KeyRound className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Understand NIST Post-Quantum Standards</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Learn how FIPS 203 (ML-KEM) replaces Diffie-Hellman and FIPS 204 (ML-DSA) replaces RSA/ECDSA signatures.
            </p>
          </div>
        </div>
        <Link
          to="/migration"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-navy-900 hover:bg-navy-750 border border-navy-700 text-cyan-300 text-xs font-medium transition"
        >
          <span>Open Migration Guide</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};
