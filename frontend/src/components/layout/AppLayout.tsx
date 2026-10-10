import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard Overview',
  '/scan': 'Quantum Security Scanner',
  '/scanner': 'Quantum Security Scanner',
  '/findings': 'Cryptographic Findings',
  '/migration': 'Post-Quantum Migration Guide',
  '/hybrid-lab': 'Hybrid Cryptography Lab',
  '/rollout-center': 'Staged Rollout Management',
  '/retirement-center': 'Classical Cryptography Decommissioning',
  '/assets': 'Asset Inventory',
  '/jobs': 'Job Processing Center',
  '/risk': 'Explainable Risk Assessment',
  '/reports': 'Audit Reports & Export',
  '/settings': 'Platform Settings',
};

export const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const currentTitle = pageTitles[location.pathname] || 'QuantumShield';

  return (
    <div className="min-h-screen bg-navy-950 text-gray-200 flex selection:bg-cyan-500/30 selection:text-cyan-200 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(14,165,233,0.07),rgba(255,255,255,0))]">
      {/* Sidebar Navigation */}
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          collapsed ? 'ml-20' : 'ml-64'
        }`}
      >
        <Header pageTitle={currentTitle} />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
