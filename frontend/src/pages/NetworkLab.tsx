import React, { useEffect, useState } from 'react';
import {
  Network,
  ShieldCheck,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Info,
  Server,
  ArrowRight,
  Loader2,
  FileText,
  Activity,
  Layers,
} from 'lucide-react';
import {
  fetchNetworkProfiles,
  createNetworkProfile,
  runNetworkVerification,
  fetchNetworkResults,
} from '../api/network';
import {
  NetworkProfile,
  NetworkVerificationResult,
  NetworkTestMode,
  NetworkTestProfile,
} from '../types';
import { LoadingState } from '../components/common/LoadingState';

export const NetworkLab: React.FC = () => {
  const [profiles, setProfiles] = useState<NetworkProfile[]>([]);
  const [results, setResults] = useState<NetworkVerificationResult[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Form State
  const [name, setName] = useState<string>('lab-standard-1500mtu');
  const [targetHost, setTargetHost] = useState<string>('127.0.0.1');
  const [targetPort, setTargetPort] = useState<number>(443);
  const [testMode, setTestMode] = useState<NetworkTestMode>('simulation');
  const [testProfile, setTestProfile] = useState<NetworkTestProfile>('standard_mtu');
  const [expectedMtu, setExpectedMtu] = useState<number>(1500);
  const [authorized, setAuthorized] = useState<boolean>(false);
  const [operatorNotes, setOperatorNotes] = useState<string>('');
  const [creating, setCreating] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Test Execution State
  const [selectedProfile, setSelectedProfile] = useState<NetworkProfile | null>(null);
  const [running, setRunning] = useState<boolean>(false);
  const [latestResult, setLatestResult] = useState<NetworkVerificationResult | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [profs, resList] = await Promise.all([
        fetchNetworkProfiles(),
        fetchNetworkResults(),
      ]);
      setProfiles(profs || []);
      setResults(resList || []);
      if (profs && profs.length > 0 && !selectedProfile) {
        setSelectedProfile(profs[0]);
      }
    } catch (err: any) {
      console.error('Failed to load network lab data:', err);
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

    if (!name.trim()) {
      setFormError('Profile name is required.');
      return;
    }
    if (testMode === 'authorised_endpoint' && !authorized) {
      setFormError('Explicit operator authorization confirmation is required for external endpoints.');
      return;
    }

    setCreating(true);
    try {
      const created = await createNetworkProfile({
        name: name.trim(),
        target_host: targetHost.trim(),
        target_port: targetPort,
        test_mode: testMode,
        test_profile: testProfile,
        expected_mtu: expectedMtu,
        authorized_by_operator: authorized,
        operator_notes: operatorNotes.trim() || undefined,
      });

      setProfiles((prev) => [created, ...prev]);
      setSelectedProfile(created);
      setName('');
      setActionMessage(`Network verification profile '${created.name}' created successfully.`);
    } catch (err: any) {
      setFormError(err.message || 'Failed to create profile.');
    } finally {
      setCreating(false);
    }
  };

  const handleRunVerification = async () => {
    if (!selectedProfile) return;
    setRunning(true);
    setActionMessage(null);
    try {
      const res = await runNetworkVerification(selectedProfile.id, 'local_operator');
      setLatestResult(res);
      setResults((prev) => [res, ...prev]);
      setActionMessage(`Verification test completed: ${res.diagnostic_classification}`);
    } catch (err: any) {
      setFormError(err.message || 'Verification execution failed.');
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return <LoadingState message="Connecting to Network Verification Engine..." />;
  }

  const getClassificationBadge = (classification: string) => {
    switch (classification) {
      case 'PASS':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'FAIL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'INCONCLUSIVE':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      case 'SIMULATED':
        return 'bg-cyan-500/10 text-cyan-300 border-cyan-500/20';
      case 'NOT_SUPPORTED':
        return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
      default:
        return 'bg-navy-800 text-gray-300 border-navy-700';
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="border-b border-navy-750 pb-5">
        <div className="flex items-center space-x-2 text-violet-400 text-xs font-mono mb-1">
          <Network className="w-4 h-4" />
          <span>Stage 3 Verification</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Network Compatibility Lab</h1>
        <p className="text-sm text-gray-400 mt-1">
          Verify whether enlarged post-quantum TLS handshake messages (~1.5 KB+) encounter Maximum Transmission Unit (MTU), IP fragmentation, or middlebox inspection barriers.
        </p>
      </div>

      {/* Safety & Realism Notice Banner */}
      <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-navy-750">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Controlled Verification Framework</h3>
              <p className="text-xs text-gray-400">SSRF-guarded probing with strict local-first defaults</p>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-mono bg-violet-500/10 text-violet-300 border border-violet-500/20">
            3 Execution Modes
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs pt-1">
          <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 space-y-1">
            <span className="font-semibold text-cyan-300 block">Mode 1: Local Simulation</span>
            <p className="text-gray-400">Deterministic tests simulating MTU fragmentation without network traffic.</p>
          </div>
          <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 space-y-1">
            <span className="font-semibold text-emerald-300 block">Mode 2: Local Loopback</span>
            <p className="text-gray-400">Measures socket connection parameters against 127.0.0.1.</p>
          </div>
          <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 space-y-1">
            <span className="font-semibold text-violet-300 block">Mode 3: Authorised Probe</span>
            <p className="text-gray-400">Low-volume probe on allowlisted hosts with explicit operator consent.</p>
          </div>
        </div>
      </div>

      {/* Profile Form & Test Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Configure Profile */}
        <div className="lg:col-span-1 rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-5">
          <div className="flex items-center space-x-3 pb-3 border-b border-navy-750">
            <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400">
              <Server className="w-4 h-4" />
            </div>
            <h3 className="text-base font-semibold text-white">Create Verification Profile</h3>
          </div>

          <form onSubmit={handleCreateProfile} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Profile Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. edge-mtu-audit"
                className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-violet-500 focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400">Execution Mode</label>
              <select
                value={testMode}
                onChange={(e) => setTestMode(e.target.value as NetworkTestMode)}
                className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-violet-500 focus:outline-none"
              >
                <option value="simulation">Mode 1: Local Simulation (No Network)</option>
                <option value="local_loopback">Mode 2: Local Loopback Test (127.0.0.1)</option>
                <option value="authorised_endpoint">Mode 3: Authorised External Endpoint</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400">Test Scenario Profile</label>
              <select
                value={testProfile}
                onChange={(e) => setTestProfile(e.target.value as NetworkTestProfile)}
                className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-violet-500 focus:outline-none"
              >
                <option value="standard_mtu">Standard 1500 MTU Payload Probe</option>
                <option value="fragmentation_sensitive">Fragmentation Sensitive (Tunnel/VPN)</option>
                <option value="middlebox_probe">Middlebox DPI Transparency Probe</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-gray-400">Target Host</label>
                <input
                  type="text"
                  value={targetHost}
                  onChange={(e) => setTargetHost(e.target.value)}
                  placeholder="127.0.0.1"
                  className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-violet-500 focus:outline-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-gray-400">Target Port</label>
                <input
                  type="number"
                  value={targetPort}
                  onChange={(e) => setTargetPort(parseInt(e.target.value, 10) || 443)}
                  className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-violet-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400">Expected Interface MTU</label>
              <input
                type="number"
                value={expectedMtu}
                onChange={(e) => setExpectedMtu(parseInt(e.target.value, 10) || 1500)}
                className="w-full bg-navy-950 border border-navy-750 rounded-xl px-3 py-2 text-xs text-white font-mono focus:border-violet-500 focus:outline-none"
              />
            </div>

            {testMode === 'authorised_endpoint' && (
              <div className="p-3.5 rounded-xl bg-navy-950 border border-amber-500/30 flex items-start space-x-2.5">
                <input
                  id="net-auth"
                  type="checkbox"
                  checked={authorized}
                  onChange={(e) => setAuthorized(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-navy-700 bg-navy-900 text-violet-500"
                />
                <label htmlFor="net-auth" className="text-[11px] text-amber-200 leading-tight cursor-pointer">
                  I confirm that I have written authorization to perform connection probing on this target.
                </label>
              </div>
            )}

            {formError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={creating}
              className="w-full py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-bold text-xs tracking-wide transition shadow-lg shadow-violet-600/20 flex items-center justify-center space-x-2"
            >
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Save Verification Profile</span>}
            </button>
          </form>
        </div>

        {/* Right: Active Profiles & Verification Execution */}
        <div className="lg:col-span-2 space-y-6">
          {actionMessage && (
            <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 text-xs text-violet-300 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{actionMessage}</span>
            </div>
          )}

          {/* Profiles Table */}
          <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-4">
            <h3 className="text-base font-semibold text-white">Network Verification Profiles</h3>

            {profiles.length === 0 ? (
              <div className="py-8 text-center text-xs text-gray-400">
                No verification profiles configured. Create one on the left.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-navy-750">
                <table className="w-full text-left text-xs">
                  <thead className="bg-navy-950 text-gray-400 font-mono text-[11px] border-b border-navy-750">
                    <tr>
                      <th className="py-2.5 px-3">Profile Name</th>
                      <th className="py-2.5 px-3">Mode</th>
                      <th className="py-2.5 px-3">Scenario</th>
                      <th className="py-2.5 px-3">MTU</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-navy-750/60 bg-navy-900/60 font-mono text-[11px]">
                    {profiles.map((p) => {
                      const isSelected = selectedProfile?.id === p.id;
                      return (
                        <tr
                          key={p.id}
                          onClick={() => setSelectedProfile(p)}
                          className={`cursor-pointer transition ${
                            isSelected ? 'bg-violet-500/10 border-l-2 border-violet-400' : 'hover:bg-navy-800/40'
                          }`}
                        >
                          <td className="py-2.5 px-3 font-semibold text-white">{p.name}</td>
                          <td className="py-2.5 px-3 text-cyan-300 capitalize">{p.test_mode.replace('_', ' ')}</td>
                          <td className="py-2.5 px-3 text-gray-300">{p.test_profile}</td>
                          <td className="py-2.5 px-3 text-white font-mono">{p.expected_mtu}</td>
                          <td className="py-2.5 px-3 text-right">
                            {isSelected ? (
                              <span className="text-violet-400 font-bold">Selected</span>
                            ) : (
                              <span className="text-gray-500 hover:text-white">Select</span>
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

          {/* Execution Controls & Results Inspector */}
          {selectedProfile && (
            <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-navy-750">
                <div>
                  <h3 className="text-base font-semibold text-white">
                    Run Verification: <span className="text-violet-400 font-mono">{selectedProfile.name}</span>
                  </h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Target: <span className="font-mono text-white">{selectedProfile.target_host}:{selectedProfile.target_port}</span> • Mode: <span className="capitalize">{selectedProfile.test_mode.replace('_', ' ')}</span>
                  </p>
                </div>

                <button
                  type="button"
                  disabled={running}
                  onClick={handleRunVerification}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-bold text-xs tracking-wide transition shadow-lg shadow-violet-600/20"
                >
                  {running ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Verifying MTU / Middlebox...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>Execute Verification</span>
                    </>
                  )}
                </button>
              </div>

              {/* Latest Result Inspection Display */}
              {latestResult && (
                <div className="rounded-xl bg-navy-950 border border-navy-800 p-5 space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-navy-800">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold border ${getClassificationBadge(latestResult.diagnostic_classification)}`}>
                        {latestResult.diagnostic_classification}
                      </span>
                      <span className="text-xs font-semibold text-white">Diagnostic Outcome</span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-navy-900 text-gray-300 border border-navy-750">
                      {latestResult.simulation_label}
                    </span>
                  </div>

                  <p className="text-xs text-gray-200 leading-relaxed font-sans">{latestResult.diagnostic_finding}</p>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-lg bg-navy-900/60 border border-navy-800 text-xs font-mono">
                    <div>
                      <span className="text-gray-400 block text-[10px]">Configured MTU:</span>
                      <span className="text-white">{latestResult.configured_mtu || '1500'} bytes</span>
                    </div>
                    <div>
                      <span className="text-gray-400 block text-[10px]">Estimated Payload:</span>
                      <span className="text-cyan-300">{latestResult.packet_size_estimate_bytes || 0} bytes</span>
                    </div>
                    <div>
                      <span className="text-gray-400 block text-[10px]">Duration:</span>
                      <span className="text-white">{latestResult.duration_ms} ms</span>
                    </div>
                    <div>
                      <span className="text-gray-400 block text-[10px]">Evidence Level:</span>
                      <span className="text-violet-300 capitalize">{latestResult.evidence_level}</span>
                    </div>
                  </div>

                  {latestResult.remediation_recommendations.length > 0 && (
                    <div className="space-y-1.5 pt-2 border-t border-navy-800">
                      <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                        Recommended Diagnostic Actions:
                      </span>
                      <ul className="space-y-1 text-xs text-gray-300 list-disc list-inside">
                        {latestResult.remediation_recommendations.map((rec, idx) => (
                          <li key={idx} className="leading-relaxed">{rec}</li>
                        ))}
                      </ul>
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
