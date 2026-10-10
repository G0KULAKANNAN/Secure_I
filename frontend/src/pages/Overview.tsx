import React, { useEffect, useState } from 'react';
import { fetchHealth, fetchVersion } from '../api/client';
import { HealthStatus, SystemVersion } from '../types';
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
} from 'lucide-react';
import { LoadingState } from '../components/common/LoadingState';

export const Overview: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [version, setVersion] = useState<SystemVersion | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchHealth().catch(() => null), fetchVersion().catch(() => null)])
      .then(([h, v]) => {
        setHealth(h);
        setVersion(v);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <LoadingState message="Connecting to QuantumShield engine..." />;
  }

  const milestones = [
    { stage: 'Stage 1', name: 'Web App Foundation & UI/UX', status: 'Completed', icon: CheckCircle2, color: 'text-emerald-400' },
    { stage: 'Stage 2', name: 'Asset Inventory & SQLite Persistence', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 3', name: 'X.509 Certificate Scanner', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 4', name: 'Source Code & Config Scanner', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 5', name: 'Authorised TLS Scanner', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 6', name: 'Unified Findings & Evidence', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 7', name: 'Explainable Risk Engine', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 8', name: 'PQC Recommendation Engine (NIST)', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 9', name: 'Migration Planner & Dependencies', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
    { stage: 'Stage 10', name: 'Dashboard Charts & Reports', status: 'Planned', icon: Clock, color: 'text-cyan-400' },
  ];

  return (
    <div className="space-y-8">
      {/* Hero / Header Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-navy-850 via-navy-800 to-navy-850 border border-navy-750 p-6 md:p-8 shadow-xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-mono">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Cryptographic Exposure Intelligence Platform</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              QuantumShield Architecture Foundation
            </h2>
            <p className="text-sm text-gray-300 max-w-2xl leading-relaxed">
              Automated platform for identifying Harvest Now, Decrypt Later (HNDL) exposure,
              discovering legacy public-key algorithms, and orchestrating migration to NIST Post-Quantum Cryptography standards.
            </p>
          </div>

          <div className="bg-navy-950/80 border border-navy-750 p-4 rounded-xl min-w-[220px]">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-2 font-mono">Platform State</div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">Environment:</span>
                <span className="text-cyan-300 font-mono font-semibold">{health?.environment || 'development'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Core Version:</span>
                <span className="text-white font-mono">{version?.version || '0.1.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Python:</span>
                <span className="text-gray-300 font-mono">{health?.python_version || '3.13.7'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">API Health:</span>
                <span className="text-emerald-400 font-semibold">{health ? 'Online' : 'Offline'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mandatory Quantum Risk Disclaimer Banner */}
      <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 p-5 flex items-start space-x-4">
        <Info className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs leading-relaxed">
          <h4 className="font-semibold text-amber-300 text-sm">
            Important Cryptographic Risk Assessment Disclaimer
          </h4>
          <p className="text-amber-200/90">
            • Potential quantum vulnerability detection is <strong>not proof of compromise</strong> or immediate system breach.<br />
            • Risk prioritization scores <strong>do not predict when a quantum computer will break a cryptographic system</strong>.<br />
            • QuantumShield provides structured defensive risk assessment and NIST-standardized migration guidance based on empirical evidence.
          </p>
        </div>
      </div>

      {/* Development Roadmap Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white tracking-wide">
            Engineering Milestones & Roadmap
          </h3>
          <span className="text-xs text-gray-400 font-mono">10 Incremental Stages</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {milestones.map((m, idx) => {
            const Icon = m.icon;
            const isCompleted = m.status === 'Completed';
            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border transition-all ${
                  isCompleted
                    ? 'bg-navy-850 border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                    : 'bg-navy-950/50 border-navy-800 hover:border-navy-750'
                } flex items-center justify-between`}
              >
                <div className="flex items-center space-x-3.5">
                  <div
                    className={`p-2 rounded-lg ${
                      isCompleted ? 'bg-emerald-500/10 text-emerald-400' : 'bg-navy-850 text-gray-500'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xs font-mono text-cyan-400">{m.stage}</div>
                    <div className="text-sm font-medium text-white">{m.name}</div>
                  </div>
                </div>
                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-mono ${
                    isCompleted
                      ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                      : 'bg-navy-800 text-gray-400 border border-navy-700'
                  }`}
                >
                  {m.status}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
