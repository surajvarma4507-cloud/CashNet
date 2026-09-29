import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  status?: number;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Failed to Load Data',
  message,
  onRetry,
  status,
}) => {
  return (
    <div
      role="alert"
      className="card"
      style={{
        borderLeft: '4px solid #be123c',
        backgroundColor: '#fff1f2',
        borderColor: '#fecdd3',
        padding: '1.25rem',
        margin: '1rem 0',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
        <AlertCircle size={20} style={{ color: '#be123c', flexShrink: 0, marginTop: '2px' }} />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#9f1239' }}>
              {title} {status ? `(HTTP ${status})` : ''}
            </h4>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#881337', marginTop: '0.25rem' }}>
            {message}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="btn btn-sm btn-secondary"
              style={{ marginTop: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}
            >
              <RefreshCw size={14} /> Retry Query
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
