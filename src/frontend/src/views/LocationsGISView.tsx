import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import {
  LocationDetail,
  LocationClusterSummary,
  LocationHotspotDetail,
} from '../types/api';
import {
  MapPin,
  Building,
  Navigation,
  RotateCw,
  Radio,
  Flame,
  Layers,
  Crosshair,
  AlertOctagon,
  Shield,
  Send,
  X,
  ExternalLink,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { LocationMap } from '../components/gis/LocationMap';

const INDIAN_CITIES = [
  'All Cities',
  'Mumbai',
  'Delhi',
  'Bengaluru',
  'Hyderabad',
  'Kolkata',
  'Pune',
  'Chennai',
  'Ahmedabad',
  'Jaipur',
  'Lucknow',
];

type GISViewTab = 'terminals' | 'clusters' | 'hotspots';

interface LocationsGISViewProps {
  initialLocationId?: string | null;
  onShowToast?: (toast: { type: 'success' | 'warning' | 'error'; title: string; description?: string }) => void;
  onOpenCase?: (caseId: string) => void;
}

export const LocationsGISView: React.FC<LocationsGISViewProps> = ({
  initialLocationId,
  onShowToast,
  onOpenCase,
}) => {
  const [activeTab, setActiveTab] = useState<GISViewTab>('terminals');
  const [locations, setLocations] = useState<LocationDetail[]>([]);
  const [clusters, setClusters] = useState<LocationClusterSummary[]>([]);
  const [hotspots, setHotspots] = useState<LocationHotspotDetail[]>([]);
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(initialLocationId || null);
  const [selectedLocation, setSelectedLocation] = useState<LocationDetail | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState<string>('');
  const [selectedCity, setSelectedCity] = useState<string>('All Cities');
  const [locationType, setLocationType] = useState<string>('');
  const [radiusSearchOpen, setRadiusSearchOpen] = useState<boolean>(false);
  const [centerLat, setCenterLat] = useState<string>('19.0760');
  const [centerLon, setCenterLon] = useState<string>('72.8777');
  const [radiusKm, setRadiusKm] = useState<number>(15);

  // Tactical Action Modal State
  const [actionModalOpen, setActionModalOpen] = useState<boolean>(false);
  const [actionCaseId, setActionCaseId] = useState<string>('');
  const [actionType, setActionType] = useState<string>('dispatch_alert');
  const [officerName, setOfficerName] = useState<string>('investigator_gis_unit');
  const [actionNotes, setActionNotes] = useState<string>('');
  const [submittingAction, setSubmittingAction] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Fetch all GIS datasets (locations, clusters, hotspots)
  const fetchGISData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const cityFilter = selectedCity !== 'All Cities' ? selectedCity : undefined;

      if (radiusSearchOpen && centerLat && centerLon) {
        const nearbyRes = await api.getNearbyLocations({
          latitude: parseFloat(centerLat),
          longitude: parseFloat(centerLon),
          radius_km: radiusKm,
          limit: 150,
        });
        setLocations(nearbyRes.items || []);
      } else {
        const listRes = await api.listLocations({
          page: 1,
          page_size: 300,
          search: search.trim() || undefined,
          city: cityFilter,
          location_type: locationType || undefined,
        });
        setLocations(listRes.items || []);
      }

      // Fetch clusters and hotspots in parallel
      const [clustersRes, hotspotsRes] = await Promise.all([
        api.getLocationClusters(cityFilter).catch(() => ({ total_clusters: 0, items: [] })),
        api.getLocationHotspots({ city: cityFilter, limit: 30, min_cashouts: 1 }).catch(() => ({ total_hotspots: 0, items: [] })),
      ]);

      setClusters(clustersRes.items || []);
      setHotspots(hotspotsRes.items || []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch GIS terminal spatial data.');
      }
    } finally {
      setLoading(false);
    }
  }, [radiusSearchOpen, centerLat, centerLon, radiusKm, search, selectedCity, locationType]);

  useEffect(() => {
    fetchGISData();
  }, [fetchGISData]);

  // Handle selecting a location
  const handleSelectLocation = async (locId: string) => {
    setSelectedLocationId(locId);
    try {
      const loc = await api.getLocation(locId);
      setSelectedLocation(loc);
    } catch (err) {
      console.warn('Could not fetch location details', err);
    }
  };

  // Center radius search on selected terminal
  const handleSetAsCenter = (loc: LocationDetail) => {
    setCenterLat(loc.latitude.toString());
    setCenterLon(loc.longitude.toString());
    setRadiusSearchOpen(true);
    if (onShowToast) {
      onShowToast({
        type: 'success',
        title: 'Radius Center Anchor Set',
        description: `Centered spatial query at ${loc.location_name} (${loc.latitude.toFixed(4)}°N, ${loc.longitude.toFixed(4)}°E)`,
      });
    }
  };

  // Handle Record Tactical Action Submission
  const handleSubmitTacticalAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);

    if (!selectedLocation) {
      setActionError('No physical terminal selected for action dispatch.');
      return;
    }

    if (!actionCaseId.trim()) {
      setActionError('A valid Case ID is required to anchor this tactical action in the audit log.');
      return;
    }

    if (!actionNotes.trim()) {
      setActionError('Operational justification notes are mandatory for the audit log.');
      return;
    }

    try {
      setSubmittingAction(true);
      const newAction = await api.createCaseAction(actionCaseId.trim(), {
        action_type: actionType,
        notes: `[GIS Terminal Dispatch: ${selectedLocation.location_name} (${selectedLocation.location_id}), Cluster: ${selectedLocation.area_cluster_id}] ${actionNotes.trim()}`,
        performed_by: officerName.trim() || 'investigator_gis_unit',
        action_status: 'completed',
      });

      if (onShowToast) {
        onShowToast({
          type: 'success',
          title: 'Tactical Action Recorded in Audit Log',
          description: `${actionType.replace('_', ' ').toUpperCase()} targeting ${selectedLocation.location_name} logged (Audit ID: ${newAction.action_id.slice(0, 8)}...)`,
        });
      }

      setActionNotes('');
      setActionModalOpen(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to record tactical action.';
      setActionError(msg);
    } finally {
      setSubmittingAction(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header & Filter Bar */}
      <div className="card" style={{ padding: '1.25rem 1.5rem', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <MapPin size={22} style={{ color: '#0d9488' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
                GIS &amp; ATM Geospatial Situational Awareness
              </h2>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.25rem' }}>
              Spatial intelligence across 300 synthetic physical cash withdrawal terminals (ATMs, bank branches, CSP kiosks) in India.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              className={`btn btn-sm ${radiusSearchOpen ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setRadiusSearchOpen(!radiusSearchOpen)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <Navigation size={14} /> {radiusSearchOpen ? 'Radius Query Active' : 'Concentric Radius Query'}
            </button>
            <button
              className="btn btn-sm btn-secondary"
              onClick={fetchGISData}
              disabled={loading}
              title="Refresh"
            >
              <RotateCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* View Mode Navigation Tabs */}
        <div
          style={{
            display: 'flex',
            gap: '0.25rem',
            borderBottom: '1px solid #e2e8f0',
            marginTop: '1.25rem',
            overflowX: 'auto',
          }}
        >
          {[
            { id: 'terminals' as GISViewTab, label: `Physical Terminals (${locations.length})`, icon: <Layers size={15} /> },
            { id: 'clusters' as GISViewTab, label: `Spatial Clusters (${clusters.length})`, icon: <Radio size={15} /> },
            { id: 'hotspots' as GISViewTab, label: `Cash-Out Hotspots (${hotspots.length})`, icon: <Flame size={15} /> },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  padding: '0.5rem 0.875rem',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  color: isActive ? '#0d9488' : '#64748b',
                  border: 'none',
                  borderBottom: isActive ? '2px solid #0d9488' : '2px solid transparent',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Concentric Spatial Radius Overlays Controls */}
        {radiusSearchOpen && (
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              backgroundColor: '#f0fdfa',
              border: '1px solid #ccfbf1',
              borderRadius: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#0f766e', fontWeight: 600, fontSize: '0.875rem' }}>
                <Crosshair size={16} /> Concentric Radius Query (Haversine Distance Overlays)
              </div>
              {/* Radius Quick Presets */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ fontSize: '0.75rem', color: '#0f766e', fontWeight: 600 }}>Presets:</span>
                {[5, 10, 25].map((preset) => (
                  <button
                    key={`preset-${preset}`}
                    onClick={() => setRadiusKm(preset)}
                    className={`btn btn-sm ${radiusKm === preset ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.15rem 0.5rem' }}
                  >
                    {preset} km
                  </button>
                ))}
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '0.75rem',
              }}
            >
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Anchor Latitude (°N)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  className="input"
                  value={centerLat}
                  onChange={(e) => setCenterLat(e.target.value)}
                  style={{ fontSize: '0.8125rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Anchor Longitude (°E)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  className="input"
                  value={centerLon}
                  onChange={(e) => setCenterLon(e.target.value)}
                  style={{ fontSize: '0.8125rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Filter Radius (km)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  className="input"
                  value={radiusKm}
                  onChange={(e) => setRadiusKm(Math.max(1, parseInt(e.target.value, 10) || 15))}
                  style={{ fontSize: '0.8125rem' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Standard Filters Form */}
        <div
          style={{
            marginTop: '1rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '0.75rem',
          }}
        >
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
              Search Keyword
            </label>
            <input
              type="text"
              className="input"
              placeholder="Terminal name, ID, cluster..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ fontSize: '0.8125rem' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
              Indian Metro City
            </label>
            <select
              className="input"
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              style={{ fontSize: '0.8125rem' }}
            >
              {INDIAN_CITIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
              Terminal Type
            </label>
            <select
              className="input"
              value={locationType}
              onChange={(e) => setLocationType(e.target.value)}
              style={{ fontSize: '0.8125rem' }}
            >
              <option value="">All Types</option>
              <option value="atm">ATM Terminal</option>
              <option value="branch">Bank Branch</option>
              <option value="kiosk">CSP / Kiosk</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <ErrorMessage
          title="Location Query Failed"
          message={error}
          onRetry={fetchGISData}
        />
      )}

      {/* Main Interactive GIS Map Component with Concentric Rings, Clusters & Hotspots */}
      <LocationMap
        locations={locations}
        clusters={clusters}
        hotspots={hotspots}
        selectedLocationId={selectedLocationId}
        onSelectLocation={handleSelectLocation}
        centerLat={radiusSearchOpen ? parseFloat(centerLat) : undefined}
        centerLon={radiusSearchOpen ? parseFloat(centerLon) : undefined}
        radiusKm={radiusKm}
        showRadiusRings={radiusSearchOpen}
        loading={loading}
      />

      {/* Tab 2 Content: Spatial Clusters Summary Table */}
      {activeTab === 'clusters' && (
        <div className="card" style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Radio size={18} style={{ color: '#0369a1' }} />
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a' }}>
                Spatial Location Clusters &amp; Centroid Aggregations ({clusters.length})
              </h4>
            </div>
          </div>

          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Cluster ID</th>
                  <th>Cluster Name &amp; Area</th>
                  <th>City / Region</th>
                  <th>Total Terminals</th>
                  <th>ATM / Branch / Kiosk</th>
                  <th>Observed Cashouts</th>
                  <th>Centroid Coordinates</th>
                  <th>Map Action</th>
                </tr>
              </thead>
              <tbody>
                {clusters.map((c) => (
                  <tr key={c.area_cluster_id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 700, color: '#0369a1' }}>
                      {c.area_cluster_id}
                    </td>
                    <td style={{ fontWeight: 600, color: '#0f172a' }}>{c.cluster_name}</td>
                    <td>{c.city}, {c.region}</td>
                    <td style={{ fontWeight: 700 }}>{c.total_locations}</td>
                    <td>
                      <span style={{ fontSize: '0.75rem', color: '#475569' }}>
                        {c.atm_count} ATM • {c.branch_count} Branch • {c.kiosk_count} Kiosk
                      </span>
                    </td>
                    <td>
                      {c.observed_cashout_events_count > 0 ? (
                        <span style={{ color: '#c2410c', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Flame size={12} /> {c.observed_cashout_events_count} (₹{Number(c.total_observed_cashout_volume).toLocaleString()})
                        </span>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>0 events</span>
                      )}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b' }}>
                      {c.center_latitude.toFixed(4)}°N, {c.center_longitude.toFixed(4)}°E
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => {
                          setCenterLat(c.center_latitude.toString());
                          setCenterLon(c.center_longitude.toString());
                          setRadiusSearchOpen(true);
                        }}
                        style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
                      >
                        Center Map
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3 Content: Historical Cash-Out Hotspots */}
      {activeTab === 'hotspots' && (
        <div className="card" style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Flame size={18} style={{ color: '#dc2626' }} />
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a' }}>
                High-Activity Historical Cashout Terminal Hotspots ({hotspots.length})
              </h4>
            </div>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Aggregated strictly from historical non-ground-truth cash-out events
            </span>
          </div>

          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Location Name &amp; ID</th>
                  <th>Type</th>
                  <th>City / Cluster</th>
                  <th>Observed Cashouts</th>
                  <th>Total Extraction Volume (₹)</th>
                  <th>Activity Risk Level</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {hotspots.map((h) => (
                  <tr key={h.location_id}>
                    <td>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{h.location_name}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>
                        {h.location_id}
                      </div>
                    </td>
                    <td>
                      <Badge variant="neutral">{h.location_type || 'ATM'}</Badge>
                    </td>
                    <td>
                      {h.city} ({h.area_cluster_id})
                    </td>
                    <td style={{ fontWeight: 700, color: '#c2410c' }}>
                      {h.observed_cashout_count} events
                    </td>
                    <td style={{ fontWeight: 700, color: '#0f172a' }}>
                      ₹{Number(h.total_observed_cashout_volume).toLocaleString()}
                    </td>
                    <td>
                      <Badge
                        variant={
                          h.activity_risk_level === 'high'
                            ? 'danger'
                            : h.activity_risk_level === 'elevated'
                            ? 'warning'
                            : 'neutral'
                        }
                      >
                        {h.activity_risk_level.toUpperCase()}
                      </Badge>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.35rem' }}>
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleSelectLocation(h.location_id)}
                          style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
                        >
                          Select Terminal
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Selected Location Details Card & One-Click Tactical Field Alert Drawer */}
      {selectedLocation && (
        <div className="card" style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Building size={18} style={{ color: '#0d9488' }} />
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a' }}>
                {selectedLocation.location_name} ({selectedLocation.location_id})
              </h4>
              <Badge variant="primary">{selectedLocation.location_type || 'ATM'}</Badge>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => handleSetAsCenter(selectedLocation)}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
              >
                <Crosshair size={14} /> Center Radius Query
              </button>
              <button
                className="btn btn-sm btn-primary"
                onClick={() => setActionModalOpen(true)}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
              >
                <AlertOctagon size={14} /> Log Tactical Alert / Surveillance
              </button>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setSelectedLocation(null)}
              >
                Close
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', fontSize: '0.8125rem' }}>
            <div>
              <span style={{ color: '#64748b' }}>City &amp; Region: </span>
              <strong>{selectedLocation.city}, {selectedLocation.region}</strong>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Cluster ID: </span>
              <span>{selectedLocation.area_cluster_id || 'N/A'}</span>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>GPS Coordinates: </span>
              <span style={{ fontFamily: 'monospace' }}>
                {selectedLocation.latitude.toFixed(6)}° N, {selectedLocation.longitude.toFixed(6)}° E
              </span>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Synthetic Group: </span>
              <span>{selectedLocation.synthetic_location_group || 'N/A'}</span>
            </div>
          </div>

          {/* Tactical Action Modal Dialog */}
          {actionModalOpen && (
            <form
              onSubmit={handleSubmitTacticalAction}
              style={{
                marginTop: '1.25rem',
                padding: '1.25rem',
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: '#0f172a' }}>
                  <Shield size={18} style={{ color: '#0d9488' }} />
                  Record Tactical Field Alert &amp; Surveillance Request
                </div>
                <button
                  type="button"
                  onClick={() => setActionModalOpen(false)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
                >
                  <X size={16} />
                </button>
              </div>

              {actionError && (
                <div
                  style={{
                    backgroundColor: '#fff1f2',
                    border: '1px solid #fecdd3',
                    color: '#9f1239',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    marginBottom: '0.75rem',
                  }}
                >
                  {actionError}
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569' }}>
                      Target Case ID *
                    </label>
                    {onOpenCase && actionCaseId.trim() && (
                      <button
                        type="button"
                        onClick={() => onOpenCase(actionCaseId.trim())}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.2rem',
                          background: 'none',
                          border: 'none',
                          color: '#0d9488',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          padding: 0,
                        }}
                      >
                        <ExternalLink size={12} /> View Dossier
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g. CASE-0001"
                    value={actionCaseId}
                    onChange={(e) => setActionCaseId(e.target.value)}
                    style={{ fontSize: '0.8125rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                    Action Type *
                  </label>
                  <select
                    className="input"
                    value={actionType}
                    onChange={(e) => setActionType(e.target.value)}
                    style={{ fontSize: '0.8125rem' }}
                  >
                    <option value="dispatch_alert">Terminal Dispatch Alert</option>
                    <option value="surveillance_requested">CCTV / Surveillance Request</option>
                    <option value="note_added">Investigator GIS Note</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                    Investigator Officer / Unit ID
                  </label>
                  <input
                    type="text"
                    className="input"
                    value={officerName}
                    onChange={(e) => setOfficerName(e.target.value)}
                    style={{ fontSize: '0.8125rem' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '0.75rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                  Operational Justification &amp; Notes *
                </label>
                <textarea
                  className="input"
                  rows={2}
                  placeholder="Provide tactical notes regarding physical terminal alert, nearby police station notification, or CCTV request..."
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  style={{ fontSize: '0.8125rem', resize: 'vertical' }}
                />
              </div>

              {/* Advisory Disclaimer Notice */}
              <div
                style={{
                  fontSize: '0.75rem',
                  color: '#64748b',
                  backgroundColor: '#ffffff',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '4px',
                  border: '1px solid #e2e8f0',
                  marginBottom: '0.75rem',
                }}
              >
                <strong>Audit Notice</strong>: Tactical field alerts and surveillance entries are recorded to the internal append-only database audit log. The system does not autonomously dispatch external law enforcement personnel.
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => setActionModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-sm btn-primary"
                  disabled={submittingAction}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                >
                  <Send size={14} /> {submittingAction ? 'Logging Action...' : 'Log Tactical Action in Audit Trail'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
};
