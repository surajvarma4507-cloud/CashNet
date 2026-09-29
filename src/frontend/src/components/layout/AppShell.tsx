import React from 'react';
import { Navbar, NavTab } from './Navbar';
import { ToastContainer, ToastMessage } from '../common/Toast';
import { HealthResponse } from '../../types/api';
import { ShieldCheck, Info } from 'lucide-react';

interface AppShellProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  toasts: ToastMessage[];
  onDismissToast: (id: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentTab,
  onSelectTab,
  health,
  healthLoading,
  toasts,
  onDismissToast,
  children,
}) => {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
      <Navbar
        currentTab={currentTab}
        onSelectTab={onSelectTab}
        health={health}
        healthLoading={healthLoading}
      />

      <main style={{ flex: 1, padding: '1.5rem 1rem', maxWidth: '1440px', width: '100%', margin: '0 auto' }}>
        {children}
      </main>

      {/* Footer */}
      <footer
        style={{
          backgroundColor: '#ffffff',
          borderTop: '1px solid #e2e8f0',
          padding: '1.25rem 1rem',
          fontSize: '0.75rem',
          color: '#64748b',
        }}
      >
        <div
          style={{
            maxWidth: '1440px',
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={16} style={{ color: '#0d9488' }} />
            <span>
              <strong>CASHNET</strong>
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <Info size={13} /> Strictly Non-Operational Prototype | Synthetic Financial Testbed
            </span>
            <span>FastAPI &amp; SQLAlchemy Backend | React 18 &amp; TypeScript UI</span>
          </div>
        </div>
      </footer>

      {/* Global Floating Toasts */}
      <ToastContainer toasts={toasts} onDismiss={onDismissToast} />
    </div>
  );
};
