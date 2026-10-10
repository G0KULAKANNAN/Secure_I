import React from 'react';
import { GitPullRequest, Shield, ArrowRight } from 'lucide-react';
import { EmptyState } from '../components/common/EmptyState';

export const Migration: React.FC = () => {
  const algorithms = [
    { from: 'RSA / ECC Key Exchange', to: 'ML-KEM (Kyber)', standard: 'FIPS 203', purpose: 'General Encryption & Key Encapsulation' },
    { from: 'RSA / ECDSA Signatures', to: 'ML-DSA (Dilithium)', standard: 'FIPS 204', purpose: 'Primary Digital Signatures' },
    { from: 'Stateful Hash Signatures', to: 'SLH-DSA (SPHINCS+)', standard: 'FIPS 205', purpose: 'Stateless Hash-Based Signatures' },
  ];

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-navy-750">
        <h2 className="text-xl font-bold text-white tracking-tight">PQC Migration & Remediation Planner</h2>
        <p className="text-xs text-gray-400 mt-1">
          NIST-standardized migration guidance and operational dependency tracking.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {algorithms.map((a, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-navy-850 border border-navy-750 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400 font-mono">{a.from}</span>
              <span className="text-xs font-mono text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                {a.standard}
              </span>
            </div>
            <div className="flex items-center space-x-2 text-sm font-semibold text-white">
              <span>Target:</span>
              <span className="text-cyan-400">{a.to}</span>
            </div>
            <p className="text-xs text-gray-400">{a.purpose}</p>
          </div>
        ))}
      </div>

      <EmptyState
        icon={GitPullRequest}
        title="Migration Task Engine Scheduled for Stages 8 & 9"
        description="Automated PQC migration recommendations and task dependency management will be activated in Stages 8 and 9."
      />
    </div>
  );
};
