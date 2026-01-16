import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Bot, 
  Search, 
  Activity, 
  Settings, 
  Database,
  Globe,
  Terminal
} from 'lucide-react';
import { AppRoute } from '../types';

const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: AppRoute.DASHBOARD },
    { name: 'Unified Agent', icon: Bot, path: AppRoute.AGENT },
    { name: 'Deep Research', icon: Search, path: AppRoute.RESEARCH },
    { name: 'System Monitor', icon: Activity, path: AppRoute.MONITOR },
  ];

  const tools = [
    { name: 'Knowledge Base', icon: Database, path: '#' },
    { name: 'Active Scrapers', icon: Globe, path: '#' },
    { name: 'Logs', icon: Terminal, path: '#' },
  ];

  return (
    <div className="w-64 h-screen bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Bot className="text-white w-5 h-5" />
        </div>
        <div>
            <h1 className="text-lg font-bold text-white tracking-tight">URWA Brain</h1>
            <span className="text-xs text-blue-400 font-mono">v3.0.0 PRO</span>
        </div>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-8 overflow-y-auto">
        <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 px-2">Platform</div>
            <ul className="space-y-1">
            {navItems.map((item) => (
                <li key={item.path}>
                <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                        ? 'bg-blue-600/10 text-blue-400'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                    }
                >
                    <item.icon className="w-4 h-4" />
                    {item.name}
                </NavLink>
                </li>
            ))}
            </ul>
        </div>

        <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 px-2">Tools</div>
            <ul className="space-y-1">
            {tools.map((item) => (
                <li key={item.name}>
                <button
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-all duration-200"
                >
                    <item.icon className="w-4 h-4" />
                    {item.name}
                </button>
                </li>
            ))}
            </ul>
        </div>
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button className="flex items-center gap-3 w-full px-3 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors">
            <Settings className="w-4 h-4" />
            Settings
        </button>
      </div>
    </div>
  );
};

export default Sidebar;