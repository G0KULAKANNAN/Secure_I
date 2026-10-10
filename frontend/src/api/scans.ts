import {
  DirectScanResponse,
  FindingListResponse,
  FindingStats,
  FindingStatsResponse,
  Finding,
  ScanRunListResponse,
  MigrationSummary,
  MigrationSummaryResponse,
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

export async function fetchFindings(params?: {
  asset_id?: string;
  severity?: string;
  scanner_type?: string;
  limit?: number;
  offset?: number;
}): Promise<FindingListResponse> {
  const query = new URLSearchParams();
  if (params?.asset_id) query.set('asset_id', params.asset_id);
  if (params?.severity) query.set('severity', params.severity);
  if (params?.scanner_type) query.set('scanner_type', params.scanner_type);
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
