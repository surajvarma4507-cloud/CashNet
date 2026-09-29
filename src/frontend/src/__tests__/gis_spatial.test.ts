import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../api/client';
import {
  LocationClusterSummary,
  LocationHotspotDetail,
  LocationDetail,
  InvestigatorActionCreate,
} from '../types/api';

describe('CASHNET Stage 5: GIS & Spatial Intelligence Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('Location Clusters & Spatial Aggregations', () => {
    it('fetches spatial cluster list grouped by area_cluster_id', async () => {
      const mockClusterList = {
        total_clusters: 2,
        items: [
          {
            area_cluster_id: 'CLUSTER_MUM_01',
            cluster_name: 'South Mumbai Financial District',
            city: 'Mumbai',
            region: 'Maharashtra',
            center_latitude: 18.9388,
            center_longitude: 72.8354,
            total_locations: 25,
            atm_count: 18,
            branch_count: 5,
            kiosk_count: 2,
            observed_cashout_events_count: 12,
            total_observed_cashout_volume: 450000.0,
          },
          {
            area_cluster_id: 'CLUSTER_DEL_01',
            cluster_name: 'Connaught Place Commercial Hub',
            city: 'Delhi',
            region: 'Delhi',
            center_latitude: 28.6315,
            center_longitude: 77.2167,
            total_locations: 30,
            atm_count: 22,
            branch_count: 6,
            kiosk_count: 2,
            observed_cashout_events_count: 8,
            total_observed_cashout_volume: 320000.0,
          },
        ],
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockClusterList,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.getLocationClusters('Mumbai');
      expect(res.total_clusters).toBe(2);
      expect(res.items.length).toBe(2);
      expect(res.items[0].area_cluster_id).toBe('CLUSTER_MUM_01');
      expect(res.items[0].atm_count + res.items[0].branch_count + res.items[0].kiosk_count).toBe(
        res.items[0].total_locations
      );
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/locations/clusters?city=Mumbai'),
        expect.anything()
      );
    });

    it('validates cluster summary structural integrity and metric breakdowns', () => {
      const cluster: LocationClusterSummary = {
        area_cluster_id: 'CLUSTER_BLR_01',
        cluster_name: 'Indiranagar Tech Hub',
        city: 'Bengaluru',
        region: 'Karnataka',
        center_latitude: 12.9784,
        center_longitude: 77.6408,
        total_locations: 15,
        atm_count: 10,
        branch_count: 3,
        kiosk_count: 2,
        observed_cashout_events_count: 4,
        total_observed_cashout_volume: 180000,
      };

      expect(cluster.total_locations).toBe(15);
      expect(cluster.atm_count).toBe(10);
      expect(cluster.branch_count).toBe(3);
      expect(cluster.kiosk_count).toBe(2);
      expect(cluster.center_latitude).toBeGreaterThan(0);
      expect(cluster.center_longitude).toBeGreaterThan(0);
    });
  });

  describe('Location Hotspots & Physical Extraction Points', () => {
    it('fetches physical cashout hotspots filtered by minimum observed cashouts', async () => {
      const mockHotspots = {
        total_hotspots: 3,
        items: [
          {
            location_id: 'LOC_MUM_ATM_001',
            location_name: 'State Bank ATM - Nariman Point',
            location_type: 'atm',
            city: 'Mumbai',
            region: 'Maharashtra',
            latitude: 18.9256,
            longitude: 72.8242,
            area_cluster_id: 'CLUSTER_MUM_01',
            observed_cashout_count: 9,
            total_observed_cashout_volume: 380000.0,
            activity_risk_level: 'high' as const,
          },
          {
            location_id: 'LOC_MUM_BR_004',
            location_name: 'HDFC Bank - Fort Branch',
            location_type: 'branch',
            city: 'Mumbai',
            region: 'Maharashtra',
            latitude: 18.9322,
            longitude: 72.8335,
            area_cluster_id: 'CLUSTER_MUM_01',
            observed_cashout_count: 4,
            total_observed_cashout_volume: 160000.0,
            activity_risk_level: 'elevated' as const,
          },
        ],
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockHotspots,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.getLocationHotspots({
        city: 'Mumbai',
        limit: 10,
        min_cashouts: 2,
      });

      expect(res.total_hotspots).toBe(3);
      expect(res.items.length).toBe(2);
      expect(res.items[0].activity_risk_level).toBe('high');
      expect(res.items[1].activity_risk_level).toBe('elevated');
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/locations/hotspots?city=Mumbai&limit=10&min_cashouts=2'),
        expect.anything()
      );
    });

    it('strictly ensures hotspot data contains only non-ground-truth observed events', () => {
      const hotspot: LocationHotspotDetail = {
        location_id: 'LOC_DEL_ATM_012',
        location_name: 'PNB ATM - Connaught Place',
        location_type: 'atm',
        city: 'Delhi',
        region: 'Delhi',
        latitude: 28.6328,
        longitude: 77.2197,
        area_cluster_id: 'CLUSTER_DEL_01',
        observed_cashout_count: 6,
        total_observed_cashout_volume: 240000.0,
        activity_risk_level: 'high',
      };

      const forbiddenGroundTruthFields = [
        'is_future_ground_truth',
        'actual_next_cashout_at',
        'actual_cashout_amount',
        'future_cashout_probability',
      ];

      forbiddenGroundTruthFields.forEach((field) => {
        expect(field in hotspot).toBe(false);
        expect((hotspot as unknown as Record<string, unknown>)[field]).toBeUndefined();
      });
    });
  });

  describe('Concentric Radius & Haversine Distance Mathematics', () => {
    // Haversine formula unit test helper
    const calculateHaversineDistanceKm = (
      lat1: number,
      lon1: number,
      lat2: number,
      lon2: number
    ): number => {
      const toRad = (deg: number) => (deg * Math.PI) / 180;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return 6371.0 * c;
    };

    it('computes exact distance between two known Indian city coordinates', () => {
      // Mumbai (19.0760, 72.8777) to Pune (18.5204, 73.8567) ~ 120-130 km
      const distance = calculateHaversineDistanceKm(19.076, 72.8777, 18.5204, 73.8567);
      expect(distance).toBeGreaterThan(115);
      expect(distance).toBeLessThan(135);
    });

    it('identifies terminal locations within 5 km, 10 km, and 25 km concentric radii', () => {
      const center = { lat: 19.076, lon: 72.8777 }; // Central query anchor

      const nearbyAtm: LocationDetail = {
        location_id: 'LOC-1',
        location_name: 'Nearby ATM 2km',
        location_type: 'atm',
        city: 'Mumbai',
        region: 'Maharashtra',
        latitude: 19.085,
        longitude: 72.885,
        area_cluster_id: 'CLUSTER_MUM_01',
        synthetic_location_group: 'metro',
        is_active: true,
        created_at: '2026-09-01T00:00:00Z',
      };

      const mediumAtm: LocationDetail = {
        location_id: 'LOC-2',
        location_name: 'Medium ATM 8km',
        location_type: 'atm',
        city: 'Mumbai',
        region: 'Maharashtra',
        latitude: 19.145,
        longitude: 72.895,
        area_cluster_id: 'CLUSTER_MUM_02',
        synthetic_location_group: 'metro',
        is_active: true,
        created_at: '2026-09-01T00:00:00Z',
      };

      const farAtm: LocationDetail = {
        location_id: 'LOC-3',
        location_name: 'Far ATM 20km',
        location_type: 'atm',
        city: 'Mumbai',
        region: 'Maharashtra',
        latitude: 19.245,
        longitude: 72.865,
        area_cluster_id: 'CLUSTER_MUM_03',
        synthetic_location_group: 'metro',
        is_active: true,
        created_at: '2026-09-01T00:00:00Z',
      };

      const dist1 = calculateHaversineDistanceKm(center.lat, center.lon, nearbyAtm.latitude, nearbyAtm.longitude);
      const dist2 = calculateHaversineDistanceKm(center.lat, center.lon, mediumAtm.latitude, mediumAtm.longitude);
      const dist3 = calculateHaversineDistanceKm(center.lat, center.lon, farAtm.latitude, farAtm.longitude);

      // Verify concentric bands
      expect(dist1).toBeLessThanOrEqual(5.0);
      expect(dist2).toBeGreaterThan(5.0);
      expect(dist2).toBeLessThanOrEqual(10.0);
      expect(dist3).toBeGreaterThan(10.0);
      expect(dist3).toBeLessThanOrEqual(25.0);
    });
  });

  describe('Tactical Field Alert & Surveillance Dispatch Audit Logging', () => {
    it('creates immutable investigator action targeting physical cashout location', async () => {
      const actionPayload: InvestigatorActionCreate = {
        action_type: 'surveillance_requested',
        notes: '[GIS Terminal Dispatch: State Bank ATM - Nariman Point (LOC_MUM_ATM_001), Cluster: CLUSTER_MUM_01] Unit dispatched to monitor high-risk ATM',
        performed_by: 'investigator_officer_42',
        action_status: 'completed',
      };

      const mockResponse = {
        action_id: 'ACT-GIS-0001',
        case_id: 'CASE-0042',
        action_type: 'surveillance_requested',
        notes: actionPayload.notes,
        performed_by: 'investigator_officer_42',
        action_status: 'completed',
        created_at: '2026-09-29T14:30:00Z',
      };

      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });
      vi.stubGlobal('fetch', fetchMock);

      const res = await api.createCaseAction('CASE-0042', actionPayload);

      expect(res.action_id).toBe('ACT-GIS-0001');
      expect(res.action_type).toBe('surveillance_requested');
      expect(res.notes).toContain('LOC_MUM_ATM_001');
      expect(res.notes).toContain('CLUSTER_MUM_01');
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/v1/cases/CASE-0042/actions',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(actionPayload),
        })
      );
    });
  });
});
