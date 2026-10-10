import React, { useState, useEffect, useCallback } from 'react';
import {
  Server,
  Plus,
  Search,
  Filter,
  Trash2,
  Edit,
  ExternalLink,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { listAssets, createAsset, updateAsset, deleteAsset } from '../api/assets';
import { Asset, AssetType, Environment, Criticality, AssetStatus } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { AssetModal } from '../components/assets/AssetModal';
import { AssetDetailsModal } from '../components/assets/AssetDetailsModal';

export const Assets: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterEnv, setFilterEnv] = useState<string>('');
  const [filterCriticality, setFilterCriticality] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');

  // Pagination
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);

  const [detailsAsset, setDetailsAsset] = useState<Asset | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  const [deletingAsset, setDeletingAsset] = useState<Asset | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  // Notification Banner
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const fetchAssetsList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listAssets({
        search: searchTerm,
        asset_type: filterType || undefined,
        environment: filterEnv || undefined,
        criticality: filterCriticality || undefined,
        status: filterStatus || undefined,
        limit,
        offset,
      });
      setAssets(data.assets);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load assets from server.');
    } finally {
      setLoading(false);
    }
  }, [searchTerm, filterType, filterEnv, filterCriticality, filterStatus, limit, offset]);

  useEffect(() => {
    fetchAssetsList();
  }, [fetchAssetsList]);

  // Handle Create / Edit
  const handleSaveAsset = async (assetData: Partial<Asset>) => {
    if (editingAsset) {
      await updateAsset(editingAsset.id, assetData);
      showNotification(`Asset '${assetData.name}' updated successfully.`);
    } else {
      await createAsset(assetData);
      showNotification(`Asset '${assetData.name}' registered successfully.`);
    }
    fetchAssetsList();
  };

  // Handle Delete
  const handleConfirmDelete = async () => {
    if (!deletingAsset) return;
    try {
      await deleteAsset(deletingAsset.id);
      showNotification(`Asset '${deletingAsset.name}' deleted successfully.`);
      setIsConfirmOpen(false);
      setDeletingAsset(null);
      fetchAssetsList();
    } catch (err: any) {
      showNotification(err.message || 'Failed to delete asset.', 'error');
    }
  };

  // Reset Filters
  const handleResetFilters = () => {
    setSearchTerm('');
    setFilterType('');
    setFilterEnv('');
    setFilterCriticality('');
    setFilterStatus('');
    setOffset(0);
  };

  const criticalityVariants: Record<string, 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose' | 'gray'> = {
    low: 'gray',
    medium: 'cyan',
    high: 'amber',
    critical: 'rose',
  };

  const statusVariants: Record<string, 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose' | 'gray'> = {
    active: 'emerald',
    inactive: 'gray',
    under_review: 'amber',
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-navy-750">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-bold text-white tracking-tight">Asset Inventory</h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
              {total} {total === 1 ? 'Asset' : 'Assets'} Discovered
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Centrally manage and monitor cryptographic discovery targets, endpoints, and server systems.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchAssetsList()}
            className="p-2 rounded-lg bg-navy-850 hover:bg-navy-800 text-gray-400 hover:text-white border border-navy-750 transition"
            title="Refresh Asset List"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setEditingAsset(null);
              setIsModalOpen(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-navy-950 text-xs font-bold transition shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Asset</span>
          </button>
        </div>
      </div>

      {/* Notification Banner */}
      {notification && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center space-x-2.5 transition animate-fadeIn ${
            notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="p-4 rounded-xl bg-navy-850 border border-navy-750 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
          {/* Search Box */}
          <div className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search assets, hostname..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setOffset(0);
              }}
              className="w-full pl-9 pr-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition"
            />
          </div>

          {/* Type Filter */}
          <div>
            <select
              value={filterType}
              onChange={(e) => {
                setFilterType(e.target.value);
                setOffset(0);
              }}
              className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 transition"
            >
              <option value="">All Types</option>
              <option value="server">Server</option>
              <option value="website">Website</option>
              <option value="application">Application</option>
              <option value="certificate">Certificate</option>
              <option value="database">Database</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Environment Filter */}
          <div>
            <select
              value={filterEnv}
              onChange={(e) => {
                setFilterEnv(e.target.value);
                setOffset(0);
              }}
              className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 transition"
            >
              <option value="">All Environments</option>
              <option value="development">Development</option>
              <option value="testing">Testing</option>
              <option value="staging">Staging</option>
              <option value="production">Production</option>
            </select>
          </div>

          {/* Criticality Filter */}
          <div>
            <select
              value={filterCriticality}
              onChange={(e) => {
                setFilterCriticality(e.target.value);
                setOffset(0);
              }}
              className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 transition"
            >
              <option value="">All Criticality</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value);
                setOffset(0);
              }}
              className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 transition"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="under_review">Under Review</option>
            </select>
          </div>
        </div>

        {/* Active Filters Summary & Reset */}
        {(searchTerm || filterType || filterEnv || filterCriticality || filterStatus) && (
          <div className="flex items-center justify-between pt-2 text-[11px] text-gray-400 border-t border-navy-800">
            <span>Filtered results active</span>
            <button
              onClick={handleResetFilters}
              className="text-cyan-400 hover:text-cyan-300 font-medium transition"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <LoadingState message="Fetching live assets from SQLite database..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAssetsList} />
      ) : assets.length === 0 ? (
        <EmptyState
          icon={Server}
          title={
            searchTerm || filterType || filterEnv || filterCriticality || filterStatus
              ? 'No matching assets found'
              : 'No assets registered yet'
          }
          description={
            searchTerm || filterType || filterEnv || filterCriticality || filterStatus
              ? 'Try adjusting your search criteria or resetting the active filters.'
              : 'Register your first server, certificate, or application asset to begin tracking cryptographic exposures.'
          }
          actionText={
            searchTerm || filterType || filterEnv || filterCriticality || filterStatus
              ? 'Clear Filters'
              : 'Add First Asset'
          }
          onAction={
            searchTerm || filterType || filterEnv || filterCriticality || filterStatus
              ? handleResetFilters
              : () => {
                  setEditingAsset(null);
                  setIsModalOpen(true);
                }
          }
        />
      ) : (
        <div className="rounded-xl border border-navy-750 bg-navy-900/60 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-navy-750 bg-navy-850/80 text-[11px] uppercase font-mono tracking-wider text-gray-400">
                  <th className="py-3 px-4">Asset</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Environment</th>
                  <th className="py-3 px-4">Criticality</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Updated</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800 text-xs">
                {assets.map((asset) => (
                  <tr
                    key={asset.id}
                    className="hover:bg-navy-850/50 transition cursor-pointer"
                    onClick={() => {
                      setDetailsAsset(asset);
                      setIsDetailsOpen(true);
                    }}
                  >
                    {/* Asset Name & Hostname */}
                    <td className="py-3.5 px-4">
                      <div className="flex flex-col">
                        <span className="font-semibold text-white tracking-wide">{asset.name}</span>
                        {asset.hostname ? (
                          <span className="text-[11px] font-mono text-cyan-400/90">{asset.hostname}</span>
                        ) : asset.ip_address ? (
                          <span className="text-[11px] font-mono text-gray-400">{asset.ip_address}</span>
                        ) : (
                          <span className="text-[11px] text-gray-500 italic">No endpoint assigned</span>
                        )}
                      </div>
                    </td>

                    {/* Type */}
                    <td className="py-3.5 px-4">
                      <StatusBadge status={asset.asset_type.toUpperCase()} variant="violet" />
                    </td>

                    {/* Environment */}
                    <td className="py-3.5 px-4">
                      <StatusBadge status={asset.environment.toUpperCase()} variant="cyan" />
                    </td>

                    {/* Criticality */}
                    <td className="py-3.5 px-4">
                      <StatusBadge
                        status={asset.criticality.toUpperCase()}
                        variant={criticalityVariants[asset.criticality] || 'cyan'}
                      />
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-4">
                      <StatusBadge
                        status={asset.status.replace('_', ' ').toUpperCase()}
                        variant={statusVariants[asset.status] || 'emerald'}
                      />
                    </td>

                    {/* Last Updated */}
                    <td className="py-3.5 px-4 font-mono text-gray-400 text-[11px]">
                      {new Date(asset.updated_at).toLocaleDateString()}
                    </td>

                    {/* Action Buttons */}
                    <td
                      className="py-3.5 px-4 text-right"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => {
                            setDetailsAsset(asset);
                            setIsDetailsOpen(true);
                          }}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-cyan-400 hover:bg-navy-800 transition"
                          title="View Details"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setEditingAsset(asset);
                            setIsModalOpen(true);
                          }}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-navy-800 transition"
                          title="Edit Asset"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setDeletingAsset(asset);
                            setIsConfirmOpen(true);
                          }}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-navy-800 transition"
                          title="Delete Asset"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {total > limit && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-navy-750 bg-navy-850/40 text-xs text-gray-400">
              <span>
                Showing {offset + 1}–{Math.min(offset + limit, total)} of {total} assets
              </span>
              <div className="flex items-center space-x-2">
                <button
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                  className="p-1.5 rounded-lg bg-navy-800 text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-navy-750 transition"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={offset + limit >= total}
                  onClick={() => setOffset(offset + limit)}
                  className="p-1.5 rounded-lg bg-navy-800 text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-navy-750 transition"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add / Edit Asset Modal */}
      <AssetModal
        isOpen={isModalOpen}
        asset={editingAsset}
        onClose={() => {
          setIsModalOpen(false);
          setEditingAsset(null);
        }}
        onSave={handleSaveAsset}
      />

      {/* Details Modal */}
      <AssetDetailsModal
        isOpen={isDetailsOpen}
        asset={detailsAsset}
        onClose={() => {
          setIsDetailsOpen(false);
          setDetailsAsset(null);
        }}
        onEdit={(asset) => {
          setEditingAsset(asset);
          setIsModalOpen(true);
        }}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={isConfirmOpen}
        title="Delete Asset"
        message={`Are you sure you want to delete '${deletingAsset?.name}'? This action will permanently remove the asset and any associated configurations from the SQLite database.`}
        confirmLabel="Delete Asset"
        onConfirm={handleConfirmDelete}
        onCancel={() => {
          setIsConfirmOpen(false);
          setDeletingAsset(null);
        }}
      />
    </div>
  );
};
