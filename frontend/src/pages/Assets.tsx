import React from 'react';
import { Server, Plus, Filter } from 'lucide-react';
import { EmptyState } from '../components/common/EmptyState';

export const Assets: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-navy-750">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Cryptographic Asset Inventory</h2>
          <p className="text-xs text-gray-400 mt-1">
            Track servers, domain endpoints, certificates, code repositories, and data storage assets.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            disabled
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-navy-800 text-gray-400 text-xs font-medium border border-navy-700 cursor-not-allowed opacity-60"
          >
            <Filter className="w-3.5 h-3.5" />
            <span>Filter</span>
          </button>
          <button
            disabled
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-cyan-500/20 text-cyan-300 text-xs font-semibold border border-cyan-500/30 cursor-not-allowed opacity-60"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Asset (Stage 2)</span>
          </button>
        </div>
      </div>

      <EmptyState
        icon={Server}
        title="Asset Inventory Scheduled for Stage 2"
        description="The SQLite database models and repository layer for managing cryptographic assets, criticality levels, and lifetime parameters will be activated in Stage 2."
      />
    </div>
  );
};
