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
    <header className="h-16 border-b border-navy-750/80 bg-navy-950/85 backdrop-blur-xl sticky top-0 z-20 px-6 flex items-center justify-between">
      {/* Page Title & Breadcrumb */}
      <div className="flex items-center space-x-3">
        <h1 className="text-base md:text-lg font-bold text-white tracking-wide font-sans">{pageTitle}</h1>
        <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-[11px] font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span>FIPS 203/204</span>
        </div>
      </div>

      {/* Backend & Environment Status Indicator */}
      <div className="flex items-center space-x-3">
        {/* Backend Connectivity Status */}
        <div className="flex items-center space-x-2 text-xs bg-navy-900/90 px-3.5 py-1.5 rounded-full border border-navy-750/90 shadow-sm">
          {loading ? (
            <>
              <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-gray-400 font-mono text-[11px]">Syncing API...</span>
            </>
          ) : error ? (
            <>
              <WifiOff className="w-3.5 h-3.5 text-rose-500" />
              <span className="text-rose-400 font-medium">API Offline</span>
            </>
          ) : (
            <>
              <Wifi className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium font-sans">Online</span>
              <span className="text-gray-500 font-mono text-[11px]">({health?.environment || 'prod'})</span>
            </>
          )}
        </div>

        {/* Security Mode Badge */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs bg-gradient-to-r from-cyan-950/60 to-violet-950/60 text-cyan-300 border border-cyan-800/50 px-3 py-1.5 rounded-full font-mono shadow-sm">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>HNDL Safe Guard</span>
        </div>
      </div>
    </header>
  );
};
