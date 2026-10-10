import React, { useEffect, useState } from 'react';
import {
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Play,
  RotateCcw,
  Activity,
  Server,
  ArrowRight,
  TrendingUp,
  Sliders,
  Info,
  Clock,
  UserCheck,
  CheckSquare,
} from 'lucide-react';
import {
  fetchEnvironments,
  fetchRolloutPlans,
  createRolloutPlan,
  assessReadiness,
  approveRolloutPlan,
  advanceCanaryStage,
  simulateCanaryTraffic,
  rollbackPlan,
  fetchTelemetry,
} from '../api/rollout';
import {
  DeploymentEnvironment,
  RolloutPlan,
  TelemetryEvent,
  ReadinessAssessment,
} from '../types';
import { LoadingState } from '../components/common/LoadingState';

const CANARY_STAGES_DEF = [
  { stage: 'STAGE_1_INTERNAL_1PCT', name: '1: Internal Dogfooding', pct: 1 },
  { stage: 'STAGE_2_CANARY_5PCT', name: '2: Low-Risk Canary', pct: 5 },
  { stage: 'STAGE_3_BROADER_25PCT', name: '3: Broader Traffic', pct: 25 },
  { stage: 'STAGE_4_MAJORITY_50PCT', name: '4: Majority Traffic', pct: 50 },
  { stage: 'STAGE_5_FULL_HYBRID_100PCT', name: '5: Full Production', pct: 100 },
];

export const RolloutCenter: React.FC = () => {
  const [environments, setEnvironments] = useState<DeploymentEnvironment[]>([]);
  const [plans, setPlans] = useState<RolloutPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<RolloutPlan | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryEvent[]>([]);
  const [assessment, setAssessment] = useState<ReadinessAssessment | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Form State
  const [planName, setPlanName] = useState<string>('production-hybrid-rollout-v1');
  const [targetEnvId, setTargetEnvId] = useState<string>('env_production');
  const [targetGroup, setTargetGroup] = useState<string>('X25519MLKEM768');
  const [rollbackThreshold, setRollbackThreshold] = useState<number>(2.0);
  const [approverName, setApproverName] = useState<string>('lead_sre_operator');
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [envs, planList] = await Promise.all([
        fetchEnvironments(),
        fetchRolloutPlans(),
      ]);
      setEnvironments(envs);
      setPlans(planList);

      if (planList.length > 0 && !selectedPlan) {
        setSelectedPlan(planList[0]);
        if (planList[0].readiness_assessment) {
          setAssessment(planList[0].readiness_assessment);
        }
        const telem = await fetchTelemetry(planList[0].id);
        setTelemetry(telem);
      }
    } catch (err: any) {
      setActionError(err.message || 'Failed to load rollout data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectPlan = async (plan: RolloutPlan) => {
    setSelectedPlan(plan);
    setAssessment(plan.readiness_assessment || null);
    setActionMessage(null);
    setActionError(null);
    try {
      const telem = await fetchTelemetry(plan.id);
      setTelemetry(telem);
    } catch {
      setTelemetry([]);
    }
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionMessage(null);
    setActionError(null);
    setSubmitting(true);
    try {
      const created = await createRolloutPlan({
        name: planName.trim(),
        environment_id: targetEnvId,
        target_config: {
          tls_version: 'TLS 1.3',
          supported_groups: [targetGroup, 'X25519'],
        },
        rollback_threshold_failure_rate: rollbackThreshold,
        deployment_mode: 'simulation',
      });
      setActionMessage(`Rollout plan '${created.name}' created successfully.`);
      await loadData();
      handleSelectPlan(created);
    } catch (err: any) {
      setActionError(err.message || 'Error creating rollout plan.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAssessReadiness = async () => {
    if (!selectedPlan) return;
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const assessResult = await assessReadiness(selectedPlan.id);
      setAssessment(assessResult);
      setActionMessage('9-point readiness gate evaluation completed.');
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to evaluate readiness gates.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedPlan) return;
    if (!approverName.trim()) {
      setActionError('Approver name is required.');
      return;
    }
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const approved = await approveRolloutPlan(selectedPlan.id, approverName.trim());
      setSelectedPlan(approved);
      setActionMessage(`Rollout plan approved by ${approverName.trim()}. Ready for canary.`);
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Approval rejected due to blockers.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAdvance = async () => {
    if (!selectedPlan) return;
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const res = await advanceCanaryStage(selectedPlan.id);
      setActionMessage(`Canary stage advanced: ${res.current_stage} (${res.canary_percentage}% traffic).`);
      await loadData();
      if (res.plan) {
        setSelectedPlan(res.plan);
      }
    } catch (err: any) {
      setActionError(err.message || 'Cannot advance canary.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSimulate = async (healthy: boolean) => {
    if (!selectedPlan) return;
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const res = await simulateCanaryTraffic(selectedPlan.id, healthy);
      if (res.rollback_triggered) {
        setActionError(`Failure rate exceeded threshold (${selectedPlan.rollback_threshold_failure_rate}%)! Automated emergency rollback triggered!`);
      } else {
        setActionMessage(`Telemetry observed: ${res.telemetry.handshake_success_rate}% success, ${res.telemetry.average_latency_ms}ms latency.`);
      }
      await loadData();
      const telem = await fetchTelemetry(selectedPlan.id);
      setTelemetry(telem);
    } catch (err: any) {
      setActionError(err.message || 'Simulation error.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRollback = async () => {
    if (!selectedPlan) return;
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const rolled = await rollbackPlan(selectedPlan.id, 'Manual operator emergency rollback', approverName || 'sre_operator');
      setSelectedPlan(rolled);
      setActionMessage('Rollback successfully executed: Classical baseline TLS config restored.');
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Rollback failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading Staged Production Rollout Control Center..." />;
  }

  const latestTelemetry = telemetry.length > 0 ? telemetry[0] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-indigo-900/40 text-indigo-400 rounded-lg border border-indigo-700/50">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Staged Production Rollout Center</h1>
            <p className="text-slate-400 text-sm">
              Stage 4: Automated Canary Rollout (1% &rarr; 5% &rarr; 25% &rarr; 50% &rarr; 100%), 9-Point Readiness Gate, and Auto-Rollback Safeguards
            </p>
          </div>
        </div>
      </div>

      {/* Honest Simulation Notice */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-700 text-slate-300 text-sm flex items-start space-x-3 shadow-sm">
        <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Simulation & Safety Architecture: </span>
          QuantumShield does not modify remote live production firewalls or edge proxies without configured IAM cloud credentials. Deployment transitions and telemetry responses are orchestrated transparently through the SQLite state machine with full audit logging.
        </div>
      </div>

      {/* Feedback alerts */}
      {actionMessage && (
        <div className="p-4 rounded-lg bg-emerald-950/60 border border-emerald-500/50 text-emerald-200 text-sm flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}
      {actionError && (
        <div className="p-4 rounded-lg bg-rose-950/60 border border-rose-500/50 text-rose-200 text-sm flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Section 1: Deployment Environments Overview */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center space-x-2">
          <Server className="w-5 h-5 text-slate-400" />
          <span>Deployment Environments</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {environments.map((env) => (
            <div
              key={env.id}
              className={`p-4 rounded-xl border bg-slate-800/80 transition-all ${
                selectedPlan?.environment_id === env.id
                  ? 'border-indigo-500 ring-1 ring-indigo-500'
                  : 'border-slate-700/60'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase font-semibold tracking-wider text-slate-400">
                  {env.category.replace('_', ' ')}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    env.rollout_status === 'completed'
                      ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/50'
                      : env.rollout_status === 'rolled_back'
                      ? 'bg-amber-900/60 text-amber-300 border border-amber-700/50'
                      : 'bg-slate-700/60 text-slate-300'
                  }`}
                >
                  {env.rollout_status}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">{env.name}</h3>
              <p className="text-xs text-slate-400 mb-2">{env.managed_service}</p>
              <div className="space-y-1 text-xs text-slate-300 border-t border-slate-700/50 pt-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Readiness:</span>
                  <span className="font-medium text-indigo-300">{env.readiness_status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">TLS:</span>
                  <span className="font-mono text-slate-200">{env.supported_tls_version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Groups:</span>
                  <span className="font-mono text-slate-200 truncate max-w-[120px]">
                    {env.supported_groups.join(', ')}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Active Plan & Canary Stepper */}
      <div className="p-6 rounded-xl bg-slate-800/90 border border-slate-700/70 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <h2 className="text-xl font-bold text-white">
                {selectedPlan ? selectedPlan.name : 'No Active Plan Selected'}
              </h2>
              {selectedPlan && (
                <span
                  className={`px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                    selectedPlan.state === 'COMPLETED'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                      : selectedPlan.state === 'ROLLED_BACK'
                      ? 'bg-rose-950 text-rose-300 border border-rose-600'
                      : selectedPlan.state === 'APPROVED' || selectedPlan.state === 'CANARY'
                      ? 'bg-indigo-950 text-indigo-300 border border-indigo-600'
                      : 'bg-slate-700 text-slate-200'
                  }`}
                >
                  {selectedPlan.state}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400">
              Target Environment: <span className="font-medium text-slate-200">{selectedPlan?.environment_id}</span> | Fail Threshold:{' '}
              <span className="font-medium text-slate-200">{selectedPlan?.rollback_threshold_failure_rate}%</span>
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedPlan?.id || ''}
              onChange={(e) => {
                const found = plans.find((p) => p.id === e.target.value);
                if (found) handleSelectPlan(found);
              }}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.state})
                </option>
              ))}
            </select>
            <button
              onClick={handleAssessReadiness}
              disabled={!selectedPlan || submitting}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-lg flex items-center space-x-2 disabled:opacity-50"
            >
              <CheckSquare className="w-4 h-4 text-indigo-400" />
              <span>Assess Gates</span>
            </button>
            {selectedPlan?.state === 'READY_FOR_APPROVAL' && (
              <button
                onClick={handleApprove}
                disabled={submitting}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg flex items-center space-x-2 disabled:opacity-50"
              >
                <UserCheck className="w-4 h-4" />
                <span>Approve Plan</span>
              </button>
            )}
            {(selectedPlan?.state === 'APPROVED' || selectedPlan?.state === 'CANARY') && (
              <button
                onClick={handleAdvance}
                disabled={submitting}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg flex items-center space-x-2 disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                <span>Advance Canary</span>
              </button>
            )}
            {selectedPlan?.state === 'CANARY' && (
              <button
                onClick={handleRollback}
                disabled={submitting}
                className="px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white text-sm font-medium rounded-lg flex items-center space-x-2 disabled:opacity-50"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Rollback</span>
              </button>
            )}
          </div>
        </div>

        {/* 5-Stage Visual Stepper */}
        <div>
          <h3 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">
            Canary Deployment Progression ({selectedPlan?.canary_percentage || 0}% Traffic Active)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {CANARY_STAGES_DEF.map((st, idx) => {
              const isCurrent = selectedPlan?.current_stage === st.stage;
              const isPassed = (selectedPlan?.canary_percentage || 0) >= st.pct;
              return (
                <div
                  key={st.stage}
                  className={`p-3.5 rounded-lg border flex flex-col justify-between transition-all ${
                    isCurrent
                      ? 'bg-indigo-950/70 border-indigo-500 shadow-md ring-1 ring-indigo-500'
                      : isPassed
                      ? 'bg-slate-900/90 border-emerald-500/50'
                      : 'bg-slate-900/40 border-slate-700/50 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-slate-400">STAGE {idx + 1}</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-bold ${
                        isCurrent
                          ? 'bg-indigo-600 text-white'
                          : isPassed
                          ? 'bg-emerald-800 text-emerald-200'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {st.pct}%
                    </span>
                  </div>
                  <div className="text-xs font-medium text-white mb-1">{st.name}</div>
                  <div className="text-[11px] text-slate-400">
                    {isCurrent ? 'Monitoring traffic...' : isPassed ? 'Stage Completed' : 'Pending Gate'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section 3: 9-Point Readiness Gate Matrix */}
        {assessment && (
          <div className="border-t border-slate-700/60 pt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-indigo-400" />
                <span>9-Point Pre-Deployment Readiness Assessment</span>
              </h3>
              <span
                className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                  assessment.all_technical_passed
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                    : 'bg-rose-950 text-rose-300 border border-rose-600'
                }`}
              >
                {assessment.all_technical_passed ? 'ALL TECHNICAL GATES PASSED' : 'GATES BLOCKED'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {assessment.gates.map((g) => (
                <div
                  key={g.gate_id}
                  className="p-3 rounded-lg bg-slate-900/70 border border-slate-700/60 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-semibold text-white">{g.title}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          g.status === 'PASS'
                            ? 'bg-emerald-900/60 text-emerald-300'
                            : g.status === 'FAIL'
                            ? 'bg-rose-900/60 text-rose-300'
                            : 'bg-amber-900/60 text-amber-300'
                        }`}
                      >
                        {g.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mb-1">{g.message}</p>
                  </div>
                  {g.recommendation && (
                    <p className="text-[11px] text-amber-300/80 italic mt-1 border-t border-slate-800 pt-1">
                      {g.recommendation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section 4: Live Telemetry & Simulation Controls */}
        <div className="border-t border-slate-700/60 pt-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Canary Health & Real-Time Telemetry</span>
              </h3>
              <p className="text-xs text-slate-400">
                Automated monitors evaluate live handshakes. Threshold limit: {selectedPlan?.rollback_threshold_failure_rate}% failure.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleSimulate(true)}
                disabled={submitting || !selectedPlan}
                className="px-3 py-1.5 bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border border-emerald-700/60 text-xs font-semibold rounded-lg flex items-center space-x-1.5 disabled:opacity-50"
              >
                <Activity className="w-3.5 h-3.5" />
                <span>Simulate Healthy Traffic</span>
              </button>
              <button
                onClick={() => handleSimulate(false)}
                disabled={submitting || !selectedPlan}
                className="px-3 py-1.5 bg-rose-950 hover:bg-rose-900 text-rose-200 border border-rose-700/60 text-xs font-semibold rounded-lg flex items-center space-x-1.5 disabled:opacity-50"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Simulate High Error Anomaly (Test Auto-Rollback)</span>
              </button>
            </div>
          </div>

          {latestTelemetry ? (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400 mb-1">Handshake Success</div>
                <div className="text-lg font-bold text-emerald-400">
                  {latestTelemetry.handshake_success_rate.toFixed(2)}%
                </div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400 mb-1">Handshake Failure</div>
                <div
                  className={`text-lg font-bold ${
                    latestTelemetry.handshake_failure_rate > (selectedPlan?.rollback_threshold_failure_rate || 2)
                      ? 'text-rose-400'
                      : 'text-slate-200'
                  }`}
                >
                  {latestTelemetry.handshake_failure_rate.toFixed(2)}%
                </div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400 mb-1">Avg Latency</div>
                <div className="text-lg font-bold text-slate-200">
                  {latestTelemetry.average_latency_ms.toFixed(1)} ms
                </div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400 mb-1">Timeout Rate</div>
                <div className="text-lg font-bold text-slate-200">
                  {latestTelemetry.timeout_rate.toFixed(2)}%
                </div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-700/50">
                <div className="text-xs text-slate-400 mb-1">Negotiated Group</div>
                <div className="text-xs font-mono font-semibold text-indigo-300 truncate">
                  {latestTelemetry.negotiated_group}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-400">
              No canary telemetry samples recorded yet. Click "Simulate Healthy Traffic" to begin observing.
            </div>
          )}
        </div>
      </div>

      {/* Section 5: Create New Rollout Plan Modal / Form */}
      <div className="p-6 rounded-xl bg-slate-800/90 border border-slate-700/70">
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center space-x-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          <span>Create New Staged Rollout Plan</span>
        </h2>
        <form onSubmit={handleCreatePlan} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Plan Name</label>
            <input
              type="text"
              value={planName}
              onChange={(e) => setPlanName(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Target Environment</label>
            <select
              value={targetEnvId}
              onChange={(e) => setTargetEnvId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            >
              {environments.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} ({e.category})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Target Hybrid Group</label>
            <select
              value={targetGroup}
              onChange={(e) => setTargetGroup(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            >
              <option value="X25519MLKEM768">X25519MLKEM768 (Standard Recommended)</option>
              <option value="SecP256r1MLKEM768">SecP256r1MLKEM768 (FIPS Hybrid)</option>
              <option value="X25519MLKEM1024">X25519MLKEM1024 (High-Assurance)</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={submitting}
              className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Layers className="w-4 h-4" />
              <span>Initialize Plan</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
