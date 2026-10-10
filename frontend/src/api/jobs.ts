import { ScanJob, JobListResponse } from '../types';

const API_BASE_URL = '/api/v1';

export interface JobFilterParams {
  asset_id?: string;
  status?: string;
  job_type?: string;
  limit?: number;
  offset?: number;
}

export async function listJobs(params?: JobFilterParams): Promise<JobListResponse> {
  const query = new URLSearchParams();
  if (params) {
    if (params.asset_id) query.set('asset_id', params.asset_id);
    if (params.status) query.set('status', params.status);
    if (params.job_type) query.set('job_type', params.job_type);
    if (params.limit !== undefined) query.set('limit', params.limit.toString());
    if (params.offset !== undefined) query.set('offset', params.offset.toString());
  }

  const url = `${API_BASE_URL}/jobs${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch jobs (HTTP ${response.status})`);
  }
  return response.json();
}

export async function getJob(jobId: string): Promise<ScanJob> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch job (HTTP ${response.status})`);
  }
  const data = await response.json();
  return data.job;
}

export async function createJob(data: Partial<ScanJob>): Promise<ScanJob> {
  const response = await fetch(`${API_BASE_URL}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to create scan job (HTTP ${response.status})`);
  }
  const result = await response.json();
  return result.job;
}

export async function cancelJob(jobId: string): Promise<ScanJob> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/cancel`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to cancel job (HTTP ${response.status})`);
  }
  const result = await response.json();
  return result.job;
}

export async function retryJob(jobId: string): Promise<ScanJob> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/retry`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to retry job (HTTP ${response.status})`);
  }
  const result = await response.json();
  return result.job;
}

export async function getWorkerStatus(): Promise<import('../types').WorkerStatus> {
  const response = await fetch(`${API_BASE_URL}/worker/status`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch worker status (HTTP ${response.status})`);
  }
  const result = await response.json();
  return result.worker;
}

