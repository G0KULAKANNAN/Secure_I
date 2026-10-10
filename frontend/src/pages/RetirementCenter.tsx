import React, { useEffect, useState } from 'react';
import {
  FileCheck2,
  AlertOctagon,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Play,
  RotateCcw,
  RefreshCw,
  Sliders,
  Layers,
  ArrowRight,
  Info,
  Lock,
  UserCheck,
  Calendar,
  FileText,
} from 'lucide-react';
import {
  fetchPolicies,
  createPolicy,
  fetchDependencies,
  discoverDependencies,
  updateDependency,
  fetchDecommissioningPlans,
  createDecommissioningPlan,
  assessPlanReadiness,
  approveDecommissioningPlan,
  executeDecommissioning,
  rollbackDecommissioning,
} from '../api/decommissioning';
import {
  DecommissioningPolicy,
  CryptoDependency,
  DecommissioningPlan,
  ReadinessAssessment,
} from '../types';
import { LoadingState } from '../components/common/LoadingState';

const POLICY_BADGE_STYLES: Record<string, string> = {
  APPROVED: 'bg-emerald-950 text-emerald-300 border-emerald-600',
  APPROVED_WITH_CONDITIONS: 'bg-cyan-950 text-cyan-300 border-cyan-600',
  MIGRATION_REQUIRED: 'bg-amber-950 text-amber-300 border-amber-600',
  DEPRECATED: 'bg-orange-950 text-orange-300 border-orange-600',
  PROHIBITED_BY_CONFIGURED_POLICY: 'bg-rose-950 text-rose-300 border-rose-600',
  NEEDS_REVIEW: 'bg-slate-800 text-slate-300 border-slate-600',
};

export const RetirementCenter: React.FC = () => {
  const [policies, setPolicies] = useState<DecommissioningPolicy[]>([]);
  const [dependencies, setDependencies] = useState<CryptoDependency[]>([]);
  const [plans, setPlans] = useState<DecommissioningPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<DecommissioningPlan | null>(null);
  const [assessment, setAssessment] = useState<ReadinessAssessment | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Form State
  const [planName, setPlanName] = useState<string>('decommission-rsa2048-api-gateway');
  const [targetPrimitive, setTargetPrimitive] = useState<string>('RSA-2048');
  const [affectedServices, setAffectedServices] = useState<string>('Public API Gateway');
  const [rollbackInstructions, setRollbackInstructions] = useState<string>(
    'Restore classical RSA cipher suites in edge ingress router configuration.'
  );
  const [approverName, setApproverName] = useState<string>('Dr. Elena Rostova');
  const [approverRole, setApproverRole] = useState<string>('Chief Information Security Officer');

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [polList, depList, planList] = await Promise.all([
        fetchPolicies(),
        fetchDependencies(),
        fetchDecommissioningPlans(),
      ]);
      setPolicies(polList);
      setDependencies(depList);
      setPlans(planList);

      if (planList.length > 0 && !selectedPlan) {
        setSelectedPlan(planList[0]);
        if (planList[0].readiness_assessment) {
          setAssessment(planList[0].readiness_assessment);
        }
      }
    } catch (err: any) {
      setActionError(err.message || 'Failed to load decommissioning data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectPlan = (plan: DecommissioningPlan) => {
    setSelectedPlan(plan);
    setAssessment(plan.readiness_assessment || null);
    setActionMessage(null);
    setActionError(null);
  };

  const handleSyncDependencies = async () => {
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const synced = await discoverDependencies();
      setDependencies(synced);
      setActionMessage(`Synchronized ${synced.length} cryptographic dependencies.`);
    } catch (err: any) {
      setActionError(err.message || 'Failed to discover dependencies.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleDepStatus = async (dep: CryptoDependency, newStatus: any) => {
    try {
      const updated = await updateDependency(dep.id, { status: newStatus });
      setDependencies((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setActionMessage(`Service '${dep.service_name}' status updated to '${newStatus}'.`);
    } catch (err: any) {
      setActionError(err.message || 'Failed to update dependency status.');
    }
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const services = affectedServices.split(',').map((s) => s.trim()).filter(Boolean);
      const created = await createDecommissioningPlan({
        name: planName.trim(),
        target_primitive: targetPrimitive.trim(),
        affected_services: services,
        rollback_instructions: rollbackInstructions.trim(),
      });
      setActionMessage(`Decommissioning plan '${created.name}' initialized.`);
      await loadData();
      handleSelectPlan(created);
    } catch (err: any) {
      setActionError(err.message || 'Failed to create plan.');
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
      const assessResult = await assessPlanReadiness(selectedPlan.id);
      setAssessment(assessResult);
      setActionMessage('10-point decommissioning readiness assessment evaluated.');
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Assessment failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprovePlan = async () => {
    if (!selectedPlan) return;
    if (!approverName.trim()) {
      setActionError('Approver name is required.');
      return;
    }
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const approved = await approveDecommissioningPlan(selectedPlan.id, approverName.trim(), approverRole.trim());
      setSelectedPlan(approved);
      setActionMessage(`Plan approved by ${approverName.trim()} (${approverRole.trim()}). Ready for decommissioning.`);
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Approval rejected due to blockers.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleExecuteDecommissioning = async () => {
    if (!selectedPlan) return;
    setSubmitting(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const executed = await executeDecommissioning(selectedPlan.id, approverName || 'security_engineer');
      setSelectedPlan(executed);
      setActionMessage(`Classical primitive '${executed.target_primitive}' permanently decommissioned across specified services.`);
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Execution failed.');
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
      const rolled = await rollbackDecommissioning(
        selectedPlan.id,
        'Operator requested recovery of classical cipher suites',
        approverName || 'security_engineer'
      );
      setSelectedPlan(rolled);
      setActionMessage(`Rollback complete: Classical primitive '${rolled.target_primitive}' restored to active state.`);
      await loadData();
    } catch (err: any) {
      setActionError(err.message || 'Rollback failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading Classical Cryptography Decommissioning Center..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-rose-950/60 text-rose-400 rounded-lg border border-rose-700/50">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Classical Cryptography Decommissioning</h1>
            <p className="text-slate-400 text-sm">
              Stage 5: Primitive-Specific Inventory, Policy Governance, 10-Point Readiness Gates, and Safe Algorithm Retirement
            </p>
          </div>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-700 text-slate-300 text-sm flex items-start space-x-3 shadow-sm">
        <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Controlled Retirement Standard: </span>
          Classical primitives are retired per cryptographic category (key exchange vs digital signature vs hashing). All transitions require formal human sign-off and preserve an automated rollback playbook in SQLite.
        </div>
      </div>

      {/* Action alerts */}
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

      {/* Section 1: Algorithmic Policy Classification Matrix */}
      <div className="p-6 rounded-xl bg-slate-800/90 border border-slate-700/70 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <span>Cryptographic Policy Classifications ({policies.length})</span>
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {policies.map((pol) => (
            <div
              key={pol.id}
              className="p-3.5 rounded-lg bg-slate-900/70 border border-slate-700/60 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-white">{pol.algorithm}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${
                      POLICY_BADGE_STYLES[pol.status] || 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {pol.status.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="text-xs text-indigo-300 font-medium mb-1 capitalize">
                  {pol.primitive_category.replace('_', ' ')}
                </div>
                <p className="text-xs text-slate-300 mb-2">{pol.name}</p>
                {pol.conditions && (
                  <p className="text-[11px] text-slate-400 border-t border-slate-800 pt-1.5 mb-1">
                    <span className="font-medium text-slate-300">Policy: </span>
                    {pol.conditions}
                  </p>
                )}
              </div>
              {pol.enforcement_deadline && (
                <div className="text-[10px] text-amber-300/80 flex items-center space-x-1 mt-2">
                  <Calendar className="w-3 h-3" />
                  <span>Deadline: {pol.enforcement_deadline.split('T')[0]}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Cryptographic Dependency Inventory */}
      <div className="p-6 rounded-xl bg-slate-800/90 border border-slate-700/70 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center space-x-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <span>Cryptographic Dependencies Inventory ({dependencies.length})</span>
            </h2>
            <p className="text-xs text-slate-400">
              Services mapped to current classical primitives and designated quantum-safe replacements.
            </p>
          </div>
          <button
            onClick={handleSyncDependencies}
            disabled={submitting}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 disabled:opacity-50 self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
            <span>Discover / Resync</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 rounded-l-lg">Service / System</th>
                <th className="px-4 py-3">Primitive</th>
                <th className="px-4 py-3">Current Classical</th>
                <th className="px-4 py-3">PQC Target</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 rounded-r-lg">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {dependencies.map((dep) => (
                <tr key={dep.id} className="hover:bg-slate-750/50">
                  <td className="px-4 py-3 font-semibold text-white">{dep.service_name}</td>
                  <td className="px-4 py-3 text-xs capitalize text-slate-400">
                    {dep.primitive_category.replace('_', ' ')}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-rose-300">{dep.current_algorithm}</td>
                  <td className="px-4 py-3 font-mono text-xs text-emerald-300">{dep.target_algorithm}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${
                        dep.status === 'decommissioned'
                          ? 'bg-slate-800 text-slate-400'
                          : dep.status === 'migrating'
                          ? 'bg-cyan-950 text-cyan-300 border border-cyan-700'
                          : 'bg-amber-950 text-amber-300 border border-amber-700'
                      }`}
                    >
                      {dep.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-1.5">
                      {dep.status === 'active' && (
                        <button
                          onClick={() => handleToggleDepStatus(dep, 'migrating')}
                          className="px-2 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 text-xs rounded border border-cyan-700"
                        >
                          Mark Migrating
                        </button>
                      )}
                      {dep.status === 'migrating' && (
                        <button
                          onClick={() => handleToggleDepStatus(dep, 'active')}
                          className="px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded"
                        >
                          Revert Active
                        </button>
                      )}
                      {dep.status === 'decommissioned' && (
                        <span className="text-xs text-slate-400 italic">Retired</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 3: Decommissioning Plans & Execution Control */}
      <div className="p-6 rounded-xl bg-slate-800/90 border border-slate-700/70 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-700/60 pb-4">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <h2 className="text-xl font-bold text-white">
                {selectedPlan ? selectedPlan.name : 'No Decommissioning Plan Selected'}
              </h2>
              {selectedPlan && (
                <span
                  className={`px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                    selectedPlan.state === 'COMPLETED'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                      : selectedPlan.state === 'ROLLED_BACK'
                      ? 'bg-rose-950 text-rose-300 border border-rose-600'
                      : selectedPlan.state === 'APPROVED'
                      ? 'bg-indigo-950 text-indigo-300 border border-indigo-600'
                      : 'bg-slate-700 text-slate-200'
                  }`}
                >
                  {selectedPlan.state}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400">
              Target Primitive: <span className="font-mono text-slate-200">{selectedPlan?.target_primitive}</span> | Affected Services:{' '}
              <span className="text-slate-200">{selectedPlan?.affected_services.join(', ')}</span>
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
              className="px-3.5 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-lg flex items-center space-x-1.5 disabled:opacity-50"
            >
              <FileCheck2 className="w-4 h-4 text-indigo-400" />
              <span>Assess 10 Gates</span>
            </button>
            {selectedPlan?.state === 'READY_FOR_REVIEW' && (
              <button
                onClick={handleApprovePlan}
                disabled={submitting}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg flex items-center space-x-2 disabled:opacity-50"
              >
                <UserCheck className="w-4 h-4" />
                <span>CISO Sign-off</span>
              </button>
            )}
            {selectedPlan?.state === 'APPROVED' && (
              <button
                onClick={handleExecuteDecommissioning}
                disabled={submitting}
                className="px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white text-sm font-medium rounded-lg flex items-center space-x-2 disabled:opacity-50"
              >
                <AlertOctagon className="w-4 h-4" />
                <span>Execute Retirement</span>
              </button>
            )}
            {selectedPlan?.state === 'COMPLETED' && (
              <button
                onClick={handleRollback}
                disabled={submitting}
                className="px-4 py-2 bg-amber-700 hover:bg-amber-600 text-white text-sm font-medium rounded-lg flex items-center space-x-2 disabled:opacity-50"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Rollback Retirement</span>
              </button>
            )}
          </div>
        </div>

        {/* 10-Point Readiness Gate Matrix */}
        {assessment && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-indigo-400" />
                <span>10-Point Decommissioning Readiness Matrix</span>
              </h3>
              <span
                className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                  assessment.all_technical_passed
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                    : 'bg-rose-950 text-rose-300 border border-rose-600'
                }`}
              >
                {assessment.all_technical_passed ? 'TECHNICAL GATES PASSED' : 'BLOCKERS ACTIVE'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-2.5">
              {assessment.gates.map((g) => (
                <div
                  key={g.gate_id}
                  className="p-3 rounded-lg bg-slate-900/80 border border-slate-700/60 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-semibold text-white">{g.title}</span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                          g.status === 'PASS'
                            ? 'bg-emerald-900/70 text-emerald-300'
                            : g.status === 'FAIL'
                            ? 'bg-rose-900/70 text-rose-300'
                            : 'bg-amber-900/70 text-amber-300'
                        }`}
                      >
                        {g.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-tight">{g.message}</p>
                  </div>
                  {g.recommendation && (
                    <p className="text-[10px] text-amber-300/80 italic mt-1 border-t border-slate-800 pt-1">
                      {g.recommendation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Section 4: Create Decommissioning Plan Form */}
      <div className="p-6 rounded-xl bg-slate-800/90 border border-slate-700/70">
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center space-x-2">
          <FileText className="w-5 h-5 text-indigo-400" />
          <span>Initialize Decommissioning Plan</span>
        </h2>
        <form onSubmit={handleCreatePlan} className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
            <label className="block text-xs font-medium text-slate-300 mb-1">Target Classical Primitive</label>
            <select
              value={targetPrimitive}
              onChange={(e) => setTargetPrimitive(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            >
              <option value="RSA-2048">RSA-2048 (Key Exchange / Signature)</option>
              <option value="Diffie-Hellman">Diffie-Hellman (Classical Key Exchange)</option>
              <option value="ECDSA-P256">ECDSA-P256 (Elliptic Curve Signature)</option>
              <option value="RSA-1024">RSA-1024 (Legacy Key Exchange)</option>
              <option value="3DES">3DES (Triple DES Symmetric)</option>
              <option value="SHA-1">SHA-1 (Hash Function)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Affected Services (comma separated)</label>
            <input
              type="text"
              value={affectedServices}
              onChange={(e) => setAffectedServices(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-300 mb-1">Emergency Rollback Instructions</label>
            <input
              type="text"
              value={rollbackInstructions}
              onChange={(e) => setRollbackInstructions(e.target.value)}
              required
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={submitting}
              className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <FileCheck2 className="w-4 h-4" />
              <span>Create Decommissioning Plan</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
