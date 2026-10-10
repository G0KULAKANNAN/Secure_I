import React from 'react';
import { X, Server, Calendar, Shield, Activity, Globe, User, Edit } from 'lucide-react';
import { Asset } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface AssetDetailsModalProps {
  isOpen: boolean;
  asset: Asset | null;
  onClose: () => void;
  onEdit: (asset: Asset) => void;
}

export const AssetDetailsModal: React.FC<AssetDetailsModalProps> = ({
  isOpen,
  asset,
  onClose,
  onEdit,
}) => {
  if (!isOpen || !asset) return null;

  const criticalityColors: Record<string, 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose' | 'gray'> = {
    low: 'gray',
    medium: 'cyan',
    high: 'amber',
    critical: 'rose',
  };

  const statusColors: Record<string, 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose' | 'gray'> = {
    active: 'emerald',
    inactive: 'gray',
    under_review: 'amber',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl p-6 bg-navy-900 border border-navy-750 rounded-2xl shadow-2xl space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-navy-750">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Server className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-wide">{asset.name}</h3>
              <span className="text-xs font-mono text-gray-400">{asset.id}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-navy-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Badges / Quick Meta */}
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={asset.asset_type.toUpperCase()} variant="violet" />
          <StatusBadge status={asset.environment.toUpperCase()} variant="cyan" />
          <StatusBadge
            status={`CRITICALITY: ${asset.criticality.toUpperCase()}`}
            variant={criticalityColors[asset.criticality] || 'cyan'}
          />
          <StatusBadge
            status={`STATUS: ${asset.status.toUpperCase()}`}
            variant={statusColors[asset.status] || 'emerald'}
          />
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-navy-950/60 border border-navy-800 text-xs">
          <div className="space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-medium">
              <Globe className="w-3.5 h-3.5 text-cyan-400" /> Hostname / FQDN
            </span>
            <p className="text-white font-mono">{asset.hostname || 'None assigned'}</p>
          </div>

          <div className="space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-medium">
              <Activity className="w-3.5 h-3.5 text-cyan-400" /> IP Address
            </span>
            <p className="text-white font-mono">{asset.ip_address || 'None assigned'}</p>
          </div>

          <div className="space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-medium">
              <User className="w-3.5 h-3.5 text-cyan-400" /> Owner / Responsible Team
            </span>
            <p className="text-white">{asset.owner || 'Unassigned'}</p>
          </div>

          <div className="space-y-1">
            <span className="text-gray-400 flex items-center gap-1.5 font-medium">
              <Calendar className="w-3.5 h-3.5 text-cyan-400" /> Last Updated
            </span>
            <p className="text-gray-300 font-mono">
              {new Date(asset.updated_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Description */}
        {asset.description && (
          <div className="space-y-1 text-xs">
            <span className="font-semibold text-gray-300 uppercase tracking-wider">Description & Scope</span>
            <p className="p-3 bg-navy-950 rounded-lg text-gray-300 border border-navy-800 leading-relaxed">
              {asset.description}
            </p>
          </div>
        )}

        {/* Actions Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-navy-750">
          <span className="text-[11px] text-gray-500 font-mono">
            Created: {new Date(asset.created_at).toLocaleDateString()}
          </span>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                onClose();
                onEdit(asset);
              }}
              className="flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 rounded-lg transition"
            >
              <Edit className="w-3.5 h-3.5" />
              <span>Edit Asset</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-gray-300 bg-navy-800 hover:bg-navy-750 border border-navy-700 rounded-lg transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
