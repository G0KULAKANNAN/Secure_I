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
  ExternalLink,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { fetchFindings, updateFindingStatus } from '../api/scans';
import { Finding } from '../types';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';

export const Findings: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [statusUpdating, setStatusUpdating] = useState<boolean>(false);

  const loadFindings = async () => {
    try {
      const res = await fetchFindings({ limit: 100 });
      setFindings(res.findings || []);
    } catch (err) {
      console.error('Failed to load findings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFindings();
  }, []);

  const handleUpdateStatus = async (newStatus: string) => {
    if (!selectedFinding) return;
    setStatusUpdating(true);
    try {
      const updated = await updateFindingStatus(selectedFinding.id, newStatus);
      setSelectedFinding(updated);
      setFindings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
    } catch (err) {
      console.error('Failed to update status:', err);
    } finally {
      setStatusUpdating(false);
    }
  };

  const filteredFindings = findings.filter((f) => {
    if (filterType !== 'all' && f.scanner_type !== filterType) return false;
    if (filterSeverity !== 'all' && f.severity !== filterSeverity) return false;
    return true;
  });

  const getScannerLabel = (type: string) => {
    switch (type) {
      case 'static_scan':
        return { label: 'Source Code', color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20' };
      case 'tls_scan':
        return { label: 'Live Server', color: 'text-violet-400 bg-violet-500/10 border-violet-500/20' };
      case 'certificate_scan':
        return { label: 'Certificate', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' };
      default:
        return { label: type, color: 'text-gray-400 bg-navy-800 border-navy-700' };
    }
  };

  const getWhyItMatters = (finding: Finding) => {
    const alg = (finding.algorithm || '').toUpperCase();
    if (alg.includes('RSA') || alg.includes('2048') || alg.includes('4096')) {
      return "Shor's algorithm can factor RSA integers on quantum computers, breaking public-key encryption and signatures.";
    }
    if (alg.includes('EC') || alg.includes('ECDH') || alg.includes('ECDSA') || alg.includes('SECP')) {
      return "Elliptic curve discrete logarithms are breakable by Shor's algorithm; network sessions risk Store-Now-Decrypt-Later (SNDL).";
    }
    if (alg.includes('DH') || alg.includes('DIFFIE')) {
      return "Classical Diffie-Hellman discrete logarithm is vulnerable to Shor's algorithm; session keys can be retroactively solved.";
    }
    if (finding.quantum_vulnerable) {
      return "Relies on classical asymmetric cryptography solvable in polynomial time by quantum algorithms.";
    }
    return "Legacy cryptographic primitive identified for security hardening.";
  };

  if (loading) {
    return <LoadingState message="Loading discovered cryptographic findings..." />;
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="border-b border-navy-750 pb-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Cryptographic Findings</h1>
          <p className="text-sm text-gray-400 mt-1">
            Empirical observations of quantum-vulnerable algorithms discovered across code and network servers.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2 bg-navy-850 border border-navy-750 rounded-xl px-3 py-1.5 text-xs text-gray-300">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-gray-400">Scan Type:</span>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-transparent text-white font-medium focus:outline-none"
            >
              <option value="all" className="bg-navy-900">All Scans</option>
              <option value="static_scan" className="bg-navy-900">Source Code</option>
              <option value="tls_scan" className="bg-navy-900">Live Server</option>
              <option value="certificate_scan" className="bg-navy-900">Certificate</option>
            </select>
          </div>

          <div className="flex items-center space-x-2 bg-navy-850 border border-navy-750 rounded-xl px-3 py-1.5 text-xs text-gray-300">
            <span className="text-gray-400">Severity:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="bg-transparent text-white font-medium focus:outline-none"
            >
              <option value="all" className="bg-navy-900">All Severities</option>
              <option value="critical" className="bg-navy-900">Critical</option>
              <option value="high" className="bg-navy-900">High</option>
              <option value="medium" className="bg-navy-900">Medium</option>
              <option value="low" className="bg-navy-900">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Findings Table */}
      {filteredFindings.length === 0 ? (
        <div className="rounded-2xl bg-navy-850 border border-navy-750 p-12 text-center space-y-4">
          <div className="p-3 w-12 h-12 mx-auto rounded-full bg-navy-950 border border-navy-800 text-gray-400 flex items-center justify-center">
            <FileSearch className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No cryptographic findings matching filters</h3>
          <p className="text-xs text-gray-400 max-w-md mx-auto">
            Run a scan on your source code or live servers from the Scan page to populate real findings.
          </p>
          <Link
            to="/scan"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold text-xs transition"
          >
            <span>Run New Scan</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="rounded-2xl bg-navy-850 border border-navy-750 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-950 text-gray-400 font-mono text-[11px] border-b border-navy-750 uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Target / Location</th>
                  <th className="py-3.5 px-4">Scan Type</th>
                  <th className="py-3.5 px-4">Detected Algorithm</th>
                  <th className="py-3.5 px-4">Why It Matters</th>
                  <th className="py-3.5 px-4">Confidence</th>
                  <th className="py-3.5 px-4">Recommended Action</th>
                  <th className="py-3.5 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-750/70 bg-navy-900/60">
                {filteredFindings.map((f) => {
                  const scannerBadge = getScannerLabel(f.scanner_type);
                  return (
                    <tr
                      key={f.id}
                      onClick={() => setSelectedFinding(f)}
                      className="hover:bg-navy-800/60 cursor-pointer transition group"
                    >
                      <td className="py-3.5 px-4 font-mono font-medium text-white max-w-[180px] truncate">
                        {f.file_path || f.asset_id}
                        {f.line_number ? `:${f.line_number}` : ''}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${scannerBadge.color}`}>
                          {scannerBadge.label}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-semibold text-amber-300">
                        {f.algorithm}
                      </td>
                      <td className="py-3.5 px-4 text-gray-300 max-w-[280px] leading-relaxed">
                        {getWhyItMatters(f)}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-sans font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          Needs verification
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-cyan-300 font-medium">
                        Migration review recommended
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <span className="text-gray-400 group-hover:text-cyan-400 inline-flex items-center space-x-1 text-[11px] font-medium">
                          <span>Review</span>
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

      {/* ========================================================================= */}
      {/* Evidence & Finding Detail Modal */}
      {/* ========================================================================= */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-2xl rounded-2xl bg-navy-850 border border-navy-750 shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-navy-750">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase font-semibold">
                    {selectedFinding.severity}
                  </span>
                  <span className="text-xs font-mono text-gray-400">
                    Rule ID: {selectedFinding.rule_id}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white">
                  {selectedFinding.title || `Quantum-Vulnerable ${selectedFinding.algorithm}`}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFinding(null)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-navy-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Target & Algorithm Metadata Grid */}
            <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-navy-950 border border-navy-800 text-xs font-mono">
              <div>
                <span className="text-gray-400 block text-[11px]">Detected Algorithm:</span>
                <span className="text-amber-300 font-semibold">{selectedFinding.algorithm}</span>
              </div>
              <div>
                <span className="text-gray-400 block text-[11px]">Primitive Type:</span>
                <span className="text-cyan-300 capitalize">
                  {selectedFinding.cryptographic_primitive.replace('_', ' ')}
                </span>
              </div>
              <div>
                <span className="text-gray-400 block text-[11px]">Location / Target:</span>
                <span className="text-white truncate block">
                  {selectedFinding.file_path || selectedFinding.asset_id}
                  {selectedFinding.line_number ? ` (Line ${selectedFinding.line_number})` : ''}
                </span>
              </div>
              <div>
                <span className="text-gray-400 block text-[11px]">Recommended PQC Standard:</span>
                <span className="text-emerald-300 font-semibold">{selectedFinding.recommended_pqc}</span>
              </div>
            </div>

            {/* Sanitized Evidence Excerpt */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">
                Sanitized Evidence Excerpt:
              </label>
              <div className="p-3.5 rounded-xl bg-navy-950 border border-navy-800 font-mono text-xs text-gray-200 overflow-x-auto leading-relaxed whitespace-pre-wrap">
                {selectedFinding.evidence || 'No raw evidence snippet available.'}
              </div>
            </div>

            {/* Why It Matters Explanation */}
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 leading-relaxed space-y-1">
              <h4 className="font-semibold text-amber-300">Why this matters:</h4>
              <p>{getWhyItMatters(selectedFinding)}</p>
            </div>

            {/* Remediation Status Buttons */}
            <div className="pt-2 border-t border-navy-750 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-gray-400">Current Status:</span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-navy-950 border border-navy-800 text-cyan-300 capitalize">
                  {selectedFinding.remediation_status.replace('_', ' ')}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  disabled={statusUpdating}
                  onClick={() => handleUpdateStatus('verified_usage')}
                  className="px-3 py-1.5 rounded-lg bg-navy-900 hover:bg-navy-750 border border-navy-700 text-xs font-medium text-gray-200 transition"
                >
                  Mark Verified
                </button>
                <button
                  type="button"
                  disabled={statusUpdating}
                  onClick={() => handleUpdateStatus('remediated')}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition"
                >
                  Mark Remediated
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
