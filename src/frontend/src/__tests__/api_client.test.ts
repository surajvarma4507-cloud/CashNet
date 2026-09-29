import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError } from '../api/client';

describe('CASHNET API Client Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('ApiError Handling', () => {
    it('correctly constructs ApiError with status, message and custom details', () => {
      const error = new ApiError('Case not found', 404, { detail: 'CASE-9999' });
      expect(error.name).toBe('ApiError');
      expect(error.message).toBe('Case not found');
      expect(error.status).toBe(404);
      expect(error.data).toEqual({ detail: 'CASE-9999' });
    });

    it('propagates HTTP error status and message on 422 Unprocessable Entity', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ detail: 'Invalid parameter: min_amount cannot be negative' }),
      });
      vi.stubGlobal('fetch', fetchMock);

      await expect(api.getCase('INVALID_ID')).rejects.toThrow(ApiError);
    });

    it('handles non-JSON error response gracefully', async () => {
      const fetchMock = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Not JSON');
        },
      });
      vi.stubGlobal('fetch', fetchMock);

      await expect(api.getHealth()).rejects.toThrow('Request failed with status 500 Internal Server Error');
    });
  });

  describe('System Health API', () => {
    it('handles successful health check request', async () => {
      const mockHealth = {
        status: 'healthy',
        version: '2.0.0',
        database_connected: true,
        simulation_mode: true,
        timestamp: '2026-09-29T12:00:00Z',
        models_status: { model_a: 'active', model_b: 'fallback_active' },
        table_counts: { accounts: 10001, cases: 5000, transactions: 65000 },
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockHealth,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.getHealth();
      expect(res).toEqual(mockHealth);
      expect(fetchMock).toHaveBeenCalledWith('/health', expect.anything());
    });
  });

  describe('Cases & Filtering API', () => {
    it('serializes query parameters correctly with aliases for case list filtering', async () => {
      const mockList = {
        items: [],
        pagination: {
          total: 0,
          page: 2,
          page_size: 50,
          total_pages: 0,
        },
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockList,
      });
      vi.stubGlobal('fetch', fetchMock);

      await api.listCases({
        page: 2,
        page_size: 50,
        status: 'registered',
        fraud_type: 'Investment Scam',
        min_amount: 10000,
        max_amount: 500000,
        order_by: 'fraud_amount',
        order_desc: true,
      });

      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/cases?page=2&page_size=50&status=registered&fraud_type=Investment+Scam&min_amount=10000&max_amount=500000&order_by=fraud_amount&order_desc=true'),
        expect.anything()
      );
    });

    it('fetches specific case dossier with point-in-time as_of parameter', async () => {
      const mockCase = {
        case_id: 'CASE-0001',
        victim_account_id: 'ACC-0001',
        fraud_amount: 50000,
        complaint_status: 'registered',
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockCase,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.getCase('CASE-0001', '2026-09-01T10:00:00Z');
      expect(res).toEqual(mockCase);
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/cases/CASE-0001?as_of=2026-09-01T10%3A00%3A00Z',
        expect.anything()
      );
    });

    it('fetches reconstructed money trail with max_hops parameter', async () => {
      const mockTrail = {
        case_id: 'CASE-0001',
        total_hops: 3,
        total_accounts: 4,
        nodes: [],
        edges: [],
        has_cycles: false,
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockTrail,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.getCaseMoneyTrail('CASE-0001', undefined, 5);
      expect(res).toEqual(mockTrail);
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/cases/CASE-0001/money-trail?max_hops=5',
        expect.anything()
      );
    });
  });

  describe('ML Prediction API & Interventions', () => {
    it('triggers on-demand ML prediction with proper POST payload', async () => {
      const mockPrediction = {
        prediction_id: 'PRED-0001',
        case_id: 'CASE-0001',
        occurrence: {
          probability_future_cashout: 0.85,
          predicted_has_future_cashout: true,
          risk_tier: 'high',
        },
        candidates: [],
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockPrediction,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.triggerPrediction('CASE-0001', {
        candidate_count: 5,
        classification_threshold: 0.5,
      });

      expect(res).toEqual(mockPrediction);
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/cases/CASE-0001/predictions',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            candidate_count: 5,
            classification_threshold: 0.5,
          }),
        })
      );
    });

    it('creates immutable investigator action audit log entry', async () => {
      const mockAction = {
        action_id: 'ACT-0001',
        case_id: 'CASE-0001',
        action_type: 'account_freeze',
        notes: 'Mule account frozen',
        performed_by: 'investigator_lead',
        action_status: 'completed',
        created_at: '2026-09-29T12:00:00Z',
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => mockAction,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.createCaseAction('CASE-0001', {
        action_type: 'account_freeze',
        notes: 'Mule account frozen',
      });

      expect(res).toEqual(mockAction);
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/cases/CASE-0001/actions',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            action_type: 'account_freeze',
            notes: 'Mule account frozen',
          }),
        })
      );
    });
  });

  describe('GIS Locations API', () => {
    it('queries nearby locations using Haversine radius endpoint', async () => {
      const mockNearby = {
        query_latitude: 19.076,
        query_longitude: 72.8777,
        radius_km: 10,
        count: 2,
        items: [],
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockNearby,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.getNearbyLocations({
        latitude: 19.076,
        longitude: 72.8777,
        radius_km: 10,
        limit: 20,
      });

      expect(res).toEqual(mockNearby);
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/locations/nearby?latitude=19.076&longitude=72.8777&radius_km=10&limit=20',
        expect.anything()
      );
    });
  });
});
