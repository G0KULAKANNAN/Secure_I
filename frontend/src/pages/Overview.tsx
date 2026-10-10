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
  Sliders,
  AlertOctagon,
  ChevronRight,
  ShieldCheck,
  Zap,
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
      {/* 1. Hero Action Banner */}
      {/* ========================================================================= */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-navy-900 via-navy-850 to-navy-900 border border-navy-750/80 p-6 md:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-gradient-to-br from-cyan-500/10 to-violet-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-mono font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              <span>NIST FIPS 203 / 204 Migration Platform</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Cryptographic Exposure Discovery & Post-Quantum Rollout
            </h1>
            <p className="text-sm md:text-base text-gray-300 leading-relaxed">
              Discover quantum-vulnerable cryptography across source code and live network servers, validate hybrid key encapsulation in staging, and coordinate controlled canary production deployments.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            <Link
              to="/scan"
              className="inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300 text-navy-950 font-bold text-sm tracking-wide transition shadow-lg shadow-cyan-500/25 hover:scale-[1.02] active:scale-[0.98]"
            >
              <Radar className="w-4 h-4" />
              <span>Launch New Scan</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
            <Link
              to="/rollout-center"
              className="inline-flex items-center justify-center space-x-2 px-5 py-3.5 rounded-xl bg-navy-800/90 hover:bg-navy-750 text-white font-semibold text-sm border border-navy-700 transition"
            >
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Rollout Center</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. Four Main Metric Cards */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Targets Scanned */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-navy-850 to-navy-900 border border-navy-750/90 space-y-3 shadow-lg hover:border-cyan-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold font-mono">Targets Scanned</span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm">
              <Server className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white font-mono tracking-tight">{totalScans}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1.5 pt-1 border-t border-navy-750/60">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>Audited targets & jobs</span>
          </div>
        </div>

        {/* Metric 2: Cryptographic Findings */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-navy-850 to-navy-900 border border-navy-750/90 space-y-3 shadow-lg hover:border-amber-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold font-mono">Crypto Findings</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm">
              <FileSearch className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-amber-300 font-mono tracking-tight">{totalFindings}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1.5 pt-1 border-t border-navy-750/60">
            <span className="text-gray-400">Quantum-vulnerable:</span>
            <span className="text-amber-400 font-mono font-bold">{stats?.quantum_vulnerable ?? 0}</span>
          </div>
        </div>

        {/* Metric 3: High-Priority Reviews */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-navy-850 to-navy-900 border border-navy-750/90 space-y-3 shadow-lg hover:border-rose-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold font-mono">High-Risk Exposure</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 shadow-sm">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-rose-400 font-mono tracking-tight">{highPriority}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1.5 pt-1 border-t border-navy-750/60">
            <span>Critical:</span>
            <span className="text-rose-400 font-mono font-bold">{stats?.critical ?? 0}</span>
            <span className="text-gray-600">•</span>
            <span>High:</span>
            <span className="text-orange-400 font-mono font-bold">{stats?.high ?? 0}</span>
          </div>
        </div>

        {/* Metric 4: Recent Scans */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-navy-850 to-navy-900 border border-navy-750/90 space-y-3 shadow-lg hover:border-emerald-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold font-mono">Recent Batch Scans</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white font-mono tracking-tight">{scanRuns.length}</div>
          <div className="text-xs text-gray-400 flex items-center space-x-1.5 pt-1 border-t border-navy-750/60">
            <span className="text-emerald-400 font-bold">{scanRuns.filter(r => r.status === 'completed').length} completed</span>
            <span>in current run</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. PQC Operations Hub - Quick Access Matrix */}
      {/* ========================================================================= */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white tracking-wide flex items-center space-x-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            <span>PQC Migration Operations Hub</span>
          </h2>
          <span className="text-xs text-gray-400 font-mono">End-to-End Post-Quantum Lifecycle</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Hub Card 1: Hybrid Staging Lab */}
          <Link
            to="/hybrid-lab"
            className="group p-5 rounded-2xl bg-gradient-to-br from-navy-850 to-navy-900 border border-navy-750/90 hover:border-cyan-500/50 transition-all hover:shadow-xl hover:shadow-cyan-500/5 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:scale-110 transition-transform">
                <Layers className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                Stage 2 Staging
              </span>
            </div>
            <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
              Hybrid Cryptography Lab
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Configure and test dual-layer key exchanges (<span className="text-cyan-300 font-mono">X25519MLKEM768</span>) with transparent host OpenSSL capability checks.
            </p>
            <div className="flex items-center text-xs text-cyan-400 font-semibold group-hover:translate-x-1 transition-transform pt-1">
              <span>Open Staging Lab</span>
              <ChevronRight className="w-4 h-4 ml-0.5" />
            </div>
          </Link>

          {/* Hub Card 2: Rollout Center */}
          <Link
            to="/rollout-center"
            className="group p-5 rounded-2xl bg-gradient-to-br from-navy-850 to-navy-900 border border-navy-750/90 hover:border-indigo-500/50 transition-all hover:shadow-xl hover:shadow-indigo-500/5 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:scale-110 transition-transform">
                <Sliders className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800">
                Stage 4 Production
              </span>
            </div>
            <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
              Staged Rollout Center
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Progressive canary controller (1% → 5% → 25% → 50% → 100%) with 9-point readiness evaluation and automated rollback safeguards.
            </p>
            <div className="flex items-center text-xs text-indigo-400 font-semibold group-hover:translate-x-1 transition-transform pt-1">
              <span>Manage Rollouts</span>
              <ChevronRight className="w-4 h-4 ml-0.5" />
            </div>
          </Link>

          {/* Hub Card 3: Retirement Center */}
          <Link
            to="/retirement-center"
            className="group p-5 rounded-2xl bg-gradient-to-br from-navy-850 to-navy-900 border border-navy-750/90 hover:border-rose-500/50 transition-all hover:shadow-xl hover:shadow-rose-500/5 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 group-hover:scale-110 transition-transform">
                <AlertOctagon className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800">
                Stage 5 Governance
              </span>
            </div>
            <h3 className="text-base font-bold text-white group-hover:text-rose-300 transition-colors">
              Decommissioning Center
            </h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Catalog cryptographic dependencies, enforce deprecation policies, evaluate 10-point readiness, and retire legacy classical algorithms.
            </p>
            <div className="flex items-center text-xs text-rose-400 font-semibold group-hover:translate-x-1 transition-transform pt-1">
              <span>View Decommissioning</span>
              <ChevronRight className="w-4 h-4 ml-0.5" />
            </div>
          </Link>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 4. Recent Scans Table */}
      {/* ========================================================================= */}
      <div className="rounded-2xl bg-navy-850/90 border border-navy-750/90 p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-navy-750">
          <div>
            <h2 className="text-lg font-bold text-white">Recent Audit Scans</h2>
            <p className="text-xs text-gray-400">Scan executions recorded persistently in SQLite database</p>
          </div>
          <Link
            to="/scan"
            className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold inline-flex items-center space-x-1"
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
              Scan your source files or authorized network servers using the Scanner to populate discovery findings and audit evidence.
            </p>
            <Link
              to="/scan"
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-semibold text-xs tracking-wide transition mt-2 shadow-md shadow-cyan-500/20"
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
                    <tr key={r.id} className="hover:bg-navy-800/50 transition-colors">
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
      {/* 5. Educational Quantum Risk Disclaimer */}
      {/* ========================================================================= */}
      <div className="rounded-2xl bg-amber-500/10 border border-amber-500/30 p-5 flex items-start space-x-4 shadow-sm">
        <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs leading-relaxed">
          <h4 className="font-bold text-amber-300 text-sm">
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
