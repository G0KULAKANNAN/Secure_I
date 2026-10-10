import { Asset, AssetListResponse } from '../types';

const API_BASE_URL = '/api/v1';

export interface AssetFilterParams {
  search?: string;
  asset_type?: string;
  environment?: string;
  criticality?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export async function listAssets(params?: AssetFilterParams): Promise<AssetListResponse> {
  const query = new URLSearchParams();
  if (params) {
    if (params.search) query.set('search', params.search);
    if (params.asset_type) query.set('asset_type', params.asset_type);
    if (params.environment) query.set('environment', params.environment);
    if (params.criticality) query.set('criticality', params.criticality);
    if (params.status) query.set('status', params.status);
    if (params.limit !== undefined) query.set('limit', params.limit.toString());
    if (params.offset !== undefined) query.set('offset', params.offset.toString());
  }

  const url = `${API_BASE_URL}/assets${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch assets (HTTP ${response.status})`);
  }
  return response.json();
}

export async function getAsset(id: string): Promise<Asset> {
  const response = await fetch(`${API_BASE_URL}/assets/${id}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to fetch asset (HTTP ${response.status})`);
  }
  const data = await response.json();
  return data.asset;
}

export async function createAsset(data: Partial<Asset>): Promise<Asset> {
  const response = await fetch(`${API_BASE_URL}/assets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to create asset (HTTP ${response.status})`);
  }
  const result = await response.json();
  return result.asset;
}

export async function updateAsset(id: string, data: Partial<Asset>): Promise<Asset> {
  const response = await fetch(`${API_BASE_URL}/assets/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to update asset (HTTP ${response.status})`);
  }
  const result = await response.json();
  return result.asset;
}

export async function deleteAsset(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/assets/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to delete asset (HTTP ${response.status})`);
  }
}
