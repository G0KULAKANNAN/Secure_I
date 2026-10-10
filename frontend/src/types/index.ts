export type Environment = 'development' | 'testing' | 'production';
export type Criticality = 'low' | 'medium' | 'high' | 'critical';
export type FindingStatus =
  | 'potential_exposure'
  | 'verified_usage'
  | 'needs_review'
  | 'insufficient_evidence'
  | 'remediated'
  | 'accepted_risk';
export type MigrationStatus = 'not_started' | 'assessment' | 'testing' | 'approved' | 'completed';

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

export interface Asset {
  id: string;
  name: string;
  type: string;
  owner: string;
  environment: Environment;
  data_sensitivity: number;
  confidentiality_lifetime_years: number;
  internet_exposure: boolean;
  business_criticality: Criticality;
  evidence_source: string;
  scan_status: string;
  remediation_status: string;
  created_at: string;
  updated_at: string;
}
