import React, { useEffect, useState } from 'react';
import {
  GitPullRequest,
  Shield,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Info,
  BookOpen,
  KeyRound,
  FileCheck,
  Cpu,
  Layers,
} from 'lucide-react';
import { fetchMigrationSummary } from '../api/scans';
import { MigrationSummary } from '../types';

export const Migration: React.FC = () => {
  const [summary, setSummary] = useState<MigrationSummary | null>(null);
  const [checklist, setChecklist] = useState<Array<{ id: number; text: string; done: boolean }>>([
    { id: 1, text: 'Verify firewalls and load balancers do not drop TLS ClientHello packets larger than 1.5 KB', done: false },
    { id: 2, text: 'Confirm cryptographic libraries (OpenSSL 3.3+, liboqs, BouncyCastle) support FIPS 203/204', done: false },
    { id: 3, text: 'Test hybrid key exchange (e.g., X25519 + ML-KEM-768) in staging environment before production', done: false },
    { id: 4, text: 'Audit database and certificate stores to ensure public key and signature buffer sizes (> 3.5 KB) fit', done: false },
    { id: 5, text: 'Benchmark handshake latency and CPU usage of lattice multiplication on test servers', done: false },
  ]);

  useEffect(() => {
    fetchMigrationSummary()
      .then(setSummary)
      .catch((err) => console.error('Failed to load migration summary:', err));
  }, []);

  const toggleChecklist = (id: number) => {
    setChecklist((prev) =>
      prev.map((item) => (item.id === id ? { ...item, done: !item.done } : item))
    );
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="border-b border-navy-750 pb-5">
        <h1 className="text-2xl font-bold text-white tracking-tight">Post-Quantum Migration Guide</h1>
        <p className="text-sm text-gray-400 mt-1">
          A beginner-friendly roadmap for replacing quantum-vulnerable cryptography with official NIST Post-Quantum Cryptography (PQC) standards.
        </p>
      </div>

      {/* Safety Policy Banner */}
      <div className="rounded-2xl bg-amber-500/10 border border-amber-500/30 p-5 flex items-start space-x-4">
        <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs leading-relaxed">
          <h3 className="text-sm font-bold text-amber-300">
            Safety First: No Automatic Changes to Production
          </h3>
          <p className="text-amber-200/90">
            QuantumShield provides defensive security intelligence and migration blueprints. <strong>It never modifies production servers, cryptographic keys, or code automatically.</strong> Always benchmark and test hybrid cryptographic configurations in an isolated staging lab first.
          </p>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 1. Core Standards Comparison Cards */}
      {/* ========================================================================= */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white tracking-wide">
          Official NIST Post-Quantum Standards (Finalized August 2024)
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: FIPS 203 (ML-KEM) */}
          <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-4 flex flex-col justify-between shadow-xl">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                  FIPS 203 Standard
                </span>
                <span className="text-[11px] text-gray-400 font-mono">Lattice-Based</span>
              </div>
              <h3 className="text-lg font-bold text-white">ML-KEM (Kyber)</h3>
              <p className="text-xs text-gray-300 leading-relaxed">
                Module-Lattice Key Encapsulation Mechanism for general encryption and session key establishment.
              </p>

              <div className="space-y-2 pt-2 border-t border-navy-750 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Replaces:</span>
                  <span className="text-amber-300 font-semibold">RSA, ECDH, Diffie-Hellman</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Recommended Set:</span>
                  <span className="text-cyan-300 font-mono">ML-KEM-768</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Primary Purpose:</span>
                  <span className="text-white">TLS Handshakes & Encryption</span>
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 text-[11px] text-cyan-200/90 leading-normal">
              💡 <strong>Important:</strong> ML-KEM is strictly for key establishment. It cannot be used to sign certificates or code.
            </div>
          </div>

          {/* Card 2: FIPS 204 (ML-DSA) */}
          <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-4 flex flex-col justify-between shadow-xl">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  FIPS 204 Standard
                </span>
                <span className="text-[11px] text-gray-400 font-mono">Lattice-Based</span>
              </div>
              <h3 className="text-lg font-bold text-white">ML-DSA (Dilithium)</h3>
              <p className="text-xs text-gray-300 leading-relaxed">
                Module-Lattice Digital Signature Algorithm for primary identity authentication and digital signatures.
              </p>

              <div className="space-y-2 pt-2 border-t border-navy-750 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Replaces:</span>
                  <span className="text-amber-300 font-semibold">RSA Signatures, ECDSA</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Recommended Set:</span>
                  <span className="text-emerald-300 font-mono">ML-DSA-65</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Primary Purpose:</span>
                  <span className="text-white">X.509 Certificates & Signing</span>
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 text-[11px] text-emerald-200/90 leading-normal">
              💡 <strong>Payload Note:</strong> ML-DSA signatures (~3.3 KB) are larger than RSA. Check network MTU and storage buffers.
            </div>
          </div>

          {/* Card 3: FIPS 205 (SLH-DSA) */}
          <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 space-y-4 flex flex-col justify-between shadow-xl">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-violet-500/15 text-violet-300 border border-violet-500/30">
                  FIPS 205 Standard
                </span>
                <span className="text-[11px] text-gray-400 font-mono">Hash-Based</span>
              </div>
              <h3 className="text-lg font-bold text-white">SLH-DSA (SPHINCS+)</h3>
              <p className="text-xs text-gray-300 leading-relaxed">
                Stateless Hash-Based Digital Signature Algorithm serving as a robust mathematical backup to lattices.
              </p>

              <div className="space-y-2 pt-2 border-t border-navy-750 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Replaces:</span>
                  <span className="text-amber-300 font-semibold">Long-Term Root CAs</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Recommended Set:</span>
                  <span className="text-violet-300 font-mono">SLH-DSA-128s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Primary Purpose:</span>
                  <span className="text-white">Firmware & Root Trust</span>
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 text-[11px] text-violet-200/90 leading-normal">
              💡 <strong>Lattice Hedge:</strong> Uses only cryptographic hashes; unaffected even if future attacks break lattice mathematics.
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. Step-by-Step Migration Phases */}
      {/* ========================================================================= */}
      <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 shadow-xl space-y-5">
        <div className="flex items-center space-x-3 pb-3 border-b border-navy-750">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Migration Roadmap (5 Phases)</h2>
            <p className="text-xs text-gray-400">Recommended operational rollout path</p>
          </div>
        </div>

        <div className="space-y-3">
          {[
            {
              step: '1',
              title: 'Cryptographic Discovery & Inventory (CBOM)',
              desc: 'Scan source code repositories and live servers using QuantumShield to catalog all RSA, ECC, and DH instances.',
              tag: 'Current Stage',
              active: true,
            },
            {
              step: '2',
              title: 'Hybrid Cryptography in Staging',
              desc: 'Deploy hybrid key exchange (e.g. X25519 + ML-KEM-768) in staging environments so legacy and post-quantum clients both connect seamlessly.',
              tag: 'Next Step',
              active: false,
            },
            {
              step: '3',
              title: 'Network MTU & Middlebox Verification',
              desc: 'Validate that firewalls, load balancers, and packet inspectors do not drop enlarged PQC TLS packets (> 1.5 KB).',
              tag: 'Testing',
              active: false,
            },
            {
              step: '4',
              title: 'Staged Production Rollout',
              desc: 'Enable PQC algorithms on internal APIs and web edge servers with active telemetry and automated fallback.',
              tag: 'Rollout',
              active: false,
            },
            {
              step: '5',
              title: 'Classical Decommissioning',
              desc: 'Disable legacy RSA and standalone ECC cipher suites once global client ecosystem support reaches threshold.',
              tag: 'Final Phase',
              active: false,
            },
          ].map((phase, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border flex items-start space-x-4 transition ${
                phase.active
                  ? 'bg-navy-950 border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                  : 'bg-navy-900/60 border-navy-800'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold font-mono flex-shrink-0 mt-0.5 ${
                  phase.active ? 'bg-cyan-500 text-navy-950' : 'bg-navy-800 text-gray-400'
                }`}
              >
                {phase.step}
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-white">{phase.title}</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-navy-950 text-cyan-300 border border-navy-800">
                    {phase.tag}
                  </span>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">{phase.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. Operational Readiness Testing Checklist */}
      {/* ========================================================================= */}
      <div className="rounded-2xl bg-navy-850 border border-navy-750 p-6 shadow-xl space-y-4">
        <div className="flex items-center space-x-3 pb-3 border-b border-navy-750">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Pre-Deployment Verification Checklist</h2>
            <p className="text-xs text-gray-400">Interactive operational validation items before migrating</p>
          </div>
        </div>

        <div className="space-y-2.5">
          {checklist.map((item) => (
            <div
              key={item.id}
              onClick={() => toggleChecklist(item.id)}
              className={`p-3.5 rounded-xl border cursor-pointer transition flex items-center space-x-3 select-none ${
                item.done
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-navy-950 border-navy-800 text-gray-300 hover:border-navy-700'
              }`}
            >
              <input
                type="checkbox"
                checked={item.done}
                onChange={() => {}}
                className="h-4 w-4 rounded border-navy-700 bg-navy-900 text-emerald-500 focus:ring-emerald-500"
              />
              <span className={`text-xs ${item.done ? 'line-through text-emerald-400/80 font-medium' : ''}`}>
                {item.text}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
