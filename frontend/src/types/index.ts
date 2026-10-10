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

export type ScanRunStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'partially_completed'
  | 'failed'
  | 'cancelled';

export interface ScanRun {
  id: string;
  asset_id: string;
  requested_scanners: string[];
  status: ScanRunStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  result_summary?: Record<string, any> | null;
  error_summary?: string | null;
}

export interface ScanRunListResponse {
  status: string;
  scan_runs: ScanRun[];
  total: number;
  limit: number;
  offset: number;
}

export type FindingSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

export interface Finding {
  id: string;
  asset_id: string;
  scan_run_id?: string | null;
  job_id?: string | null;
  scanner_type: string;
  algorithm: string;
  cryptographic_primitive: string;
  quantum_vulnerable: boolean;
  recommended_pqc: string;
  rule_id: string;
  title: string;
  description: string;
  severity: FindingSeverity;
  evidence: string;
  file_path?: string | null;
  line_number?: number | null;
  confidence: string;
  remediation_status: string;
  fingerprint: string;
  created_at: string;
  updated_at: string;
}

export interface FindingListResponse {
  status: string;
  findings: Finding[];
  total: number;
  limit: number;
  offset: number;
}

export interface FindingStats {
  total: number;
  total_findings?: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  quantum_vulnerable: number;
}

export interface FindingStatsResponse {
  status: string;
  stats: FindingStats;
}

export interface DirectScanResponse {
  status: string;
  job_id: string;
  asset_id: string;
  scan_result: {
    scanner_type: string;
    asset_id: string;
    status: string;
    findings: any[];
    metadata?: Record<string, any>;
    error_message?: string | null;
  };
  findings: Finding[];
}

export interface MigrationSummary {
  total_assets: number;
  vulnerable_assets: number;
  ml_kem_target_assets: number;
  ml_dsa_target_assets: number;
  fips_standards: Array<{
    name: string;
    title: string;
    status: string;
  }>;
}

export interface MigrationSummaryResponse {
  status: string;
  migration_summary: MigrationSummary;
}

// ==========================================
// Stage 2: Hybrid Cryptography Lab Types
// ==========================================

export interface HostProviderInfo {
  openssl_version: string;
  supports_native_hybrid: boolean;
  supported_hybrid_groups: string[];
  python_ssl_native_pqc: boolean;
  provider_status: string;
  recommendation: string;
}

export interface CryptoCapability {
  id: string;
  classical_group: string;
  pqc_algorithm: string;
  hybrid_combination: string;
  standard_reference: string;
  implementation_provider: string;
  library_version: string;
  client_compatibility: string;
  server_compatibility: string;
  staging_test_status: string;
  negotiation_status: string;
  failure_reason?: string | null;
  security_notes?: string | null;
  last_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CapabilitiesResponse {
  status: string;
  host_provider: HostProviderInfo;
  capabilities: CryptoCapability[];
}

export type HybridMigrationState =
  | 'PLANNED'
  | 'CONFIGURED'
  | 'TESTING'
  | 'VERIFIED'
  | 'FAILED'
  | 'APPROVED';

export interface HybridProfile {
  id: string;
  profile_name: string;
  classical_component: string;
  pqc_component: string;
  hybrid_combination: string;
  environment: string;
  rollout_status: 'disabled' | 'enabled';
  migration_state: HybridMigrationState;
  automatic_production_prohibited: boolean;
  previous_config: Record<string, any>;
  proposed_config: Record<string, any>;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface HybridProfileListResponse {
  status: string;
  profiles: HybridProfile[];
  total: number;
}

export interface HybridProfileResponse {
  status: string;
  profile: HybridProfile;
  runs?: HybridVerificationRun[];
}

export interface HybridVerificationRun {
  id: string;
  profile_id: string;
  test_mode: 'real_tls' | 'simulation';
  status: 'passed' | 'failed' | 'unsupported';
  negotiation_outcome: string;
  classical_client_compatible: boolean;
  hybrid_client_compatible: boolean;
  observed_tls_version?: string | null;
  negotiated_group?: string | null;
  error_details?: string | null;
  duration_ms: number;
  is_simulated: boolean;
  simulation_label: string;
  operator: string;
  created_at: string;
}

export interface HybridTestResponse {
  status: string;
  verification_run: HybridVerificationRun;
}
