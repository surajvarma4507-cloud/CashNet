import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description = 'No data matched your search or filter parameters.',
  action,
  icon,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3.5rem 1.5rem',
        textAlign: 'center',
        color: '#64748b',
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px dashed #cbd5e1',
        margin: '1rem 0',
      }}
    >
      <div style={{ color: '#94a3b8', marginBottom: '1rem' }}>
        {icon || <Inbox size={40} strokeWidth={1.5} />}
      </div>
      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.25rem' }}>
        {title}
      </h3>
      <p style={{ fontSize: '0.875rem', color: '#64748b', maxWidth: '400px', marginBottom: action ? '1rem' : 0 }}>
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
};
