import React from 'react';
import { Settings as SettingsIcon, Shield, Database, Lock } from 'lucide-react';

export const Settings: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <div className="pb-4 border-b border-navy-750">
        <h2 className="text-xl font-bold text-white tracking-tight">Platform Settings & Security Policies</h2>
        <p className="text-xs text-gray-400 mt-1">
          Configure scanning boundaries, safe timeout limits, and local database settings.
        </p>
      </div>

      <div className="space-y-4">
        {/* Policy Card 1 */}
        <div className="p-5 rounded-xl bg-navy-850 border border-navy-750 flex items-start space-x-4">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Lock className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-white">TLS Authorisation & SSRF Guard</h4>
            <p className="text-xs text-gray-400 leading-relaxed">
              Enforces explicit hostname allowlists. Local loopback, private ranges, and non-public IPs are rejected by default.
            </p>
          </div>
        </div>

        {/* Policy Card 2 */}
        <div className="p-5 rounded-xl bg-navy-850 border border-navy-750 flex items-start space-x-4">
          <div className="p-2.5 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20">
            <Shield className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-white">Zero Credential Exposure Policy</h4>
            <p className="text-xs text-gray-400 leading-relaxed">
              Automated log and evidence sanitization redacts PEM private keys, bearer tokens, and passwords prior to persistence.
            </p>
          </div>
        </div>

        {/* Policy Card 3 */}
        <div className="p-5 rounded-xl bg-navy-850 border border-navy-750 flex items-start space-x-4">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Database className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-white">Local SQLite Isolation</h4>
            <p className="text-xs text-gray-400 leading-relaxed">
              All asset inventory data, scans, and evidence are stored locally in parameterised SQLite without external cloud dependencies.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
