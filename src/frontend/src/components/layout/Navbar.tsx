import React from 'react';
import {
  ShieldAlert,
  LayoutDashboard,
  FolderOpen,
  Network,
  MapPin,
  Activity,
  CheckCircle2,
  AlertCircle,
  Menu,
  X
} from 'lucide-react';
import { HealthResponse } from '../../types/api';

export type NavTab = 'dashboard' | 'cases' | 'accounts' | 'locations';

interface NavbarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  health: HealthResponse | null;
  healthLoading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  health,
  healthLoading,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navLinks: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'cases', label: 'Cases & Money Trails', icon: <FolderOpen size={18} /> },
    { id: 'accounts', label: 'Network Intelligence', icon: <Network size={18} /> },
    { id: 'locations', label: 'GIS & Terminals', icon: <MapPin size={18} /> },
  ];

  return (
    <header
      style={{
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Simulation Mode Disclaimer Bar */}
      <div
        style={{
          backgroundColor: '#fffbeb',
          borderBottom: '1px solid #fde68a',
          padding: '0.25rem 1rem',
          fontSize: '0.75rem',
          color: '#92400e',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 auto', textAlign: 'center' }}>
          <span style={{ fontWeight: 700, letterSpacing: '0.05em' }}>[PROTOTYPE / SIMULATION ENVIRONMENT]</span>
          <span>All cases, transaction histories, Aadhaar-like IDs, and coordinates are synthetic test data.</span>
        </div>
      </div>

      {/* Main Header Bar */}
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '0.625rem 1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand Logo & Title */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}
          onClick={() => onSelectTab('dashboard')}
        >
          <div
            style={{
              backgroundColor: '#0d9488',
              color: '#ffffff',
              padding: '0.5rem',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldAlert size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.125rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#0f172a' }}>
                CASHNET
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#64748b', lineHeight: 1 }}>
              Cybercrime Cash-Out Intervention Engine
            </p>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav
          style={{
            display: 'none',
            gap: '0.25rem',
          }}
          className="desktop-nav"
        >
          {navLinks.map((link) => {
            const isActive = currentTab === link.id;
            return (
              <button
                key={link.id}
                onClick={() => onSelectTab(link.id)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 0.875rem',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: isActive ? '#f0fdfa' : 'transparent',
                  color: isActive ? '#0d9488' : '#475569',
                  transition: 'all 0.15s ease',
                }}
              >
                {link.icon}
                <span>{link.label}</span>
              </button>
            );
          })}
        </nav>

        {/* System & Connection Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.35rem 0.625rem',
              borderRadius: '6px',
              backgroundColor: health?.database_connected ? '#ecfdf5' : '#fff1f2',
              border: `1px solid ${health?.database_connected ? '#a7f3d0' : '#fecdd3'}`,
              fontSize: '0.75rem',
              fontWeight: 500,
              color: health?.database_connected ? '#047857' : '#be123c',
            }}
            title={health?.database_connected ? 'Backend API and Database connected' : 'Backend connection unavailable'}
          >
            {healthLoading ? (
              <Activity size={13} className="animate-spin" />
            ) : health?.database_connected ? (
              <CheckCircle2 size={13} />
            ) : (
              <AlertCircle size={13} />
            )}
            <span>
              {healthLoading
                ? 'Connecting...'
                : health?.database_connected
                ? 'API v1 Online'
                : 'API Offline'}
            </span>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              display: 'inline-flex',
              padding: '0.375rem',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              backgroundColor: '#ffffff',
              color: '#475569',
              cursor: 'pointer',
            }}
            className="mobile-toggle"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Nav */}
      {mobileMenuOpen && (
        <div
          style={{
            borderTop: '1px solid #e2e8f0',
            backgroundColor: '#ffffff',
            padding: '0.75rem 1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.375rem',
          }}
        >
          {navLinks.map((link) => {
            const isActive = currentTab === link.id;
            return (
              <button
                key={link.id}
                onClick={() => {
                  onSelectTab(link.id);
                  setMobileMenuOpen(false);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.625rem',
                  padding: '0.625rem 0.875rem',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: isActive ? '#f0fdfa' : 'transparent',
                  color: isActive ? '#0d9488' : '#475569',
                  textAlign: 'left',
                }}
              >
                {link.icon}
                <span>{link.label}</span>
              </button>
            );
          })}
        </div>
      )}

      <style>{`
        @media (min-width: 768px) {
          .desktop-nav {
            display: flex !important;
          }
          .mobile-toggle {
            display: none !important;
          }
        }
      `}</style>
    </header>
  );
};
