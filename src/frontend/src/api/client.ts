/**
 * CASHNET Typed Centralized API Client
 * Interfaces with all FastAPI endpoints under /api/v1 and /health
 */

import {
  HealthResponse,
  CaseListResponse,
  CaseDetailResponse,
  TransactionListResponse,
  TransactionDetail,
  CaseAccountListResponse,
  MoneyTrailResponse,
  CaseGraphResponse,
  CaseNetworkResponse,
  RelatedCaseListResponse,
  InvestigatorActionDetail,
  InvestigatorActionCreate,
  CasePredictionHistoryResponse,
  PredictionDetailResponse,
  LocationListResponse,
  LocationDetail,
  LocationClusterListResponse,
  LocationHotspotListResponse,
  NearbyLocationsResponse,
  AccountDetail,
  AccountNetworkResponse,
  AccountMoneyTrailsResponse,
} from '../types/api';

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

const BASE_URL = ((typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) || '').replace(/\/+$/, '');
const API_PREFIX = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resolvedPath = path.startsWith('/api') || path.startsWith('/health') ? path : `${API_PREFIX}${path}`;
  const url = BASE_URL ? `${BASE_URL}${resolvedPath}` : resolvedPath;

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status} ${response.statusText}`;
    let errorData: unknown = null;
    try {
      errorData = await response.json();
      if (typeof errorData === 'object' && errorData !== null && 'detail' in errorData) {
        errorDetail = (errorData as { detail: string }).detail;
      }
    } catch {
      // Body not JSON
    }
    throw new ApiError(errorDetail, response.status, errorData);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // 1. Health Diagnostics
  getHealth: (): Promise<HealthResponse> => {
    return request<HealthResponse>('/health');
  },

  // 2. Cases & Complaints
  listCases: (params: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
    fraud_type?: string;
    fraud_category?: string; // alias
    fraud_channel?: string;
    channel?: string; // alias
    min_amount?: number;
    max_amount?: number;
    from_date?: string;
    to_date?: string;
    as_of?: string;
    order_by?: string;
    sort_by?: string; // alias
    order_desc?: boolean;
    sort_order?: 'asc' | 'desc'; // alias
  } = {}): Promise<CaseListResponse> => {
    const query = new URLSearchParams();
    if (params.page !== undefined) query.set('page', String(params.page));
    if (params.page_size !== undefined) query.set('page_size', String(params.page_size));
    if (params.search) query.set('search', params.search);
    if (params.status) query.set('status', params.status);

    const fType = params.fraud_type || params.fraud_category;
    if (fType) query.set('fraud_type', fType);

    const fChannel = params.fraud_channel || params.channel;
    if (fChannel) query.set('fraud_channel', fChannel);

    if (params.min_amount !== undefined) query.set('min_amount', String(params.min_amount));
    if (params.max_amount !== undefined) query.set('max_amount', String(params.max_amount));
    if (params.from_date) query.set('from_date', params.from_date);
    if (params.to_date) query.set('to_date', params.to_date);
    if (params.as_of) query.set('as_of', params.as_of);

    const orderBy = params.order_by || params.sort_by;
    if (orderBy) query.set('order_by', orderBy);

    const isDesc = params.order_desc !== undefined ? params.order_desc : params.sort_order ? params.sort_order === 'desc' : undefined;
    if (isDesc !== undefined) query.set('order_desc', String(isDesc));

    const qs = query.toString();
    return request<CaseListResponse>(`/cases${qs ? `?${qs}` : ''}`);
  },

  getCase: (caseId: string, asOf?: string, snapshotId?: string): Promise<CaseDetailResponse> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    if (snapshotId) query.set('snapshot_id', snapshotId);
    const qs = query.toString();
    return request<CaseDetailResponse>(`/cases/${encodeURIComponent(caseId)}${qs ? `?${qs}` : ''}`);
  },

  getCaseTransactions: (caseId: string, asOf?: string): Promise<TransactionListResponse> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    const qs = query.toString();
    return request<TransactionListResponse>(`/cases/${encodeURIComponent(caseId)}/transactions${qs ? `?${qs}` : ''}`);
  },

  getCaseAccounts: (caseId: string): Promise<CaseAccountListResponse> => {
    return request<CaseAccountListResponse>(`/cases/${encodeURIComponent(caseId)}/accounts`);
  },

  getCaseMoneyTrail: (caseId: string, asOf?: string, maxHops = 10): Promise<MoneyTrailResponse> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    if (maxHops) query.set('max_hops', String(maxHops));
    const qs = query.toString();
    return request<MoneyTrailResponse>(`/cases/${encodeURIComponent(caseId)}/money-trail${qs ? `?${qs}` : ''}`);
  },

  getCaseGraph: (caseId: string, asOf?: string): Promise<CaseGraphResponse> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    const qs = query.toString();
    return request<CaseGraphResponse>(`/cases/${encodeURIComponent(caseId)}/graph${qs ? `?${qs}` : ''}`);
  },

  getCaseNetwork: (caseId: string, asOf?: string, snapshotId?: string): Promise<CaseNetworkResponse> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    if (snapshotId) query.set('snapshot_id', snapshotId);
    const qs = query.toString();
    return request<CaseNetworkResponse>(`/cases/${encodeURIComponent(caseId)}/network${qs ? `?${qs}` : ''}`);
  },

  getCaseRelatedCases: (caseId: string, params: { page?: number; page_size?: number; as_of?: string } = {}): Promise<RelatedCaseListResponse> => {
    const query = new URLSearchParams();
    if (params.page !== undefined) query.set('page', String(params.page));
    if (params.page_size !== undefined) query.set('page_size', String(params.page_size));
    if (params.as_of) query.set('as_of', params.as_of);
    const qs = query.toString();
    return request<RelatedCaseListResponse>(`/cases/${encodeURIComponent(caseId)}/related-cases${qs ? `?${qs}` : ''}`);
  },

  createCaseAction: (caseId: string, action: InvestigatorActionCreate): Promise<InvestigatorActionDetail> => {
    return request<InvestigatorActionDetail>(`/cases/${encodeURIComponent(caseId)}/actions`, {
      method: 'POST',
      body: JSON.stringify(action),
    });
  },

  listCaseActions: (caseId: string): Promise<InvestigatorActionDetail[]> => {
    return request<InvestigatorActionDetail[]>(`/cases/${encodeURIComponent(caseId)}/actions`);
  },

  // 3. Predictions & Decision Support
  getCasePredictions: (caseId: string, params: { page?: number; page_size?: number } = {}): Promise<CasePredictionHistoryResponse> => {
    const query = new URLSearchParams();
    if (params.page !== undefined) query.set('page', String(params.page));
    if (params.page_size !== undefined) query.set('page_size', String(params.page_size));
    const qs = query.toString();
    return request<CasePredictionHistoryResponse>(`/cases/${encodeURIComponent(caseId)}/predictions${qs ? `?${qs}` : ''}`);
  },

  getLatestCasePrediction: (caseId: string): Promise<PredictionDetailResponse> => {
    return request<PredictionDetailResponse>(`/cases/${encodeURIComponent(caseId)}/predictions/latest`);
  },

  triggerPrediction: (
    caseId: string,
    payload: {
      snapshot_id?: string;
      as_of?: string;
      candidate_count?: number;
      classification_threshold?: number;
      disclose_provenance?: boolean;
    } = {}
  ): Promise<PredictionDetailResponse> => {
    return request<PredictionDetailResponse>(`/cases/${encodeURIComponent(caseId)}/predictions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getPrediction: (predictionId: string): Promise<PredictionDetailResponse> => {
    return request<PredictionDetailResponse>(`/predictions/${encodeURIComponent(predictionId)}`);
  },

  // 4. Locations & GIS
  listLocations: (params: {
    page?: number;
    page_size?: number;
    search?: string;
    location_type?: string;
    city?: string;
    region?: string;
    area_cluster_id?: string;
    is_active?: boolean;
    lat?: number;
    lon?: number;
    radius_km?: number;
    bank_name?: string;
  } = {}): Promise<LocationListResponse> => {
    const query = new URLSearchParams();
    if (params.page !== undefined) query.set('page', String(params.page));
    if (params.page_size !== undefined) query.set('page_size', String(params.page_size));
    if (params.search) query.set('search', params.search);
    if (params.location_type) query.set('location_type', params.location_type);
    if (params.city) query.set('city', params.city);
    if (params.region) query.set('region', params.region);
    if (params.area_cluster_id) query.set('area_cluster_id', params.area_cluster_id);
    if (params.is_active !== undefined) query.set('is_active', String(params.is_active));
    if (params.lat !== undefined) query.set('lat', String(params.lat));
    if (params.lon !== undefined) query.set('lon', String(params.lon));
    if (params.radius_km !== undefined) query.set('radius_km', String(params.radius_km));
    const qs = query.toString();
    return request<LocationListResponse>(`/locations${qs ? `?${qs}` : ''}`);
  },

  getLocation: (locationId: string): Promise<LocationDetail> => {
    return request<LocationDetail>(`/locations/${encodeURIComponent(locationId)}`);
  },

  getLocationClusters: (city?: string): Promise<LocationClusterListResponse> => {
    const query = new URLSearchParams();
    if (city) query.set('city', city);
    const qs = query.toString();
    return request<LocationClusterListResponse>(`/locations/clusters${qs ? `?${qs}` : ''}`);
  },

  getLocationHotspots: (params: {
    city?: string;
    limit?: number;
    min_cashouts?: number;
  } = {}): Promise<LocationHotspotListResponse> => {
    const query = new URLSearchParams();
    if (params.city) query.set('city', params.city);
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    if (params.min_cashouts !== undefined) query.set('min_cashouts', String(params.min_cashouts));
    const qs = query.toString();
    return request<LocationHotspotListResponse>(`/locations/hotspots${qs ? `?${qs}` : ''}`);
  },

  getNearbyLocations: (params: {
    latitude: number;
    longitude: number;
    radius_km?: number;
    limit?: number;
  }): Promise<NearbyLocationsResponse> => {
    const query = new URLSearchParams();
    query.set('latitude', String(params.latitude));
    query.set('longitude', String(params.longitude));
    if (params.radius_km !== undefined) query.set('radius_km', String(params.radius_km));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    return request<NearbyLocationsResponse>(`/locations/nearby?${query.toString()}`);
  },

  // 5. Account Profiles & Intelligence
  getAccount: (accountId: string, asOf?: string): Promise<AccountDetail> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    const qs = query.toString();
    return request<AccountDetail>(`/accounts/${encodeURIComponent(accountId)}${qs ? `?${qs}` : ''}`);
  },

  getAccountNetwork: (accountId: string, asOf?: string): Promise<AccountNetworkResponse> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    const qs = query.toString();
    return request<AccountNetworkResponse>(`/accounts/${encodeURIComponent(accountId)}/network${qs ? `?${qs}` : ''}`);
  },

  getAccountMoneyTrails: (accountId: string, asOf?: string): Promise<AccountMoneyTrailsResponse> => {
    const query = new URLSearchParams();
    if (asOf) query.set('as_of', asOf);
    const qs = query.toString();
    return request<AccountMoneyTrailsResponse>(`/accounts/${encodeURIComponent(accountId)}/money-trails${qs ? `?${qs}` : ''}`);
  },

  getAccountTransactions: (
    accountId: string,
    params: { page?: number; page_size?: number; as_of?: string } = {}
  ): Promise<{ items: TransactionDetail[]; total: number }> => {
    const query = new URLSearchParams();
    if (params.page !== undefined) query.set('page', String(params.page));
    if (params.page_size !== undefined) query.set('page_size', String(params.page_size));
    if (params.as_of) query.set('as_of', params.as_of);
    const qs = query.toString();
    return request<{ items: TransactionDetail[]; total: number }>(`/accounts/${encodeURIComponent(accountId)}/transactions${qs ? `?${qs}` : ''}`);
  },
};
