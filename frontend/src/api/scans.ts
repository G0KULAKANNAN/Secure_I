import {
  DirectScanResponse,
  FindingListResponse,
  FindingStats,
  FindingStatsResponse,
  Finding,
  ScanRunListResponse,
  MigrationSummary,
  MigrationSummaryResponse,
  SystemScanResponse,
  SystemScanConfig,
  RemediationQueueData,
  RemediationQueueResponse,
} from '../types';

const API_BASE_URL = '/api/v1';

export async function scanSourceCode(options: {
  source_content?: string;
  file?: File;
  file_name?: string;
}): Promise<DirectScanResponse> {
  let response: Response;

  if (options.file) {
    const formData = new FormData();
    formData.append('file', options.file);
    response = await fetch(`${API_BASE_URL}/scanners/source`, {
      method: 'POST',
      body: formData,
    });
  } else {
    response = await fetch(`${API_BASE_URL}/scanners/source`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_content: options.source_content || '',
        file_name: options.file_name || 'source_code.py',
      }),
    });
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || data?.message || 'Failed to scan source code.');
  }
  return data;
}

export async function scanLiveServer(options: {
  hostname: string;
  port?: number;
  authorized: boolean;
}): Promise<DirectScanResponse> {
  const response = await fetch(`${API_BASE_URL}/scanners/tls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      hostname: options.hostname.trim(),
      port: options.port || 443,
      authorized: options.authorized,
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || data?.message || 'Failed to scan live server.');
  }
  return data;
}

export async function scanCertificate(options: {
  file?: File;
  certificate_data?: string;
  file_name?: string;
}): Promise<DirectScanResponse> {
  let response: Response;

  if (options.file) {
    const formData = new FormData();
    formData.append('file', options.file);
    response = await fetch(`${API_BASE_URL}/scanners/certificate`, {
      method: 'POST',
      body: formData,
    });
  } else {
    response = await fetch(`${API_BASE_URL}/scanners/certificate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        certificate_data: options.certificate_data || '',
        file_name: options.file_name || 'certificate.pem',
      }),
    });
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || data?.message || 'Failed to scan certificate.');
  }
  return data;
}

export async function startSystemScan(options?: {
  target_scope?: string;
  target_directory?: string;
  max_file_size_bytes?: number;
  include_extensions?: string[];
  exclude_directories?: string[];
}): Promise<SystemScanResponse> {
  const response = await fetch(`${API_BASE_URL}/scanners/system`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options || { target_scope: 'project' }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || data?.message || 'Failed to start system file scan.');
  }
  return data;
}

export async function fetchSystemScanConfig(): Promise<SystemScanConfig> {
  const response = await fetch(`${API_BASE_URL}/scanners/system/config`);
  if (!response.ok) {
    throw new Error('Failed to load system scanner configuration.');
  }
  const data = await response.json();
  return data.config;
}

export async function fetchFindings(params?: {
  asset_id?: string;
  severity?: string;
  scanner_type?: string;
  status?: string;
  risk_category?: string;
  algorithm?: string;
  owner?: string;
  queue_group?: string;
  sort_by?: string;
  order?: string;
  limit?: number;
  offset?: number;
}): Promise<FindingListResponse> {
  const query = new URLSearchParams();
  if (params?.asset_id) query.set('asset_id', params.asset_id);
  if (params?.severity) query.set('severity', params.severity);
  if (params?.scanner_type) query.set('scanner_type', params.scanner_type);
  if (params?.status) query.set('status', params.status);
  if (params?.risk_category) query.set('risk_category', params.risk_category);
  if (params?.algorithm) query.set('algorithm', params.algorithm);
  if (params?.owner) query.set('owner', params.owner);
  if (params?.queue_group) query.set('queue_group', params.queue_group);
  if (params?.sort_by) query.set('sort_by', params.sort_by);
  if (params?.order) query.set('order', params.order);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));

  const qs = query.toString();
  const url = `${API_BASE_URL}/findings${qs ? `?${qs}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load findings (Status ${response.status})`);
  }
  return response.json();
}

export async function fetchFindingStats(asset_id?: string): Promise<FindingStats> {
  const url = asset_id
    ? `${API_BASE_URL}/findings/stats?asset_id=${encodeURIComponent(asset_id)}`
    : `${API_BASE_URL}/findings/stats`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load finding statistics (Status ${response.status})`);
  }
  const data: FindingStatsResponse = await response.json();
  return data.stats;
}

export async function updateFindingStatus(
  findingId: string,
  remediationStatus: string
): Promise<Finding> {
  const response = await fetch(`${API_BASE_URL}/findings/${findingId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ remediation_status: remediationStatus }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || 'Failed to update finding status.');
  }
  return data.finding;
}

export async function assessFinding(
  findingId: string,
  data: {
    data_sensitivity?: number | null;
    exposure?: number | null;
    confidentiality_lifetime?: number | null;
    assigned_owner?: string | null;
    target_remediation_date?: string | null;
    remediation_status?: string;
  }
): Promise<Finding> {
  const response = await fetch(`${API_BASE_URL}/findings/${findingId}/assess`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData?.error || 'Failed to update finding risk assessment.');
  }
  return resData.finding;
}

export async function fetchRemediationQueue(): Promise<RemediationQueueData> {
  const response = await fetch(`${API_BASE_URL}/findings/queue`);
  if (!response.ok) {
    throw new Error('Failed to load Monday Morning Remediation Queue.');
  }
  const data: RemediationQueueResponse = await response.json();
  return data.queue;
}

export async function fetchScanRuns(limit: number = 10, offset: number = 0): Promise<ScanRunListResponse> {
  const response = await fetch(`${API_BASE_URL}/scans?limit=${limit}&offset=${offset}`);
  if (!response.ok) {
    throw new Error(`Failed to load scan runs (Status ${response.status})`);
  }
  return response.json();
}

export async function fetchMigrationSummary(): Promise<MigrationSummary> {
  const response = await fetch(`${API_BASE_URL}/migration`);
  if (!response.ok) {
    throw new Error(`Failed to load migration summary (Status ${response.status})`);
  }
  const data: MigrationSummaryResponse = await response.json();
  return data.migration_summary;
}
