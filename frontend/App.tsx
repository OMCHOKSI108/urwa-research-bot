import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast';
import Dashboard from './pages/Dashboard';
import AgentConsole from './pages/AgentConsole';
import Research from './pages/Research';
import Scraper from './pages/Scraper';
import SystemHealth from './pages/SystemHealth';
import Settings from './pages/Settings';
import { AppRoute } from './types';
import './index.css';

const App: React.FC = () => {
  return (
    <ToastProvider>
      <Router>
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar Navigation */}
          <Sidebar />

          {/* Main Content Area */}
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
            <ErrorBoundary>
              <Routes>
                <Route path={AppRoute.DASHBOARD} element={<Dashboard />} />
                <Route path={AppRoute.AGENT} element={<AgentConsole />} />
                <Route path={AppRoute.RESEARCH} element={<Research />} />
                <Route path={AppRoute.SCRAPER} element={<Scraper />} />
                <Route path={AppRoute.MONITOR} element={<SystemHealth />} />
                <Route path={AppRoute.SETTINGS} element={<Settings />} />
                <Route path="*" element={<Navigate to={AppRoute.DASHBOARD} replace />} />
              </Routes>
            </ErrorBoundary>
          </main>
        </div>
      </Router>
    </ToastProvider>
  );
};

export default App;