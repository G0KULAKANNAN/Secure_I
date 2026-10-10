import {
  DecommissioningPolicy,
  PolicyListResponse,
  CryptoDependency,
  DependencyListResponse,
  DecommissioningPlan,
  DecommissioningPlanListResponse,
  DecommissioningPlanResponse,
  ReadinessAssessment,
} from '../types';

const API_BASE_URL = '/api/v1';

export async function fetchPolicies(status?: string, category?: string): Promise<DecommissioningPolicy[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (category) params.append('category', category);

  const url = `${API_BASE_URL}/decommissioning/policies${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load decommissioning policies (${res.status})`);
  }
  const data: PolicyListResponse = await res.json();
  return data.policies;
}

export async function createPolicy(payload: {
  name: string;
  algorithm: string;
  primitive_category: string;
  status: string;
  conditions?: string;
  enforcement_deadline?: string;
  rationale?: string;
}): Promise<DecommissioningPolicy> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/policies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to create policy.');
  }
  return data.policy;
}

export async function fetchDependencies(
  status?: string,
  category?: string,
  service?: string
): Promise<CryptoDependency[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (category) params.append('primitive_category', category);
  if (service) params.append('service_name', service);

  const url = `${API_BASE_URL}/decommissioning/dependencies${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load cryptographic dependencies (${res.status})`);
  }
  const data: DependencyListResponse = await res.json();
  return data.dependencies;
}

export async function discoverDependencies(): Promise<CryptoDependency[]> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/dependencies/discover`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const data: DependencyListResponse = await res.json();
  if (!res.ok) {
    throw new Error('Failed to discover dependencies.');
  }
  return data.dependencies;
}

export async function updateDependency(
  depId: string,
  updates: Partial<CryptoDependency>
): Promise<CryptoDependency> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/dependencies/${depId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to update dependency.');
  }
  return data.dependency;
}

export async function fetchDecommissioningPlans(state?: string): Promise<DecommissioningPlan[]> {
  const params = new URLSearchParams();
  if (state) params.append('state', state);

  const url = `${API_BASE_URL}/decommissioning/plans${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load decommissioning plans (${res.status})`);
  }
  const data: DecommissioningPlanListResponse = await res.json();
  return data.plans;
}

export async function fetchDecommissioningPlan(planId: string): Promise<DecommissioningPlan> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/plans/${planId}`);
  if (!res.ok) {
    throw new Error(`Failed to load plan ${planId} (${res.status})`);
  }
  const data: DecommissioningPlanResponse = await res.json();
  return data.plan;
}

export async function createDecommissioningPlan(payload: {
  name: string;
  target_primitive: string;
  affected_services: string[];
  rollback_instructions?: string;
}): Promise<DecommissioningPlan> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to create decommissioning plan.');
  }
  return data.plan;
}

export async function assessPlanReadiness(planId: string): Promise<ReadinessAssessment> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/plans/${planId}/assess-readiness`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to assess decommissioning readiness.');
  }
  return data.assessment;
}

export async function approveDecommissioningPlan(
  planId: string,
  approvedBy: string,
  role: string = 'CISO'
): Promise<DecommissioningPlan> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/plans/${planId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy, role }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to approve decommissioning plan.');
  }
  return data.plan;
}

export async function executeDecommissioning(
  planId: string,
  operator: string = 'security_engineer'
): Promise<DecommissioningPlan> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/plans/${planId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operator }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to execute decommissioning.');
  }
  return data.plan;
}

export async function rollbackDecommissioning(
  planId: string,
  reason: string,
  operator: string = 'security_engineer'
): Promise<DecommissioningPlan> {
  const res = await fetch(`${API_BASE_URL}/decommissioning/plans/${planId}/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason, operator }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to rollback decommissioning.');
  }
  return data.plan;
}
