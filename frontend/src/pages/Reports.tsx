import React from 'react';
import { FileBarChart, Download } from 'lucide-react';
import { EmptyState } from '../components/common/EmptyState';

export const Reports: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-navy-750">
        <h2 className="text-xl font-bold text-white tracking-tight">Audit Reports & Data Export</h2>
        <p className="text-xs text-gray-400 mt-1">
          Export sanitized scan summaries, finding inventories, and migration plans in CSV and JSON formats.
        </p>
      </div>

      <EmptyState
        icon={FileBarChart}
        title="Reporting Engine Scheduled for Stage 10"
        description="CSV formula-injection mitigation, executive summaries, and compliance audit exports will be added in Stage 10."
      />
    </div>
  );
};
