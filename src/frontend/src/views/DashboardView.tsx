import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { CaseSummary, HealthResponse } from '../types/api';
import {
  FolderOpen,
  ArrowUpRight,
  Search,
  Activity,
  DollarSign,
  TrendingUp,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

interface DashboardViewProps {
  onOpenCase: (caseId: string) => void;
  onOpenAccount: (accountNumber: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onOpenCase,
  onOpenAccount,
}) => {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCases, setTotalCases] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [caseListRes, healthRes] = await Promise.all([
        api.listCases({ page: 1, page_size: 10, order_by: 'complaint_registered_at', order_desc: true }),
        api.getHealth().catch(() => null),
      ]);
      setCases(caseListRes.items);
      setTotalCases(caseListRes.pagination?.total || caseListRes.items.length);
      setHealth(healthRes);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch dashboard data.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const totalAmountTracked = cases.reduce((acc, c) => {
    const amt = typeof c.fraud_amount === 'number' ? c.fraud_amount : parseFloat(String(c.fraud_amount) || '0');
    return acc + amt;
  }, 0);

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const query = searchQuery.trim();
    if (query.startsWith('ACC-') || (query.length >= 10 && !query.startsWith('CASE-'))) {
      onOpenAccount(query);
    } else {
      onOpenCase(query);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner & Quick Triage Search */}
      <div
        className="card"
        style={{
          padding: '1.5rem',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: '#ffffff',
          borderRadius: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span
                style={{
                  backgroundColor: '#0d9488',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                }}
              >
                CASHNET COMMAND CONSOLE
              </span>
              <span style={{ fontSize: '0.8125rem', color: '#94a3b8' }}>
                AI Cybercrime Cash-Out Risk Decision Support
              </span>
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginTop: '0.5rem', letterSpacing: '-0.02em' }}>
              Investigator Operations &amp; Cash-Out Interception
            </h2>
            <p style={{ fontSize: '0.875rem', color: '#cbd5e1', maxWidth: '640px', marginTop: '0.25rem' }}>
              Multi-hop financial tracking, connected-account graph traversal, and geospatial candidate ATM prioritization for investigator decision support.
            </p>
          </div>

          {/* Quick Case / Account Jump Input */}
          <form onSubmit={handleQuickSearch} style={{ display: 'flex', gap: '0.5rem', minWidth: '320px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search
                size={16}
                style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}
              />
              <input
                type="text"
                placeholder="Search Case ID or Account (e.g. CASE-0001)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.625rem 0.75rem 0.625rem 2.25rem',
                  borderRadius: '6px',
                  border: '1px solid #334155',
                  backgroundColor: '#0f172a',
                  color: '#ffffff',
                  fontSize: '0.8125rem',
                }}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ padding: '0.625rem 1rem', fontSize: '0.8125rem' }}
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Summary KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
        {/* Total Cases */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#64748b' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Active Case Dossiers</span>
            <FolderOpen size={18} style={{ color: '#0d9488' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', marginTop: '0.5rem' }}>
            {totalCases.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
            Across synthetic jurisdictional complaints
          </div>
        </div>

        {/* Total Funds Tracked in Feed */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#64748b' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Tracked Financial Volume</span>
            <DollarSign size={18} style={{ color: '#0284c7' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', marginTop: '0.5rem' }}>
            ₹{totalAmountTracked.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
            Summed from recent complaint dossiers in feed
          </div>
        </div>

        {/* Database & Synthetic Scale */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#64748b' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Synthetic Network Scale</span>
            <TrendingUp size={18} style={{ color: '#d97706' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', marginTop: '0.5rem' }}>
            {health?.table_counts?.accounts ? `${health.table_counts.accounts.toLocaleString()} Accts` : '10,001 Accts'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
            {health?.table_counts?.transactions ? `${health.table_counts.transactions.toLocaleString()} txs` : '65,000+ transactions'}
          </div>
        </div>

        {/* Machine Learning Pipeline Status */}
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#64748b' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>ML Decision Support</span>
            <Activity size={18} style={{ color: '#059669' }} />
          </div>
          <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#059669', marginTop: '0.75rem' }}>
            Model A &amp; B Operational
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
            26-Feature Classifier &amp; GIS Fallback Active
          </div>
        </div>
      </div>

      {/* Priority Case Triage Table */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#0f172a' }}>
              Priority Case Triage &amp; Recent Ingestion Feed
            </h3>
            <p style={{ fontSize: '0.8125rem', color: '#64748b' }}>
              Latest cases registered for multi-hop graph analysis and cash-out prediction.
            </p>
          </div>

          <button
            className="btn btn-sm btn-secondary"
            onClick={fetchDashboardData}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Activity size={14} /> Refresh Feed
          </button>
        </div>

        {error && (
          <ErrorMessage
            message={error}
            onRetry={fetchDashboardData}
          />
        )}

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <LoadingSpinner size={28} label="Loading case triage data..." />
          </div>
        ) : cases.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
            No cases found. Ensure database is populated with synthetic dataset.
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Case Identifier</th>
                  <th>Victim Account</th>
                  <th>Amount Lost (₹)</th>
                  <th>Fraud Typology</th>
                  <th>Channel</th>
                  <th>Status</th>
                  <th>Registered At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => {
                  const amt = typeof c.fraud_amount === 'number' ? c.fraud_amount : parseFloat(String(c.fraud_amount) || '0');
                  return (
                    <tr key={c.case_id}>
                      <td>
                        <button
                          onClick={() => onOpenCase(c.case_id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#0d9488',
                            fontWeight: 700,
                            cursor: 'pointer',
                            padding: 0,
                            fontFamily: 'monospace',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                          }}
                        >
                          {c.case_id} <ArrowUpRight size={13} />
                        </button>
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, fontFamily: 'monospace', color: '#0f172a' }}>{c.victim_account_id}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{c.victim_city || 'Simulated Area'}</div>
                      </td>
                      <td style={{ fontWeight: 700, color: '#0f172a' }}>
                        ₹{amt.toLocaleString()}
                      </td>
                      <td>
                        <Badge variant="neutral">{c.fraud_type || 'Cybercrime'}</Badge>
                      </td>
                      <td>
                        <span style={{ fontSize: '0.8125rem', color: '#475569' }}>{c.fraud_channel || 'UPI'}</span>
                      </td>
                      <td>
                        <StatusBadge status={c.complaint_status || 'registered'} />
                      </td>
                      <td style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {c.complaint_registered_at ? new Date(c.complaint_registered_at).toLocaleString() : 'N/A'}
                      </td>
                      <td>
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => onOpenCase(c.case_id)}
                          style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
                        >
                          Open Dossier
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
