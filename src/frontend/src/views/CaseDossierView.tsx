import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import {
  CaseDetailResponse,
  MoneyTrailResponse,
  CaseNetworkResponse,
  PredictionDetailResponse,
  InvestigatorActionDetail,
  RelatedCaseEvidence,
} from '../types/api';
import {
  ArrowLeft,
  Layers,
  Network,
  Cpu,
  Shield,
  FileText,
  User,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { MoneyTrailGraph } from '../components/moneytrail/MoneyTrailGraph';
import { PredictionPanel } from '../components/predictions/PredictionPanel';
import { ActionDrawer } from '../components/actions/ActionDrawer';

type DossierTab = 'overview' | 'trail' | 'network' | 'prediction' | 'actions';

interface CaseDossierViewProps {
  caseId: string;
  onBackToList: () => void;
  onOpenAccount: (accountNumber: string) => void;
  onSelectLocation?: (locationId: string) => void;
  onShowToast: (toast: { type: 'success' | 'warning' | 'error'; title: string; description?: string }) => void;
}

export const CaseDossierView: React.FC<CaseDossierViewProps> = ({
  caseId,
  onBackToList,
  onOpenAccount,
  onSelectLocation,
  onShowToast,
}) => {
  const [activeTab, setActiveTab] = useState<DossierTab>('overview');

  // Case Data States
  const [caseData, setCaseData] = useState<CaseDetailResponse | null>(null);
  const [moneyTrail, setMoneyTrail] = useState<MoneyTrailResponse | null>(null);
  const [caseNetwork, setCaseNetwork] = useState<CaseNetworkResponse | null>(null);
  const [prediction, setPrediction] = useState<PredictionDetailResponse | null>(null);
  const [actions, setActions] = useState<InvestigatorActionDetail[]>([]);

  // Loading & Submitting states
  const [loading, setLoading] = useState<boolean>(true);
  const [trailLoading, setTrailLoading] = useState<boolean>(false);
  const [networkLoading, setNetworkLoading] = useState<boolean>(false);
  const [predLoading, setPredLoading] = useState<boolean>(false);
  const [triggeringPred, setTriggeringPred] = useState<boolean>(false);
  const [submittingAction, setSubmittingAction] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial case summary and actions
  const fetchCaseDetails = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCase(caseId);
      setCaseData(data);
      if (data.actions) {
        setActions(data.actions);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(`Failed to load dossier for ${caseId}`);
      }
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  // Load money trail
  const fetchMoneyTrail = useCallback(async () => {
    try {
      setTrailLoading(true);
      const trail = await api.getCaseMoneyTrail(caseId);
      setMoneyTrail(trail);
    } catch (err) {
      console.warn('Could not fetch money trail', err);
    } finally {
      setTrailLoading(false);
    }
  }, [caseId]);

  // Load syndicate network intelligence
  const fetchNetwork = useCallback(async () => {
    try {
      setNetworkLoading(true);
      const net = await api.getCaseNetwork(caseId);
      setCaseNetwork(net);
    } catch (err) {
      console.warn('Could not fetch case network intelligence', err);
    } finally {
      setNetworkLoading(false);
    }
  }, [caseId]);

  // Load latest prediction
  const fetchLatestPrediction = useCallback(async () => {
    try {
      setPredLoading(true);
      const pred = await api.getLatestCasePrediction(caseId);
      setPrediction(pred);
    } catch {
      // Prediction may not yet exist
      setPrediction(null);
    } finally {
      setPredLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    fetchCaseDetails();
    fetchMoneyTrail();
    fetchNetwork();
    fetchLatestPrediction();
  }, [fetchCaseDetails, fetchMoneyTrail, fetchNetwork, fetchLatestPrediction]);

  // Trigger On-demand ML Risk Prediction
  const handleTriggerPrediction = async () => {
    try {
      setTriggeringPred(true);
      const predRes = await api.triggerPrediction(caseId);
      setPrediction(predRes);
      onShowToast({
        type: 'success',
        title: 'Risk Assessment Generated',
        description: `Model A Probability: ${((predRes.occurrence?.probability_future_cashout ?? 0) * 100).toFixed(1)}% (${predRes.occurrence?.risk_tier?.toUpperCase()})`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to trigger prediction';
      onShowToast({
        type: 'error',
        title: 'Inference Failure',
        description: msg,
      });
    } finally {
      setTriggeringPred(false);
    }
  };

  // Submit Investigator Action
  const handleSubmitAction = async (actionData: {
    action_type: string;
    target_entity_type?: string;
    target_entity_id?: string;
    details?: Record<string, unknown>;
    notes?: string;
  }) => {
    try {
      setSubmittingAction(true);
      const newAction = await api.createCaseAction(caseId, {
        action_type: actionData.action_type,
        notes: actionData.notes,
        performed_by: 'investigator_lead',
        action_status: 'completed',
      });
      setActions((prev) => [newAction, ...prev]);
      onShowToast({
        type: 'success',
        title: 'Action Logged in Audit Trail',
        description: `${actionData.action_type.replace('_', ' ').toUpperCase()} recorded with Audit ID ${newAction.action_id.slice(0, 8)}...`,
      });
    } finally {
      setSubmittingAction(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center' }}>
        <LoadingSpinner size={36} label={`Retrieving case dossier for ${caseId}...`} />
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div>
        <button
          className="btn btn-secondary"
          onClick={onBackToList}
          style={{ marginBottom: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          <ArrowLeft size={16} /> Back to Case List
        </button>
        <ErrorMessage
          title="Case Dossier Unavailable"
          message={error || 'Case could not be found or loaded.'}
          onRetry={fetchCaseDetails}
        />
      </div>
    );
  }

  const fraudAmount = typeof caseData.fraud_amount === 'number' ? caseData.fraud_amount : parseFloat(String(caseData.fraud_amount) || '0');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Dossier Header Card */}
      <div className="card" style={{ padding: '1.25rem 1.5rem', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <button
            className="btn btn-sm btn-secondary"
            onClick={onBackToList}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <ArrowLeft size={14} /> Back to Case List
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <StatusBadge status={caseData.complaint_status} />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', backgroundColor: '#f1f5f9', padding: '0.2rem 0.5rem', borderRadius: '4px', fontWeight: 700, color: '#334155' }}>
                {caseData.case_id}
              </span>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
                {caseData.victim_account_id} — Financial Cybercrime Dossier
              </h1>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', marginTop: '0.25rem' }}>
              Registered on {new Date(caseData.complaint_registered_at).toLocaleString()} • Incident occurred {new Date(caseData.fraud_occurred_at).toLocaleString()}
            </p>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Total Fraud Loss Reported</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>
              ₹{fraudAmount.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
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
            { id: 'overview' as DossierTab, label: 'Overview & Evidence', icon: <FileText size={16} /> },
            { id: 'trail' as DossierTab, label: 'Money Trail Graph', icon: <Layers size={16} /> },
            { id: 'network' as DossierTab, label: 'Connected-Account Network', icon: <Network size={16} /> },
            { id: 'prediction' as DossierTab, label: 'AI Risk & ATM Decision Support', icon: <Cpu size={16} /> },
            { id: 'actions' as DossierTab, label: `Actions & Audit (${actions.length})`, icon: <Shield size={16} /> },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.625rem 1rem',
                  fontSize: '0.875rem',
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
      </div>

      {/* Tab 1: Overview & Evidence */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {/* Victim Profile & Incident Details */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <User size={16} style={{ color: '#0d9488' }} /> Victim Profile &amp; Incident Metadata
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8125rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Victim Account:</span>
                <span style={{ fontWeight: 600, fontFamily: 'monospace', color: '#0f172a' }}>
                  {caseData.victim_account_id}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Fraud Typology:</span>
                <Badge variant="neutral">{caseData.fraud_type}</Badge>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Extraction Channel:</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{caseData.fraud_channel}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Complaint Delay:</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{caseData.complaint_delay_minutes} minutes</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Accounts Involved in Trail:</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{caseData.total_accounts_involved}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Transactions Count:</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{caseData.total_transactions_count}</span>
              </div>
            </div>
          </div>

          {/* Complaint Description */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={16} style={{ color: '#0d9488' }} /> Complaint Narrative &amp; Description
            </h4>
            <div
              style={{
                backgroundColor: '#f8fafc',
                padding: '1rem',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                color: '#334155',
                lineHeight: 1.5,
                border: '1px solid #e2e8f0',
              }}
            >
              {caseData.synthetic_description || 'Victim reported unauthorized fund transfer initiated via deceptive social engineering/phishing protocol.'}
            </div>

            {/* Quick Action Link to Money Trail */}
            <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem' }}>
              <button
                className="btn btn-sm btn-primary"
                onClick={() => setActiveTab('trail')}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
              >
                <Layers size={14} /> Reconstruct Money Trail
              </button>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => setActiveTab('prediction')}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
              >
                <Cpu size={14} /> Run Cash-Out Risk Model
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Money Trail Graph */}
      {activeTab === 'trail' && (
        <div>
          <MoneyTrailGraph
            moneyTrail={moneyTrail}
            loading={trailLoading}
            onSelectAccount={(acc) => onOpenAccount(acc)}
          />
        </div>
      )}

      {/* Tab 3: Connected-Account Network & Cross-Case Intelligence */}
      {activeTab === 'network' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Network size={20} style={{ color: '#0d9488' }} />
              <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: '#0f172a' }}>
                Connected-Account Network &amp; Shared Accounts
              </h3>
            </div>
            <p style={{ fontSize: '0.8125rem', color: '#64748b' }}>
              Cross-case analysis identifying accounts observed across multiple synthetic cybercrime complaints.
            </p>

            {networkLoading ? (
              <div style={{ padding: '2rem', textAlign: 'center' }}>
                <LoadingSpinner size={24} label="Analyzing shared accounts across network..." />
              </div>
            ) : !caseNetwork || (!caseNetwork.relationships.length && !caseNetwork.direct_shared_accounts.length) ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.875rem' }}>
                No cross-case shared accounts identified for this complaint. The account trail appears confined to this single incident.
              </div>
            ) : (
              <div style={{ marginTop: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
                  <div style={{ backgroundColor: '#f8fafc', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Direct Shared Accounts</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
                      {caseNetwork.direct_shared_accounts.length}
                    </div>
                  </div>
                  <div style={{ backgroundColor: '#f8fafc', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Connected Cases in Network</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#dc2626' }}>
                      {caseNetwork.connected_cases_count}
                    </div>
                  </div>
                </div>

                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Connected Case ID</th>
                        <th>Relationship Type</th>
                        <th>Shared Account</th>
                        <th>Role in Current Case</th>
                        <th>Volume Shared (₹)</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {caseNetwork.relationships.map((rel: RelatedCaseEvidence, idx: number) => {
                        const vol = typeof rel.shared_amount_volume === 'number' ? rel.shared_amount_volume : parseFloat(String(rel.shared_amount_volume) || '0');
                        return (
                          <tr key={`rel-${idx}`}>
                            <td style={{ fontFamily: 'monospace', fontWeight: 700 }}>
                              {rel.related_case_id}
                            </td>
                            <td>
                              <Badge variant="neutral">{rel.relationship_type.replace('_', ' ')}</Badge>
                            </td>
                            <td style={{ fontFamily: 'monospace', fontWeight: 700 }}>
                              <button
                                onClick={() => onOpenAccount(rel.shared_account_id)}
                                style={{ background: 'none', border: 'none', color: '#0d9488', cursor: 'pointer', padding: 0 }}
                              >
                                {rel.shared_account_id}
                              </button>
                            </td>
                            <td>{rel.shared_account_role_in_current_case.replace('_', ' ')}</td>
                            <td style={{ fontWeight: 600 }}>₹{vol.toLocaleString()}</td>
                            <td>
                              <button
                                className="btn btn-sm btn-secondary"
                                onClick={() => onOpenAccount(rel.shared_account_id)}
                                style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
                              >
                                Inspect Account
                              </button>
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
        </div>
      )}

      {/* Tab 4: AI Prediction & Decision Support */}
      {activeTab === 'prediction' && (
        <div>
          <PredictionPanel
            prediction={prediction}
            loading={predLoading}
            onTriggerPrediction={handleTriggerPrediction}
            triggering={triggeringPred}
            onSelectLocation={onSelectLocation}
          />
        </div>
      )}

      {/* Tab 5: Actions & Audit Trail */}
      {activeTab === 'actions' && (
        <div>
          <ActionDrawer
            caseId={caseId}
            actions={actions}
            onSubmitAction={handleSubmitAction}
            submitting={submittingAction}
          />
        </div>
      )}
    </div>
  );
};
