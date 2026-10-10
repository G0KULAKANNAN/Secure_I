import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileSearch,
  AlertTriangle,
  CheckCircle2,
  Filter,
  X,
  Code,
  Globe,
  ShieldCheck,
  ArrowRight,
  ChevronRight,
  Sparkles,
  Flame,
  Clock,
  User,
  Calendar,
  Layers,
  Sliders,
  ListOrdered,
  AlertOctagon,
  ShieldAlert,
  Calculator,
  RotateCcw,
} from 'lucide-react';
import {
  fetchFindings,
  fetchFindingStats,
  updateFindingStatus,
  assessFinding,
  fetchRemediationQueue,
} from '../api/scans';
import {
  Finding,
  FindingStats,
  RemediationQueueData,
  RemediationQueueItem,
} from '../types';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';

export const Findings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'prioritized' | 'queue'>('prioritized');
  const [findings, setFindings] = useState<Finding[]>([]);
  const [stats, setStats] = useState<FindingStats | null>(null);
  const [queueData, setQueueData] = useState<RemediationQueueData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  // Filters
  const [filterRiskCategory, setFilterRiskCategory] = useState<string>('all');
  const [filterScannerType, setFilterScannerType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterAlgorithm, setFilterAlgorithm] = useState<string>('all');

  // Assessment Edit State inside drawer
  const [editSensitivity, setEditSensitivity] = useState<number>(3);
  const [editExposure, setEditExposure] = useState<number>(3);
  const [editLifetime, setEditLifetime] = useState<number>(3);
  const [editOwner, setEditOwner] = useState<string>('');
  const [editTargetDate, setEditTargetDate] = useState<string>('');
  const [editStatus, setEditStatus] = useState<string>('potential_exposure');
  const [savingAssessment, setSavingAssessment] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [findingsRes, statsRes, queueRes] = await Promise.all([
        fetchFindings({
          limit: 150,
          sort_by: 'risk_score',
          order: 'desc',
        }),
        fetchFindingStats(),
        fetchRemediationQueue(),
      ]);

      setFindings(findingsRes.findings || []);
      setStats(statsRes);
      setQueueData(queueRes);
    } catch (err) {
      console.error('Failed to load findings data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // When selecting a finding for drawer, initialize assessment inputs
  const handleSelectFinding = (finding: Finding) => {
    setSelectedFinding(finding);
    setEditSensitivity(finding.data_sensitivity ?? 3);
    setEditExposure(finding.exposure ?? 3);
    setEditLifetime(finding.confidentiality_lifetime ?? 3);
    setEditOwner(finding.assigned_owner || '');
    setEditTargetDate(finding.target_remediation_date || '');
    setEditStatus(finding.remediation_status || 'potential_exposure');
    setSaveSuccessMsg(null);
  };

  // Save assessment from drawer
  const handleSaveAssessment = async () => {
    if (!selectedFinding) return;
    setSavingAssessment(true);
    setSaveSuccessMsg(null);
    try {
      const updated = await assessFinding(selectedFinding.id, {
        data_sensitivity: editSensitivity,
        exposure: editExposure,
        confidentiality_lifetime: editLifetime,
        assigned_owner: editOwner.trim() || null,
        target_remediation_date: editTargetDate || null,
        remediation_status: editStatus,
      });

      setSelectedFinding(updated);
      setFindings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
      setSaveSuccessMsg('Assessment recalculated and persisted successfully.');

      // Refresh stats & queue
      fetchFindingStats().then(setStats);
      fetchRemediationQueue().then(setQueueData);
    } catch (err: any) {
      console.error('Failed to save assessment:', err);
    } finally {
      setSavingAssessment(false);
    }
  };

  // Quick status toggle
  const handleQuickStatusUpdate = async (newStatus: string) => {
    if (!selectedFinding) return;
    try {
      const updated = await updateFindingStatus(selectedFinding.id, newStatus);
      setSelectedFinding(updated);
      setFindings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
      fetchFindingStats().then(setStats);
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  // Filtered list
  const filteredFindings = findings.filter((f) => {
    if (filterRiskCategory !== 'all') {
      if (filterRiskCategory === 'needs_assessment') {
        if (f.risk_score !== null && f.risk_category !== 'Needs Assessment') return false;
      } else if (f.risk_category?.toLowerCase() !== filterRiskCategory.toLowerCase()) {
        return false;
      }
    }
    if (filterScannerType !== 'all' && f.scanner_type !== filterScannerType) return false;
    if (filterStatus !== 'all' && f.remediation_status !== filterStatus) return false;
    if (filterAlgorithm !== 'all' && !f.algorithm.toLowerCase().includes(filterAlgorithm.toLowerCase())) return false;
    return true;
  });

  // Top Fix First item(s)
  const fixFirstFindings = findings
    .filter((f) => f.risk_category === 'Critical' || (f.risk_score && f.risk_score >= 75) || f.queue_group === 'immediate_investigation')
    .slice(0, 3);

  // Badge Helpers
  const getRiskBadge = (category?: string, score?: number | null) => {
    if (score === null || score === undefined || category === 'Needs Assessment') {
      return {
        label: 'Needs Assessment',
        color: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
        scoreText: 'Pending',
      };
    }
    if (category === 'Critical' || score >= 75) {
      return {
        label: 'Critical',
        color: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
        scoreText: `${score}/100`,
      };
    }
    if (category === 'High' || score >= 50) {
      return {
        label: 'High',
        color: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
        scoreText: `${score}/100`,
      };
    }
    if (category === 'Moderate' || score >= 30) {
      return {
        label: 'Moderate',
        color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
        scoreText: `${score}/100`,
      };
    }
    return {
      label: 'Low',
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
      scoreText: `${score}/100`,
    };
  };

  const getDetectionBadge = (category?: string) => {
    switch (category) {
      case 'Confirmed cryptographic API usage':
        return { label: 'Confirmed API', color: 'text-rose-400 bg-rose-500/10 border-rose-500/20' };
      case 'Configuration-based evidence':
        return { label: 'Config Setting', color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20' };
      case 'Certificate-based evidence':
        return { label: 'Certificate', color: 'text-violet-400 bg-violet-500/10 border-violet-500/20' };
      case 'Textual reference only':
        return { label: 'Textual Reference', color: 'text-gray-400 bg-navy-800 border-navy-700' };
      default:
        return { label: 'Needs Validation', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' };
    }
  };

  // Preview score calculation in drawer
  const previewScore = Math.round(((editSensitivity + editExposure + editLifetime) / 15) * 100);

  if (loading) {
    return <LoadingState message="Loading risk-prioritized cryptographic findings..." />;
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="border-b border-navy-750 pb-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs uppercase tracking-widest font-semibold mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Risk Prioritization Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Cryptographic Exposure Findings</h1>
          <p className="text-xs text-gray-400 mt-1 max-w-2xl">
            Prioritized by explainable multi-factor risk scores derived from data sensitivity, system exposure, and confidentiality lifetime.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center bg-navy-850 p-1 rounded-xl border border-navy-750">
          <button
            type="button"
            onClick={() => setActiveTab('prioritized')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center space-x-2 ${
              activeTab === 'prioritized'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Prioritized Findings</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('queue')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center space-x-2 ${
              activeTab === 'queue'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <ListOrdered className="w-3.5 h-3.5" />
            <span>Monday Morning Queue</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TOP METRICS KPI CARDS */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="p-4 rounded-xl bg-navy-850 border border-navy-750">
          <span className="text-[11px] font-mono text-gray-400 uppercase">Total Findings</span>
          <div className="text-2xl font-bold text-white font-mono mt-1">{stats?.total || findings.length}</div>
          <span className="text-[10px] text-gray-400 mt-0.5 block">Discovered in scope</span>
        </div>

        <div className="p-4 rounded-xl bg-navy-850 border border-rose-500/30">
          <span className="text-[11px] font-mono text-rose-400 uppercase">Critical Risk</span>
          <div className="text-2xl font-bold text-rose-400 font-mono mt-1">
            {stats?.risk_critical || findings.filter((f) => f.risk_category === 'Critical').length}
          </div>
          <span className="text-[10px] text-rose-400/80 mt-0.5 block">Score ≥ 75 / Immediate</span>
        </div>

        <div className="p-4 rounded-xl bg-navy-850 border border-orange-500/30">
          <span className="text-[11px] font-mono text-orange-400 uppercase">High Risk</span>
          <div className="text-2xl font-bold text-orange-400 font-mono mt-1">
            {stats?.risk_high || findings.filter((f) => f.risk_category === 'High').length}
          </div>
          <span className="text-[10px] text-orange-400/80 mt-0.5 block">Score 50–74</span>
        </div>

        <div className="p-4 rounded-xl bg-navy-850 border border-amber-500/30">
          <span className="text-[11px] font-mono text-amber-400 uppercase">Needs Assessment</span>
          <div className="text-2xl font-bold text-amber-400 font-mono mt-1">
            {stats?.needs_assessment || findings.filter((f) => f.risk_category === 'Needs Assessment').length}
          </div>
          <span className="text-[10px] text-amber-400/80 mt-0.5 block">Missing S / E / L factors</span>
        </div>

        <div className="p-4 rounded-xl bg-navy-850 border border-violet-500/30">
          <span className="text-[11px] font-mono text-violet-400 uppercase">Overdue Tasks</span>
          <div className="text-2xl font-bold text-violet-400 font-mono mt-1">
            {stats?.overdue_remediations || 0}
          </div>
          <span className="text-[10px] text-violet-400/80 mt-0.5 block">Past target date</span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* "FIX FIRST" CALLOUT BANNER */}
      {/* ========================================================================= */}
      {fixFirstFindings.length > 0 && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-rose-950/40 via-navy-900 to-navy-950 border border-rose-500/40 shadow-xl space-y-3">
          <div className="flex items-center space-x-2 text-rose-400">
            <Flame className="w-5 h-5 animate-pulse" />
            <h3 className="text-sm font-bold uppercase tracking-wider">Fix First: Priority Remediation Action</h3>
          </div>
          <p className="text-xs text-gray-300">
            Based on active exposure, cryptographic primitive vulnerability, and confidentiality lifetime, the security team should triage these findings first:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
            {fixFirstFindings.map((f) => (
              <div
                key={f.id}
                onClick={() => handleSelectFinding(f)}
                className="p-3.5 rounded-xl bg-navy-950 border border-rose-500/30 hover:border-rose-400 cursor-pointer transition space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono font-bold text-rose-300 truncate max-w-[160px]">{f.algorithm}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                    {f.risk_score ? `${f.risk_score}/100` : 'Critical'}
                  </span>
                </div>
                <p className="text-xs font-semibold text-white truncate">{f.title}</p>
                <p className="text-[11px] text-gray-400 line-clamp-2">{f.recommended_action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: PRIORITIZED FINDINGS TABLE */}
      {/* ========================================================================= */}
      {activeTab === 'prioritized' && (
        <div className="space-y-4">
          {/* Multi-Filter Bar */}
          <div className="flex flex-wrap items-center gap-3 p-3.5 rounded-xl bg-navy-900 border border-navy-750 text-xs">
            <div className="flex items-center space-x-1.5 text-gray-400 font-medium">
              <Filter className="w-3.5 h-3.5 text-cyan-400" />
              <span>Filters:</span>
            </div>

            {/* Risk Category Filter */}
            <select
              value={filterRiskCategory}
              onChange={(e) => setFilterRiskCategory(e.target.value)}
              className="bg-navy-950 border border-navy-750 text-white rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-400"
            >
              <option value="all">All Risk Levels</option>
              <option value="Critical">Critical (≥ 75)</option>
              <option value="High">High (50–74)</option>
              <option value="Moderate">Moderate (30–49)</option>
              <option value="Low">Low (0–29)</option>
              <option value="needs_assessment">Needs Assessment</option>
            </select>

            {/* Scan Source */}
            <select
              value={filterScannerType}
              onChange={(e) => setFilterScannerType(e.target.value)}
              className="bg-navy-950 border border-navy-750 text-white rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-400"
            >
              <option value="all">All Scan Sources</option>
              <option value="system_scan">System Files</option>
              <option value="static_scan">Source Code</option>
              <option value="tls_scan">Live Server</option>
              <option value="certificate_scan">Certificate</option>
            </select>

            {/* Status */}
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-navy-950 border border-navy-750 text-white rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-400"
            >
              <option value="all">All Statuses</option>
              <option value="potential_exposure">Potential Exposure</option>
              <option value="verified_usage">Verified Usage</option>
              <option value="needs_review">Needs Review</option>
              <option value="remediated">Remediated</option>
              <option value="accepted_risk">Accepted Risk</option>
            </select>

            {/* Algorithm Filter */}
            <select
              value={filterAlgorithm}
              onChange={(e) => setFilterAlgorithm(e.target.value)}
              className="bg-navy-950 border border-navy-750 text-white rounded-lg px-2.5 py-1 focus:outline-none focus:border-cyan-400"
            >
              <option value="all">All Algorithms</option>
              <option value="RSA">RSA</option>
              <option value="ECC">ECC / ECDSA</option>
              <option value="ECDH">ECDH / DH</option>
              <option value="DES">DES / RC4</option>
              <option value="SHA-1">SHA-1 / MD5</option>
              <option value="ML-KEM">ML-KEM (PQC)</option>
              <option value="ML-DSA">ML-DSA (PQC)</option>
            </select>
          </div>

          {/* Table */}
          {filteredFindings.length === 0 ? (
            <div className="p-12 rounded-2xl bg-navy-850 border border-navy-750 text-center space-y-3">
              <FileSearch className="w-8 h-8 text-gray-500 mx-auto" />
              <h3 className="text-sm font-semibold text-white">No cryptographic findings match the selected filters</h3>
              <p className="text-xs text-gray-400">Try loosening your filter criteria or run a new scan from the Scanner page.</p>
            </div>
          ) : (
            <div className="rounded-2xl bg-navy-850 border border-navy-750 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-navy-950 text-gray-400 font-mono text-[11px] border-b border-navy-750 uppercase tracking-wider">
                    <tr>
                      <th className="py-3.5 px-4">Risk Priority</th>
                      <th className="py-3.5 px-4">Algorithm & Classification</th>
                      <th className="py-3.5 px-4">Target Location</th>
                      <th className="py-3.5 px-4">Factor Breakdown</th>
                      <th className="py-3.5 px-4">Recommended Next Action</th>
                      <th className="py-3.5 px-4">Status & Owner</th>
                      <th className="py-3.5 px-4 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-navy-750/70 bg-navy-900/60">
                    {filteredFindings.map((f) => {
                      const riskBadge = getRiskBadge(f.risk_category, f.risk_score);
                      const detBadge = getDetectionBadge(f.detection_category);

                      return (
                        <tr
                          key={f.id}
                          onClick={() => handleSelectFinding(f)}
                          className="hover:bg-navy-800/60 cursor-pointer transition group"
                        >
                          {/* Risk Priority */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-0.5 rounded font-mono font-bold text-[11px] border ${riskBadge.color}`}>
                                {riskBadge.scoreText}
                              </span>
                              <span className="text-[10px] text-gray-400 font-mono hidden sm:inline">
                                {riskBadge.label}
                              </span>
                            </div>
                          </td>

                          {/* Algorithm & Classification */}
                          <td className="py-3.5 px-4">
                            <div className="font-mono font-semibold text-white">{f.algorithm}</div>
                            <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono border mt-0.5 inline-block ${detBadge.color}`}>
                              {detBadge.label}
                            </span>
                          </td>

                          {/* Target Location */}
                          <td className="py-3.5 px-4 font-mono text-gray-200 max-w-[200px] truncate">
                            {f.file_path || f.asset_id}
                            {f.line_number ? `:${f.line_number}` : ''}
                          </td>

                          {/* Factor Breakdown */}
                          <td className="py-3.5 px-4 whitespace-nowrap font-mono text-[11px]">
                            {f.data_sensitivity !== null && f.data_sensitivity !== undefined ? (
                              <span className="text-cyan-300">
                                S:{f.data_sensitivity} · E:{f.exposure} · L:{f.confidentiality_lifetime}
                              </span>
                            ) : (
                              <span className="text-amber-400/80 italic text-[10px]">Needs S/E/L</span>
                            )}
                          </td>

                          {/* Action */}
                          <td className="py-3.5 px-4 max-w-[260px] text-gray-300 truncate leading-relaxed">
                            {f.recommended_action || 'Review usage'}
                          </td>

                          {/* Status & Owner */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="text-[11px] font-mono capitalize text-gray-300">
                              {f.remediation_status.replace('_', ' ')}
                            </div>
                            {f.assigned_owner && (
                              <span className="text-[10px] text-gray-400 flex items-center space-x-1 mt-0.5">
                                <User className="w-2.5 h-2.5" />
                                <span>{f.assigned_owner}</span>
                              </span>
                            )}
                          </td>

                          {/* Link */}
                          <td className="py-3.5 px-4 text-right">
                            <span className="text-gray-400 group-hover:text-cyan-400 inline-flex items-center space-x-1 text-[11px] font-medium">
                              <span>Triage</span>
                              <ChevronRight className="w-3.5 h-3.5" />
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: MONDAY MORNING REMEDIATION QUEUE */}
      {/* ========================================================================= */}
      {activeTab === 'queue' && queueData && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-navy-900 border border-navy-750 flex items-center justify-between text-xs">
            <span className="text-gray-300">
              The <strong>Monday Morning Queue</strong> groups all verified findings into 4 actionable priority tiers for weekly engineering triage.
            </span>
            <span className="font-mono text-cyan-400 font-bold">{queueData.total_items} Total Items in Queue</span>
          </div>

          {Object.entries(queueData.tiers).map(([tierKey, tier]) => {
            const isImmediate = tierKey === 'immediate_investigation';
            const isHigh = tierKey === 'high_priority_migration';
            const isScheduled = tierKey === 'scheduled_remediation';
            const isNeeds = tierKey === 'needs_assessment';

            const borderColor = isImmediate
              ? 'border-rose-500/40 bg-rose-950/10'
              : isHigh
              ? 'border-orange-500/40 bg-orange-950/10'
              : isScheduled
              ? 'border-cyan-500/40 bg-cyan-950/10'
              : isNeeds
              ? 'border-amber-500/40 bg-amber-950/10'
              : 'border-navy-750 bg-navy-850/60';

            return (
              <div key={tierKey} className={`rounded-2xl border p-5 space-y-4 shadow-xl ${borderColor}`}>
                <div className="flex items-center justify-between pb-3 border-b border-navy-750/70">
                  <div className="flex items-center space-x-2">
                    {isImmediate ? (
                      <Flame className="w-5 h-5 text-rose-400" />
                    ) : isHigh ? (
                      <AlertTriangle className="w-5 h-5 text-orange-400" />
                    ) : isScheduled ? (
                      <Clock className="w-5 h-5 text-cyan-400" />
                    ) : (
                      <Calculator className="w-5 h-5 text-amber-400" />
                    )}
                    <h3 className="text-sm font-bold text-white tracking-tight">{tier.title}</h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-navy-950 text-white border border-navy-750">
                    {tier.count} Items
                  </span>
                </div>

                {tier.items.length === 0 ? (
                  <p className="text-xs text-gray-500 italic py-2">No findings currently pending in this tier.</p>
                ) : (
                  <div className="space-y-3">
                    {tier.items.map((item) => (
                      <div
                        key={item.finding_id}
                        onClick={() => {
                          const full = findings.find((f) => f.id === item.finding_id);
                          if (full) handleSelectFinding(full);
                        }}
                        className="p-4 rounded-xl bg-navy-950/90 border border-navy-800 hover:border-cyan-500/40 cursor-pointer transition space-y-2 group"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
                          <div className="flex items-center space-x-2">
                            <span className="font-mono text-cyan-400 font-bold">#{item.priority_rank}</span>
                            <span className="font-semibold text-white group-hover:text-cyan-300 transition">
                              {item.title}
                            </span>
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-navy-900 text-gray-300 border border-navy-750">
                              {item.algorithm}
                            </span>
                          </div>

                          <div className="flex items-center space-x-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-navy-900 border border-navy-700 text-cyan-300">
                              {item.risk_score ? `Score ${item.risk_score}` : 'Needs Assessment'}
                            </span>
                            <span className="text-[10px] text-gray-400 font-mono truncate max-w-[150px]">
                              {item.file_path}
                              {item.line_number ? `:${item.line_number}` : ''}
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs pt-1">
                          <div>
                            <span className="text-gray-400 text-[11px] block">Why Address Now:</span>
                            <p className="text-gray-200 text-xs">{item.why_now}</p>
                          </div>
                          <div>
                            <span className="text-gray-400 text-[11px] block">First Concrete Action:</span>
                            <p className="text-cyan-300 text-xs font-medium">{item.first_concrete_action}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ========================================================================= */}
      {/* SLIDE-OUT DETAIL & RISK ASSESSMENT DRAWER */}
      {/* ========================================================================= */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-3xl rounded-2xl bg-navy-850 border border-navy-750 shadow-2xl p-6 space-y-6 max-h-[92vh] overflow-y-auto">
            {/* Drawer Header */}
            <div className="flex items-start justify-between pb-4 border-b border-navy-750">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase">
                    {selectedFinding.severity}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-navy-950 text-cyan-300 border border-navy-800">
                    {selectedFinding.detection_category || 'Confirmed API'}
                  </span>
                  <span className="text-xs font-mono text-gray-400">Rule ID: {selectedFinding.rule_id}</span>
                </div>
                <h3 className="text-lg font-bold text-white">{selectedFinding.title}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFinding(null)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-navy-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Target Location & Algorithm Meta */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 rounded-xl bg-navy-950 border border-navy-800 text-xs font-mono">
              <div>
                <span className="text-gray-400 block text-[11px]">Algorithm:</span>
                <span className="text-amber-300 font-semibold">{selectedFinding.algorithm}</span>
              </div>
              <div>
                <span className="text-gray-400 block text-[11px]">Primitive:</span>
                <span className="text-cyan-300 capitalize">{selectedFinding.cryptographic_primitive}</span>
              </div>
              <div>
                <span className="text-gray-400 block text-[11px]">Location:</span>
                <span className="text-white truncate block">
                  {selectedFinding.file_path || selectedFinding.asset_id}
                  {selectedFinding.line_number ? ` (L${selectedFinding.line_number})` : ''}
                </span>
              </div>
              <div>
                <span className="text-gray-400 block text-[11px]">Recommended PQC:</span>
                <span className="text-emerald-300 font-semibold">{selectedFinding.recommended_pqc}</span>
              </div>
            </div>

            {/* Evidence Snippet */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
                Sanitized Code & Location Evidence:
              </label>
              <div className="p-3.5 rounded-xl bg-navy-950 border border-navy-800 font-mono text-xs text-gray-200 overflow-x-auto leading-relaxed whitespace-pre-wrap">
                {selectedFinding.evidence || 'No evidence snippet available.'}
              </div>
            </div>

            {/* Action & Migration Guidance */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs space-y-1">
                <h4 className="font-semibold text-amber-300">Why Address First:</h4>
                <p className="text-amber-200/90 leading-relaxed">
                  {selectedFinding.score_rationale || 'Prioritized based on cryptographic primitive and exposure factors.'}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xs space-y-1">
                <h4 className="font-semibold text-cyan-300">First Concrete Action:</h4>
                <p className="text-cyan-200/90 leading-relaxed">{selectedFinding.recommended_action}</p>
                <div className="pt-1 text-[11px] text-cyan-400/80">
                  Target: <strong>{selectedFinding.migration_approach}</strong>
                </div>
              </div>
            </div>

            {/* ================================================================= */}
            {/* INTERACTIVE RISK ASSESSMENT SLIDERS & GOVERNANCE FORM */}
            {/* ================================================================= */}
            <div className="p-5 rounded-xl bg-navy-900 border border-navy-750 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-navy-800">
                <div className="flex items-center space-x-2 text-white font-semibold text-xs">
                  <Calculator className="w-4 h-4 text-cyan-400" />
                  <span>Explainable Risk Assessment Form (S, E, L Factors)</span>
                </div>
                <div className="text-xs font-mono">
                  Calculated Score: <strong className="text-cyan-300">{previewScore}/100</strong>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                {/* 1. Sensitivity (1-5) */}
                <div className="space-y-1.5 p-3 rounded-lg bg-navy-950 border border-navy-800">
                  <div className="flex justify-between font-mono">
                    <span className="text-gray-400">Data Sensitivity (S):</span>
                    <strong className="text-cyan-400">{editSensitivity}/5</strong>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={editSensitivity}
                    onChange={(e) => setEditSensitivity(Number(e.target.value))}
                    className="w-full accent-cyan-400"
                  />
                  <span className="text-[10px] text-gray-400 block">
                    {editSensitivity === 5
                      ? '5: Highly confidential / critical'
                      : editSensitivity === 4
                      ? '4: Financial / PII records'
                      : editSensitivity === 3
                      ? '3: Confidential business'
                      : editSensitivity === 2
                      ? '2: Internal low-sensitivity'
                      : '1: Public data'}
                  </span>
                </div>

                {/* 2. Exposure (1-5) */}
                <div className="space-y-1.5 p-3 rounded-lg bg-navy-950 border border-navy-800">
                  <div className="flex justify-between font-mono">
                    <span className="text-gray-400">System Exposure (E):</span>
                    <strong className="text-cyan-400">{editExposure}/5</strong>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={editExposure}
                    onChange={(e) => setEditExposure(Number(e.target.value))}
                    className="w-full accent-cyan-400"
                  />
                  <span className="text-[10px] text-gray-400 block">
                    {editExposure === 5
                      ? '5: Critical external endpoint'
                      : editExposure === 4
                      ? '4: Internet-facing service'
                      : editExposure === 3
                      ? '3: Internal multi-team'
                      : editExposure === 2
                      ? '2: Restricted internal'
                      : '1: Isolated test environment'}
                  </span>
                </div>

                {/* 3. Lifetime (1-5) */}
                <div className="space-y-1.5 p-3 rounded-lg bg-navy-950 border border-navy-800">
                  <div className="flex justify-between font-mono">
                    <span className="text-gray-400">Confidentiality Lifetime (L):</span>
                    <strong className="text-cyan-400">{editLifetime}/5</strong>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={editLifetime}
                    onChange={(e) => setEditLifetime(Number(e.target.value))}
                    className="w-full accent-cyan-400"
                  />
                  <span className="text-[10px] text-gray-400 block">
                    {editLifetime === 5
                      ? '5: > 10 years secrecy required'
                      : editLifetime === 4
                      ? '4: 6–10 years secrecy'
                      : editLifetime === 3
                      ? '3: 3–5 years secrecy'
                      : editLifetime === 2
                      ? '2: 1–2 years'
                      : '1: < 1 year (ephemeral)'}
                  </span>
                </div>
              </div>

              {/* Formula Math Breakdown */}
              <div className="p-3 bg-navy-950 rounded-lg font-mono text-[11px] text-cyan-300 border border-navy-800 flex items-center justify-between">
                <span>
                  Formula: round((({editSensitivity} + {editExposure} + {editLifetime}) / 15) × 100)
                </span>
                <span className="font-bold text-white">Score = {previewScore}</span>
              </div>

              {/* Ownership & Remediation Inputs */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Assigned Owner:</label>
                  <input
                    type="text"
                    value={editOwner}
                    onChange={(e) => setEditOwner(e.target.value)}
                    placeholder="e.g. sec-ops, alice"
                    className="w-full px-3 py-1.5 rounded-lg bg-navy-950 border border-navy-750 text-white font-mono text-xs focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Target Remediation Date:</label>
                  <input
                    type="date"
                    value={editTargetDate}
                    onChange={(e) => setEditTargetDate(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-navy-950 border border-navy-750 text-white font-mono text-xs focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Remediation Status:</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-navy-950 border border-navy-750 text-white font-mono text-xs focus:outline-none focus:border-cyan-400"
                  >
                    <option value="potential_exposure">Potential Exposure</option>
                    <option value="needs_review">Needs Review</option>
                    <option value="verified_usage">Verified Usage</option>
                    <option value="remediated">Remediated</option>
                    <option value="accepted_risk">Accepted Risk</option>
                  </select>
                </div>
              </div>

              {saveSuccessMsg && (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
                  {saveSuccessMsg}
                </div>
              )}

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  disabled={savingAssessment}
                  onClick={handleSaveAssessment}
                  className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold text-xs transition shadow-lg shadow-cyan-500/20"
                >
                  {savingAssessment ? 'Saving Assessment...' : 'Save Assessment & Recalculate Score'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
