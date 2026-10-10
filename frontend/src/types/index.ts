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
  | 'cancel_requested'
  | 'cancelled';

export type JobType =
  | 'health_check'
  | 'asset_validation'
  | 'certificate_scan'
  | 'tls_scan'
  | 'static_scan'
  | 'full_orchestrated_scan'
  | 'change_detection';

export interface ScanJob {
  id: string;
  job_type: JobType | string;
  asset_id?: string | null;
  operation: string;
  status: JobStatus;
  priority: number;
  payload_json?: any;
  result_json?: any;
  progress: number;
  attempt_count: number;
  max_attempts: number;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  updated_at: string;
  next_retry_at?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  // Backward compatibility fields
  retry_count?: number;
  max_retries?: number;
  completed_at?: string | null;
  result_data?: any;
}

export interface JobListResponse {
  status: string;
  jobs: ScanJob[];
  total: number;
  limit: number;
  offset: number;
}

export interface WorkerStatus {
  engine: string;
  status: string;
  uptime_seconds: number;
  max_workers: number;
  active_workers: number;
  queue_depth: number;
  processed_count: number;
  succeeded_count: number;
  failed_count: number;
  retried_count: number;
}

export interface WorkerStatusResponse {
  status: string;
  worker: WorkerStatus;
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
