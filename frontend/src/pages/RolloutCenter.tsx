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
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 bg-cyan-500/10 text-cyan-400 rounded-xl border border-cyan-500/30 shadow-md shadow-cyan-500/10">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">Staged Production Rollout Center</h1>
            <p className="text-gray-400 text-sm">
              Stage 4: Automated Canary Rollout (1% &rarr; 5% &rarr; 25% &rarr; 50% &rarr; 100%), 9-Point Readiness Gate, and Auto-Rollback Safeguards
            </p>
          </div>
        </div>
      </div>

      {/* Honest Simulation Notice */}
      <div className="p-4 rounded-2xl bg-navy-900/90 border border-navy-750 text-gray-300 text-xs md:text-sm flex items-start space-x-3 shadow-md">
        <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Simulation & Safety Architecture: </span>
          QuantumShield does not modify remote live production firewalls or edge proxies without configured IAM cloud credentials. Deployment transitions and telemetry responses are orchestrated transparently through the SQLite state machine with full audit logging.
        </div>
      </div>

      {/* Feedback alerts */}
      {actionMessage && (
        <div className="p-4 rounded-2xl bg-emerald-950/70 border border-emerald-500/50 text-emerald-200 text-sm flex items-center space-x-2 shadow-md">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}
      {actionError && (
        <div className="p-4 rounded-2xl bg-rose-950/70 border border-rose-500/50 text-rose-200 text-sm flex items-center space-x-2 shadow-md">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Section 1: Deployment Environments Overview */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Server className="w-5 h-5 text-gray-400" />
          <span>Deployment Environments</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {environments.map((env) => (
            <div
              key={env.id}
              className={`p-5 rounded-2xl border bg-gradient-to-b from-navy-850 to-navy-900 shadow-md transition-all ${
                selectedPlan?.environment_id === env.id
                  ? 'border-cyan-500 ring-1 ring-cyan-500 shadow-cyan-500/10'
                  : 'border-navy-750/90 hover:border-navy-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase font-bold tracking-wider font-mono text-cyan-400">
                  {env.category.replace('_', ' ')}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                    env.rollout_status === 'completed'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-700/60'
                      : env.rollout_status === 'rolled_back'
                      ? 'bg-amber-950 text-amber-300 border border-amber-700/60'
                      : 'bg-navy-800 text-gray-300 border border-navy-700'
                  }`}
                >
                  {env.rollout_status}
                </span>
              </div>
              <h3 className="text-sm font-bold text-white mb-1">{env.name}</h3>
              <p className="text-xs text-gray-400 mb-3">{env.managed_service}</p>
              <div className="space-y-1.5 text-xs text-gray-300 border-t border-navy-750/80 pt-2.5">
                <div className="flex justify-between">
                  <span className="text-gray-400">Readiness:</span>
                  <span className="font-semibold text-cyan-300">{env.readiness_status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TLS:</span>
                  <span className="font-mono text-white">{env.supported_tls_version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Groups:</span>
                  <span className="font-mono text-cyan-300 truncate max-w-[130px]">
                    {env.supported_groups.join(', ')}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Active Plan & Canary Stepper */}
      <div className="p-6 md:p-8 rounded-3xl bg-gradient-to-b from-navy-850 to-navy-900 border border-navy-750/90 shadow-xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-navy-750/80 pb-6">
          <div>
            <div className="flex items-center space-x-3 mb-1.5">
              <h2 className="text-xl md:text-2xl font-extrabold text-white">
                {selectedPlan ? selectedPlan.name : 'No Active Plan Selected'}
              </h2>
              {selectedPlan && (
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                    selectedPlan.state === 'COMPLETED'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                      : selectedPlan.state === 'ROLLED_BACK'
                      ? 'bg-rose-950 text-rose-300 border border-rose-600'
                      : selectedPlan.state === 'APPROVED' || selectedPlan.state === 'CANARY'
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-600'
                      : 'bg-navy-800 text-gray-300 border border-navy-700'
                  }`}
                >
                  {selectedPlan.state}
                </span>
              )}
            </div>
            <p className="text-xs md:text-sm text-gray-400">
              Target Environment: <span className="font-medium text-white">{selectedPlan?.environment_id}</span> | Auto-Rollback Threshold:{' '}
              <span className="font-semibold text-rose-400 font-mono">{selectedPlan?.rollback_threshold_failure_rate}% failure</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedPlan?.id || ''}
              onChange={(e) => {
                const found = plans.find((p) => p.id === e.target.value);
                if (found) handleSelectPlan(found);
              }}
              className="px-3.5 py-2 bg-navy-950 border border-navy-750 rounded-xl text-xs md:text-sm text-gray-200 focus:outline-none focus:border-cyan-500 shadow-sm"
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
              className="px-4 py-2 bg-navy-750 hover:bg-navy-700 text-white text-xs md:text-sm font-semibold rounded-xl flex items-center space-x-2 disabled:opacity-50 transition shadow-sm"
            >
              <CheckSquare className="w-4 h-4 text-cyan-400" />
              <span>Assess Gates</span>
            </button>
            {selectedPlan?.state === 'READY_FOR_APPROVAL' && (
              <button
                onClick={handleApprove}
                disabled={submitting}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-navy-950 text-xs md:text-sm font-bold rounded-xl flex items-center space-x-2 disabled:opacity-50 transition shadow-md shadow-cyan-500/20"
              >
                <UserCheck className="w-4 h-4" />
                <span>Approve Plan</span>
              </button>
            )}
            {(selectedPlan?.state === 'APPROVED' || selectedPlan?.state === 'CANARY') && (
              <button
                onClick={handleAdvance}
                disabled={submitting}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs md:text-sm font-bold rounded-xl flex items-center space-x-2 disabled:opacity-50 transition shadow-md shadow-emerald-500/20"
              >
                <Play className="w-4 h-4" />
                <span>Advance Canary</span>
              </button>
            )}
            {selectedPlan?.state === 'CANARY' && (
              <button
                onClick={handleRollback}
                disabled={submitting}
                className="px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white text-xs md:text-sm font-bold rounded-xl flex items-center space-x-2 disabled:opacity-50 transition shadow-md shadow-rose-500/20"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Rollback</span>
              </button>
            )}
          </div>
        </div>

        {/* 5-Stage Visual Stepper */}
        <div>
          <h3 className="text-xs font-bold text-gray-300 mb-3 uppercase tracking-wider font-mono">
            Canary Deployment Progression ({selectedPlan?.canary_percentage || 0}% Traffic Active)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {CANARY_STAGES_DEF.map((st, idx) => {
              const isCurrent = selectedPlan?.current_stage === st.stage;
              const isPassed = (selectedPlan?.canary_percentage || 0) >= st.pct;
              return (
                <div
                  key={st.stage}
                  className={`p-4 rounded-2xl border flex flex-col justify-between transition-all ${
                    isCurrent
                      ? 'bg-cyan-950/80 border-cyan-400 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-400'
                      : isPassed
                      ? 'bg-navy-900/90 border-emerald-500/40'
                      : 'bg-navy-950/60 border-navy-800 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono text-gray-400 font-bold">STAGE {idx + 1}</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-bold font-mono ${
                        isCurrent
                          ? 'bg-cyan-500 text-navy-950'
                          : isPassed
                          ? 'bg-emerald-900 text-emerald-200 border border-emerald-700'
                          : 'bg-navy-800 text-gray-400'
                      }`}
                    >
                      {st.pct}%
                    </span>
                  </div>
                  <div className="text-xs font-bold text-white mb-1">{st.name}</div>
                  <div className="text-[11px] text-gray-400 font-mono">
                    {isCurrent ? 'Monitoring traffic...' : isPassed ? 'Stage Completed' : 'Pending Gate'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section 3: 9-Point Readiness Gate Matrix */}
        {assessment && (
          <div className="border-t border-navy-750/80 pt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <span>9-Point Pre-Deployment Readiness Assessment</span>
              </h3>
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold font-mono ${
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
                  className="p-4 rounded-xl bg-navy-900/90 border border-navy-750/80 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-white">{g.title}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          g.status === 'PASS'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                            : g.status === 'FAIL'
                            ? 'bg-rose-950 text-rose-300 border border-rose-700'
                            : 'bg-amber-950 text-amber-300 border border-amber-700'
                        }`}
                      >
                        {g.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mb-1">{g.message}</p>
                  </div>
                  {g.recommendation && (
                    <p className="text-[11px] text-amber-300/90 italic mt-2 border-t border-navy-800 pt-1.5">
                      {g.recommendation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section 4: Live Telemetry & Simulation Controls */}
        <div className="border-t border-navy-750/80 pt-6 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Canary Health & Real-Time Telemetry</span>
              </h3>
              <p className="text-xs text-gray-400">
                Automated monitors evaluate live handshakes. Threshold limit: {selectedPlan?.rollback_threshold_failure_rate}% failure.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleSimulate(true)}
                disabled={submitting || !selectedPlan}
                className="px-3.5 py-1.5 bg-emerald-950/80 hover:bg-emerald-900 text-emerald-200 border border-emerald-700/80 text-xs font-semibold rounded-xl flex items-center space-x-1.5 disabled:opacity-50 transition"
              >
                <Activity className="w-3.5 h-3.5" />
                <span>Simulate Healthy Traffic</span>
              </button>
              <button
                onClick={() => handleSimulate(false)}
                disabled={submitting || !selectedPlan}
                className="px-3.5 py-1.5 bg-rose-950/80 hover:bg-rose-900 text-rose-200 border border-rose-700/80 text-xs font-semibold rounded-xl flex items-center space-x-1.5 disabled:opacity-50 transition"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Simulate High Error Anomaly</span>
              </button>
            </div>
          </div>

          {latestTelemetry ? (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="p-3.5 bg-navy-900/90 rounded-xl border border-navy-750">
                <div className="text-xs text-gray-400 mb-1">Handshake Success</div>
                <div className="text-xl font-bold text-emerald-400 font-mono">
                  {latestTelemetry.handshake_success_rate.toFixed(2)}%
                </div>
              </div>
              <div className="p-3.5 bg-navy-900/90 rounded-xl border border-navy-750">
                <div className="text-xs text-gray-400 mb-1">Handshake Failure</div>
                <div
                  className={`text-xl font-bold font-mono ${
                    latestTelemetry.handshake_failure_rate > (selectedPlan?.rollback_threshold_failure_rate || 2)
                      ? 'text-rose-400'
                      : 'text-white'
                  }`}
                >
                  {latestTelemetry.handshake_failure_rate.toFixed(2)}%
                </div>
              </div>
              <div className="p-3.5 bg-navy-900/90 rounded-xl border border-navy-750">
                <div className="text-xs text-gray-400 mb-1">Avg Latency</div>
                <div className="text-xl font-bold text-white font-mono">
                  {latestTelemetry.average_latency_ms.toFixed(1)} ms
                </div>
              </div>
              <div className="p-3.5 bg-navy-900/90 rounded-xl border border-navy-750">
                <div className="text-xs text-gray-400 mb-1">Timeout Rate</div>
                <div className="text-xl font-bold text-white font-mono">
                  {latestTelemetry.timeout_rate.toFixed(2)}%
                </div>
              </div>
              <div className="p-3.5 bg-navy-900/90 rounded-xl border border-navy-750">
                <div className="text-xs text-gray-400 mb-1">Negotiated Group</div>
                <div className="text-xs font-mono font-bold text-cyan-300 truncate">
                  {latestTelemetry.negotiated_group}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-5 rounded-2xl bg-navy-950/60 border border-navy-800 text-center text-xs text-gray-400">
              No canary telemetry samples recorded yet. Click "Simulate Healthy Traffic" to begin observing.
            </div>
          )}
        </div>
      </div>

      {/* Section 5: Create New Rollout Plan Form */}
      <div className="p-6 md:p-8 rounded-3xl bg-gradient-to-b from-navy-850 to-navy-900 border border-navy-750/90 shadow-xl space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <span>Initialize Staged Canary Rollout Plan</span>
        </h2>
        <form onSubmit={handleCreatePlan} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Plan Name</label>
            <input
              type="text"
              value={planName}
              onChange={(e) => setPlanName(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 bg-navy-950 border border-navy-750 rounded-xl text-sm text-gray-100 focus:outline-none focus:border-cyan-500 shadow-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Target Environment</label>
            <select
              value={targetEnvId}
              onChange={(e) => setTargetEnvId(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-navy-950 border border-navy-750 rounded-xl text-sm text-gray-100 focus:outline-none focus:border-cyan-500 shadow-sm"
            >
              {environments.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} ({e.category})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Target Hybrid Group</label>
            <select
              value={targetGroup}
              onChange={(e) => setTargetGroup(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-navy-950 border border-navy-750 rounded-xl text-sm text-gray-100 focus:outline-none focus:border-cyan-500 shadow-sm"
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
              className="w-full px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300 text-navy-950 text-sm font-bold rounded-xl flex items-center justify-center space-x-2 disabled:opacity-50 transition shadow-lg shadow-cyan-500/20"
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
