import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FolderSearch,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  ArrowRight,
  Loader2,
  FolderTree,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  FileCode,
  Globe,
  Upload,
  RefreshCw,
  StopCircle,
  FileSearch,
  ShieldCheck,
  HardDrive,
} from 'lucide-react';
import {
  startSystemScan,
  fetchSystemScanConfig,
  scanSourceCode,
  scanLiveServer,
} from '../api/scans';
import { getJob, cancelJob } from '../api/jobs';
import { Finding, SystemScanConfig, ScanJob } from '../types';

export const Scanner: React.FC = () => {
  const navigate = useNavigate();

  // -------------------------------------------------------------
  // Automatic System File Scanner State
  // -------------------------------------------------------------
  const [scanConfig, setScanConfig] = useState<SystemScanConfig | null>(null);
  const [scopeType, setScopeType] = useState<'project' | 'custom'>('project');
  const [customPath, setCustomPath] = useState<string>('');
  const [maxSizeMb, setMaxSizeMb] = useState<number>(5);
  const [showAdvancedConfig, setShowAdvancedConfig] = useState<boolean>(false);
  const [activeJob, setActiveJob] = useState<ScanJob | null>(null);
  const [systemScanning, setSystemScanning] = useState<boolean>(false);
  const [systemError, setSystemError] = useState<string | null>(null);
  const [systemSuccess, setSystemSuccess] = useState<boolean>(false);
  const [telemetry, setTelemetry] = useState<{
    files_discovered: number;
    files_scanned: number;
    files_skipped: number;
    files_errored: number;
    findings_count: number;
  }>({
    files_discovered: 0,
    files_scanned: 0,
    files_skipped: 0,
    files_errored: 0,
    findings_count: 0,
  });

  // Polling ref
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  // -------------------------------------------------------------
  // Manual Scanners State (Source upload & TLS probe)
  // -------------------------------------------------------------
  const [manualSectionOpen, setManualSectionOpen] = useState<boolean>(false);
  const [sourceMode, setSourceMode] = useState<'upload' | 'paste'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceCodeText, setSourceCodeText] = useState<string>('');
  const [fileNameInput, setFileNameInput] = useState<string>('sample_service.py');
  const [sourceScanning, setSourceScanning] = useState<boolean>(false);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [sourceSuccess, setSourceSuccess] = useState<boolean>(false);
  const [sourceFindings, setSourceFindings] = useState<Finding[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [hostname, setHostname] = useState<string>('');
  const [port, setPort] = useState<number>(443);
  const [authorized, setAuthorized] = useState<boolean>(false);
  const [serverScanning, setServerScanning] = useState<boolean>(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [serverSuccess, setServerSuccess] = useState<boolean>(false);
  const [serverFindings, setServerFindings] = useState<Finding[]>([]);

  // Load config on mount
  useEffect(() => {
    fetchSystemScanConfig()
      .then((cfg) => {
        setScanConfig(cfg);
        setCustomPath(cfg.project_root || '');
        setMaxSizeMb(cfg.max_file_size_mb || 5);
      })
      .catch((err) => console.error('Failed to load scan config:', err));

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  // Poll active background job
  const pollJobStatus = (jobId: string) => {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    pollTimerRef.current = setInterval(async () => {
      try {
        const job = await getJob(jobId);
        setActiveJob(job);

        // Update telemetry from result_json if available
        if (job.result_json) {
          const res = job.result_json;
          if (res.telemetry) {
            setTelemetry(res.telemetry);
          } else if (res.metadata) {
            setTelemetry({
              files_discovered: res.metadata.files_discovered || 0,
              files_scanned: res.metadata.files_scanned || 0,
              files_skipped: res.metadata.files_skipped || 0,
              files_errored: res.metadata.files_errored || 0,
              findings_count: res.metadata.findings_count || (res.findings?.length || 0),
            });
          }
        }

        if (job.status === 'completed') {
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          setSystemScanning(false);
          setSystemSuccess(true);
        } else if (job.status === 'failed' || job.status === 'cancelled') {
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          setSystemScanning(false);
          if (job.status === 'failed') {
            setSystemError(job.error_message || 'System file scan encountered an error.');
          }
        }
      } catch (err: any) {
        console.error('Job polling error:', err);
      }
    }, 1500);
  };

  // -------------------------------------------------------------
  // Handler: Start One-Click System Scan
  // -------------------------------------------------------------
  const handleStartSystemScan = async () => {
    setSystemError(null);
    setSystemSuccess(false);
    setTelemetry({
      files_discovered: 0,
      files_scanned: 0,
      files_skipped: 0,
      files_errored: 0,
      findings_count: 0,
    });

    const targetDir = scopeType === 'custom' && customPath.trim() ? customPath.trim() : scanConfig?.project_root;

    setSystemScanning(true);
    try {
      const res = await startSystemScan({
        target_scope: scopeType,
        target_directory: targetDir,
        max_file_size_bytes: maxSizeMb * 1024 * 1024,
      });

      setActiveJob(res.job);
      pollJobStatus(res.job_id);
    } catch (err: any) {
      setSystemError(err.message || 'Failed to start system file scan.');
      setSystemScanning(false);
    }
  };

  // Handler: Cancel Active Scan
  const handleCancelScan = async () => {
    if (!activeJob) return;
    try {
      await cancelJob(activeJob.id);
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      setSystemScanning(false);
      setActiveJob((prev) => (prev ? { ...prev, status: 'cancelled' } : null));
    } catch (err: any) {
      console.error('Failed to cancel job:', err);
    }
  };

  // -------------------------------------------------------------
  // Handlers for Manual Single-File / TLS Scans
  // -------------------------------------------------------------
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

  const handleRunServerScan = async () => {
    setServerError(null);
    setServerSuccess(false);

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
      <div className="border-b border-navy-750 pb-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs uppercase tracking-widest font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Automated Discovery Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Quantum Security Scanner</h1>
          <p className="text-xs text-gray-400 mt-1 max-w-2xl">
            Automatically discover cryptographic usage, vulnerable RSA/ECC keys, legacy ciphers, and certificates across authorized project files with real-time risk prioritization.
          </p>
        </div>

        <Link
          to="/findings"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-navy-850 hover:bg-navy-800 border border-navy-750 text-gray-200 text-xs font-semibold transition"
        >
          <FileSearch className="w-4 h-4 text-cyan-400" />
          <span>View All Findings</span>
        </Link>
      </div>

      {/* ========================================================================= */}
      {/* MAIN COMMAND HERO: AUTOMATIC SYSTEM FILE SCANNER */}
      {/* ========================================================================= */}
      <div className="rounded-2xl bg-gradient-to-br from-navy-900 via-navy-850 to-navy-900 border border-cyan-500/30 p-6 md:p-8 shadow-2xl relative overflow-hidden space-y-6">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Header & Status */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-navy-750/80">
          <div className="flex items-start space-x-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/40 text-cyan-300 shadow-lg shadow-cyan-500/10">
              <FolderSearch className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h2 className="text-xl font-bold text-white tracking-tight">Automatic System File Scanner</h2>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  Read-Only Safe
                </span>
              </div>
              <p className="text-xs text-gray-300 mt-1">
                Recursively scans source code (.py, .java, .js, .ts, .c, .go), configurations (.yaml, .conf), and certificates (.pem, .crt) without manual file-by-file upload.
              </p>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex items-center space-x-3">
            {systemScanning ? (
              <button
                type="button"
                onClick={handleCancelScan}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg transition"
              >
                <StopCircle className="w-4 h-4" />
                <span>Cancel Scan</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStartSystemScan}
                className="inline-flex items-center space-x-2.5 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300 text-navy-950 font-bold text-sm shadow-xl shadow-cyan-500/20 transition transform active:scale-95"
              >
                <Play className="w-4 h-4 fill-navy-950" />
                <span>Scan System</span>
              </button>
            )}
          </div>
        </div>

        {/* Scope Selector & Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            onClick={() => setScopeType('project')}
            className={`p-4 rounded-xl border cursor-pointer transition flex items-start space-x-3 ${
              scopeType === 'project'
                ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                : 'bg-navy-950/70 border-navy-750 hover:bg-navy-900'
            }`}
          >
            <HardDrive className={`w-5 h-5 mt-0.5 ${scopeType === 'project' ? 'text-cyan-400' : 'text-gray-400'}`} />
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold text-white">Project Scope (Default)</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  Recommended
                </span>
              </div>
              <p className="text-[11px] text-gray-400 mt-1 font-mono break-all">
                {scanConfig?.project_root || 'Current workspace'}
              </p>
            </div>
          </div>

          <div
            onClick={() => setScopeType('custom')}
            className={`p-4 rounded-xl border cursor-pointer transition flex items-start space-x-3 ${
              scopeType === 'custom'
                ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                : 'bg-navy-950/70 border-navy-750 hover:bg-navy-900'
            }`}
          >
            <FolderTree className={`w-5 h-5 mt-0.5 ${scopeType === 'custom' ? 'text-cyan-400' : 'text-gray-400'}`} />
            <div className="flex-1">
              <span className="text-sm font-semibold text-white">Authorized Custom Directory</span>
              <p className="text-[11px] text-gray-400 mt-0.5">Specify an authorized application folder</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-navy-950/70 border border-navy-750 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">File Size Limit:</span>
              <span className="text-xs font-mono font-bold text-cyan-300">{maxSizeMb} MB</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={maxSizeMb}
              onChange={(e) => setMaxSizeMb(Number(e.target.value))}
              className="w-full accent-cyan-400 mt-2"
            />
            <div className="flex justify-between text-[10px] text-gray-400 font-mono mt-1">
              <span>1 MB</span>
              <span>10 MB</span>
              <span>20 MB</span>
            </div>
          </div>
        </div>

        {/* Custom Path Input if selected */}
        {scopeType === 'custom' && (
          <div className="p-4 rounded-xl bg-navy-950 border border-navy-750 space-y-2">
            <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
              Authorized Target Directory Path:
            </label>
            <input
              type="text"
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              placeholder="e:\path\to\authorized\source"
              className="w-full px-3 py-2 rounded-lg bg-navy-900 border border-navy-700 text-white font-mono text-xs focus:outline-none focus:border-cyan-400"
            />
            <p className="text-[11px] text-gray-400">
              Only accessible directories within approved permissions will be scanned. Symlinks outside the target are skipped.
            </p>
          </div>
        )}

        {/* Advanced Config Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvancedConfig(!showAdvancedConfig)}
            className="inline-flex items-center space-x-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>{showAdvancedConfig ? 'Hide Scope Guardrails' : 'View Scope Guardrails & File Extensions'}</span>
            {showAdvancedConfig ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {showAdvancedConfig && scanConfig && (
            <div className="mt-3 p-4 rounded-xl bg-navy-950 border border-navy-800 text-xs space-y-3 font-mono">
              <div>
                <span className="text-gray-400 block text-[11px]">Included Extensions:</span>
                <span className="text-cyan-300">
                  {scanConfig.supported_extensions?.join(', ')}
                </span>
              </div>
              <div>
                <span className="text-gray-400 block text-[11px]">Excluded Directories (by default):</span>
                <span className="text-gray-300">
                  {scanConfig.excluded_directories?.join(', ')}
                </span>
              </div>
              <div className="text-[11px] text-emerald-400">
                Guards: Read-only traversal, zero code execution, private key disclosure protection active.
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {systemError && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start space-x-3 text-xs text-rose-300">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
            <span>{systemError}</span>
          </div>
        )}

        {/* ========================================================================= */}
        {/* LIVE SCAN TELEMETRY CARD */}
        {/* ========================================================================= */}
        {(systemScanning || activeJob || systemSuccess) && (
          <div className="p-5 rounded-xl bg-navy-950 border border-cyan-500/30 space-y-4 animate-fade-in shadow-inner">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center space-x-2">
                {systemScanning ? (
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                ) : systemSuccess ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400" />
                )}
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                  Job {activeJob?.id || 'Running'}:{' '}
                  <span
                    className={
                      systemScanning
                        ? 'text-cyan-400'
                        : systemSuccess
                        ? 'text-emerald-400'
                        : 'text-amber-400'
                    }
                  >
                    {activeJob?.status || 'Active'}
                  </span>
                </span>
              </div>

              <span className="text-xs font-mono text-gray-400">
                Progress: <strong className="text-white">{activeJob?.progress || 0}%</strong>
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-2 rounded-full bg-navy-800 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  systemSuccess
                    ? 'bg-emerald-400'
                    : 'bg-gradient-to-r from-cyan-500 to-violet-500'
                }`}
                style={{ width: `${Math.max(5, activeJob?.progress || 0)}%` }}
              />
            </div>

            {/* Telemetry Counter Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
              <div className="p-3 rounded-lg bg-navy-900 border border-navy-800 text-center">
                <span className="text-[10px] text-gray-400 block uppercase font-mono">Discovered</span>
                <span className="text-lg font-bold text-white font-mono">{telemetry.files_discovered}</span>
              </div>
              <div className="p-3 rounded-lg bg-navy-900 border border-navy-800 text-center">
                <span className="text-[10px] text-gray-400 block uppercase font-mono">Scanned</span>
                <span className="text-lg font-bold text-cyan-400 font-mono">{telemetry.files_scanned}</span>
              </div>
              <div className="p-3 rounded-lg bg-navy-900 border border-navy-800 text-center">
                <span className="text-[10px] text-gray-400 block uppercase font-mono">Skipped</span>
                <span className="text-lg font-bold text-gray-300 font-mono">{telemetry.files_skipped}</span>
              </div>
              <div className="p-3 rounded-lg bg-navy-900 border border-navy-800 text-center">
                <span className="text-[10px] text-gray-400 block uppercase font-mono">Errors</span>
                <span className={`text-lg font-bold font-mono ${telemetry.files_errored > 0 ? 'text-amber-400' : 'text-gray-400'}`}>
                  {telemetry.files_errored}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-navy-900 border border-navy-800 text-center">
                <span className="text-[10px] text-gray-400 block uppercase font-mono">Findings</span>
                <span className={`text-lg font-bold font-mono ${telemetry.findings_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {telemetry.findings_count}
                </span>
              </div>
            </div>

            {/* Post-Scan Fix First Banner */}
            {systemSuccess && (
              <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-cyan-950/80 via-navy-900 to-navy-950 border border-cyan-500/40 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2 text-cyan-300 font-semibold text-xs">
                    <ShieldAlert className="w-4 h-4 text-cyan-400" />
                    <span>System Scan Completed Successfully</span>
                  </div>
                  <p className="text-[11px] text-gray-300">
                    Discovered {telemetry.findings_count} cryptographic findings prioritized by explainable risk score.
                  </p>
                </div>
                <Link
                  to="/findings"
                  className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold text-xs inline-flex items-center space-x-1.5 transition flex-shrink-0"
                >
                  <span>Open Prioritized Findings</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* SECONDARY / TARGETED PROBES (Collapsible) */}
      {/* ========================================================================= */}
      <div className="border border-navy-750/80 rounded-2xl bg-navy-950/50 overflow-hidden">
        <button
          type="button"
          onClick={() => setManualSectionOpen(!manualSectionOpen)}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-navy-900/60 transition"
        >
          <div className="flex items-center space-x-3">
            <SlidersHorizontal className="w-4 h-4 text-gray-400" />
            <div>
              <h3 className="text-sm font-semibold text-white">Targeted Probing & Manual Analysis</h3>
              <p className="text-xs text-gray-400">Inspect single uploaded files, pasted code, or live TLS servers</p>
            </div>
          </div>
          {manualSectionOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </button>

        {manualSectionOpen && (
          <div className="p-6 border-t border-navy-750/70 grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* 1. Single File Upload / Paste */}
            <div className="rounded-xl bg-navy-850 border border-navy-750 p-5 space-y-4">
              <div className="flex items-center space-x-2.5 pb-2 border-b border-navy-750">
                <FileCode className="w-5 h-5 text-cyan-400" />
                <h4 className="text-sm font-semibold text-white">Inspect Single Code Snippet</h4>
              </div>

              <div className="flex rounded-lg bg-navy-950 p-1 border border-navy-800">
                <button
                  type="button"
                  onClick={() => setSourceMode('upload')}
                  className={`flex-1 py-1 px-3 text-xs font-medium rounded-md transition ${
                    sourceMode === 'upload' ? 'bg-cyan-500/20 text-cyan-300' : 'text-gray-400'
                  }`}
                >
                  File Upload
                </button>
                <button
                  type="button"
                  onClick={() => setSourceMode('paste')}
                  className={`flex-1 py-1 px-3 text-xs font-medium rounded-md transition ${
                    sourceMode === 'paste' ? 'bg-cyan-500/20 text-cyan-300' : 'text-gray-400'
                  }`}
                >
                  Paste Code
                </button>
              </div>

              {sourceMode === 'upload' ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-navy-750 hover:border-cyan-500/40 rounded-xl p-6 text-center cursor-pointer transition bg-navy-950/60"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                  <Upload className="w-6 h-6 text-gray-400 mx-auto mb-2" />
                  <span className="text-xs text-white block font-medium">
                    {selectedFile ? selectedFile.name : 'Select code file to inspect'}
                  </span>
                </div>
              ) : (
                <textarea
                  rows={4}
                  value={sourceCodeText}
                  onChange={(e) => setSourceCodeText(e.target.value)}
                  placeholder="Paste Python, Java, or C/C++ code here..."
                  className="w-full p-2.5 rounded-lg bg-navy-950 border border-navy-750 text-white font-mono text-xs focus:outline-none focus:border-cyan-400"
                />
              )}

              {sourceError && <p className="text-xs text-rose-400">{sourceError}</p>}
              {sourceSuccess && (
                <p className="text-xs text-emerald-400">Scan complete: {sourceFindings.length} findings discovered.</p>
              )}

              <button
                type="button"
                disabled={sourceScanning}
                onClick={handleRunSourceScan}
                className="w-full py-2 rounded-lg bg-navy-900 hover:bg-navy-800 border border-navy-700 text-cyan-300 text-xs font-semibold transition"
              >
                {sourceScanning ? 'Scanning...' : 'Inspect Snippet'}
              </button>
            </div>

            {/* 2. Live Server TLS Probing */}
            <div className="rounded-xl bg-navy-850 border border-navy-750 p-5 space-y-4">
              <div className="flex items-center space-x-2.5 pb-2 border-b border-navy-750">
                <Globe className="w-5 h-5 text-violet-400" />
                <h4 className="text-sm font-semibold text-white">Live Server TLS Handshake</h4>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="text-[11px] text-gray-400 block mb-1">Target Hostname:</label>
                  <input
                    type="text"
                    value={hostname}
                    onChange={(e) => setHostname(e.target.value)}
                    placeholder="api.example.com"
                    className="w-full px-3 py-1.5 rounded-lg bg-navy-950 border border-navy-750 text-white font-mono text-xs focus:outline-none focus:border-violet-400"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Port:</label>
                  <input
                    type="number"
                    value={port}
                    onChange={(e) => setPort(Number(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg bg-navy-950 border border-navy-750 text-white font-mono text-xs focus:outline-none"
                  />
                </div>
              </div>

              <label className="flex items-center space-x-2 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={authorized}
                  onChange={(e) => setAuthorized(e.target.checked)}
                  className="rounded border-navy-700 text-violet-500 focus:ring-0"
                />
                <span className="text-[11px] text-gray-300">I confirm explicit authorization to inspect this target.</span>
              </label>

              {serverError && <p className="text-xs text-rose-400">{serverError}</p>}
              {serverSuccess && (
                <p className="text-xs text-emerald-400">TLS scan complete: {serverFindings.length} findings discovered.</p>
              )}

              <button
                type="button"
                disabled={serverScanning}
                onClick={handleRunServerScan}
                className="w-full py-2 rounded-lg bg-navy-900 hover:bg-navy-800 border border-navy-700 text-violet-300 text-xs font-semibold transition"
              >
                {serverScanning ? 'Probing Handshake...' : 'Inspect TLS Server'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
