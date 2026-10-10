import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  Radar,
  FileSearch,
  GitPullRequest,
  ChevronLeft,
  ChevronRight,
  Layers,
  Sliders,
  AlertOctagon,
  Sparkles,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavGroup {
  label: string;
  items: Array<{
    name: string;
    path: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string;
  }>;
}

const navGroups: NavGroup[] = [
  {
    label: 'Core Discovery',
    items: [
      { name: 'Dashboard', path: '/', icon: LayoutDashboard },
      { name: 'Scan', path: '/scan', icon: Radar },
      { name: 'Findings', path: '/findings', icon: FileSearch },
      { name: 'Migration Guide', path: '/migration', icon: GitPullRequest },
    ],
  },
  {
    label: 'PQC Operations',
    items: [
      { name: 'Hybrid Lab', path: '/hybrid-lab', icon: Layers },
      { name: 'Rollout Center', path: '/rollout-center', icon: Sliders },
      { name: 'Retirement Center', path: '/retirement-center', icon: AlertOctagon },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen transition-all duration-300 ease-in-out border-r border-navy-750/90 bg-navy-950/95 backdrop-blur-xl flex flex-col ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 border-b border-navy-750/80 justify-between">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="relative p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/40 text-cyan-400 shadow-lg shadow-cyan-500/10">
            <ShieldAlert className="w-5 h-5 animate-pulse" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-extrabold tracking-wider text-white text-base font-mono flex items-center space-x-1">
                <span>QUANTUM</span>
                <span className="text-cyan-400">SHIELD</span>
              </span>
              <span className="text-[10px] text-cyan-300/70 tracking-widest uppercase font-semibold font-mono">
                PQC Exposure Intel
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-navy-800 transition"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-1">
            {!collapsed && (
              <div className="px-3 pb-1 text-[10px] font-semibold text-gray-400/80 uppercase tracking-widest font-mono">
                {group.label}
              </div>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `group flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-500/15 via-cyan-500/10 to-transparent text-cyan-300 border-l-2 border-cyan-400 shadow-sm shadow-cyan-500/10 font-semibold'
                        : 'text-gray-400 hover:text-gray-100 hover:bg-navy-850/80 border-l-2 border-transparent'
                    }`
                  }
                  title={collapsed ? item.name : undefined}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110 ${collapsed ? 'mx-auto' : 'mr-3'}`} />
                  {!collapsed && (
                    <div className="flex items-center justify-between w-full">
                      <span>{item.name}</span>
                      {item.badge && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer / System Status */}
      <div className="p-3.5 border-t border-navy-750/80 bg-navy-950/40">
        {!collapsed ? (
          <div className="rounded-xl bg-gradient-to-br from-navy-900 to-navy-850 p-3 border border-navy-750 shadow-inner">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-gray-400 flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-medium text-gray-300">Defense Engine</span>
              </span>
              <span className="text-cyan-400 font-mono text-[11px] font-bold">NIST PQC</span>
            </div>
            <div className="text-[11px] text-gray-400 flex items-center justify-between font-mono">
              <span>Standards</span>
              <span className="text-violet-300">FIPS 203 / 204</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center py-1">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
          </div>
        )}
      </div>
    </aside>
  );
};
