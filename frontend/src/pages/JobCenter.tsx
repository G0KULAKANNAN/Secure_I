import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Cpu,
  Play,
  RotateCw,
  XCircle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Search,
  Filter,
  RefreshCw,
  Eye,
  Plus,
  Server,
  Check,
  Copy,
  Terminal,
  Shield,
  Activity,
  Layers,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { listJobs, createJob, cancelJob, retryJob, getWorkerStatus } from '../api/jobs';
import { listAssets } from '../api/assets';
import { ScanJob, JobStatus, JobType, WorkerStatus, Asset } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';

export const JobCenter: React.FC = () => {
  const [jobs, setJobs] = useState<ScanJob[]>([]);
  const [total, setTotal] = useState(0);
  const [workerStatus, setWorkerStatus] = useState<WorkerStatus | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Filters & Pagination
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const [limit] = useState(15);
  const [offset, setOffset] = useState(0);

  // Modals & Action States
  const [isNewJobModalOpen, setIsNewJobModalOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState<ScanJob | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // New Job Form State
  const [newJobType, setNewJobType] = useState<string>('health_check');
  const [newAssetId, setNewAssetId] = useState<string>('');
  const [newPriority, setNewPriority] = useState<number>(5);
  const [newOperation, setNewOperation] = useState<string>('execute');
  const [newPayloadJson, setNewPayloadJson] = useState<string>('');

  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const fetchWorkerAndJobs = useCallback(async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    try {
      const [workerRes, jobsRes] = await Promise.all([
        getWorkerStatus().catch(() => null),
        listJobs({
          status: filterStatus || undefined,
          job_type: filterType || undefined,
          limit,
          offset,
        }),
      ]);

      if (workerRes) setWorkerStatus(workerRes);
      setJobs(jobsRes.jobs || []);
      setTotal(jobsRes.total || 0);
      setError(null);
    } catch (err: any) {
      if (!isBackground) {
        setError(err.message || 'Failed to load background job queue.');
      }
    } finally {
      if (!isBackground) setLoading(false);
    }
  }, [filterStatus, filterType, limit, offset]);

  // Load assets once for dropdown
  useEffect(() => {
    listAssets({ limit: 100 })
      .then((res) => setAssets(res.assets || []))
      .catch(() => {});
  }, []);

  // Primary data load
  useEffect(() => {
    fetchWorkerAndJobs(false);
  }, [fetchWorkerAndJobs]);

  // Auto-refresh interval (every 5 seconds)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchWorkerAndJobs(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchWorkerAndJobs]);

  const handleCopyId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCancelJob = async (jobId: string) => {
    setActionLoading(true);
    try {
      const res = await cancelJob(jobId);
      showNotification(`Job ${jobId} cancellation requested.`, 'success');
      setJobs((prev) => prev.map((j) => (j.id === jobId ? res : j)));
      fetchWorkerAndJobs(true);
    } catch (err: any) {
      showNotification(err.message || 'Failed to cancel job.', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    setActionLoading(true);
    try {
      const res = await retryJob(jobId);
      showNotification(`Job ${jobId} re-queued for execution.`, 'success');
      setJobs((prev) => prev.map((j) => (j.id === jobId ? res : j)));
      fetchWorkerAndJobs(true);
    } catch (err: any) {
      showNotification(err.message || 'Failed to retry job.', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      let parsedPayload: any = undefined;
      if (newPayloadJson.trim()) {
        try {
          parsedPayload = JSON.parse(newPayloadJson);
        } catch {
          throw new Error('Payload must be valid JSON format.');
        }
      }

      await createJob({
        job_type: newJobType as JobType,
        asset_id: newAssetId || undefined,
        priority: newPriority,
        operation: newOperation || 'execute',
        payload_json: parsedPayload,
      });

      showNotification('New background job enqueued successfully.', 'success');
      setIsNewJobModalOpen(false);
      // Reset form
      setNewJobType('health_check');
      setNewAssetId('');
      setNewPriority(5);
      setNewOperation('execute');
      setNewPayloadJson('');
      fetchWorkerAndJobs(false);
    } catch (err: any) {
      showNotification(err.message || 'Failed to create job.', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // Filter jobs by search term on client side
  const filteredJobs = useMemo(() => {
    if (!searchTerm.trim()) return jobs;
    const term = searchTerm.toLowerCase();
    return jobs.filter(
      (j) =>
        j.id.toLowerCase().includes(term) ||
        j.job_type.toLowerCase().includes(term) ||
        (j.asset_id && j.asset_id.toLowerCase().includes(term)) ||
        j.operation.toLowerCase().includes(term)
    );
  }, [jobs, searchTerm]);

  // Metrics calculation
  const metrics = useMemo(() => {
    const running = jobs.filter((j) => j.status === 'running').length;
    const queued = jobs.filter((j) => j.status === 'queued' || j.status === 'pending').length;
    const completed = jobs.filter((j) => j.status === 'completed').length;
    const failed = jobs.filter((j) => j.status === 'failed').length;
    return { running, queued, completed, failed, total: total || jobs.length };
  }, [jobs, total]);

  const getStatusBadge = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return <StatusBadge status="Completed" variant="emerald" />;
      case 'running':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border font-mono tracking-wide bg-cyan-500/10 text-cyan-300 border-cyan-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            Running
          </span>
        );
      case 'queued':
        return <StatusBadge status="Queued" variant="amber" />;
      case 'pending':
        return <StatusBadge status="Pending" variant="gray" />;
      case 'cancel_requested':
        return <StatusBadge status="Cancel Req." variant="amber" />;
      case 'cancelled':
        return <StatusBadge status="Cancelled" variant="gray" />;
      case 'failed':
        return <StatusBadge status="Failed" variant="rose" />;
      case 'partially_completed':
        return <StatusBadge status="Partial" variant="violet" />;
      default:
        return <StatusBadge status={status} variant="gray" />;
    }
  };

  const getJobTypeBadge = (jobType: string) => {
    const typeStyles: Record<string, string> = {
      health_check: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      asset_validation: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
      certificate_scan: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
      tls_scan: 'bg-violet-500/10 text-violet-400 border-violet-500/30',
      static_scan: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      full_orchestrated_scan: 'bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/30',
      change_detection: 'bg-teal-500/10 text-teal-400 border-teal-500/30',
    };
    const style = typeStyles[jobType] || 'bg-navy-800 text-gray-300 border-navy-700';
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border ${style}`}>
        {jobType.replace(/_/g, ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center p-4 rounded-lg border shadow-lg backdrop-blur-md transition-all ${
            notification.type === 'success'
              ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-200'
              : 'bg-rose-950/80 border-rose-500/50 text-rose-200'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 mr-3 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-5 h-5 mr-3 text-rose-400" />
          )}
          <span className="text-sm font-medium">{notification.message}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Background Job Center</h1>
              <p className="text-sm text-gray-400">
                Persistent SQLite queue orchestration, thread worker health monitoring, and asynchronous scan lifecycle.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
              autoRefresh
                ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                : 'bg-navy-900 text-gray-400 border-navy-750 hover:text-gray-300'
            }`}
            title="Toggle 5-second polling"
          >
            <span className={`w-2 h-2 rounded-full ${autoRefresh ? 'bg-cyan-400 animate-pulse' : 'bg-gray-500'}`} />
            Auto-refresh {autoRefresh ? 'On (5s)' : 'Off'}
          </button>

          <button
            onClick={() => fetchWorkerAndJobs(false)}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-navy-850 hover:bg-navy-800 text-gray-300 border border-navy-750 hover:border-navy-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            Refresh
          </button>

          <button
            onClick={() => setIsNewJobModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            Trigger New Job
          </button>
        </div>
      </div>

      {/* Worker Health Status & Queue Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Engine Card */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-750 backdrop-blur-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Worker Engine</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-white">
              {workerStatus?.status === 'running' ? 'Active' : workerStatus?.status || 'Online'}
            </span>
            <span className="text-xs text-cyan-400 font-mono">
              {workerStatus ? `${workerStatus.active_workers}/${workerStatus.max_workers} Threads` : 'Ready'}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400 font-mono flex items-center justify-between border-t border-navy-800 pt-2">
            <span>Uptime:</span>
            <span className="text-gray-300">
              {workerStatus ? `${Math.round(workerStatus.uptime_seconds)}s` : '0s'}
            </span>
          </div>
        </div>

        {/* Total Jobs */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-750 backdrop-blur-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Total Jobs</span>
            <Layers className="w-4 h-4 text-violet-400" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold font-mono text-white">{metrics.total}</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400 font-mono border-t border-navy-800 pt-2">
            Lifetime database records
          </div>
        </div>

        {/* Running Jobs */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-750 backdrop-blur-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Executing</span>
            <Clock className="w-4 h-4 text-cyan-400 animate-spin" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-cyan-400">{metrics.running}</span>
            <span className="text-xs text-gray-400">active threads</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400 font-mono border-t border-navy-800 pt-2">
            Processing in background
          </div>
        </div>

        {/* Queued / Pending */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-750 backdrop-blur-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Queued / Pending</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold font-mono text-amber-400">{metrics.queued}</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400 font-mono border-t border-navy-800 pt-2">
            Awaiting worker claim
          </div>
        </div>

        {/* Completed vs Failed */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-750 backdrop-blur-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Completed / Failed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">{metrics.completed}</span>
            <span className="text-sm text-gray-400">/</span>
            <span className="text-2xl font-bold font-mono text-rose-400">{metrics.failed}</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400 font-mono border-t border-navy-800 pt-2">
            Finished execution states
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-750 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search Job ID, Type, Asset..."
            className="w-full pl-9 pr-4 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <select
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value);
                setOffset(0);
              }}
              className="bg-navy-950 border border-navy-750 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Statuses</option>
              <option value="running">Running</option>
              <option value="queued">Queued</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
              <option value="cancel_requested">Cancel Requested</option>
            </select>
          </div>

          {/* Job Type Filter */}
          <select
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setOffset(0);
            }}
            className="bg-navy-950 border border-navy-750 rounded-lg px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Job Types</option>
            <option value="health_check">Health Check</option>
            <option value="asset_validation">Asset Validation</option>
            <option value="certificate_scan">Certificate Scan</option>
            <option value="tls_scan">TLS Scan</option>
            <option value="static_scan">Static Scan</option>
            <option value="full_orchestrated_scan">Full Orchestrated Scan</option>
            <option value="change_detection">Change Detection</option>
          </select>
        </div>
      </div>

      {/* Main Jobs Table */}
      <div className="rounded-xl border border-navy-750 bg-navy-900/60 overflow-hidden shadow-xl">
        {loading && jobs.length === 0 ? (
          <div className="p-12">
            <LoadingState message="Connecting to SQLite persistent job engine..." />
          </div>
        ) : error && jobs.length === 0 ? (
          <div className="p-12">
            <ErrorState message={error} onRetry={() => fetchWorkerAndJobs(false)} />
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="p-12">
            <EmptyState
              title="No scan jobs found"
              description="No background execution tasks match your selected search or filter criteria."
              actionText="Trigger New Job"
              onAction={() => setIsNewJobModalOpen(true)}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-navy-750 bg-navy-950/70 text-xs text-gray-400 font-semibold uppercase tracking-wider">
                  <th className="py-3.5 px-4">Job ID</th>
                  <th className="py-3.5 px-4">Job Type</th>
                  <th className="py-3.5 px-4">Target Asset</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Progress</th>
                  <th className="py-3.5 px-4">Priority</th>
                  <th className="py-3.5 px-4">Attempts</th>
                  <th className="py-3.5 px-4">Created / Finished</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800 text-sm">
                {filteredJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-navy-850/50 transition-colors">
                    {/* Job ID */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-cyan-300">{job.id}</span>
                        <button
                          onClick={() => handleCopyId(job.id)}
                          className="p-1 hover:text-white text-gray-500 transition"
                          title="Copy ID"
                        >
                          {copiedId === job.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </td>

                    {/* Job Type */}
                    <td className="py-3.5 px-4">{getJobTypeBadge(job.job_type)}</td>

                    {/* Target Asset */}
                    <td className="py-3.5 px-4">
                      {job.asset_id ? (
                        <span className="inline-flex items-center gap-1.5 font-mono text-xs text-gray-300">
                          <Server className="w-3 h-3 text-gray-500" />
                          {job.asset_id}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-500 italic">System / Engine</span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-4">{getStatusBadge(job.status)}</td>

                    {/* Progress */}
                    <td className="py-3.5 px-4">
                      <div className="w-28 space-y-1">
                        <div className="flex justify-between text-[11px] font-mono text-gray-400">
                          <span>{job.progress}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-navy-950 rounded-full overflow-hidden border border-navy-800">
                          <div
                            className={`h-full transition-all duration-300 ${
                              job.status === 'completed'
                                ? 'bg-emerald-500'
                                : job.status === 'failed'
                                ? 'bg-rose-500'
                                : 'bg-gradient-to-r from-cyan-500 to-blue-500'
                            }`}
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Priority */}
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-navy-950 border border-navy-750 text-gray-300">
                        P{job.priority || 5}
                      </span>
                    </td>

                    {/* Attempts */}
                    <td className="py-3.5 px-4">
                      <span
                        className={`text-xs font-mono ${
                          (job.attempt_count || job.retry_count || 0) > 1 ? 'text-amber-400' : 'text-gray-400'
                        }`}
                      >
                        {job.attempt_count ?? job.retry_count ?? 0} / {job.max_attempts ?? job.max_retries ?? 3}
                      </span>
                    </td>

                    {/* Timestamps */}
                    <td className="py-3.5 px-4">
                      <div className="flex flex-col text-xs font-mono">
                        <span className="text-gray-300">{new Date(job.created_at).toLocaleTimeString()}</span>
                        <span className="text-[10px] text-gray-500">
                          {job.finished_at || job.completed_at
                            ? `Done: ${new Date(job.finished_at || job.completed_at!).toLocaleTimeString()}`
                            : job.started_at
                            ? `Started: ${new Date(job.started_at).toLocaleTimeString()}`
                            : 'In queue'}
                        </span>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setSelectedJob(job)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-cyan-300 hover:bg-navy-800 transition"
                          title="Inspect Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {(job.status === 'running' || job.status === 'queued' || job.status === 'pending') && (
                          <button
                            onClick={() => handleCancelJob(job.id)}
                            disabled={actionLoading}
                            className="p-1.5 rounded-lg text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition"
                            title="Cancel Job"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}

                        {(job.status === 'failed' || job.status === 'cancelled') &&
                          (job.attempt_count ?? job.retry_count ?? 0) <
                            (job.max_attempts ?? job.max_retries ?? 3) && (
                            <button
                              onClick={() => handleRetryJob(job.id)}
                              disabled={actionLoading}
                              className="p-1.5 rounded-lg text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 transition"
                              title="Retry Job"
                            >
                              <RotateCw className="w-4 h-4" />
                            </button>
                          )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        <div className="py-3.5 px-4 border-t border-navy-750 bg-navy-950/60 flex items-center justify-between text-xs text-gray-400">
          <span>
            Showing <strong className="text-gray-200">{filteredJobs.length}</strong> of{' '}
            <strong className="text-gray-200">{total}</strong> jobs
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="p-1.5 rounded-lg border border-navy-750 disabled:opacity-40 hover:bg-navy-850 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-xs">
              Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(total / limit))}
            </span>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="p-1.5 rounded-lg border border-navy-750 disabled:opacity-40 hover:bg-navy-850 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Trigger New Job Modal                                         */}
      {/* ------------------------------------------------------------- */}
      {isNewJobModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl bg-navy-900 border border-navy-750 shadow-2xl p-6 space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-navy-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  <Play className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Enqueue Background Task</h2>
                  <p className="text-xs text-gray-400">Schedule a persistent job in the SQLite execution queue.</p>
                </div>
              </div>
              <button
                onClick={() => setIsNewJobModalOpen(false)}
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-navy-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateJob} className="space-y-4">
              {/* Job Type */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                  Job Type *
                </label>
                <select
                  value={newJobType}
                  onChange={(e) => {
                    setNewJobType(e.target.value);
                    if (e.target.value === 'health_check') {
                      setNewAssetId('');
                      setNewOperation('run_health_probe');
                    } else if (e.target.value === 'asset_validation') {
                      setNewOperation('validate_asset_config');
                    }
                  }}
                  className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="health_check">health_check (Safe system diagnosis, no asset required)</option>
                  <option value="asset_validation">asset_validation (Validates asset configuration)</option>
                  <option value="certificate_scan">certificate_scan (Inspects certificates)</option>
                  <option value="tls_scan">tls_scan (TLS cipher probe)</option>
                  <option value="static_scan">static_scan (Static cryptography audit)</option>
                  <option value="full_orchestrated_scan">full_orchestrated_scan (End-to-end inspection)</option>
                  <option value="change_detection">change_detection (Drift detection)</option>
                </select>
              </div>

              {/* Target Asset */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                  Target Asset {newJobType === 'asset_validation' ? '*' : '(Optional)'}
                </label>
                <select
                  value={newAssetId}
                  onChange={(e) => setNewAssetId(e.target.value)}
                  className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500 font-mono text-xs"
                >
                  <option value="">None (System / Global Engine Job)</option>
                  {assets.map((ast) => (
                    <option key={ast.id} value={ast.id}>
                      [{ast.asset_type.toUpperCase()}] {ast.name} ({ast.id})
                    </option>
                  ))}
                </select>
                {newJobType === 'asset_validation' && !newAssetId && (
                  <p className="text-[11px] text-amber-400 mt-1">Asset selection is required for asset_validation.</p>
                )}
              </div>

              {/* Priority and Operation */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                    Priority (1 to 10)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={newPriority}
                    onChange={(e) => setNewPriority(parseInt(e.target.value) || 5)}
                    className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                  <span className="text-[10px] text-gray-500">10 = Highest priority</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                    Operation Name
                  </label>
                  <input
                    type="text"
                    value={newOperation}
                    onChange={(e) => setNewOperation(e.target.value)}
                    placeholder="e.g. run_health_probe"
                    className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>

              {/* Optional JSON Payload */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                  Parameters / Payload (JSON)
                </label>
                <textarea
                  rows={3}
                  value={newPayloadJson}
                  onChange={(e) => setNewPayloadJson(e.target.value)}
                  placeholder='{"depth": "thorough", "timeout_seconds": 30}'
                  className="w-full px-3 py-2 bg-navy-950 border border-navy-750 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-navy-800">
                <button
                  type="button"
                  onClick={() => setIsNewJobModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-navy-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || (newJobType === 'asset_validation' && !newAssetId)}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
                >
                  {actionLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  Enqueue Job
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Job Details & Output Viewer Modal                             */}
      {/* ------------------------------------------------------------- */}
      {selectedJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm">
          <div className="w-full max-w-3xl rounded-2xl bg-navy-900 border border-navy-750 shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-navy-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white">Job Inspector</h2>
                    <span className="font-mono text-xs text-cyan-400">[{selectedJob.id}]</span>
                  </div>
                  <p className="text-xs text-gray-400">Detailed execution trace and output payload.</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-navy-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick Metadata Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-navy-950/60 border border-navy-800 text-xs">
              <div>
                <span className="text-gray-500 block">Status</span>
                <span className="mt-1 block">{getStatusBadge(selectedJob.status)}</span>
              </div>
              <div>
                <span className="text-gray-500 block">Job Type</span>
                <span className="font-mono text-white mt-1 block">{selectedJob.job_type}</span>
              </div>
              <div>
                <span className="text-gray-500 block">Target Asset</span>
                <span className="font-mono text-gray-300 mt-1 block">{selectedJob.asset_id || 'System'}</span>
              </div>
              <div>
                <span className="text-gray-500 block">Priority / Attempts</span>
                <span className="font-mono text-white mt-1 block">
                  P{selectedJob.priority} | {selectedJob.attempt_count ?? selectedJob.retry_count ?? 0}/
                  {selectedJob.max_attempts ?? selectedJob.max_retries ?? 3}
                </span>
              </div>
            </div>

            {/* Timestamps */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono p-3 rounded-lg bg-navy-950/40 border border-navy-800">
              <div>
                <span className="text-gray-500">Created: </span>
                <span className="text-gray-300">{new Date(selectedJob.created_at).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-gray-500">Started: </span>
                <span className="text-gray-300">
                  {selectedJob.started_at ? new Date(selectedJob.started_at).toLocaleString() : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Finished: </span>
                <span className="text-gray-300">
                  {selectedJob.finished_at || selectedJob.completed_at
                    ? new Date(selectedJob.finished_at || selectedJob.completed_at!).toLocaleString()
                    : 'N/A'}
                </span>
              </div>
            </div>

            {/* Error Message if failed */}
            {selectedJob.error_message && (
              <div className="p-3.5 rounded-lg bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-rose-400">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Error Code: {selectedJob.error_code || 'EXECUTION_FAILED'}</span>
                </div>
                <p className="font-mono">{selectedJob.error_message}</p>
              </div>
            )}

            {/* Output Result JSON */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Result Output</span>
                {selectedJob.result_json && (
                  <button
                    onClick={() => handleCopyId(JSON.stringify(selectedJob.result_json, null, 2))}
                    className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300"
                  >
                    <Copy className="w-3 h-3" />
                    Copy JSON
                  </button>
                )}
              </div>
              <div className="p-3.5 rounded-xl bg-navy-950 border border-navy-800 font-mono text-xs text-gray-200 overflow-x-auto max-h-60">
                {selectedJob.result_json || selectedJob.result_data ? (
                  <pre>{JSON.stringify(selectedJob.result_json || selectedJob.result_data, null, 2)}</pre>
                ) : (
                  <span className="text-gray-500 italic">No execution result available yet.</span>
                )}
              </div>
            </div>

            {/* Payload JSON */}
            {selectedJob.payload_json && (
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 block mb-2">
                  Input Payload
                </span>
                <div className="p-3.5 rounded-xl bg-navy-950 border border-navy-800 font-mono text-xs text-gray-300 overflow-x-auto max-h-40">
                  <pre>{JSON.stringify(selectedJob.payload_json, null, 2)}</pre>
                </div>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-navy-800">
              <button
                onClick={() => setSelectedJob(null)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-gray-300 hover:text-white bg-navy-800 hover:bg-navy-750 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobCenter;
