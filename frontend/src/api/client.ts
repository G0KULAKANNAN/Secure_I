import { HealthStatus, SystemVersion } from '../types';

const API_BASE_URL = '/api/v1';

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchVersion(): Promise<SystemVersion> {
  const response = await fetch(`${API_BASE_URL}/version`);
  if (!response.ok) {
    throw new Error(`Version check failed with status ${response.status}`);
  }
  return response.json();
}
