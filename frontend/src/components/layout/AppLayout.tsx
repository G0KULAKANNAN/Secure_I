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
  '/network-lab': 'Network Compatibility Lab',
  '/rollout-center': 'Staged Rollout Management',
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
    <div className="min-h-screen bg-navy-900 text-gray-200 flex">
      {/* Sidebar Navigation */}
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          collapsed ? 'ml-20' : 'ml-64'
        }`}
      >
        <Header pageTitle={currentTitle} />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
