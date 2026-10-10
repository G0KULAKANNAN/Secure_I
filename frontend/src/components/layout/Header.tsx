import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../../api/client';
import { HealthStatus } from '../../types';
import { ShieldCheck, ShieldAlert, Wifi, WifiOff, Terminal } from 'lucide-react';

interface HeaderProps {
  pageTitle: string;
}

export const Header: React.FC<HeaderProps> = ({ pageTitle }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let mounted = true;
    const checkStatus = async () => {
      try {
        const data = await fetchHealth();
        if (mounted) {
          setHealth(data);
          setError(false);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError(true);
          setLoading(false);
        }
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 15000); // Check every 15s
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-navy-750 bg-navy-900/80 backdrop-blur-md sticky top-0 z-20 px-6 flex items-center justify-between">
      {/* Page Title & Breadcrumb */}
      <div className="flex items-center space-x-3">
        <h1 className="text-lg font-semibold text-white tracking-wide">{pageTitle}</h1>
        <span className="text-xs px-2 py-0.5 rounded bg-navy-800 text-gray-400 font-mono">
          Stage 1 / v0.1.0
        </span>
      </div>

      {/* Backend & Environment Status Indicator */}
      <div className="flex items-center space-x-4">
        {/* Backend Connectivity Status */}
        <div className="flex items-center space-x-2 text-xs bg-navy-950/80 px-3 py-1.5 rounded-full border border-navy-750">
          {loading ? (
            <>
              <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-gray-400">Connecting API...</span>
            </>
          ) : error ? (
            <>
              <WifiOff className="w-3.5 h-3.5 text-rose-500" />
              <span className="text-rose-400 font-medium">API Offline</span>
            </>
          ) : (
            <>
              <Wifi className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">API Online</span>
              <span className="text-gray-500 font-mono">({health?.environment})</span>
            </>
          )}
        </div>

        {/* Security Mode Badge */}
        <div className="flex items-center space-x-1.5 text-xs bg-cyan-950/40 text-cyan-300 border border-cyan-800/40 px-2.5 py-1.5 rounded-lg font-mono">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>HNDL Protection Mode</span>
        </div>
      </div>
    </header>
  );
};
