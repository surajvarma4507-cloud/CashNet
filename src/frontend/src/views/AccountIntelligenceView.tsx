import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import {
  AccountDetail,
  AccountNetworkResponse,
  TransactionDetail,
} from '../types/api';
import {
  Network,
  Search,
  ArrowUpRight,
  ArrowDownLeft,
  FolderOpen,
  Layers,
  ShieldAlert
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';

interface AccountIntelligenceViewProps {
  initialAccountNumber?: string | null;
  onOpenCase: (caseId: string) => void;
  onSelectAccount?: (accountNumber: string) => void;
}

export const AccountIntelligenceView: React.FC<AccountIntelligenceViewProps> = ({
  initialAccountNumber,
  onOpenCase,
  onSelectAccount: _onSelectAccount,
}) => {
  const [accountNumber, setAccountNumber] = useState<string>(initialAccountNumber || '');
  const [searchInput, setSearchInput] = useState<string>(initialAccountNumber || '');
  const [accountData, setAccountData] = useState<AccountDetail | null>(null);
  const [accountNetwork, setAccountNetwork] = useState<AccountNetworkResponse | null>(null);
  const [transactions, setTransactions] = useState<TransactionDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAccountProfile = useCallback(async (accNum: string) => {
    if (!accNum.trim()) return;
    try {
      setLoading(true);
      setError(null);
      const [accRes, netRes, txRes] = await Promise.all([
        api.getAccount(accNum.trim()),
        api.getAccountNetwork(accNum.trim()).catch(() => null),
        api.getAccountTransactions(accNum.trim(), { page: 1, page_size: 20 }).catch(() => ({ items: [], total: 0 })),
      ]);
      setAccountData(accRes);
      setAccountNetwork(netRes);
      setTransactions(txRes.items || []);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(`Failed to retrieve intelligence profile for account ${accNum}`);
      }
      setAccountData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialAccountNumber) {
      setAccountNumber(initialAccountNumber);
      setSearchInput(initialAccountNumber);
      fetchAccountProfile(initialAccountNumber);
    }
  }, [initialAccountNumber, fetchAccountProfile]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    setAccountNumber(searchInput.trim());
    fetchAccountProfile(searchInput.trim());
  };

  const isMule = accountData?.label?.is_synthetic_mule === 1 || (accountData?.synthetic_profile_type && accountData.synthetic_profile_type !== 'regular');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Search Header Card */}
      <div className="card" style={{ padding: '1.25rem 1.5rem', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Network size={22} style={{ color: '#0d9488' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
                Account Intelligence &amp; Connected-Network Profile
              </h2>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.25rem' }}>
              Investigate account-level layering velocity, cross-complaint participation, and connected counterparties.
            </p>
          </div>
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearch} style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search
              size={16}
              style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}
            />
            <input
              type="text"
              className="input"
              placeholder="Enter Account Number (e.g. ACC-491029)..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              style={{ paddingLeft: '2.25rem', fontSize: '0.875rem' }}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            <Search size={14} /> Look Up Account
          </button>
        </form>
      </div>

      {error && (
        <ErrorMessage
          title="Account Query Failed"
          message={error}
          onRetry={() => fetchAccountProfile(accountNumber)}
        />
      )}

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center' }}>
          <LoadingSpinner size={32} label={`Retrieving account profile for ${accountNumber}...`} />
        </div>
      ) : !accountData ? (
        <EmptyState
          title="No Account Profile Selected"
          description="Enter an account number above or select an account node from a case money trail to inspect its intelligence dossier."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Account Profile Summary Header */}
          <div className="card" style={{ padding: '1.25rem 1.5rem', backgroundColor: '#ffffff' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'monospace', color: '#0f172a' }}>
                    {accountData.account_id}
                  </span>
                  {isMule && (
                    <Badge variant="danger">
                      <ShieldAlert size={12} /> Synthetic Profile: {accountData.label?.synthetic_behaviour_type || accountData.synthetic_profile_type}
                    </Badge>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.35rem', fontSize: '0.8125rem', color: '#475569' }}>
                  <span>Status: <strong>{accountData.account_status}</strong></span>
                  <span>Type: <strong>{accountData.account_type || 'Savings'}</strong></span>
                  <span>Age: <strong>{accountData.account_age_days} days</strong></span>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Cross-Case Complaints</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#dc2626' }}>
                  {accountNetwork?.participating_cases_count ?? 1}
                </div>
              </div>
            </div>
          </div>

          {/* Associated Cybercrime Complaints Grid */}
          <div className="card" style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <FolderOpen size={18} style={{ color: '#0d9488' }} />
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a' }}>
                Participating Cybercrime Case Dossiers ({accountNetwork?.participating_cases?.length || 0})
              </h4>
            </div>

            {accountNetwork?.participating_cases && accountNetwork.participating_cases.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
                {accountNetwork.participating_cases.map((caseId: string) => (
                  <div
                    key={caseId}
                    style={{
                      padding: '0.875rem',
                      borderRadius: '6px',
                      border: '1px solid #e2e8f0',
                      backgroundColor: '#f8fafc',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: '0.5rem',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontFamily: 'monospace', color: '#0d9488', fontSize: '0.875rem' }}>
                        {caseId}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                        Observed in multi-hop transfer network
                      </div>
                    </div>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => onOpenCase(caseId)}
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', width: '100%' }}
                    >
                      Open Case Dossier →
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.8125rem', color: '#64748b' }}>No associated cases linked.</p>
            )}
          </div>

          {/* Recent Account Transactions Feed */}
          <div className="card" style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Layers size={18} style={{ color: '#0d9488' }} />
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a' }}>
                Account Transaction History ({transactions.length})
              </h4>
            </div>

            {transactions.length === 0 ? (
              <p style={{ fontSize: '0.8125rem', color: '#64748b' }}>No transactions recorded for this account.</p>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Direction</th>
                      <th>Counterparty Account</th>
                      <th>Amount (₹)</th>
                      <th>Channel</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx: TransactionDetail, idx: number) => {
                      const isOutflow = tx.from_account_id === accountData.account_id;
                      const counterparty = isOutflow ? tx.to_account_id : tx.from_account_id;
                      const amt = typeof tx.amount === 'number' ? tx.amount : parseFloat(String(tx.amount) || '0');

                      return (
                        <tr key={tx.transaction_id || `tx-${idx}`}>
                          <td>
                            {isOutflow ? (
                              <span style={{ color: '#dc2626', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontWeight: 600, fontSize: '0.75rem' }}>
                                <ArrowUpRight size={13} /> OUTFLOW
                              </span>
                            ) : (
                              <span style={{ color: '#16a34a', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontWeight: 600, fontSize: '0.75rem' }}>
                                <ArrowDownLeft size={13} /> INFLOW
                              </span>
                            )}
                          </td>
                          <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                            <button
                              onClick={() => {
                                setAccountNumber(counterparty);
                                setSearchInput(counterparty);
                                fetchAccountProfile(counterparty);
                              }}
                              style={{ background: 'none', border: 'none', color: '#0d9488', cursor: 'pointer', padding: 0 }}
                            >
                              {counterparty}
                            </button>
                          </td>
                          <td style={{ fontWeight: 700, color: '#0f172a' }}>
                            ₹{amt.toLocaleString()}
                          </td>
                          <td>
                            <Badge variant="neutral">{tx.channel || 'UPI'}</Badge>
                          </td>
                          <td style={{ fontSize: '0.75rem', color: '#64748b' }}>
                            {tx.initiated_at ? new Date(tx.initiated_at).toLocaleString() : 'N/A'}
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
      )}
    </div>
  );
};
