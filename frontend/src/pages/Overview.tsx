import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Server,
  Radar,
  FileSearch,
  AlertTriangle,
  GitPullRequest,
  CheckCircle2,
  Clock,
  Sparkles,
  Info,
  ArrowRight,
  TrendingUp,
  Activity,
  Layers,
} from 'lucide-react';
import { fetchHealth, fetchVersion } from '../api/client';
import { fetchFindingStats, fetchScanRuns } from '../api/scans';
import { HealthStatus, SystemVersion, FindingStats, ScanRun } from '../types';
import { LoadingState } from '../components/common/LoadingState';

export const Overview: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [version, setVersion] = useState<SystemVersion | null>(null);
  const [stats, setStats] = useState<FindingStats | null>(null);
  const [scanRuns, setScanRuns] = useState<ScanRun[]>([]);
  const [totalScans, setTotalScans] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    Promise.all([
      fetchHealth().catch(() => null),
      fetchVersion().catch(() => null),
      fetchFindingStats().catch(() => null),
      fetchScanRuns(5, 0).catch(() => null),
    ]).then(([h, v, s, r]) => {
      setHealth(h);
      setVersion(v);
      setStats(s);
      if (r) {
        setScanRuns(r.scan_runs || []);
        setTotalScans(r.total || 0);
      }
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <LoadingState message="Loading QuantumShield dashboard..." />;
  }

  const totalFindings = stats?.total_findings ?? stats?.total ?? 0;
  const highPriority = (stats?.critical ?? 0) + (stats?.high ?? 0);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* ========================================================================= */}
      {/* 1. Quick Action Banner */}
      {/* ========================================================================= */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-navy-850 via-navy-800 to-navy-850 border border-navy-750 p-6 md:p-8 shadow-xl">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-mono">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Post-Quantum Cryptography Audit Platform</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              Start a scan to discover quantum-vulnerable cryptography
            </h1>
            <p className="text-sm text-gray-300 leading-relaxed">
              Identify legacy RSA, Elliptic Curve, and Diffie-Hellman algorithms across source code, config files, and live network servers before Cryptanalytically Relevant Quantum Computers (CRQCs) emerge.
            </p>
          </div>

          <div className="flex-shrink-0">
            <Link
              to="/scan"
              className="inline-flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold text-sm tracking-wide transition shadow-lg shadow-cyan-500/25 hover:scale-105"
            >
              <Radar className="w-5 h-5" />
              <span>Launch New Scan</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. Four Main Metric Cards (Real Database Data) */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Targets Scanned */}
        <div className="p-5 rounded-2xl bg-navy-850 border border-navy-750 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Targets Scanned</span>
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Server className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono">{totalScans}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>Executed scan runs</span>
          </div>
        </div>

        {/* Metric 2: Cryptographic Findings */}
        <div className="p-5 rounded-2xl bg-navy-850 border border-navy-750 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Cryptographic Findings</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <FileSearch className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-amber-300 font-mono">{totalFindings}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1">
            <span>Quantum-vulnerable:</span>
            <span className="text-amber-400 font-mono font-semibold">{stats?.quantum_vulnerable ?? 0}</span>
          </div>
        </div>

        {/* Metric 3: High-Priority Reviews */}
        <div className="p-5 rounded-2xl bg-navy-850 border border-navy-750 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">High-Priority Reviews</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-rose-400 font-mono">{highPriority}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1">
            <span>Critical:</span>
            <span className="text-rose-400 font-mono font-semibold">{stats?.critical ?? 0}</span>
            <span className="mx-1">•</span>
            <span>High:</span>
            <span className="text-orange-400 font-mono font-semibold">{stats?.high ?? 0}</span>
          </div>
        </div>

        {/* Metric 4: Recent Scans */}
        <div className="p-5 rounded-2xl bg-navy-850 border border-navy-750 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Recent Scans</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-white font-mono">{scanRuns.length}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1">
            <span className="text-emerald-400 font-semibold">{scanRuns.filter(r => r.status === 'completed').length} completed</span>
            <span>in latest batch</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. Recent Scans Table (Zero Mock Data) */}
      {/* ========================================================================= */}
      <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-navy-750">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent Scan Activity</h2>
            <p className="text-xs text-gray-400">Past scan executions recorded persistently in SQLite database</p>
          </div>
          <Link
            to="/scan"
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center space-x-1"
          >
            <span>Run New Scan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {scanRuns.length === 0 ? (
          <div className="py-12 text-center space-y-3">
            <div className="p-3 w-12 h-12 mx-auto rounded-full bg-navy-950 border border-navy-800 text-gray-500 flex items-center justify-center">
              <Radar className="w-6 h-6" />
            </div>
            <p className="text-sm text-gray-300 font-medium">No scan runs recorded yet</p>
            <p className="text-xs text-gray-500 max-w-md mx-auto">
              Scan your source files or network servers using the Scanner to populate audit data and discovery findings.
            </p>
            <Link
              to="/scan"
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-semibold text-xs tracking-wide transition mt-2"
            >
              <Radar className="w-3.5 h-3.5" />
              <span>Perform First Scan</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-navy-750">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-950 text-gray-400 font-mono text-[11px] border-b border-navy-750">
                <tr>
                  <th className="py-3 px-4">Scan ID</th>
                  <th className="py-3 px-4">Target Asset</th>
                  <th className="py-3 px-4">Scanners</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Jobs</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-750/60 bg-navy-900/60 font-mono text-[11px]">
                {scanRuns.map((r) => {
                  const statusColors: Record<string, string> = {
                    completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
                    running: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
                    queued: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                    failed: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
                    cancelled: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
                  };

                  return (
                    <tr key={r.id} className="hover:bg-navy-800/50">
                      <td className="py-3 px-4 font-semibold text-white">{r.id}</td>
                      <td className="py-3 px-4 text-gray-300">{r.asset_id}</td>
                      <td className="py-3 px-4 text-cyan-300">
                        {Array.isArray(r.requested_scanners)
                          ? r.requested_scanners.join(', ')
                          : r.requested_scanners}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium border ${
                            statusColors[r.status] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-400">
                        {r.completed_jobs} / {r.total_jobs}
                      </td>
                      <td className="py-3 px-4 text-gray-400">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 4. Educational Quantum Risk Disclaimer */}
      {/* ========================================================================= */}
      <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 p-5 flex items-start space-x-4">
        <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs leading-relaxed">
          <h4 className="font-semibold text-amber-300 text-sm">
            Defensive Cryptographic Risk Assessment Notice
          </h4>
          <p className="text-amber-200/90">
            • Detection of classical algorithms (RSA, ECC, Diffie-Hellman) indicates future exposure to Shor's algorithm on Cryptanalytically Relevant Quantum Computers (CRQC).<br />
            • QuantumShield performs non-destructive discovery and provides NIST FIPS 203/204 migration guidance to protect against <em>Store Now, Decrypt Later (SNDL)</em> attacks.
          </p>
        </div>
      </div>
    </div>
  );
};
