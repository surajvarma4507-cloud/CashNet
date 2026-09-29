import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'warning' | 'error';
  title: string;
  description?: string;
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '1.5rem',
        right: '1.5rem',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        maxWidth: '400px',
        width: '100%',
      }}
    >
      {toasts.map((toast) => {
        let border = '#10b981';
        let bg = '#ecfdf5';
        let icon = <CheckCircle2 size={18} style={{ color: '#059669' }} />;

        if (toast.type === 'error') {
          border = '#ef4444';
          bg = '#fef2f2';
          icon = <XCircle size={18} style={{ color: '#dc2626' }} />;
        } else if (toast.type === 'warning') {
          border = '#f59e0b';
          bg = '#fffbeb';
          icon = <AlertTriangle size={18} style={{ color: '#d97706' }} />;
        }

        return (
          <div
            key={toast.id}
            className="card"
            style={{
              padding: '0.875rem 1rem',
              backgroundColor: bg,
              borderLeft: `4px solid ${border}`,
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
            }}
          >
            <div style={{ flexShrink: 0, marginTop: '2px' }}>{icon}</div>
            <div style={{ flex: 1 }}>
              <h5 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a' }}>{toast.title}</h5>
              {toast.description && (
                <p style={{ fontSize: '0.8125rem', color: '#475569', marginTop: '0.25rem' }}>
                  {toast.description}
                </p>
              )}
            </div>
            <button
              onClick={() => onDismiss(toast.id)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#94a3b8',
                padding: '2px',
              }}
              aria-label="Dismiss Notification"
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
};
