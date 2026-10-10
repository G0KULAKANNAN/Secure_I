import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Overview } from './pages/Overview';
import { Assets } from './pages/Assets';
import { Scanner } from './pages/Scanner';
import { Findings } from './pages/Findings';
import { RiskAssessment } from './pages/RiskAssessment';
import { Migration } from './pages/Migration';
import { HybridLab } from './pages/HybridLab';
import { NetworkLab } from './pages/NetworkLab';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { JobCenter } from './pages/JobCenter';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Overview />} />
          <Route path="assets" element={<Assets />} />
          <Route path="jobs" element={<JobCenter />} />
          <Route path="scan" element={<Scanner />} />
          <Route path="scanner" element={<Scanner />} />
          <Route path="findings" element={<Findings />} />
          <Route path="risk" element={<RiskAssessment />} />
          <Route path="migration" element={<Migration />} />
          <Route path="hybrid-lab" element={<HybridLab />} />
          <Route path="network-lab" element={<NetworkLab />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
