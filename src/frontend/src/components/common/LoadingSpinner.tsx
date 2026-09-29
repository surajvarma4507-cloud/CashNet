import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: number;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading investigative intelligence...',
  size = 24,
  className = '',
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex flex-col items-center justify-center py-12 px-4 text-slate-500 ${className}`}
      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 1rem', color: '#64748b' }}
    >
      <Loader2 size={size} className="animate-spin text-teal-600 mb-3" style={{ animation: 'spin 1s linear infinite', color: '#0d9488', marginBottom: '0.75rem' }} />
      {label && <p style={{ fontSize: '0.875rem', fontWeight: 500 }}>{label}</p>}
      <span className="sr-only" style={{ position: 'absolute', width: 1, height: 1, padding: 0, margin: -1, overflow: 'hidden', clip: 'rect(0,0,0,0)', border: 0 }}>
        Loading
      </span>
    </div>
  );
};
