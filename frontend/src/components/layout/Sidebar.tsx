import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  Server,
  Radar,
  FileSearch,
  AlertTriangle,
  GitPullRequest,
  FileBarChart,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'Asset Inventory', path: '/assets', icon: Server },
  { name: 'Scanner', path: '/scanner', icon: Radar },
  { name: 'Findings', path: '/findings', icon: FileSearch },
  { name: 'Risk Assessment', path: '/risk', icon: AlertTriangle },
  { name: 'PQC Migration', path: '/migration', icon: GitPullRequest },
  { name: 'Reports', path: '/reports', icon: FileBarChart },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen transition-all duration-300 ease-in-out border-r border-navy-750 bg-navy-950 flex flex-col ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 border-b border-navy-750/80 justify-between">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold tracking-wider text-white text-base font-mono">
                QUANTUM<span className="text-cyan-400">SHIELD</span>
              </span>
              <span className="text-[10px] text-gray-400 tracking-wider uppercase font-semibold">
                Exposure Intel
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-navy-800 transition"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-navy-850'
                }`
              }
              title={collapsed ? item.name : undefined}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${collapsed ? 'mx-auto' : 'mr-3'}`} />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer / System Status */}
      <div className="p-4 border-t border-navy-750/80">
        {!collapsed ? (
          <div className="rounded-lg bg-navy-900/60 p-2.5 border border-navy-800">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-400">PQC Status</span>
              <span className="text-cyan-400 font-mono font-semibold">NIST Draft</span>
            </div>
            <div className="w-full bg-navy-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-500 to-violet-500 h-full w-2/3" />
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
          </div>
        )}
      </div>
    </aside>
  );
};
