import React, { useState, useEffect } from 'react';
import { X, Server, AlertCircle } from 'lucide-react';
import { Asset, AssetType, Environment, Criticality, AssetStatus } from '../../types';

interface AssetModalProps {
  isOpen: boolean;
  asset?: Asset | null;
  onClose: () => void;
  onSave: (assetData: Partial<Asset>) => Promise<void>;
}

export const AssetModal: React.FC<AssetModalProps> = ({
  isOpen,
  asset,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState('');
  const [assetType, setAssetType] = useState<AssetType>('server');
  const [environment, setEnvironment] = useState<Environment>('production');
  const [hostname, setHostname] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [owner, setOwner] = useState('');
  const [criticality, setCriticality] = useState<Criticality>('medium');
  const [status, setStatus] = useState<AssetStatus>('active');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (asset) {
      setName(asset.name);
      setAssetType(asset.asset_type);
      setEnvironment(asset.environment);
      setHostname(asset.hostname || '');
      setIpAddress(asset.ip_address || '');
      setOwner(asset.owner || '');
      setCriticality(asset.criticality);
      setStatus(asset.status);
      setDescription(asset.description || '');
    } else {
      setName('');
      setAssetType('server');
      setEnvironment('production');
      setHostname('');
      setIpAddress('');
      setOwner('');
      setCriticality('medium');
      setStatus('active');
      setDescription('');
    }
    setError(null);
  }, [asset, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Asset name is required.');
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      await onSave({
        name: name.trim(),
        asset_type: assetType,
        environment,
        hostname: hostname.trim() || null,
        ip_address: ipAddress.trim() || null,
        owner: owner.trim() || null,
        criticality,
        status,
        description: description.trim() || null,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save asset.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm animate-fadeIn overflow-y-auto">
      <div className="relative w-full max-w-xl p-6 bg-navy-900 border border-navy-750 rounded-2xl shadow-2xl my-8">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-navy-750">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Server className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">
              {asset ? 'Edit Cryptographic Asset' : 'Register New Asset'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-navy-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Name */}
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Asset Name <span className="text-cyan-400">*</span>
              </label>
              <input
                type="text"
                required
                maxLength={255}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Core Payment Gateway"
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition"
              />
            </div>

            {/* Type */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Asset Type
              </label>
              <select
                value={assetType}
                onChange={(e) => setAssetType(e.target.value as AssetType)}
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-400 transition"
              >
                <option value="server">Server</option>
                <option value="website">Website</option>
                <option value="application">Application</option>
                <option value="certificate">Certificate</option>
                <option value="database">Database</option>
                <option value="other">Other</option>
              </select>
            </div>

            {/* Environment */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Environment
              </label>
              <select
                value={environment}
                onChange={(e) => setEnvironment(e.target.value as Environment)}
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-400 transition"
              >
                <option value="development">Development</option>
                <option value="testing">Testing</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
            </div>

            {/* Hostname */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Hostname / FQDN
              </label>
              <input
                type="text"
                maxLength={255}
                value={hostname}
                onChange={(e) => setHostname(e.target.value)}
                placeholder="e.g., pay.internal.bank.net"
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition"
              />
            </div>

            {/* IP Address */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                IP Address
              </label>
              <input
                type="text"
                maxLength={45}
                value={ipAddress}
                onChange={(e) => setIpAddress(e.target.value)}
                placeholder="e.g., 10.20.30.40"
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition"
              />
            </div>

            {/* Owner */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Owner / Team
              </label>
              <input
                type="text"
                maxLength={255}
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="e.g., Security & Payments Team"
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition"
              />
            </div>

            {/* Criticality */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Business Criticality
              </label>
              <select
                value={criticality}
                onChange={(e) => setCriticality(e.target.value as Criticality)}
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-400 transition"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            {/* Status */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Operational Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as AssetStatus)}
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-400 transition"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="under_review">Under Review</option>
              </select>
            </div>

            {/* Description */}
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Description / Cryptographic Scope
              </label>
              <textarea
                rows={3}
                maxLength={2000}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Briefly describe cryptographic mechanisms or purpose of this asset..."
                className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-navy-750">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-xs font-semibold text-gray-300 bg-navy-800 hover:bg-navy-750 border border-navy-700 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-navy-950 rounded-lg transition shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : asset ? 'Update Asset' : 'Register Asset'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
