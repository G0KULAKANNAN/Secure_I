export type AssetType = 'server' | 'website' | 'application' | 'certificate' | 'database' | 'other';
export type Environment = 'development' | 'testing' | 'staging' | 'production';
export type Criticality = 'low' | 'medium' | 'high' | 'critical';
export type AssetStatus = 'active' | 'inactive' | 'under_review';

export interface Asset {
  id: string;
  name: string;
  asset_type: AssetType;
  environment: Environment;
  hostname?: string | null;
  ip_address?: string | null;
  owner?: string | null;
  description?: string | null;
  criticality: Criticality;
  status: AssetStatus;
  created_at: string;
  updated_at: string;
}

export interface AssetListResponse {
  status: string;
  assets: Asset[];
  total: number;
  limit: number;
  offset: number;
}

export type JobStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'completed'
  | 'partially_completed'
  | 'failed'
  | 'cancelled';

export type JobType =
  | 'certificate_scan'
  | 'tls_scan'
  | 'static_scan'
  | 'full_orchestrated_scan'
  | 'change_detection';

export interface ScanJob {
  id: string;
  job_type: JobType;
  asset_id: string;
  operation: string;
  status: JobStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  progress: number;
  retry_count: number;
  max_retries: number;
  error_message?: string | null;
  result_data?: Record<string, any> | string | null;
}

export interface JobListResponse {
  status: string;
  jobs: ScanJob[];
  total: number;
  limit: number;
  offset: number;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  python_version: string;
}

export interface SystemVersion {
  status: string;
  name: string;
  version: string;
  api_version: string;
  disclaimer: string;
}
