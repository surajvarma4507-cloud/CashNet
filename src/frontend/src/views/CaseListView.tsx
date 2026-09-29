import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { CaseSummary, PaginationMeta } from '../types/api';
import {
  FolderOpen,
  Search,
  RotateCw,
  ArrowRight,
  SlidersHorizontal,
  X,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { Badge } from '../components/common/Badge';
import { Pagination } from '../components/common/Pagination';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';

interface CaseListViewProps {
  onOpenCase: (caseId: string) => void;
}

export const CaseListView: React.FC<CaseListViewProps> = ({ onOpenCase }) => {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter & Pagination States
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(20);
  const [search, setSearch] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [fraudType, setFraudType] = useState<string>('');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');
  const [orderBy, setOrderBy] = useState<string>('complaint_registered_at');
  const [orderDesc, setOrderDesc] = useState<boolean>(true);
  const [showFilters, setShowFilters] = useState<boolean>(false);

  const [pagination, setPagination] = useState<PaginationMeta>({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 1,
  });

  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await api.listCases({
        page,
        page_size: pageSize,
        order_by: orderBy,
        order_desc: orderDesc,
        search: search.trim() || undefined,
        status: status || undefined,
        fraud_type: fraudType || undefined,
        min_amount: minAmount ? parseFloat(minAmount) : undefined,
        max_amount: maxAmount ? parseFloat(maxAmount) : undefined,
      });

      setCases(res.items);
      setPagination(res.pagination || {
        page: 1,
        page_size: pageSize,
        total: res.items.length,
        total_pages: 1,
      });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch case list.');
      }
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, orderBy, orderDesc, search, status, fraudType, minAmount, maxAmount]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCases();
  };

  const handleClearFilters = () => {
    setSearch('');
    setStatus('');
    setFraudType('');
    setMinAmount('');
    setMaxAmount('');
    setPage(1);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header & Main Search */}
      <div className="card" style={{ padding: '1.25rem 1.5rem', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FolderOpen size={22} style={{ color: '#0d9488' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
                Case Dossiers &amp; Money Trails
              </h2>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.25rem' }}>
              Search, filter, and triage cybercrime complaints and multi-hop mule account trails.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              className="btn btn-sm btn-secondary"
              onClick={() => setShowFilters(!showFilters)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <SlidersHorizontal size={14} />
              {showFilters ? 'Hide Filters' : 'Advanced Filters'}
            </button>
            <button
              className="btn btn-sm btn-secondary"
              onClick={fetchCases}
              disabled={loading}
              title="Refresh List"
            >
              <RotateCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Quick Search Bar */}
        <form onSubmit={handleSearchSubmit} style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search
              size={16}
              style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}
            />
            <input
              type="text"
              className="input"
              placeholder="Search by Case ID, Victim Account, or Typology..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '2.25rem', fontSize: '0.875rem' }}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            <Search size={14} /> Filter
          </button>
          {(search || status || fraudType || minAmount || maxAmount) && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClearFilters}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
            >
              <X size={14} /> Clear
            </button>
          )}
        </form>

        {/* Filter Drawer */}
        {showFilters && (
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.75rem',
            }}
          >
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Complaint Status
              </label>
              <select
                className="input"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  setPage(1);
                }}
                style={{ fontSize: '0.8125rem' }}
              >
                <option value="">All Statuses</option>
                <option value="registered">Registered</option>
                <option value="under_investigation">Under Investigation</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Fraud Typology
              </label>
              <select
                className="input"
                value={fraudType}
                onChange={(e) => {
                  setFraudType(e.target.value);
                  setPage(1);
                }}
                style={{ fontSize: '0.8125rem' }}
              >
                <option value="">All Typologies</option>
                <option value="investment_scam">Investment Scam</option>
                <option value="loan_fraud">Loan Fraud</option>
                <option value="impersonation">Impersonation</option>
                <option value="part_time_job_scam">Part-Time Job Scam</option>
                <option value="upi_phishing">UPI Phishing</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Min Loss (₹)
              </label>
              <input
                type="number"
                className="input"
                placeholder="0"
                value={minAmount}
                onChange={(e) => {
                  setMinAmount(e.target.value);
                  setPage(1);
                }}
                style={{ fontSize: '0.8125rem' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Sort Field
              </label>
              <select
                className="input"
                value={orderBy}
                onChange={(e) => setOrderBy(e.target.value)}
                style={{ fontSize: '0.8125rem' }}
              >
                <option value="complaint_registered_at">Registration Time</option>
                <option value="fraud_amount">Fraud Amount</option>
                <option value="fraud_occurred_at">Incident Occurrence</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Sort Direction
              </label>
              <select
                className="input"
                value={orderDesc ? 'desc' : 'asc'}
                onChange={(e) => setOrderDesc(e.target.value === 'desc')}
                style={{ fontSize: '0.8125rem' }}
              >
                <option value="desc">Descending (Newest / Highest First)</option>
                <option value="asc">Ascending (Oldest / Lowest First)</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Case Table Card */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', backgroundColor: '#ffffff' }}>
        {error && (
          <div style={{ padding: '1rem' }}>
            <ErrorMessage message={error} onRetry={fetchCases} />
          </div>
        )}

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <LoadingSpinner size={32} label="Retrieving case records from database..." />
          </div>
        ) : cases.length === 0 ? (
          <EmptyState
            title="No Case Records Found"
            description="No cases matched your search query or filter parameters. Try clearing your filters."
            action={
              <button className="btn btn-secondary" onClick={handleClearFilters}>
                Clear All Filters
              </button>
            }
          />
        ) : (
          <div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Case ID</th>
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
                        <td style={{ fontFamily: 'monospace', fontWeight: 700 }}>
                          <button
                            onClick={() => onOpenCase(c.case_id)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#0d9488',
                              cursor: 'pointer',
                              padding: 0,
                              fontWeight: 700,
                            }}
                          >
                            {c.case_id}
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
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                          >
                            Dossier <ArrowRight size={12} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Component */}
            <Pagination
              pagination={pagination}
              onPageChange={(newPage) => setPage(newPage)}
              disabled={loading}
            />
          </div>
        )}
      </div>
    </div>
  );
};
