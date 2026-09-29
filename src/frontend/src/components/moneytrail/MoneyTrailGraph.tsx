import React, { useState, useMemo } from 'react';
import {
  MoneyTrailResponse,
  MoneyTrailNode,
  MoneyTrailEdge
} from '../../types/api';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  List,
  Network,
  AlertTriangle,
  ArrowRight,
  Layers
} from 'lucide-react';
import { Badge } from '../common/Badge';

interface MoneyTrailGraphProps {
  moneyTrail: MoneyTrailResponse | null;
  loading?: boolean;
  onSelectAccount?: (accountNumber: string) => void;
  selectedAccountNumber?: string | null;
}

export const MoneyTrailGraph: React.FC<MoneyTrailGraphProps> = ({
  moneyTrail,
  loading = false,
  onSelectAccount,
  selectedAccountNumber,
}) => {
  const [viewMode, setViewMode] = useState<'graph' | 'table'>('graph');
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<MoneyTrailNode | null>(null);

  // Group nodes by hop_level for hierarchical layout
  const layout = useMemo(() => {
    if (!moneyTrail || !moneyTrail.nodes || moneyTrail.nodes.length === 0) {
      return { nodePositions: new Map<string, { x: number; y: number }>(), width: 800, height: 450 };
    }

    const nodesByHop: { [hop: number]: MoneyTrailNode[] } = {};
    let maxHop = 0;

    moneyTrail.nodes.forEach((n) => {
      const hop = Math.max(0, n.hop_level ?? 0);
      if (!nodesByHop[hop]) nodesByHop[hop] = [];
      nodesByHop[hop].push(n);
      if (hop > maxHop) maxHop = hop;
    });

    const nodePositions = new Map<string, { x: number; y: number }>();
    const hopColumnWidth = 240;
    const verticalSpacing = 90;
    const startX = 100;
    const startY = 80;

    let maxNodesInHop = 0;

    Object.keys(nodesByHop).forEach((hopStr) => {
      const hop = parseInt(hopStr, 10);
      const hopNodes = nodesByHop[hop];
      if (hopNodes.length > maxNodesInHop) {
        maxNodesInHop = hopNodes.length;
      }

      hopNodes.forEach((node, idx) => {
        const x = startX + hop * hopColumnWidth;
        const totalHeightForHop = hopNodes.length * verticalSpacing;
        const offsetY = (maxNodesInHop * verticalSpacing - totalHeightForHop) / 2;
        const y = startY + idx * verticalSpacing + Math.max(0, offsetY);
        nodePositions.set(node.account_id, { x, y });
      });
    });

    const totalWidth = Math.max(850, startX + (maxHop + 1) * hopColumnWidth + 120);
    const totalHeight = Math.max(450, startY + maxNodesInHop * verticalSpacing + 100);

    return { nodePositions, width: totalWidth, height: totalHeight };
  }, [moneyTrail]);

  // Set of cyclic accounts
  const cyclicAccountSet = useMemo(() => {
    const s = new Set<string>();
    if (moneyTrail?.anomalies?.cycles) {
      moneyTrail.anomalies.cycles.forEach((cycle) => {
        cycle.forEach((acc) => s.add(acc));
      });
    }
    return s;
  }, [moneyTrail]);

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

  const handleZoomIn = () => setZoom((z) => Math.min(2.0, z + 0.2));
  const handleZoomOut = () => setZoom((z) => Math.max(0.4, z - 0.2));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  if (loading) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: '8px' }}>
        <div className="skeleton" style={{ height: '320px', width: '100%', borderRadius: '8px' }} />
        <p style={{ marginTop: '1rem', color: '#64748b', fontSize: '0.875rem' }}>
          Reconstructing multi-hop transaction graph...
        </p>
      </div>
    );
  }

  if (!moneyTrail || !moneyTrail.nodes || moneyTrail.nodes.length === 0) {
    return (
      <div
        style={{
          padding: '3rem 1.5rem',
          textAlign: 'center',
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          border: '1px dashed #cbd5e1',
        }}
      >
        <Network size={36} style={{ color: '#94a3b8', margin: '0 auto 0.75rem' }} />
        <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#0f172a' }}>No Money Trail Traversal Available</h4>
        <p style={{ fontSize: '0.8125rem', color: '#64748b', maxWidth: '420px', margin: '0.25rem auto 0' }}>
          This case has no recorded multi-hop transfers or outgoing mule hops matching the current filter parameters.
        </p>
      </div>
    );
  }

  const { nodePositions } = layout;
  const edges = moneyTrail.ledger || [];
  const hasCycles = moneyTrail.anomalies?.has_cycles || false;
  const cycleCount = moneyTrail.anomalies?.cycles?.length || 0;

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', backgroundColor: '#ffffff' }}>
      {/* Controls & Metrics Header */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={18} style={{ color: '#0d9488' }} />
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#0f172a' }}>
              Multi-Hop Money Trail &amp; Mule Network
            </h4>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: '#475569' }}>
            <span style={{ padding: '0.2rem 0.5rem', backgroundColor: '#ffffff', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
              <strong>{moneyTrail.nodes.length}</strong> Accounts
            </span>
            <span style={{ padding: '0.2rem 0.5rem', backgroundColor: '#ffffff', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
              <strong>{edges.length}</strong> Transfers
            </span>
            <span style={{ padding: '0.2rem 0.5rem', backgroundColor: '#ffffff', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
              Max Depth: <strong>{moneyTrail.anomalies?.max_depth ?? 0} hops</strong>
            </span>
            {hasCycles && (
              <span
                style={{
                  padding: '0.2rem 0.5rem',
                  backgroundColor: '#fef2f2',
                  color: '#991b1b',
                  borderRadius: '4px',
                  border: '1px solid #fecdd3',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  fontWeight: 600,
                }}
              >
                <AlertTriangle size={12} /> {cycleCount} Transfer Cycle(s) Identified
              </span>
            )}
          </div>
        </div>

        {/* View Switcher & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ display: 'inline-flex', backgroundColor: '#e2e8f0', borderRadius: '6px', padding: '2px' }}>
            <button
              onClick={() => setViewMode('graph')}
              style={{
                border: 'none',
                background: viewMode === 'graph' ? '#ffffff' : 'transparent',
                color: viewMode === 'graph' ? '#0f172a' : '#64748b',
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
              <Network size={14} /> Graph
            </button>
            <button
              onClick={() => setViewMode('table')}
              style={{
                border: 'none',
                background: viewMode === 'table' ? '#ffffff' : 'transparent',
                color: viewMode === 'table' ? '#0f172a' : '#64748b',
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
              <List size={14} /> Table View
            </button>
          </div>

          {viewMode === 'graph' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginLeft: '0.5rem' }}>
              <button
                className="btn btn-sm btn-secondary"
                onClick={handleZoomIn}
                title="Zoom In"
              >
                <ZoomIn size={14} />
              </button>
              <button
                className="btn btn-sm btn-secondary"
                onClick={handleZoomOut}
                title="Zoom Out"
              >
                <ZoomOut size={14} />
              </button>
              <button
                className="btn btn-sm btn-secondary"
                onClick={handleResetZoom}
                title="Reset View"
              >
                <RotateCcw size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {viewMode === 'graph' ? (
        <div style={{ position: 'relative', width: '100%', height: '480px', overflow: 'hidden', backgroundColor: '#fcfdfd' }}>
          {/* Graph Legend */}
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
              boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.35rem',
            }}
          >
            <div style={{ fontWeight: 600, color: '#334155', marginBottom: '0.125rem' }}>Node Legend</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#0284c7', display: 'inline-block' }} />
              <span>Hop 0: Victim Source</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#d97706', display: 'inline-block' }} />
              <span>Hop 1: Intermediary Account Layer</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#dc2626', display: 'inline-block' }} />
              <span>Hop 2+: Destination / Terminal Transfer</span>
            </div>
            {hasCycles && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#991b1b' }}>
                <span style={{ width: 12, height: 12, borderRadius: '2px', border: '2px dashed #dc2626', display: 'inline-block' }} />
                <span>Cyclic Flow Link</span>
              </div>
            )}
          </div>

          {/* SVG Canvas for Graph */}
          <svg
            width="100%"
            height="100%"
            style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="18"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#94a3b8" />
              </marker>
              <marker
                id="arrowhead-cycle"
                markerWidth="8"
                markerHeight="6"
                refX="18"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#dc2626" />
              </marker>
            </defs>

            <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
              {/* Draw Edges */}
              {edges.map((edge: MoneyTrailEdge, idx: number) => {
                const srcPos = nodePositions.get(edge.from_account_id);
                const tgtPos = nodePositions.get(edge.to_account_id);

                if (!srcPos || !tgtPos) return null;

                const isCyclic = cyclicAccountSet.has(edge.from_account_id) && cyclicAccountSet.has(edge.to_account_id);
                const isSelected =
                  selectedAccountNumber &&
                  (edge.from_account_id === selectedAccountNumber || edge.to_account_id === selectedAccountNumber);

                const midX = (srcPos.x + tgtPos.x) / 2;
                const midY = (srcPos.y + tgtPos.y) / 2;

                const amtNum = typeof edge.amount === 'number' ? edge.amount : parseFloat(String(edge.amount) || '0');

                return (
                  <g key={`edge-${edge.from_account_id}-${edge.to_account_id}-${idx}`}>
                    <line
                      x1={srcPos.x}
                      y1={srcPos.y}
                      x2={tgtPos.x}
                      y2={tgtPos.y}
                      stroke={isCyclic ? '#dc2626' : isSelected ? '#0d9488' : '#cbd5e1'}
                      strokeWidth={isSelected ? 3 : isCyclic ? 2.5 : 1.75}
                      strokeDasharray={isCyclic ? '5,5' : 'none'}
                      markerEnd={isCyclic ? 'url(#arrowhead-cycle)' : 'url(#arrowhead)'}
                    />

                    {/* Transaction Amount Tag on Edge */}
                    <g transform={`translate(${midX}, ${midY - 8})`}>
                      <rect
                        x="-36"
                        y="-10"
                        width="72"
                        height="18"
                        rx="4"
                        fill="#ffffff"
                        stroke={isCyclic ? '#fca5a5' : '#e2e8f0'}
                        strokeWidth="1"
                      />
                      <text
                        x="0"
                        y="2"
                        textAnchor="middle"
                        fontSize="9"
                        fontWeight="600"
                        fill={isCyclic ? '#991b1b' : '#334155'}
                      >
                        ₹{amtNum.toLocaleString()}
                      </text>
                    </g>
                  </g>
                );
              })}

              {/* Draw Nodes */}
              {moneyTrail.nodes.map((node: MoneyTrailNode) => {
                const pos = nodePositions.get(node.account_id);
                if (!pos) return null;

                const hop = Math.max(0, node.hop_level ?? 0);
                let fillColor = '#0284c7';
                if (hop === 1) fillColor = '#d97706';
                if (hop >= 2) fillColor = '#dc2626';

                const isSelected = selectedAccountNumber === node.account_id;
                const isCyclic = cyclicAccountSet.has(node.account_id);

                return (
                  <g
                    key={`node-${node.account_id}`}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    style={{ cursor: 'pointer' }}
                    onClick={() => onSelectAccount && onSelectAccount(node.account_id)}
                    onMouseEnter={() => setHoveredNode(node)}
                    onMouseLeave={() => setHoveredNode(null)}
                  >
                    {isCyclic && (
                      <circle
                        r="24"
                        fill="none"
                        stroke="#f87171"
                        strokeWidth="2"
                        strokeDasharray="4,4"
                        opacity="0.8"
                      />
                    )}

                    {isSelected && (
                      <circle
                        r="22"
                        fill="none"
                        stroke="#0d9488"
                        strokeWidth="3"
                        opacity="0.6"
                      />
                    )}

                    <circle
                      r="16"
                      fill={fillColor}
                      stroke="#ffffff"
                      strokeWidth="2.5"
                    />

                    <text
                      textAnchor="middle"
                      y="4"
                      fill="#ffffff"
                      fontSize="10"
                      fontWeight="bold"
                    >
                      H{hop}
                    </text>

                    <text
                      textAnchor="middle"
                      y="30"
                      fontSize="11"
                      fontWeight="600"
                      fill="#1e293b"
                    >
                      {node.account_id.slice(0, 8)}...
                    </text>

                    <text
                      textAnchor="middle"
                      y="42"
                      fontSize="9"
                      fill="#64748b"
                    >
                      {node.role.replace('_', ' ')}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>

          {/* Hover Tooltip */}
          {hoveredNode && (
            <div
              style={{
                position: 'absolute',
                bottom: '1rem',
                right: '1rem',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                fontSize: '0.8125rem',
                maxWidth: '280px',
                zIndex: 20,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <span style={{ fontWeight: 700, color: '#0f172a' }}>Account Details</span>
                <Badge variant={hoveredNode.hop_level === 0 ? 'info' : 'warning'}>
                  Hop {hoveredNode.hop_level}
                </Badge>
              </div>
              <div style={{ color: '#334155', fontWeight: 600 }}>{hoveredNode.account_id}</div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                Role: {hoveredNode.role.replace('_', ' ')}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.75rem' }}>
                Flow: In ₹{Number(hoveredNode.total_received).toLocaleString()} | Out ₹{Number(hoveredNode.total_sent).toLocaleString()}
              </div>
              {cyclicAccountSet.has(hoveredNode.account_id) && (
                <div style={{ color: '#dc2626', fontSize: '0.75rem', fontWeight: 600, marginTop: '0.25rem' }}>
                  ⚠ Part of cyclic mule routing loop
                </div>
              )}
              <div style={{ marginTop: '0.5rem', borderTop: '1px solid #f1f5f9', paddingTop: '0.35rem', fontSize: '0.75rem', color: '#0d9488' }}>
                Click to inspect account profile →
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Accessible Table View */
        <div style={{ padding: '1rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>
              Reconstructed Transfer Edges ({edges.length})
            </h5>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Source Account</th>
                    <th>Direction</th>
                    <th>Destination Account</th>
                    <th>Amount (₹)</th>
                    <th>Channel</th>
                    <th>Timestamp</th>
                    <th>Cycle Status</th>
                  </tr>
                </thead>
                <tbody>
                  {edges.map((edge: MoneyTrailEdge, i: number) => {
                    const isCyclic = cyclicAccountSet.has(edge.from_account_id) && cyclicAccountSet.has(edge.to_account_id);
                    const amt = typeof edge.amount === 'number' ? edge.amount : parseFloat(String(edge.amount) || '0');

                    return (
                      <tr key={`tbl-edge-${i}`}>
                        <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                          <button
                            onClick={() => onSelectAccount && onSelectAccount(edge.from_account_id)}
                            style={{ background: 'none', border: 'none', color: '#0d9488', cursor: 'pointer', padding: 0 }}
                          >
                            {edge.from_account_id}
                          </button>
                        </td>
                        <td style={{ textAlign: 'center', color: '#94a3b8' }}>
                          <ArrowRight size={14} style={{ display: 'inline' }} />
                        </td>
                        <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                          <button
                            onClick={() => onSelectAccount && onSelectAccount(edge.to_account_id)}
                            style={{ background: 'none', border: 'none', color: '#0d9488', cursor: 'pointer', padding: 0 }}
                          >
                            {edge.to_account_id}
                          </button>
                        </td>
                        <td style={{ fontWeight: 600 }}>₹{amt.toLocaleString()}</td>
                        <td>
                          <Badge variant="neutral">{edge.channel || 'TRANSFER'}</Badge>
                        </td>
                        <td style={{ fontSize: '0.75rem', color: '#64748b' }}>
                          {edge.completed_at ? new Date(edge.completed_at).toLocaleString() : 'N/A'}
                        </td>
                        <td>
                          {isCyclic ? (
                            <Badge variant="danger">Cyclic Loop</Badge>
                          ) : (
                            <Badge variant="neutral">Linear</Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
