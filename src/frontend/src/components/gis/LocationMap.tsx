import React, { useState, useMemo } from 'react';
import {
  LocationDetail,
  RankedLocationCandidate,
  LocationClusterSummary,
  LocationHotspotDetail,
} from '../../types/api';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  List,
  Map as MapIcon,
  Layers,
  Flame,
  Radio,
  Crosshair,
} from 'lucide-react';
import { Badge } from '../common/Badge';

interface LocationMapProps {
  locations: LocationDetail[];
  candidates?: RankedLocationCandidate[];
  clusters?: LocationClusterSummary[];
  hotspots?: LocationHotspotDetail[];
  selectedLocationId?: string | null;
  onSelectLocation?: (locationId: string) => void;
  centerLat?: number;
  centerLon?: number;
  radiusKm?: number;
  showRadiusRings?: boolean;
  loading?: boolean;
}

export const LocationMap: React.FC<LocationMapProps> = ({
  locations,
  candidates = [],
  clusters = [],
  hotspots = [],
  selectedLocationId,
  onSelectLocation,
  centerLat,
  centerLon,
  radiusKm,
  showRadiusRings = true,
  loading = false,
}) => {
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [hoveredLoc, setHoveredLoc] = useState<LocationDetail | null>(null);
  const [hoveredCluster, setHoveredCluster] = useState<LocationClusterSummary | null>(null);

  // Layer Visibility Toggles
  const [showTerminalsLayer, setShowTerminalsLayer] = useState<boolean>(true);
  const [showClustersLayer, setShowClustersLayer] = useState<boolean>(true);
  const [showHotspotsLayer, setShowHotspotsLayer] = useState<boolean>(true);
  const [showRingsLayer, setShowRingsLayer] = useState<boolean>(showRadiusRings);

  // Candidate ID lookup set
  const candidateIdSet = useMemo(() => {
    const s = new Set<string>();
    candidates.forEach((c) => s.add(c.location_id));
    return s;
  }, [candidates]);

  // Hotspot lookup map
  const hotspotMap = useMemo(() => {
    const m = new Map<string, LocationHotspotDetail>();
    hotspots.forEach((h) => m.set(h.location_id, h));
    return m;
  }, [hotspots]);

  // Calculate bounding box of coordinates to fit neatly in SVG
  const geoBounds = useMemo(() => {
    let minLat = 90,
      maxLat = -90,
      minLon = 180,
      maxLon = -180;

    const allPoints: { lat: number; lon: number }[] = [];

    locations.forEach((l) => allPoints.push({ lat: l.latitude, lon: l.longitude }));
    clusters.forEach((c) =>
      allPoints.push({ lat: c.center_latitude, lon: c.center_longitude })
    );
    if (centerLat !== undefined && centerLon !== undefined) {
      allPoints.push({ lat: centerLat, lon: centerLon });
    }

    if (allPoints.length === 0) {
      return { minLat: 18.8, maxLat: 28.8, minLon: 72.6, maxLon: 88.5 };
    }

    allPoints.forEach((p) => {
      if (p.lat < minLat) minLat = p.lat;
      if (p.lat > maxLat) maxLat = p.lat;
      if (p.lon < minLon) minLon = p.lon;
      if (p.lon > maxLon) maxLon = p.lon;
    });

    // Add margin
    const latPadding = Math.max(0.04, (maxLat - minLat) * 0.12);
    const lonPadding = Math.max(0.04, (maxLon - minLon) * 0.12);

    return {
      minLat: minLat - latPadding,
      maxLat: maxLat + latPadding,
      minLon: minLon - lonPadding,
      maxLon: maxLon + lonPadding,
    };
  }, [locations, clusters, centerLat, centerLon]);

  // Project lat/lon to SVG coordinates
  const project = (lat: number, lon: number, width = 860, height = 500) => {
    const { minLat, maxLat, minLon, maxLon } = geoBounds;
    const x = ((lon - minLon) / (maxLon - minLon || 1)) * (width - 120) + 60;
    const y = height - (((lat - minLat) / (maxLat - minLat || 1)) * (height - 120) + 60);
    return { x, y };
  };

  // Calculate pixel radius for a given km distance around center coordinate
  const getPixelRadius = (
    lat: number,
    lon: number,
    distKm: number,
    width = 860,
    height = 500
  ) => {
    const p1 = project(lat, lon, width, height);
    // 1 deg lat is approximately 111 km
    const latOffset = distKm / 111.0;
    const p2 = project(lat + latOffset, lon, width, height);
    return Math.abs(p1.y - p2.y);
  };

  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  if (loading) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="skeleton" style={{ height: '400px', width: '100%', borderRadius: '8px' }} />
        <p style={{ marginTop: '1rem', color: '#64748b', fontSize: '0.875rem' }}>
          Loading GIS coordinates &amp; physical terminal infrastructure...
        </p>
      </div>
    );
  }

  // Active anchor center
  const hasCenterAnchor = centerLat !== undefined && centerLon !== undefined;
  const anchorPos = hasCenterAnchor ? project(centerLat, centerLon) : null;

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', backgroundColor: '#ffffff' }}>
      {/* Header & Controls Toolbar */}
      <div
        style={{
          padding: '0.875rem 1.25rem',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          backgroundColor: '#f8fafc',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MapIcon size={18} style={{ color: '#0d9488' }} />
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#0f172a' }}>
              Interactive GIS Map &amp; Spatial Intelligence
            </h4>
          </div>
          <span
            style={{
              fontSize: '0.75rem',
              color: '#475569',
              backgroundColor: '#ffffff',
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              border: '1px solid #e2e8f0',
            }}
          >
            <strong>{locations.length}</strong> Terminals Plotted
          </span>
          {clusters.length > 0 && (
            <span
              style={{
                fontSize: '0.75rem',
                color: '#475569',
                backgroundColor: '#ffffff',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                border: '1px solid #e2e8f0',
              }}
            >
              <strong>{clusters.length}</strong> Clusters
            </span>
          )}
          {hotspots.length > 0 && (
            <span
              style={{
                fontSize: '0.75rem',
                color: '#b91c1c',
                backgroundColor: '#fef2f2',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                border: '1px solid #fecaca',
                fontWeight: 600,
              }}
            >
              <strong>{hotspots.length}</strong> Hotspots
            </span>
          )}
        </div>

        {/* View Mode & Map Zoom Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {/* Layer Toggles */}
          {viewMode === 'map' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <button
                className={`btn btn-sm ${showTerminalsLayer ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setShowTerminalsLayer(!showTerminalsLayer)}
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                title="Toggle Terminals Layer"
              >
                <Layers size={13} /> Terminals
              </button>
              <button
                className={`btn btn-sm ${showClustersLayer ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setShowClustersLayer(!showClustersLayer)}
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                title="Toggle Spatial Clusters Layer"
              >
                <Radio size={13} /> Clusters
              </button>
              <button
                className={`btn btn-sm ${showHotspotsLayer ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setShowHotspotsLayer(!showHotspotsLayer)}
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                title="Toggle Hotspots Layer"
              >
                <Flame size={13} /> Hotspots
              </button>
              {hasCenterAnchor && (
                <button
                  className={`btn btn-sm ${showRingsLayer ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setShowRingsLayer(!showRingsLayer)}
                  style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                  title="Toggle Concentric Radius Rings"
                >
                  <Crosshair size={13} /> Rings (5/10/25km)
                </button>
              )}
            </div>
          )}

          <div style={{ display: 'inline-flex', backgroundColor: '#e2e8f0', borderRadius: '6px', padding: '2px' }}>
            <button
              onClick={() => setViewMode('map')}
              style={{
                border: 'none',
                background: viewMode === 'map' ? '#ffffff' : 'transparent',
                color: viewMode === 'map' ? '#0f172a' : '#64748b',
                padding: '0.25rem 0.625rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              <MapIcon size={14} /> Map View
            </button>
            <button
              onClick={() => setViewMode('list')}
              style={{
                border: 'none',
                background: viewMode === 'list' ? '#ffffff' : 'transparent',
                color: viewMode === 'list' ? '#0f172a' : '#64748b',
                padding: '0.25rem 0.625rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              <List size={14} /> Terminal List
            </button>
          </div>

          {viewMode === 'map' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setZoom((z) => Math.min(3.0, z + 0.25))}
                title="Zoom In"
              >
                <ZoomIn size={14} />
              </button>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}
                title="Zoom Out"
              >
                <ZoomOut size={14} />
              </button>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => {
                  setZoom(1);
                  setPan({ x: 0, y: 0 });
                }}
                title="Reset View"
              >
                <RotateCcw size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {viewMode === 'map' ? (
        <div style={{ position: 'relative', width: '100%', height: '520px', backgroundColor: '#f1f5f9', overflow: 'hidden' }}>
          {/* Map Grid Background pattern */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              opacity: 0.6,
            }}
          />

          {/* Map Legend */}
          <div
            style={{
              position: 'absolute',
              top: '1rem',
              left: '1rem',
              zIndex: 10,
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              padding: '0.5rem 0.75rem',
              fontSize: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.35rem',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
              maxWidth: '240px',
            }}
          >
            <div style={{ fontWeight: 700, color: '#0f172a' }}>Spatial Layer Legend</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#dc2626', display: 'inline-block', boxShadow: '0 0 6px #ef4444' }} />
              <span>Prioritized Candidate ATM (Model B)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#ea580c', display: 'inline-block' }} />
              <span>Cash-Out Hotspot Terminal</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#0d9488', display: 'inline-block' }} />
              <span>Standard ATM Terminal</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#2563eb', display: 'inline-block' }} />
              <span>Bank Branch</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#7c3aed', display: 'inline-block' }} />
              <span>CSP / Kiosk Point</span>
            </div>
            {hasCenterAnchor && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: 12, height: 12, border: '2px dashed #0d9488', borderRadius: '50%', display: 'inline-block' }} />
                <span>Radius Ring (5/10/25km)</span>
              </div>
            )}
          </div>

          <svg
            width="100%"
            height="100%"
            style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
              {/* LAYER 1: Concentric Spatial Radius Overlays */}
              {showRingsLayer && hasCenterAnchor && anchorPos && (
                <g className="radius-overlays">
                  {/* Preset Radii: 5km, 10km, 25km (and custom radiusKm) */}
                  {[
                    { km: 5, color: '#0d9488', strokeWidth: 1.5, dash: '4,4', fillOpacity: 0.04 },
                    { km: 10, color: '#0284c7', strokeWidth: 1.5, dash: '5,5', fillOpacity: 0.03 },
                    { km: 25, color: '#6366f1', strokeWidth: 1.5, dash: '6,6', fillOpacity: 0.02 },
                    ...(radiusKm && ![5, 10, 25].includes(radiusKm)
                      ? [{ km: radiusKm, color: '#f59e0b', strokeWidth: 2, dash: '3,3', fillOpacity: 0.05 }]
                      : []),
                  ].map((ring) => {
                    const rPixels = getPixelRadius(centerLat!, centerLon!, ring.km);
                    if (rPixels <= 0) return null;
                    return (
                      <g key={`radius-ring-${ring.km}`}>
                        <circle
                          cx={anchorPos.x}
                          cy={anchorPos.y}
                          r={rPixels}
                          fill={ring.color}
                          fillOpacity={ring.fillOpacity}
                          stroke={ring.color}
                          strokeWidth={ring.strokeWidth}
                          strokeDasharray={ring.dash}
                        />
                        {/* Distance Label Badge on top edge of ring */}
                        <g transform={`translate(${anchorPos.x}, ${anchorPos.y - rPixels})`}>
                          <rect
                            x="-22"
                            y="-14"
                            width="44"
                            height="16"
                            rx="3"
                            fill="#ffffff"
                            stroke={ring.color}
                            strokeWidth="1"
                            opacity="0.95"
                          />
                          <text
                            x="0"
                            y="-3"
                            textAnchor="middle"
                            fontSize="9"
                            fontWeight="700"
                            fill={ring.color}
                          >
                            {ring.km} km
                          </text>
                        </g>
                      </g>
                    );
                  })}

                  {/* Anchor Point Marker (Mule Home / Query Center) */}
                  <g transform={`translate(${anchorPos.x}, ${anchorPos.y})`}>
                    <circle r="14" fill="#0d9488" opacity="0.15" />
                    <circle r="8" fill="#0d9488" stroke="#ffffff" strokeWidth="2" />
                    <circle r="3" fill="#ffffff" />
                    <text
                      x="0"
                      y="18"
                      textAnchor="middle"
                      fontSize="9"
                      fontWeight="700"
                      fill="#0f172a"
                      stroke="#ffffff"
                      strokeWidth="2"
                      paintOrder="stroke"
                    >
                      Anchor (Mule Home)
                    </text>
                  </g>
                </g>
              )}

              {/* LAYER 2: Spatial Clusters Centroids */}
              {showClustersLayer &&
                clusters.map((cluster) => {
                  const { x, y } = project(cluster.center_latitude, cluster.center_longitude);
                  const isHovered = hoveredCluster?.area_cluster_id === cluster.area_cluster_id;
                  const clusterRadius = Math.max(16, Math.min(36, 12 + cluster.total_locations * 1.5));

                  return (
                    <g
                      key={`cluster-${cluster.area_cluster_id}`}
                      transform={`translate(${x}, ${y})`}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredCluster(cluster)}
                      onMouseLeave={() => setHoveredCluster(null)}
                    >
                      {/* Cluster Area Bounding Bubble */}
                      <circle
                        r={clusterRadius + (isHovered ? 6 : 0)}
                        fill="#0284c7"
                        fillOpacity={isHovered ? 0.25 : 0.12}
                        stroke="#0284c7"
                        strokeWidth={isHovered ? 2 : 1}
                        strokeDasharray="3,3"
                      />
                      {/* Centroid Pin */}
                      <circle
                        r={isHovered ? 12 : 9}
                        fill="#0369a1"
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                      <text
                        x="0"
                        y="3"
                        textAnchor="middle"
                        fontSize="8"
                        fontWeight="700"
                        fill="#ffffff"
                      >
                        {cluster.total_locations}
                      </text>
                      <text
                        x="0"
                        y={clusterRadius + 10}
                        textAnchor="middle"
                        fontSize="9"
                        fontWeight="600"
                        fill="#0369a1"
                        stroke="#ffffff"
                        strokeWidth="2"
                        paintOrder="stroke"
                      >
                        {cluster.area_cluster_id.replace('CLUSTER_', '')}
                      </text>
                    </g>
                  );
                })}

              {/* LAYER 3: Hotspot Density Glow */}
              {showHotspotsLayer &&
                hotspots.map((h) => {
                  const { x, y } = project(h.latitude, h.longitude);
                  const glowColor =
                    h.activity_risk_level === 'high'
                      ? '#ef4444'
                      : h.activity_risk_level === 'elevated'
                      ? '#f97316'
                      : '#eab308';

                  return (
                    <g key={`hotspot-glow-${h.location_id}`} transform={`translate(${x}, ${y})`}>
                      <circle
                        r="18"
                        fill={glowColor}
                        fillOpacity="0.3"
                        stroke={glowColor}
                        strokeWidth="1.5"
                      >
                        <animate
                          attributeName="r"
                          values="14;22;14"
                          dur="3s"
                          repeatCount="indefinite"
                        />
                        <animate
                          attributeName="fill-opacity"
                          values="0.35;0.1;0.35"
                          dur="3s"
                          repeatCount="indefinite"
                        />
                      </circle>
                    </g>
                  );
                })}

              {/* LAYER 4: Physical Terminals Plotted */}
              {showTerminalsLayer &&
                locations.map((loc) => {
                  const { x, y } = project(loc.latitude, loc.longitude);
                  const isCandidate = candidateIdSet.has(loc.location_id);
                  const isHotspot = hotspotMap.has(loc.location_id);
                  const isSelected = selectedLocationId === loc.location_id;
                  const isBranch = loc.location_type?.toLowerCase().includes('branch');
                  const isKiosk = loc.location_type?.toLowerCase().includes('kiosk') || loc.location_type?.toLowerCase().includes('csp');

                  let pinColor = '#0d9488';
                  if (isCandidate) pinColor = '#dc2626';
                  else if (isHotspot) pinColor = '#ea580c';
                  else if (isBranch) pinColor = '#2563eb';
                  else if (isKiosk) pinColor = '#7c3aed';

                  return (
                    <g
                      key={loc.location_id}
                      transform={`translate(${x}, ${y})`}
                      style={{ cursor: 'pointer' }}
                      onClick={() => onSelectLocation && onSelectLocation(loc.location_id)}
                      onMouseEnter={() => setHoveredLoc(loc)}
                      onMouseLeave={() => setHoveredLoc(null)}
                    >
                      {isCandidate && (
                        <circle
                          r="16"
                          fill="#fee2e2"
                          stroke="#ef4444"
                          strokeWidth="2"
                          opacity="0.9"
                        />
                      )}
                      {isSelected && (
                        <circle
                          r="18"
                          fill="none"
                          stroke="#0d9488"
                          strokeWidth="3"
                        />
                      )}
                      <circle
                        r={isCandidate ? 8 : isHotspot ? 6.5 : 5}
                        fill={pinColor}
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                      {(isCandidate || isSelected) && (
                        <text
                          x="0"
                          y="-12"
                          textAnchor="middle"
                          fontSize="10"
                          fontWeight="700"
                          fill="#0f172a"
                          stroke="#ffffff"
                          strokeWidth="2.5"
                          paintOrder="stroke"
                        >
                          {loc.location_name.slice(0, 16)}
                        </text>
                      )}
                    </g>
                  );
                })}
            </g>
          </svg>

          {/* Hover / Selected Info Tooltip */}
          {hoveredLoc && (
            <div
              style={{
                position: 'absolute',
                bottom: '1rem',
                right: '1rem',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
                fontSize: '0.8125rem',
                maxWidth: '320px',
                zIndex: 20,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem', gap: '0.5rem' }}>
                <span style={{ fontWeight: 700, color: '#0f172a' }}>{hoveredLoc.location_name}</span>
                <Badge variant={candidateIdSet.has(hoveredLoc.location_id) ? 'danger' : 'neutral'}>
                  {hoveredLoc.location_type || 'ATM'}
                </Badge>
              </div>
              <div style={{ color: '#475569', fontSize: '0.75rem' }}>
                {hoveredLoc.city}, {hoveredLoc.region}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.75rem', color: '#64748b' }}>
                <span>Cluster: <strong>{hoveredLoc.area_cluster_id || 'N/A'}</strong></span>
                <span style={{ fontFamily: 'monospace' }}>ID: {hoveredLoc.location_id}</span>
              </div>
              {hotspotMap.has(hoveredLoc.location_id) && (
                <div style={{ marginTop: '0.35rem', padding: '0.25rem 0.5rem', backgroundColor: '#fff7ed', borderRadius: '4px', border: '1px solid #fed7aa', fontSize: '0.75rem', color: '#9a3412', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Flame size={12} />
                  <span>
                    Observed Cashouts: <strong>{hotspotMap.get(hoveredLoc.location_id)?.observed_cashout_count}</strong> (₹{Number(hotspotMap.get(hoveredLoc.location_id)?.total_observed_cashout_volume).toLocaleString()})
                  </span>
                </div>
              )}
              <div style={{ marginTop: '0.35rem', fontSize: '0.6875rem', color: '#94a3b8' }}>
                GPS: {hoveredLoc.latitude.toFixed(6)}° N, {hoveredLoc.longitude.toFixed(6)}° E
              </div>
            </div>
          )}

          {/* Hovered Cluster Tooltip */}
          {hoveredCluster && !hoveredLoc && (
            <div
              style={{
                position: 'absolute',
                bottom: '1rem',
                right: '1rem',
                backgroundColor: '#ffffff',
                border: '1px solid #0284c7',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
                fontSize: '0.8125rem',
                maxWidth: '320px',
                zIndex: 20,
              }}
            >
              <div style={{ fontWeight: 700, color: '#0369a1', marginBottom: '0.25rem' }}>
                {hoveredCluster.cluster_name}
              </div>
              <div style={{ color: '#475569', fontSize: '0.75rem' }}>
                {hoveredCluster.city}, {hoveredCluster.region} ({hoveredCluster.area_cluster_id})
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '0.5rem', textAlign: 'center', fontSize: '0.75rem' }}>
                <div style={{ backgroundColor: '#f0f9ff', padding: '0.25rem', borderRadius: '4px' }}>
                  <div style={{ color: '#0369a1', fontWeight: 700 }}>{hoveredCluster.atm_count}</div>
                  <div style={{ color: '#64748b', fontSize: '0.6875rem' }}>ATMs</div>
                </div>
                <div style={{ backgroundColor: '#f0f9ff', padding: '0.25rem', borderRadius: '4px' }}>
                  <div style={{ color: '#0369a1', fontWeight: 700 }}>{hoveredCluster.branch_count}</div>
                  <div style={{ color: '#64748b', fontSize: '0.6875rem' }}>Branches</div>
                </div>
                <div style={{ backgroundColor: '#f0f9ff', padding: '0.25rem', borderRadius: '4px' }}>
                  <div style={{ color: '#0369a1', fontWeight: 700 }}>{hoveredCluster.kiosk_count}</div>
                  <div style={{ color: '#64748b', fontSize: '0.6875rem' }}>Kiosks</div>
                </div>
              </div>
              <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#64748b' }}>
                Centroid: {hoveredCluster.center_latitude.toFixed(4)}° N, {hoveredCluster.center_longitude.toFixed(4)}° E
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Terminal List Table */
        <div style={{ padding: '1rem' }}>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Location ID</th>
                  <th>Location Name</th>
                  <th>Type</th>
                  <th>City</th>
                  <th>Region / District</th>
                  <th>Cluster ID</th>
                  <th>Historical Cashouts</th>
                  <th>Coordinates</th>
                </tr>
              </thead>
              <tbody>
                {locations.map((loc) => {
                  const isCandidate = candidateIdSet.has(loc.location_id);
                  const isHotspot = hotspotMap.has(loc.location_id);
                  const hotspotInfo = hotspotMap.get(loc.location_id);

                  return (
                    <tr
                      key={loc.location_id}
                      style={{
                        backgroundColor: isCandidate ? '#fef2f2' : isHotspot ? '#fff7ed' : undefined,
                      }}
                    >
                      <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                        <button
                          onClick={() => onSelectLocation && onSelectLocation(loc.location_id)}
                          style={{ background: 'none', border: 'none', color: '#0d9488', cursor: 'pointer', padding: 0 }}
                        >
                          {loc.location_id}
                        </button>
                      </td>
                      <td style={{ fontWeight: 600, color: '#0f172a' }}>{loc.location_name}</td>
                      <td>
                        <Badge variant={isCandidate ? 'danger' : isHotspot ? 'warning' : 'neutral'}>
                          {loc.location_type || 'ATM'}
                        </Badge>
                      </td>
                      <td>{loc.city}</td>
                      <td>{loc.region}</td>
                      <td>{loc.area_cluster_id}</td>
                      <td>
                        {hotspotInfo ? (
                          <span style={{ color: '#c2410c', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Flame size={12} /> {hotspotInfo.observed_cashout_count} events
                          </span>
                        ) : (
                          <span style={{ color: '#94a3b8' }}>0 observed</span>
                        )}
                      </td>
                      <td style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>
                        {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
