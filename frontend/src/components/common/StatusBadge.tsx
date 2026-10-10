import React from 'react';

interface StatusBadgeProps {
  status: string;
  variant?: 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose' | 'gray';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, variant = 'cyan' }) => {
  const variantStyles = {
    cyan: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
    violet: 'bg-violet-500/10 text-violet-300 border-violet-500/30',
    emerald: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    amber: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    rose: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
    gray: 'bg-navy-800 text-gray-400 border-navy-700',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border font-mono tracking-wide ${
        variantStyles[variant]
      }`}
    >
      {status}
    </span>
  );
};
