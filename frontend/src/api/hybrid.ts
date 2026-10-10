import {
  CapabilitiesResponse,
  HybridProfile,
  HybridProfileListResponse,
  HybridProfileResponse,
  HybridTestResponse,
  HybridVerificationRun,
} from '../types';

const API_BASE_URL = '/api/v1';

export async function fetchCapabilities(): Promise<CapabilitiesResponse> {
  const res = await fetch(`${API_BASE_URL}/hybrid/capabilities`);
  if (!res.ok) {
    throw new Error(`Failed to load capabilities (${res.status})`);
  }
  return res.json();
}

export async function fetchProfiles(): Promise<HybridProfile[]> {
  const res = await fetch(`${API_BASE_URL}/hybrid/profiles`);
  if (!res.ok) {
    throw new Error(`Failed to load hybrid profiles (${res.status})`);
  }
  const data: HybridProfileListResponse = await res.json();
  return data.profiles;
}

export async function createProfile(payload: {
  profile_name: string;
  classical_component?: string;
  pqc_component?: string;
  operator?: string;
}): Promise<HybridProfile> {
  const res = await fetch(`${API_BASE_URL}/hybrid/profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to create hybrid staging profile.');
  }
  return data.profile;
}

export async function fetchProfileDetails(profileId: string): Promise<HybridProfileResponse> {
  const res = await fetch(`${API_BASE_URL}/hybrid/profiles/${profileId}`);
  if (!res.ok) {
    throw new Error(`Failed to load profile details (${res.status})`);
  }
  return res.json();
}

export async function testProfile(
  profileId: string,
  testMode: 'real_tls' | 'simulation' = 'simulation',
  operator: string = 'local_operator'
): Promise<HybridVerificationRun> {
  const res = await fetch(`${API_BASE_URL}/hybrid/profiles/${profileId}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ test_mode: testMode, operator }),
  });
  const data: HybridTestResponse = await res.json();
  if (!res.ok) {
    throw new Error((data as any)?.error || 'Interoperability test failed.');
  }
  return data.verification_run;
}

export async function approveProfile(
  profileId: string,
  approvedBy: string = 'local_operator'
): Promise<HybridProfile> {
  const res = await fetch(`${API_BASE_URL}/hybrid/profiles/${profileId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to approve hybrid profile.');
  }
  return data.profile;
}

export async function rollbackProfile(
  profileId: string,
  operator: string = 'local_operator'
): Promise<HybridProfile> {
  const res = await fetch(`${API_BASE_URL}/hybrid/profiles/${profileId}/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operator }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to roll back hybrid profile.');
  }
  return data.profile;
}

export async function deleteProfile(profileId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/hybrid/profiles/${profileId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data?.error || 'Failed to delete hybrid profile.');
  }
}
