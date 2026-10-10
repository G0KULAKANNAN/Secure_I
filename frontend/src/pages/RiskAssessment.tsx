import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calculator,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  Layers,
  ArrowRight,
  Sliders,
  Sparkles,
  HelpCircle,
  Clock,
  User,
  Flame,
  AlertOctagon,
  RefreshCw,
} from 'lucide-react';
import {
  fetchRiskFormula,
  calculateSimulatedRisk,
  fetchRiskSummary,
  fetchRiskQueue,
} from '../api/risk';
import {
  RiskFormulaMetadata,
  FindingStats,
  RemediationQueueData,
  RiskCalculateResponse,
} from '../types';
import { LoadingState } from '../components/common/LoadingState';

export const RiskAssessment: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [formulaMeta, setFormulaMeta] = useState<RiskFormulaMetadata | null>(null);
  const [summaryStats, setSummaryStats] = useState<FindingStats | null>(null);
  const [queueData, setQueueData] = useState<RemediationQueueData | null>(null);

  // Interactive Simulator State
  const [simSensitivity, setSimSensitivity] = useState<number>(4);
  const [simExposure, setSimExposure] = useState<number>(5);
  const [simLifetime, setSimLifetime] = useState<number>(4);
  const [simOmitLifetime, setSimOmitLifetime] = useState<boolean>(false);
  const [simApiResult, setSimApiResult] = useState<RiskCalculateResponse | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [metaRes, summaryRes, queueRes] = await Promise.all([
        fetchRiskFormula().catch(() => null),
        fetchRiskSummary().catch(() => null),
        fetchRiskQueue().catch(() => null),
      ]);

      if (metaRes) setFormulaMeta(metaRes);
      if (summaryRes?.stats) setSummaryStats(summaryRes.stats);
      if (queueRes) setQueueData(queueRes);
    } catch (err) {
      console.error('Failed to load risk assessment data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Update simulator via API or local deterministic formula
  useEffect(() => {
    const runSimulation = async () => {
      setSimulating(true);
      try {
        const payload: { sensitivity?: number; exposure?: number; lifetime?: number } = {
          sensitivity: simSensitivity,
          exposure: simExposure,
        };
        if (!simOmitLifetime) {
          payload.lifetime = simLifetime;
        }
        const res = await calculateSimulatedRisk(payload);
        setSimApiResult(res);
      } catch (err) {
        console.error('Simulation calculation failed:', err);
      } finally {
        setSimulating(false);
      }
    };

    const timeout = setTimeout(runSimulation, 150);
    return () => clearTimeout(timeout);
  }, [simSensitivity, simExposure, simLifetime, simOmitLifetime]);

  if (loading) {
    return <LoadingState message="Loading risk scoring model and portfolio telemetry..." />;
  }

  // Calculate local display math for simulator
  const localSum = simOmitLifetime ? null : simSensitivity + simExposure + simLifetime;
  const localScore = localSum !== null ? Math.round((localSum / 15) * 100) : null;
  let localCategory = 'Needs Assessment';
  if (localScore !== null) {
    if (localScore >= 75) localCategory = 'Critical';
    else if (localScore >= 50) localCategory = 'High';
    else if (localScore >= 30) localCategory = 'Moderate';
    else localCategory = 'Low';
  }

  // Portfolio total for percentages
  const stats = summaryStats || {
    total: 0,
    risk_critical: 0,
    risk_high: 0,
    risk_moderate: 0,
    risk_low: 0,
    needs_assessment: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    quantum_vulnerable: 0,
  };

  const totalAssessed = (stats.risk_critical || 0) + (stats.risk_high || 0) + (stats.risk_moderate || 0) + (stats.risk_low || 0);
  const totalFindings = (stats.total || totalAssessed + (stats.needs_assessment || 0)) || 1;

  const pctCritical = Math.round(((stats.risk_critical || 0) / totalFindings) * 100);
  const pctHigh = Math.round(((stats.risk_high || 0) / totalFindings) * 100);
  const pctMod = Math.round(((stats.risk_moderate || 0) / totalFindings) * 100);
  const pctLow = Math.round(((stats.risk_low || 0) / totalFindings) * 100);
  const pctNeeds = Math.round(((stats.needs_assessment || 0) / totalFindings) * 100);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-4 border-b border-navy-750 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-white tracking-tight">Explainable Risk Assessment</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
              QS-PRIORITY-V1
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1 max-w-3xl">
            Deterministic, evidence-based prioritization scoring engine evaluating cryptographic assets across 
            three independent risk dimensions: Data Sensitivity, Attack Exposure, and Confidentiality Longevity.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              setLoading(true);
              loadData();
            }}
            className="p-2 rounded-lg bg-navy-800 text-gray-300 hover:text-white hover:bg-navy-700 transition"
            title="Refresh Telemetry"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/findings"
            className="px-3.5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-cyan-900/30 transition"
          >
            <Flame className="w-4 h-4 text-amber-300" />
            <span>Open Monday Morning Queue</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>
      </div>

      {/* Model & Non-NIST Disclaimer Alert */}
      <div className="p-4 rounded-xl bg-navy-900/90 border border-amber-500/30 flex items-start space-x-3">
        <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-gray-300 space-y-1">
          <p className="font-semibold text-amber-300">
            Transparency Notice — Explainable Scoring vs Standards
          </p>
          <p className="leading-relaxed">
            {formulaMeta?.disclaimer ||
              'Risk scoring methodology (QS-PRIORITY-V1) is an engineering prioritization model developed for QuantumShield triage. It is not an official NIST standard. NIST standardizes cryptographic algorithms (FIPS 203 ML-KEM, FIPS 204 ML-DSA, FIPS 205 SLH-DSA), whereas QuantumShield calculates remediation urgency so security teams know what to fix first.'}
          </p>
          <p className="text-[11px] text-gray-400">
            Rule enforcement: Incomplete factors are never fabricated or defaulted; findings with missing context are strictly designated as{' '}
            <span className="text-purple-300 font-medium">Needs Assessment</span> until assessed by an authorized engineer.
          </p>
        </div>
      </div>

      {/* Mathematical Formula Explanation Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 p-5 rounded-xl bg-navy-850/80 border border-navy-750 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-cyan-400">
              <Calculator className="w-5 h-5" />
              <h3 className="text-sm font-semibold text-white">Mathematical Prioritization Formula</h3>
            </div>
            <span className="text-[11px] font-mono text-cyan-400/80 bg-navy-900 px-2 py-0.5 rounded border border-navy-700">
              Scale: 0 — 100
            </span>
          </div>

          <div className="p-4 bg-navy-950/90 rounded-xl border border-cyan-500/20 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="font-mono text-sm md:text-base text-cyan-300 font-bold tracking-wide">
              Risk Score = round( <span className="text-pink-400">(S + E + L)</span> / 15 × 100 )
            </div>
            <div className="text-xs text-gray-400 text-right">
              Where <span className="text-pink-400 font-mono">S, E, L ∈ [1, 5]</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            <div className="p-3 bg-navy-900/70 rounded-lg border border-navy-750">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-pink-400 font-mono">S: Sensitivity</span>
                <span className="text-[10px] text-gray-500">1 — 5</span>
              </div>
              <p className="text-[11px] text-gray-300 mt-1.5 leading-snug">
                Impact of compromise on confidentiality. Covers PII, financial credentials, and master signing keys.
              </p>
              <div className="text-[10px] text-gray-400 mt-2">
                1: Public / Low · 5: Critical Secrets
              </div>
            </div>

            <div className="p-3 bg-navy-900/70 rounded-lg border border-navy-750">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cyan-400 font-mono">E: Exposure</span>
                <span className="text-[10px] text-gray-500">1 — 5</span>
              </div>
              <p className="text-[11px] text-gray-300 mt-1.5 leading-snug">
                Network reachability and attack surface. Considers public ingress, DMZs, and isolated VPCs.
              </p>
              <div className="text-[10px] text-gray-400 mt-2">
                1: Air-gapped · 5: Public Internet
              </div>
            </div>

            <div className="p-3 bg-navy-900/70 rounded-lg border border-navy-750">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-400 font-mono">L: Longevity</span>
                <span className="text-[10px] text-gray-500">1 — 5</span>
              </div>
              <p className="text-[11px] text-gray-300 mt-1.5 leading-snug">
                Confidentiality lifetime window. Addresses Harvest Now, Decrypt Later (HNDL) data retention risks.
              </p>
              <div className="text-[10px] text-gray-400 mt-2">
                1: Ephemeral (&lt;30d) · 5: &gt;10 Years
              </div>
            </div>
          </div>
        </div>

        {/* Category Tiers Card */}
        <div className="p-5 rounded-xl bg-navy-850/80 border border-navy-750 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-white mb-3">
              <Layers className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold">Priority Tiers & Thresholds</h3>
            </div>
            <div className="space-y-2.5">
              <div className="p-2.5 rounded-lg bg-navy-900/80 border border-red-900/40 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-red-400">Critical Priority</span>
                  <div className="text-[10px] text-gray-400">Immediate containment required</div>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-red-950/80 text-red-300 border border-red-800">
                  75 — 100
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-navy-900/80 border border-amber-900/40 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-amber-400">High Priority</span>
                  <div className="text-[10px] text-gray-400">Queue for current sprint</div>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-amber-950/80 text-amber-300 border border-amber-800">
                  50 — 74
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-navy-900/80 border border-blue-900/40 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-blue-400">Moderate Priority</span>
                  <div className="text-[10px] text-gray-400">Scheduled migration roadmap</div>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-blue-950/80 text-blue-300 border border-blue-800">
                  30 — 49
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-navy-900/80 border border-emerald-900/40 flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-emerald-400">Low Priority</span>
                  <div className="text-[10px] text-gray-400">Routine maintenance review</div>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                  0 — 29
                </span>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-navy-750 text-[10px] text-gray-400 flex items-center justify-between">
            <span>Missing factors:</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-950 text-purple-300 border border-purple-800">
              Needs Assessment
            </span>
          </div>
        </div>
      </div>

      {/* Portfolio Risk Distribution & KPIs */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            <span>Active Portfolio Risk Profile</span>
          </h3>
          <span className="text-xs text-gray-400">
            {stats.total || 0} Total Findings Across All Scopes
          </span>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          <div className="p-3.5 rounded-xl bg-navy-850/80 border border-red-900/30 relative overflow-hidden">
            <div className="text-[11px] font-medium text-red-400">Critical (75–100)</div>
            <div className="text-2xl font-bold text-white mt-1">{stats.risk_critical ?? 0}</div>
            <div className="text-[10px] text-gray-400 mt-1">{pctCritical}% of portfolio</div>
            <div className="absolute top-0 right-0 w-12 h-12 bg-red-500/5 rounded-full blur-xl pointer-events-none" />
          </div>

          <div className="p-3.5 rounded-xl bg-navy-850/80 border border-amber-900/30 relative overflow-hidden">
            <div className="text-[11px] font-medium text-amber-400">High (50–74)</div>
            <div className="text-2xl font-bold text-white mt-1">{stats.risk_high ?? 0}</div>
            <div className="text-[10px] text-gray-400 mt-1">{pctHigh}% of portfolio</div>
            <div className="absolute top-0 right-0 w-12 h-12 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
          </div>

          <div className="p-3.5 rounded-xl bg-navy-850/80 border border-blue-900/30 relative overflow-hidden">
            <div className="text-[11px] font-medium text-blue-400">Moderate (30–49)</div>
            <div className="text-2xl font-bold text-white mt-1">{stats.risk_moderate ?? 0}</div>
            <div className="text-[10px] text-gray-400 mt-1">{pctMod}% of portfolio</div>
            <div className="absolute top-0 right-0 w-12 h-12 bg-blue-500/5 rounded-full blur-xl pointer-events-none" />
          </div>

          <div className="p-3.5 rounded-xl bg-navy-850/80 border border-emerald-900/30 relative overflow-hidden">
            <div className="text-[11px] font-medium text-emerald-400">Low (0–29)</div>
            <div className="text-2xl font-bold text-white mt-1">{stats.risk_low ?? 0}</div>
            <div className="text-[10px] text-gray-400 mt-1">{pctLow}% of portfolio</div>
            <div className="absolute top-0 right-0 w-12 h-12 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
          </div>

          <div className="p-3.5 rounded-xl bg-navy-850/80 border border-purple-900/30 relative overflow-hidden">
            <div className="text-[11px] font-medium text-purple-400">Needs Assessment</div>
            <div className="text-2xl font-bold text-white mt-1">{stats.needs_assessment ?? 0}</div>
            <div className="text-[10px] text-gray-400 mt-1">{pctNeeds}% awaiting inputs</div>
            <div className="absolute top-0 right-0 w-12 h-12 bg-purple-500/5 rounded-full blur-xl pointer-events-none" />
          </div>
        </div>

        {/* Visual Multi-Segment Distribution Bar */}
        <div className="p-4 rounded-xl bg-navy-850/80 border border-navy-750 space-y-2">
          <div className="flex justify-between text-xs text-gray-400">
            <span>Portfolio Breakdown</span>
            <span>{totalAssessed} Assessed · {stats.needs_assessment ?? 0} Pending Assessment</span>
          </div>
          <div className="w-full h-3 rounded-full bg-navy-950 overflow-hidden flex border border-navy-750">
            <div
              style={{ width: `${pctCritical}%` }}
              className="bg-red-500 transition-all duration-300"
              title={`Critical: ${stats.risk_critical ?? 0} (${pctCritical}%)`}
            />
            <div
              style={{ width: `${pctHigh}%` }}
              className="bg-amber-500 transition-all duration-300"
              title={`High: ${stats.risk_high ?? 0} (${pctHigh}%)`}
            />
            <div
              style={{ width: `${pctMod}%` }}
              className="bg-blue-500 transition-all duration-300"
              title={`Moderate: ${stats.risk_moderate ?? 0} (${pctMod}%)`}
            />
            <div
              style={{ width: `${pctLow}%` }}
              className="bg-emerald-500 transition-all duration-300"
              title={`Low: ${stats.risk_low ?? 0} (${pctLow}%)`}
            />
            <div
              style={{ width: `${pctNeeds}%` }}
              className="bg-purple-600 transition-all duration-300"
              title={`Needs Assessment: ${stats.needs_assessment ?? 0} (${pctNeeds}%)`}
            />
          </div>
          <div className="flex flex-wrap gap-4 pt-1 text-[11px] text-gray-400">
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
              <span>Critical ({stats.risk_critical ?? 0})</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
              <span>High ({stats.risk_high ?? 0})</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
              <span>Moderate ({stats.risk_moderate ?? 0})</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              <span>Low ({stats.risk_low ?? 0})</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600 inline-block" />
              <span>Needs Assessment ({stats.needs_assessment ?? 0})</span>
            </span>
          </div>
        </div>
      </div>

      {/* Interactive What-If Simulator */}
      <div className="p-6 rounded-xl bg-navy-850/90 border border-cyan-500/20 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-navy-750 gap-2">
          <div className="flex items-center space-x-2 text-cyan-400">
            <Sliders className="w-5 h-5" />
            <h3 className="text-sm font-bold text-white">Interactive What-If Risk Simulator</h3>
          </div>
          <span className="text-xs text-gray-400">
            Live evaluation verified against <code className="font-mono text-cyan-300">/api/v1/risk/calculate</code>
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Controls Column */}
          <div className="lg:col-span-7 space-y-5">
            {/* Sensitivity Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <label className="font-semibold text-gray-200 flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-pink-400 inline-block" />
                  <span>Data Sensitivity (S)</span>
                </label>
                <span className="font-mono font-bold text-pink-400 text-sm">{simSensitivity} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={simSensitivity}
                onChange={(e) => setSimSensitivity(Number(e.target.value))}
                className="w-full accent-pink-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-gray-500">
                <span>1: Public / Low</span>
                <span>2: Internal</span>
                <span>3: Confidential</span>
                <span>4: Highly Restricted</span>
                <span>5: Critical / Top Secret</span>
              </div>
            </div>

            {/* Exposure Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <label className="font-semibold text-gray-200 flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
                  <span>Exposure (E)</span>
                </label>
                <span className="font-mono font-bold text-cyan-400 text-sm">{simExposure} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={simExposure}
                onChange={(e) => setSimExposure(Number(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-gray-500">
                <span>1: Air-gapped</span>
                <span>2: Isolated VPC</span>
                <span>3: Intranet / VPN</span>
                <span>4: DMZ / Partner</span>
                <span>5: Public Internet Edge</span>
              </div>
            </div>

            {/* Lifetime Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <label className="font-semibold text-gray-200 flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
                  <span>Confidentiality Lifetime (L)</span>
                </label>
                <span className="font-mono font-bold text-amber-400 text-sm">
                  {simOmitLifetime ? 'Unspecified' : `${simLifetime} / 5`}
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                disabled={simOmitLifetime}
                value={simLifetime}
                onChange={(e) => setSimLifetime(Number(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer disabled:opacity-30"
              />
              <div className="flex justify-between text-[10px] text-gray-500">
                <span>1: &lt;30 days</span>
                <span>2: 1-12 mos</span>
                <span>3: 1-5 yrs</span>
                <span>4: 5-10 yrs</span>
                <span>5: &gt;10 yrs (HNDL Threat)</span>
              </div>
            </div>

            {/* Incomplete Context Toggle */}
            <div className="pt-2">
              <label className="flex items-center space-x-2.5 text-xs text-gray-300 cursor-pointer bg-navy-900/60 p-2.5 rounded-lg border border-navy-750">
                <input
                  type="checkbox"
                  checked={simOmitLifetime}
                  onChange={(e) => setSimOmitLifetime(e.target.checked)}
                  className="rounded border-navy-700 text-cyan-500 focus:ring-0 bg-navy-950"
                />
                <span className="leading-snug">
                  Demonstrate missing factor behavior: omit Lifetime factor to enforce <strong className="text-purple-300">Needs Assessment</strong> without guessing
                </span>
              </label>
            </div>
          </div>

          {/* Result Card Column */}
          <div className="lg:col-span-5 p-5 rounded-xl bg-navy-950 border border-cyan-500/30 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs text-gray-400 pb-2 border-b border-navy-800">
                <span>Calculated Risk Result</span>
                {simulating && (
                  <span className="text-[10px] text-cyan-400 animate-pulse font-mono">Syncing API...</span>
                )}
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div>
                  <div className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold">Priority Score</div>
                  <div className="text-4xl font-black text-white mt-1">
                    {localScore !== null ? localScore : '—'}
                    {localScore !== null && <span className="text-sm font-normal text-gray-400"> / 100</span>}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold mb-1">Classification</div>
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${
                      localCategory === 'Critical'
                        ? 'bg-red-950 text-red-300 border-red-700 shadow-md shadow-red-900/30'
                        : localCategory === 'High'
                        ? 'bg-amber-950 text-amber-300 border-amber-700 shadow-md shadow-amber-900/30'
                        : localCategory === 'Moderate'
                        ? 'bg-blue-950 text-blue-300 border-blue-700'
                        : localCategory === 'Low'
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                        : 'bg-purple-950 text-purple-300 border-purple-700'
                    }`}
                  >
                    {localCategory}
                  </span>
                </div>
              </div>

              {/* Arithmetic breakdown */}
              <div className="mt-4 p-3 bg-navy-900/80 rounded-lg border border-navy-800 font-mono text-xs text-gray-300 space-y-1">
                <div className="text-[10px] uppercase text-gray-500 font-sans font-semibold">Formula Walkthrough:</div>
                {localScore !== null ? (
                  <div>
                    round( ({simSensitivity} + {simExposure} + {simLifetime}) / 15 × 100 ) = <span className="text-cyan-300 font-bold">{localScore}</span>
                  </div>
                ) : (
                  <div className="text-purple-300 font-sans text-[11px]">
                    L factor missing → Risk Score = null, Category = "Needs Assessment"
                  </div>
                )}
              </div>
            </div>

            {/* Remediation Guidance Preview */}
            <div className="pt-2 border-t border-navy-800/80 text-xs space-y-1 text-gray-400">
              <div className="font-semibold text-gray-300">Prescribed Action:</div>
              <p className="text-[11px] leading-relaxed">
                {localCategory === 'Critical' &&
                  'Immediate containment. Restrict network edge, isolate legacy certificates, and schedule migration to ML-KEM or ML-DSA in the current maintenance window.'}
                {localCategory === 'High' &&
                  'Queue for the next sprint. Review cryptographic library bindings and plan dual-certificate or hybrid TLS deployment.'}
                {localCategory === 'Moderate' &&
                  'Include in standard post-quantum roadmap. Monitor key exchange and certificate renewal dates.'}
                {localCategory === 'Low' &&
                  'Accept risk or schedule during routine decommissioning. Isolated exposure and minimal lifetime mitigate HNDL risks.'}
                {localCategory === 'Needs Assessment' &&
                  'Factor context incomplete. Dispatch asset owner questionnaire to record data sensitivity and network topology before calculating risk.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Monday Morning Queue Highlights */}
      {queueData && (
        <div className="p-5 rounded-xl bg-navy-850/80 border border-navy-750 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                <Flame className="w-4 h-4 text-amber-400" />
                <span>Monday Morning Remediation Queue Highlights</span>
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">
                Top prioritized findings organized by immediate triage tier and actionable remediation guidance.
              </p>
            </div>
            <Link
              to="/findings"
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 font-medium"
            >
              <span>View Full Queue ({queueData.total_items} items)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {/* Immediate Investigation */}
            <div className="p-3.5 rounded-lg bg-navy-900/70 border border-red-900/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-red-400">Immediate Investigation</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-300 border border-red-800">
                  {queueData.tiers.immediate_investigation.count}
                </span>
              </div>
              <p className="text-[11px] text-gray-400">
                Critical exposures and quantum-vulnerable endpoints facing public networks.
              </p>
              {queueData.tiers.immediate_investigation.items.slice(0, 2).map((item) => (
                <div key={item.finding_id} className="p-2 rounded bg-navy-950/80 border border-navy-800 text-xs">
                  <div className="flex justify-between font-medium text-white truncate">
                    <span className="truncate">{item.title}</span>
                    <span className="text-red-400 font-mono ml-2">{item.risk_score}</span>
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1 truncate">{item.first_concrete_action}</div>
                </div>
              ))}
            </div>

            {/* High Priority Migration */}
            <div className="p-3.5 rounded-lg bg-navy-900/70 border border-amber-900/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-400">High Priority Migration</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
                  {queueData.tiers.high_priority_migration.count}
                </span>
              </div>
              <p className="text-[11px] text-gray-400">
                Core applications requiring hybrid or PQC algorithm replacements.
              </p>
              {queueData.tiers.high_priority_migration.items.slice(0, 2).map((item) => (
                <div key={item.finding_id} className="p-2 rounded bg-navy-950/80 border border-navy-800 text-xs">
                  <div className="flex justify-between font-medium text-white truncate">
                    <span className="truncate">{item.title}</span>
                    <span className="text-amber-400 font-mono ml-2">{item.risk_score}</span>
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1 truncate">{item.first_concrete_action}</div>
                </div>
              ))}
            </div>

            {/* Scheduled Remediation */}
            <div className="p-3.5 rounded-lg bg-navy-900/70 border border-blue-900/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-blue-400">Scheduled Remediation</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800">
                  {queueData.tiers.scheduled_remediation.count}
                </span>
              </div>
              <p className="text-[11px] text-gray-400">
                Internal or staging workloads to update in planned sprint cycles.
              </p>
              {queueData.tiers.scheduled_remediation.items.slice(0, 2).map((item) => (
                <div key={item.finding_id} className="p-2 rounded bg-navy-950/80 border border-navy-800 text-xs">
                  <div className="flex justify-between font-medium text-white truncate">
                    <span className="truncate">{item.title}</span>
                    <span className="text-blue-400 font-mono ml-2">{item.risk_score}</span>
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1 truncate">{item.first_concrete_action}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
