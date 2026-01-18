import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  Search,
  Activity,
  Settings,
  Globe,
  ChevronLeft,
  Zap,
  HelpCircle,
  ExternalLink
} from 'lucide-react';
import { AppRoute } from '../types';

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  const navItems = [
    {
      name: 'Dashboard',
      icon: LayoutDashboard,
      path: AppRoute.DASHBOARD,
      description: 'Overview & metrics'
    },
    {
      name: 'AI Agent',
      icon: Bot,
      path: AppRoute.AGENT,
      description: 'Unified intelligence',
      badge: 'AI'
    },
    {
      name: 'Research',
      icon: Search,
      path: AppRoute.RESEARCH,
      description: 'Deep web analysis'
    },
    {
      name: 'Scraper',
      icon: Globe,
      path: AppRoute.SCRAPER,
      description: 'Site extraction'
    },
    {
      name: 'Monitor',
      icon: Activity,
      path: AppRoute.MONITOR,
      description: 'System health'
    },
  ];

  return (
    <aside
      className={`h-screen flex flex-col flex-shrink-0 relative transition-all duration-300 ease-out ${isCollapsed ? 'w-20' : 'w-64'
        }`}
      style={{
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-light)',
      }}
    >
      {/* Header / Logo */}
      <div className={`p-5 flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
        <div
          className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
          style={{
            background: 'linear-gradient(135deg, var(--primary), var(--accent))',
            boxShadow: '0 4px 12px rgba(124, 58, 237, 0.25)',
          }}
        >
          <Zap className="w-5 h-5 text-white" />
        </div>

        {!isCollapsed && (
          <div>
            <h1
              className="text-lg font-bold font-display"
              style={{ color: 'var(--text-primary)' }}
            >
              URWA Brain
            </h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  background: 'var(--success)',
                  boxShadow: '0 0 6px var(--success)',
                }}
              />
              <span
                className="text-xs font-medium"
                style={{ color: 'var(--text-muted)' }}
              >
                v3.5.0
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-16 w-6 h-6 rounded-full flex items-center justify-center transition-all hover:scale-110"
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)',
          color: 'var(--text-muted)',
        }}
      >
        <ChevronLeft
          className={`w-4 h-4 transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${isCollapsed ? 'justify-center' : ''
                    }`}
                  style={{
                    background: isActive ? 'var(--primary-bg)' : 'transparent',
                    color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = 'var(--bg-muted)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <item.icon
                    className="w-5 h-5 flex-shrink-0 transition-colors"
                    style={{
                      color: isActive ? 'var(--primary)' : 'var(--text-muted)',
                    }}
                  />

                  {!isCollapsed && (
                    <>
                      <div className="flex-1">
                        <div
                          className="text-sm font-medium"
                          style={{
                            color: isActive ? 'var(--primary)' : 'var(--text-primary)',
                          }}
                        >
                          {item.name}
                        </div>
                        <div
                          className="text-xs"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          {item.description}
                        </div>
                      </div>

                      {item.badge && (
                        <span
                          className="text-xs font-semibold px-2 py-0.5 rounded-full"
                          style={{
                            background: 'var(--primary-bg)',
                            color: 'var(--primary)',
                          }}
                        >
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div
        className="p-3 space-y-2"
        style={{ borderTop: '1px solid var(--border-light)' }}
      >
        <NavLink
          to={AppRoute.SETTINGS}
          className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg transition-all ${isCollapsed ? 'justify-center' : ''
            }`}
          style={{
            color: 'var(--text-muted)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--bg-muted)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <Settings className="w-4 h-4" />
          {!isCollapsed && <span className="text-sm">Settings</span>}
        </NavLink>

        {!isCollapsed && (
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 w-full px-3 py-2 rounded-lg transition-all"
            style={{ color: 'var(--text-muted)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg-muted)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <ExternalLink className="w-4 h-4" />
            <span className="text-sm">API Docs</span>
          </a>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;