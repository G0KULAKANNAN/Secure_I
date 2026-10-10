import {
  NetworkProfile,
  NetworkProfileListResponse,
  NetworkRunResponse,
  NetworkResultListResponse,
  NetworkVerificationResult,
} from '../types';

const API_BASE_URL = '/api/v1';

export async function fetchNetworkProfiles(): Promise<NetworkProfile[]> {
  const res = await fetch(`${API_BASE_URL}/network/profiles`);
  if (!res.ok) {
    throw new Error(`Failed to load network profiles (${res.status})`);
  }
  const data: NetworkProfileListResponse = await res.json();
  return data.profiles;
}

export async function createNetworkProfile(payload: {
  name: string;
  target_host?: string;
  target_port?: number;
  environment?: string;
  test_profile?: string;
  test_mode?: string;
  expected_mtu?: number;
  authorized_by_operator?: boolean;
  operator_notes?: string;
}): Promise<NetworkProfile> {
  const res = await fetch(`${API_BASE_URL}/network/profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error || 'Failed to create network verification profile.');
  }
  return data.profile;
}

export async function runNetworkVerification(
  profileId: string,
  operator: string = 'local_operator'
): Promise<NetworkVerificationResult> {
  const res = await fetch(`${API_BASE_URL}/network/profiles/${profileId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operator }),
  });
  const data: NetworkRunResponse = await res.json();
  if (!res.ok) {
    throw new Error((data as any)?.error || 'Network verification test failed.');
  }
  return data.result;
}

export async function fetchNetworkResults(profileId?: string): Promise<NetworkVerificationResult[]> {
  const url = profileId
    ? `${API_BASE_URL}/network/results?profile_id=${encodeURIComponent(profileId)}`
    : `${API_BASE_URL}/network/results`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load network results (${res.status})`);
  }
  const data: NetworkResultListResponse = await res.json();
  return data.results;
}

export async function deleteNetworkProfile(profileId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/network/profiles/${profileId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data?.error || 'Failed to delete network profile.');
  }
}
