import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import AgentConsole from './pages/AgentConsole';
import SystemHealth from './pages/SystemHealth';
import { AppRoute } from './types';

const App: React.FC = () => {
  return (
    <Router>
      <div className="flex h-screen bg-background text-slate-200">
        {/* Fixed Sidebar */}
        <Sidebar />
        
        {/* Main Content Area */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          <ErrorBoundary>
            <Routes>
              <Route path={AppRoute.DASHBOARD} element={<Dashboard />} />
              <Route path={AppRoute.AGENT} element={<AgentConsole />} />
              <Route path={AppRoute.MONITOR} element={<SystemHealth />} />
              <Route path={AppRoute.RESEARCH} element={<AgentConsole />} /> {/* Reusing Agent for Research for demo */}
              <Route path="*" element={<Navigate to={AppRoute.DASHBOARD} replace />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </Router>
  );
};

export default App;