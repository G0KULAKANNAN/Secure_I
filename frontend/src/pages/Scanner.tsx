import React from 'react';
import { Radar, FileCode, ShieldCheck, Globe } from 'lucide-react';
import { EmptyState } from '../components/common/EmptyState';

export const Scanner: React.FC = () => {
  const scanners = [
    {
      title: 'X.509 Certificate Scanner',
      desc: 'Inspect PEM and DER certificates for RSA/ECC key sizes and signature algorithms.',
      stage: 'Stage 3',
      icon: ShieldCheck,
    },
    {
      title: 'Source Code & Config Scanner',
      desc: 'Static traversal for cryptographic APIs in Python, Java, YAML, Nginx, and OpenSSL configs.',
      stage: 'Stage 4',
      icon: FileCode,
    },
    {
      title: 'Authorised TLS Scanner',
      desc: 'Controlled handshake inspection of allowed endpoints with SSRF & rebinding protection.',
      stage: 'Stage 5',
      icon: Globe,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-navy-750">
        <h2 className="text-xl font-bold text-white tracking-tight">Cryptographic Discovery Scanners</h2>
        <p className="text-xs text-gray-400 mt-1">
          Perform non-destructive, evidence-based cryptographic scanning across endpoints, certificates, and source code.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scanners.map((s, idx) => {
          const Icon = s.icon;
          return (
            <div key={idx} className="p-5 rounded-xl bg-navy-850 border border-navy-750 space-y-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-xs font-mono text-cyan-300 px-2 py-0.5 rounded bg-navy-950 border border-navy-800">
                  {s.stage}
                </span>
              </div>
              <h3 className="text-base font-semibold text-white">{s.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed">{s.desc}</p>
            </div>
          );
        })}
      </div>

      <EmptyState
        icon={Radar}
        title="Scanner Engines are in Development"
        description="Scanners will be implemented incrementally with strict safety controls, SSRF mitigations, and redaction formatters."
      />
    </div>
  );
};
