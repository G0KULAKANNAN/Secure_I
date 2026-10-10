import {
  FindingStats,
  RiskFormulaMetadata,
  RiskCalculateResponse,
  RemediationQueueData,
  RemediationQueueResponse,
} from '../types';

const API_BASE_URL = '/api/v1';

export async function fetchRiskFormula(): Promise<RiskFormulaMetadata> {
  const response = await fetch(`${API_BASE_URL}/risk/formula`);
  if (!response.ok) {
    throw new Error('Failed to load risk formula metadata.');
  }
  return response.json();
}

export async function calculateSimulatedRisk(factors: {
  sensitivity?: number;
  exposure?: number;
  lifetime?: number;
}): Promise<RiskCalculateResponse> {
  const response = await fetch(`${API_BASE_URL}/risk/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(factors),
  });
  if (!response.ok) {
    throw new Error('Failed to simulate risk score.');
  }
  return response.json();
}

export async function fetchRiskSummary(): Promise<{ status: string; stats: FindingStats; disclaimer: string }> {
  const response = await fetch(`${API_BASE_URL}/risk/summary`);
  if (!response.ok) {
    throw new Error('Failed to load risk summary.');
  }
  return response.json();
}

export async function fetchRiskQueue(): Promise<RemediationQueueData> {
  const response = await fetch(`${API_BASE_URL}/risk/queue`);
  if (!response.ok) {
    throw new Error('Failed to load risk queue.');
  }
  const data: RemediationQueueResponse = await response.json();
  return data.queue;
}
