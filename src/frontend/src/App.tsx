import React, { useState, useEffect } from 'react';
import { AppShell } from './components/layout/AppShell';
import { NavTab } from './components/layout/Navbar';
import { ToastMessage } from './components/common/Toast';
import { HealthResponse } from './types/api';
import { api } from './api/client';

// Views
import { DashboardView } from './views/DashboardView';
import { CaseListView } from './views/CaseListView';
import { CaseDossierView } from './views/CaseDossierView';
import { AccountIntelligenceView } from './views/AccountIntelligenceView';
import { LocationsGISView } from './views/LocationsGISView';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [activeAccountNumber, setActiveAccountNumber] = useState<string | null>(null);
  const [activeLocationId, setActiveLocationId] = useState<string | null>(null);

  // Health Status
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);

  // Toasts
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Poll backend health status
  const checkHealth = async () => {
    try {
      setHealthLoading(true);
      const res = await api.getHealth();
      setHealth(res);
    } catch {
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  // Navigation handlers
  const handleOpenCase = (caseId: string) => {
    setActiveCaseId(caseId);
    setCurrentTab('cases');
  };

  const handleBackToCaseList = () => {
    setActiveCaseId(null);
  };

  const handleOpenAccount = (accountNumber: string) => {
    setActiveAccountNumber(accountNumber);
    setCurrentTab('accounts');
  };

  const handleSelectLocation = (locationId: string) => {
    setActiveLocationId(locationId);
    setCurrentTab('locations');
  };

  return (
    <AppShell
      currentTab={currentTab}
      onSelectTab={(tab) => {
        setCurrentTab(tab);
        if (tab !== 'cases') {
          // Keep activeCaseId unless switching to other views
        }
      }}
      health={health}
      healthLoading={healthLoading}
      toasts={toasts}
      onDismissToast={removeToast}
    >
      {currentTab === 'dashboard' && (
        <DashboardView
          onOpenCase={handleOpenCase}
          onOpenAccount={handleOpenAccount}
        />
      )}

      {currentTab === 'cases' && (
        activeCaseId ? (
          <CaseDossierView
            caseId={activeCaseId}
            onBackToList={handleBackToCaseList}
            onOpenAccount={handleOpenAccount}
            onSelectLocation={handleSelectLocation}
            onShowToast={addToast}
          />
        ) : (
          <CaseListView onOpenCase={handleOpenCase} />
        )
      )}

      {currentTab === 'accounts' && (
        <AccountIntelligenceView
          initialAccountNumber={activeAccountNumber}
          onOpenCase={handleOpenCase}
          onSelectAccount={(acc) => setActiveAccountNumber(acc)}
        />
      )}

      {currentTab === 'locations' && (
        <LocationsGISView
          initialLocationId={activeLocationId}
          onShowToast={addToast}
          onOpenCase={handleOpenCase}
        />
      )}
    </AppShell>
  );
};
