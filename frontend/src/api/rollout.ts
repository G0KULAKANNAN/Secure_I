import {
  DeploymentEnvironment,
  EnvironmentListResponse,
  RolloutPlan,
  RolloutPlanListResponse,
  RolloutPlanResponse,
  ReadinessAssessment,
  TelemetryEvent,
  TelemetryListResponse,
} from '../types';

const API_BASE_URL = '/api/v1';

export async function fetchEnvironments(): Promise<DeploymentEnvironment[]> {
  const res = await fetch(`${API_BASE_URL}/rollout/environments`);
  if (!res.ok) {
    throw new Error(`Failed to load deployment environments (${res.status})`);
  }
  const data: EnvironmentListResponse = await res.json();
  return data.environments;
}

export async function fetchRolloutPlans(envId?: string, state?: string): Promise<RolloutPlan[]> {
  const params = new URLSearchParams();
  if (envId) params.append('environment_id', envId);
  if (state) params.append('state', state);

  const url = `${API_BASE_URL}/rollout/plans${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load rollout plans (${res.status})`);
  }
  const data: RolloutPlanListResponse = await res.json();
  return data.plans;
}

export async function fetchRolloutPlan(planId: string): Promise<{ plan: RolloutPlan; recent_telemetry: TelemetryEvent[] }> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans/${planId}`);
  if (!res.ok) {
    throw new Error(`Failed to load rollout plan ${planId} (${res.status})`);
  }
  const data: RolloutPlanResponse = await res.json();
  return { plan: data.plan, recent_telemetry: data.recent_telemetry || [] };
}

export async function createRolloutPlan(payload: {
  name: string;
  environment_id: string;
  target_config: Record<string, any>;
  previous_config?: Record<string, any>;
  rollback_threshold_failure_rate?: number;
  deployment_mode?: string;
}): Promise<RolloutPlan> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to create rollout plan.');
  }
  return data.plan;
}

export async function assessReadiness(planId: string): Promise<ReadinessAssessment> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans/${planId}/assess-readiness`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to assess readiness.');
  }
  return data.assessment;
}

export async function approveRolloutPlan(planId: string, approvedBy: string): Promise<RolloutPlan> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans/${planId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to approve rollout plan.');
  }
  return data.plan;
}

export async function advanceCanaryStage(planId: string, force: boolean = false): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans/${planId}/advance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to advance canary stage.');
  }
  return data.result;
}

export async function simulateCanaryTraffic(planId: string, healthy: boolean = true): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans/${planId}/simulate-traffic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ healthy }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to simulate traffic.');
  }
  return data.result;
}

export async function rollbackPlan(planId: string, reason: string, operator: string): Promise<RolloutPlan> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans/${planId}/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason, operator }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to rollback plan.');
  }
  return data.plan;
}

export async function fetchTelemetry(planId: string, limit: number = 20): Promise<TelemetryEvent[]> {
  const res = await fetch(`${API_BASE_URL}/rollout/plans/${planId}/telemetry?limit=${limit}`);
  if (!res.ok) {
    throw new Error(`Failed to load telemetry (${res.status})`);
  }
  const data: TelemetryListResponse = await res.json();
  return data.telemetry;
}
