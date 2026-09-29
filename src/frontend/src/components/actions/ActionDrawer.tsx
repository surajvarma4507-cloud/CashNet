import React, { useState } from 'react';
import {
  InvestigatorActionDetail,
  ActionType
} from '../../types/api';
import {
  Shield,
  Send,
  Lock,
  Radio,
  FileText,
  AlertOctagon,
  Clock,
  User,
  PlusCircle,
  X
} from 'lucide-react';
import { Badge } from '../common/Badge';

interface ActionDrawerProps {
  caseId: string;
  actions: InvestigatorActionDetail[];
  loading?: boolean;
  onSubmitAction: (actionData: {
    action_type: ActionType;
    target_entity_type?: string;
    target_entity_id?: string;
    details?: Record<string, unknown>;
    notes?: string;
  }) => Promise<void>;
  submitting?: boolean;
}

export const ActionDrawer: React.FC<ActionDrawerProps> = ({
  caseId: _caseId,
  actions,
  loading = false,
  onSubmitAction,
  submitting = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [actionType, setActionType] = useState<ActionType>('account_freeze');
  const [targetType, setTargetType] = useState<string>('account');
  const [targetId, setTargetId] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!notes.trim()) {
      setError('Investigation justification/notes are required for the audit trail.');
      return;
    }

    try {
      await onSubmitAction({
        action_type: actionType,
        target_entity_type: targetType || undefined,
        target_entity_id: targetId.trim() || undefined,
        notes: notes.trim(),
      });
      // Clear form on success
      setNotes('');
      setTargetId('');
      setIsOpen(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to record investigator action.');
      }
    }
  };

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'account_freeze':
        return <Lock size={15} style={{ color: '#dc2626' }} />;
      case 'dispatch_alert':
        return <Radio size={15} style={{ color: '#d97706' }} />;
      case 'bank_subpoena':
      case 'bank_notification':
        return <Shield size={15} style={{ color: '#0284c7' }} />;
      case 'surveillance_requested':
      case 'escalate_case':
        return <AlertOctagon size={15} style={{ color: '#7c3aed' }} />;
      default:
        return <FileText size={15} style={{ color: '#64748b' }} />;
    }
  };

  return (
    <div className="card" style={{ padding: '1.25rem', backgroundColor: '#ffffff' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1rem',
          flexWrap: 'wrap',
          gap: '0.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Shield size={18} style={{ color: '#0d9488' }} />
          <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#0f172a' }}>
            Investigator Action Log &amp; Audit Trail ({actions.length})
          </h4>
        </div>

        <button
          className="btn btn-sm btn-primary"
          onClick={() => setIsOpen(!isOpen)}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
        >
          {isOpen ? <X size={14} /> : <PlusCircle size={14} />}
          {isOpen ? 'Cancel Action' : 'Record New Action'}
        </button>
      </div>

      {/* New Action Form Container */}
      {isOpen && (
        <form
          onSubmit={handleSubmit}
          style={{
            marginBottom: '1.25rem',
            padding: '1rem',
            backgroundColor: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '8px',
          }}
        >
          <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0f172a', marginBottom: '0.75rem' }}>
            Record Authorized Investigator Action
          </div>

          {error && (
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
              {error}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Action Type *
              </label>
              <select
                className="input"
                value={actionType}
                onChange={(e) => setActionType(e.target.value as ActionType)}
                style={{ fontSize: '0.8125rem' }}
              >
                <option value="account_freeze">Account Freeze Request</option>
                <option value="dispatch_alert">Terminal Dispatch Alert</option>
                <option value="bank_subpoena">Bank Subpoena</option>
                <option value="surveillance_requested">Surveillance / CCTV Request</option>
                <option value="note_added">Investigator Case Note</option>
                <option value="case_reclassified">Case Reclassified</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Target Entity Type
              </label>
              <select
                className="input"
                value={targetType}
                onChange={(e) => setTargetType(e.target.value)}
                style={{ fontSize: '0.8125rem' }}
              >
                <option value="account">Bank Account</option>
                <option value="location">ATM / Branch Terminal</option>
                <option value="case">Case Dossier</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
                Target Identifier (Account No / Terminal ID)
              </label>
              <input
                type="text"
                className="input"
                placeholder="e.g. ACC-491029 or LOC-042"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                style={{ fontSize: '0.8125rem' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '0.25rem' }}>
              Investigator Justification &amp; Notes *
            </label>
            <textarea
              className="input"
              rows={2}
              placeholder="Provide operational basis for this action (recorded in audit log)..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ fontSize: '0.8125rem', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-sm btn-primary"
              disabled={submitting}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <Send size={14} /> {submitting ? 'Recording Action...' : 'Record Action in Log'}
            </button>
          </div>
        </form>
      )}

      {/* Action Audit Timeline */}
      {loading ? (
        <div className="skeleton" style={{ height: '120px', width: '100%', borderRadius: '6px' }} />
      ) : actions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '1.5rem', color: '#64748b', fontSize: '0.8125rem' }}>
          No formal investigator actions logged for this case yet.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {actions.map((action) => (
            <div
              key={action.action_id}
              style={{
                padding: '0.75rem 1rem',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                backgroundColor: '#fafafa',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
              }}
            >
              <div
                style={{
                  padding: '0.35rem',
                  backgroundColor: '#ffffff',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0',
                  marginTop: '2px',
                }}
              >
                {getActionIcon(action.action_type)}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.35rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0f172a' }}>
                      {action.action_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <Badge variant="neutral">
                      Status: {action.action_status}
                    </Badge>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: '#64748b' }}>
                    <Clock size={12} />
                    <span>{new Date(action.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {action.notes && (
                  <p style={{ fontSize: '0.8125rem', color: '#334155', marginTop: '0.35rem', lineHeight: 1.4 }}>
                    {action.notes}
                  </p>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem', fontSize: '0.6875rem', color: '#64748b' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                    <User size={11} /> {action.performed_by || 'Investigator Unit'}
                  </span>
                  <span>•</span>
                  <span style={{ fontFamily: 'monospace' }}>Audit ID: {action.action_id}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
