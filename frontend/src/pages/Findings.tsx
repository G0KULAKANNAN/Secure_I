import React from 'react';
import { FileSearch } from 'lucide-react';
import { EmptyState } from '../components/common/EmptyState';

export const Findings: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-navy-750">
        <h2 className="text-xl font-bold text-white tracking-tight">Unified Findings & Evidence</h2>
        <p className="text-xs text-gray-400 mt-1">
          Deduplicated cryptographic observations with sanitized evidence excerpts and confidence tracking.
        </p>
      </div>

      <EmptyState
        icon={FileSearch}
        title="Findings Management Scheduled for Stage 6"
        description="Evidence correlation, credential redaction, and finding lifecycle management will be enabled in Stage 6."
      />
    </div>
  );
};
