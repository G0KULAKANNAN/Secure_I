import React from 'react';
import { AlertTriangle, Calculator, HelpCircle } from 'lucide-react';
import { EmptyState } from '../components/common/EmptyState';

export const RiskAssessment: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-navy-750">
        <h2 className="text-xl font-bold text-white tracking-tight">Explainable Risk Assessment</h2>
        <p className="text-xs text-gray-400 mt-1">
          Deterministic scoring engine prioritizing cryptographic exposure using transparent factor weights.
        </p>
      </div>

      {/* Formula Explanation Card */}
      <div className="p-5 rounded-xl bg-navy-850 border border-cyan-500/20 space-y-3">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Calculator className="w-5 h-5" />
          <h3 className="text-sm font-semibold text-white">QuantumShield Scoring Model (Prototype)</h3>
        </div>
        <div className="p-3 bg-navy-950 rounded-lg font-mono text-xs text-cyan-300 border border-navy-800">
          R = 20 × (0.35C + 0.30S + 0.25L + 0.10E)
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-300 pt-1">
          <div><span className="font-semibold text-cyan-400">C:</span> Cryptographic Exposure (1-5)</div>
          <div><span className="font-semibold text-cyan-400">S:</span> Data Sensitivity (1-5)</div>
          <div><span className="font-semibold text-cyan-400">L:</span> Confidentiality Lifetime (1-5)</div>
          <div><span className="font-semibold text-cyan-400">E:</span> Internet Exposure (1-5)</div>
        </div>
      </div>

      <EmptyState
        icon={AlertTriangle}
        title="Risk Scoring Engine Scheduled for Stage 7"
        description="The explainable risk calculator with factor breakdown and override tracking will be implemented in Stage 7."
      />
    </div>
  );
};
