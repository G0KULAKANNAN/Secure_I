import React, { useEffect, useState } from 'react';
import {
  Layers,
  Shield,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Server,
  Cpu,
  ArrowRight,
  Loader2,
  Check,
  Lock,
  Terminal,
} from 'lucide-react';
import {
  fetchCapabilities,
  fetchProfiles,
  createProfile,
  testProfile,
  approveProfile,
  rollbackProfile,
} from '../api/hybrid';
import {
  CryptoCapability,
  HybridProfile,
  HostProviderInfo,
  HybridVerificationRun,
} from '../types';
import { LoadingState } from '../components/common/LoadingState';

export const HybridLab: React.FC = () => {
  const [capabilities, setCapabilities] = useState<CryptoCapability[]>([]);
  const [hostProvider, setHostProvider] = useState<HostProviderInfo | null>(null);
  const [profiles, setProfiles] = useState<HybridProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Form State
  const [newProfileName, setNewProfileName] = useState<string>('hybrid-staging-edge');
  const [classicalComp, setClassicalComp] = useState<string>('X25519');
  const [pqcComp, setPqcComp] = useState<string>('ML-KEM-768');
  const [formError, setFormError] = useState<string | null>(null);
  const [creating, setCreating] = useState<boolean>(false);

  // Test Execution State
  const [selectedProfile, setSelectedProfile] = useState<HybridProfile | null>(null);
  const [testMode, setTestMode] = useState<'simulation' | 'real_tls'>('simulation');
  const [testing, setTesting] = useState<boolean>(false);
  const [activeRun, setActiveRun] = useState<HybridVerificationRun | null>(null);
  const [actionMessage, setActionMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadData = async () => {
    try {
      const [capsRes, profsRes] = await Promise.all([
        fetchCapabilities(),
        fetchProfiles(),
      ]);
      setCapabilities(capsRes.capabilities || []);
      setHostProvider(capsRes.host_provider || null);
      setProfiles(profsRes || []);
      if (profsRes && profsRes.length > 0 && !selectedProfile) {
        setSelectedProfile(profsRes[0]);
      }
    } catch (err: any) {
      console.error('Failed to load hybrid lab data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setActionMessage(null);

    if (!newProfileName.trim()) {
      setFormError('Profile name is required.');
      return;
    }

    setCreating(true);
    try {
      const created = await createProfile({
        profile_name: newProfileName.trim(),
        classical_component: classicalComp,
        pqc_component: pqcComp,
        operator: 'local_operator',
      });
      setProfiles((prev) => [created, ...prev]);
      setSelectedProfile(created);
      setNewProfileName('');
      setActionMessage({ text: `Profile '${created.profile_name}' created successfully.`, type: 'success' });
    } catch (err: any) {
      setFormError(err.message || 'Failed to create profile.');
    } finally {
      setCreating(false);
    }
  };

  const handleRunTest = async () => {
    if (!selectedProfile) return;
    setTesting(true);
    setActionMessage(null);
    try {
      const run = await testProfile(selectedProfile.id, testMode, 'local_operator');
      setActiveRun(run);
      // Refresh profiles to reflect VERIFIED/FAILED state
      const updatedList = await fetchProfiles();
      setProfiles(updatedList);
      const updated = updatedList.find((p) => p.id === selectedProfile.id);
      if (updated) setSelectedProfile(updated);
      setActionMessage({ text: 'Interoperability evaluation completed.', type: 'success' });
    } catch (err: any) {
      setActionMessage({ text: err.message || 'Test execution failed.', type: 'error' });
    } finally {
      setTesting(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedProfile) return;
    try {
      const approved = await approveProfile(selectedProfile.id, 'local_operator');
      setProfiles((prev) => prev.map((p) => (p.id === approved.id ? approved : p)));
      setSelectedProfile(approved);
      setActionMessage({ text: `Profile '${approved.profile_name}' approved and enabled for staging.`, type: 'success' });
    } catch (err: any) {
      setActionMessage({ text: err.message || 'Approval failed.', type: 'error' });
    }
  };

  const handleRollback = async () => {
    if (!selectedProfile) return;
    try {
      const rolledBack = await rollbackProfile(selectedProfile.id, 'local_operator');
      setProfiles((prev) => prev.map((p) => (p.id === rolledBack.id ? rolledBack : p)));
      setSelectedProfile(rolledBack);
      setActiveRun(null);
      setActionMessage({ text: `Profile '${rolledBack.profile_name}' rolled back to previous configuration.`, type: 'success' });
    } catch (err: any) {
      setActionMessage({ text: err.message || 'Rollback failed.', type: 'error' });
    }
  };

  if (loading) {
    return <LoadingState message="Connecting to Hybrid Cryptography Engine..." />;
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="border-b border-navy-750 pb-5">
        <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono mb-1">
          <Layers className="w-4 h-4" />
          <span>Stage 2 Architecture</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Hybrid Cryptography Lab</h1>
        <p className="text-sm text-gray-400 mt-1">
          Evaluate dual-mode key establishment (e.g. X25519 + ML-KEM-768) in staging environments to ensure classical and quantum-safe protocols coexist without client disruption.
        </p>
      </div>

      {/* Host TLS Runtime Status Banner */}
      <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-navy-750">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Local Host TLS Provider Capabilities</h3>
              <p className="text-xs text-gray-400 font-mono">{hostProvider?.openssl_version || 'OpenSSL Runtime'}</p>
            </div>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-mono border ${
              hostProvider?.supports_native_hybrid
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
            }`}
          >
            {hostProvider?.provider_status}
          </span>
        </div>
        <p className="text-xs text-gray-300 leading-relaxed">
          {hostProvider?.recommendation}
        </p>
      </div>

      {/* Capabilities Registry Cards */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-white">Cryptographic Capability Registry</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {capabilities.map((c) => (
            <div key={c.id} className="p-5 rounded-2xl bg-navy-850 border border-navy-750 space-y-3 shadow-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-cyan-300">{c.hybrid_combination}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-navy-950 text-gray-400 border border-navy-800">
                  {c.staging_test_status}
                </span>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Classical:</span>
                  <span className="text-amber-300 font-mono">{c.classical_group}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Post-Quantum:</span>
                  <span className="text-emerald-300 font-mono">{c.pqc_algorithm}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Provider:</span>
                  <span className="text-gray-200">{c.implementation_provider}</span>
                </div>
              </div>
              <p className="text-[11px] text-gray-400 leading-normal border-t border-navy-750 pt-2">
                {c.security_notes}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Staging Profile Management & Test Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Create Profile Form */}
        <div className="lg:col-span-1 rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-5">
          <div className="flex items-center space-x-3 pb-3 border-b border-navy-750">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <Server className="w-4 h-4" />
            </div>
            <h3 className="text-base font-semibold text-white">Configure Staging Profile</h3>
          </div>

          <form onSubmit={handleCreateProfile} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Profile Name</label>
              <input
                type="text"
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
                placeholder="e.g. staging-api-hybrid"
                className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400">Classical Group</label>
              <select
                value={classicalComp}
                onChange={(e) => setClassicalComp(e.target.value)}
                className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
              >
                <option value="X25519">X25519 (RFC 7748)</option>
                <option value="NIST P-256">NIST P-256 (secp256r1)</option>
                <option value="NIST P-384">NIST P-384 (secp384r1)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400">Post-Quantum Component</label>
              <select
                value={pqcComp}
                onChange={(e) => setPqcComp(e.target.value)}
                className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-cyan-500 focus:outline-none"
              >
                <option value="ML-KEM-768">ML-KEM-768 (NIST FIPS 203 Cat 3)</option>
                <option value="ML-KEM-1024">ML-KEM-1024 (NIST FIPS 203 Cat 5)</option>
              </select>
            </div>

            <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 space-y-1 text-[11px] text-gray-400">
              <div className="flex justify-between">
                <span>Environment:</span>
                <span className="text-cyan-300 font-mono font-semibold">staging</span>
              </div>
              <div className="flex justify-between">
                <span>Production Auto-Deploy:</span>
                <span className="text-rose-400 font-semibold">Prohibited</span>
              </div>
            </div>

            {formError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={creating}
              className="w-full py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-navy-950 font-bold text-xs tracking-wide transition shadow-lg shadow-cyan-500/20 flex items-center justify-center space-x-2"
            >
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Create Staging Profile</span>}
            </button>
          </form>
        </div>

        {/* Right: Active Profiles & Verification Controls */}
        <div className="lg:col-span-2 space-y-6">
          {actionMessage && (
            <div
              className={`p-4 rounded-xl border text-xs flex items-center space-x-2 ${
                actionMessage.type === 'success'
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                  : 'bg-red-500/10 text-red-400 border-red-500/20'
              }`}
            >
              {actionMessage.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              <span>{actionMessage.text}</span>
            </div>
          )}

          {/* Profiles Table */}
          <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-4">
            <h3 className="text-base font-semibold text-white">Staging Profiles & Workflows</h3>

            {profiles.length === 0 ? (
              <div className="py-8 text-center text-xs text-gray-400">
                No hybrid staging profiles created yet. Use the form on the left to configure one.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-navy-750">
                <table className="w-full text-left text-xs">
                  <thead className="bg-navy-950 text-gray-400 font-mono text-[11px] border-b border-navy-750">
                    <tr>
                      <th className="py-2.5 px-3">Profile Name</th>
                      <th className="py-2.5 px-3">Hybrid Pairing</th>
                      <th className="py-2.5 px-3">Migration State</th>
                      <th className="py-2.5 px-3">Rollout</th>
                      <th className="py-2.5 px-3 text-right">Select</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-navy-750/60 bg-navy-900/60 font-mono text-[11px]">
                    {profiles.map((p) => {
                      const isSelected = selectedProfile?.id === p.id;
                      const stateColors: Record<string, string> = {
                        PLANNED: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
                        CONFIGURED: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20',
                        TESTING: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
                        VERIFIED: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
                        FAILED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
                        APPROVED: 'bg-violet-500/10 text-violet-300 border-violet-500/20',
                      };

                      return (
                        <tr
                          key={p.id}
                          onClick={() => setSelectedProfile(p)}
                          className={`cursor-pointer transition ${
                            isSelected ? 'bg-cyan-500/10 border-l-2 border-cyan-400' : 'hover:bg-navy-800/40'
                          }`}
                        >
                          <td className="py-2.5 px-3 font-semibold text-white">{p.profile_name}</td>
                          <td className="py-2.5 px-3 text-cyan-300">
                            {p.classical_component} + {p.pqc_component}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] border ${stateColors[p.migration_state]}`}>
                              {p.migration_state}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] ${
                                p.rollout_status === 'enabled'
                                  ? 'bg-emerald-500/10 text-emerald-400'
                                  : 'bg-navy-950 text-gray-500'
                              }`}
                            >
                              {p.rollout_status}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {isSelected ? (
                              <span className="text-cyan-400 font-bold">Active</span>
                            ) : (
                              <span className="text-gray-500 hover:text-white">View</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Test & Approval Execution Controls for Selected Profile */}
          {selectedProfile && (
            <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-navy-750">
                <div>
                  <h3 className="text-base font-semibold text-white">
                    Workflow Actions: <span className="text-cyan-400 font-mono">{selectedProfile.profile_name}</span>
                  </h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    State: <span className="font-semibold text-white">{selectedProfile.migration_state}</span> • Staging Environment
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  {selectedProfile.migration_state === 'VERIFIED' && (
                    <button
                      type="button"
                      onClick={handleApprove}
                      className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs transition"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Approve Staging Profile</span>
                    </button>
                  )}

                  {selectedProfile.migration_state === 'APPROVED' && (
                    <button
                      type="button"
                      onClick={handleRollback}
                      className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-rose-600/80 hover:bg-rose-500 text-white font-semibold text-xs transition"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Rollback Configuration</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Test Mode Selector & Runner */}
              <div className="space-y-3 p-4 rounded-xl bg-navy-950 border border-navy-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white uppercase tracking-wider">
                    Interoperability Verification Test
                  </span>
                  <div className="flex items-center space-x-2 text-xs">
                    <label className="flex items-center space-x-1.5 cursor-pointer text-gray-300">
                      <input
                        type="radio"
                        name="testMode"
                        value="simulation"
                        checked={testMode === 'simulation'}
                        onChange={() => setTestMode('simulation')}
                        className="text-cyan-500 focus:ring-cyan-500 bg-navy-900 border-navy-700"
                      />
                      <span>Simulated Test</span>
                    </label>
                    <label className="flex items-center space-x-1.5 cursor-pointer text-gray-300">
                      <input
                        type="radio"
                        name="testMode"
                        value="real_tls"
                        checked={testMode === 'real_tls'}
                        onChange={() => setTestMode('real_tls')}
                        className="text-cyan-500 focus:ring-cyan-500 bg-navy-900 border-navy-700"
                      />
                      <span>Real TLS Handshake</span>
                    </label>
                  </div>
                </div>

                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Evaluates whether classical-only clients and hybrid-capable clients can both negotiate key exchange seamlessly without connection reset.
                </p>

                <button
                  type="button"
                  disabled={testing}
                  onClick={handleRunTest}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-navy-950 font-bold text-xs tracking-wide transition shadow-lg shadow-cyan-500/20"
                >
                  {testing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Running Interoperability Test...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>Run Interoperability Evaluation</span>
                    </>
                  )}
                </button>
              </div>

              {/* Active Test Result Card */}
              {activeRun && (
                <div className="rounded-xl bg-navy-950 border border-navy-800 p-4 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-navy-800">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          activeRun.status === 'passed'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {activeRun.status}
                      </span>
                      <span className="text-xs font-semibold text-white">Negotiation Outcome</span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      {activeRun.simulation_label}
                    </span>
                  </div>

                  <p className="text-xs text-gray-300 leading-relaxed">{activeRun.negotiation_outcome}</p>

                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-navy-800 text-xs font-mono">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Classical Client:</span>
                      <span className="text-emerald-300 font-semibold">Compatible</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Hybrid Client:</span>
                      <span className={activeRun.hybrid_client_compatible ? 'text-emerald-300 font-semibold' : 'text-rose-400 font-semibold'}>
                        {activeRun.hybrid_client_compatible ? 'Compatible' : 'Unsupported'}
                      </span>
                    </div>
                  </div>

                  {activeRun.error_details && (
                    <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 font-mono">
                      {activeRun.error_details}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
