import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Server,
  Globe,
  DollarSign,
  Zap,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Bot,
  Search,
  ArrowRight,
  Clock,
  ExternalLink
} from 'lucide-react';
import {
  getSystemMetrics,
  getCircuitStatus,
  getScraperStats,
  checkBackendHealth,
  exportToCSV
} from '../services/api';
import { SystemMetrics, CircuitStatus, AppRoute } from '../types';
import { useToast } from '../components/Toast';

/* ═══════════════════════════════════════════════════════════════════════════
   STAT CARD COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  trend?: { value: string; up: boolean };
  color: 'primary' | 'success' | 'warning' | 'error';
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = ({
  title, value, subtitle, icon: Icon, trend, color, onClick
}) => {
  const colorStyles = {
    primary: { bg: 'var(--primary-bg)', color: 'var(--primary)' },
    success: { bg: 'var(--success-bg)', color: 'var(--success)' },
    warning: { bg: 'var(--warning-bg)', color: 'var(--warning)' },
    error: { bg: 'var(--error-bg)', color: 'var(--error)' },
  };

  const styles = colorStyles[color];

  return (
    <div
      className={`saas-card p-5 ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-4">
        <div
          className="p-2.5 rounded-lg"
          style={{ background: styles.bg }}
        >
          <Icon className="w-5 h-5" style={{ color: styles.color }} />
        </div>

        {trend && (
          <div
            className="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full"
            style={{
              background: trend.up ? 'var(--success-bg)' : 'var(--error-bg)',
              color: trend.up ? 'var(--success)' : 'var(--error)',
            }}
          >
            {trend.up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {trend.value}
          </div>
        )}
      </div>

      <div
        className="text-2xl font-bold font-display mb-1"
        style={{ color: 'var(--text-primary)' }}
      >
        {value}
      </div>

      <div
        className="text-sm font-medium"
        style={{ color: 'var(--text-secondary)' }}
      >
        {title}
      </div>

      {subtitle && (
        <div
          className="text-xs mt-2 flex items-center gap-1"
          style={{ color: 'var(--text-muted)' }}
        >
          <Clock className="w-3 h-3" />
          {subtitle}
        </div>
      )}
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════════════════════
   PROGRESS BAR COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
const ProgressBar: React.FC<{
  label: string;
  value: number;
  color: string;
  showValue?: boolean;
}> = ({ label, value, color, showValue = true }) => (
  <div className="space-y-2">
    <div className="flex justify-between text-sm">
      <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
      {showValue && (
        <span className="font-mono font-semibold" style={{ color: 'var(--text-primary)' }}>
          {value.toFixed(1)}%
        </span>
      )}
    </div>
    <div
      className="h-2 rounded-full overflow-hidden"
      style={{ background: 'var(--bg-muted)' }}
    >
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{
          width: `${Math.min(value, 100)}%`,
          background: color,
        }}
      />
    </div>
  </div>
);

/* ═══════════════════════════════════════════════════════════════════════════
   CIRCUIT STATUS COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
const CircuitCard: React.FC<{ circuit: CircuitStatus }> = ({ circuit }) => {
  const statusConfig = {
    CLOSED: { label: 'Operational', color: 'var(--success)', bg: 'var(--success-bg)' },
    OPEN: { label: 'Offline', color: 'var(--error)', bg: 'var(--error-bg)' },
    'HALF-OPEN': { label: 'Degraded', color: 'var(--warning)', bg: 'var(--warning-bg)' },
  };

  const config = statusConfig[circuit.status] || statusConfig.CLOSED;

  return (
    <div
      className="flex items-center justify-between p-3 rounded-lg transition-all hover:shadow-sm"
      style={{ background: 'var(--bg-muted)' }}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-2 h-2 rounded-full"
          style={{ background: config.color }}
        />
        <span
          className="text-sm font-medium"
          style={{ color: 'var(--text-secondary)' }}
        >
          {circuit.service}
        </span>
      </div>

      <span
        className="text-xs font-semibold px-2 py-1 rounded-full flex items-center gap-1"
        style={{ background: config.bg, color: config.color }}
      >
        {circuit.status === 'CLOSED' ? (
          <CheckCircle2 className="w-3 h-3" />
        ) : (
          <AlertTriangle className="w-3 h-3" />
        )}
        {config.label}
      </span>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════════════════════
   QUICK ACTION CARD COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
interface QuickActionProps {
  title: string;
  description: string;
  icon: React.ElementType;
  onClick: () => void;
  color: string;
}

const QuickAction: React.FC<QuickActionProps> = ({
  title, description, icon: Icon, onClick, color
}) => (
  <button
    onClick={onClick}
    className="saas-card p-5 text-left w-full group"
  >
    <div className="flex items-start gap-4">
      <div
        className="p-3 rounded-xl transition-transform group-hover:scale-110"
        style={{ background: color + '15' }}
      >
        <Icon className="w-6 h-6" style={{ color }} />
      </div>
      <div className="flex-1">
        <h3
          className="font-semibold mb-1 flex items-center gap-2"
          style={{ color: 'var(--text-primary)' }}
        >
          {title}
          <ArrowRight
            className="w-4 h-4 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0"
            style={{ color }}
          />
        </h3>
        <p
          className="text-sm"
          style={{ color: 'var(--text-muted)' }}
        >
          {description}
        </p>
      </div>
    </div>
  </button>
);

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN DASHBOARD COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();

  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [circuits, setCircuits] = useState<CircuitStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isBackendOnline, setIsBackendOnline] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = async () => {
    setIsLoading(true);

    // Check backend health first
    const isOnline = await checkBackendHealth();
    setIsBackendOnline(isOnline);

    if (!isOnline) {
      setIsLoading(false);
      return;
    }

    try {
      const [metricsRes, circuitsRes] = await Promise.all([
        getSystemMetrics(),
        getCircuitStatus()
      ]);

      if (metricsRes.success && metricsRes.data) {
        setMetrics(metricsRes.data);
      }

      if (circuitsRes.success && circuitsRes.data) {
        setCircuits(circuitsRes.data);
      }

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      toast.error('Failed to fetch data', 'Please check your connection');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleExportMetrics = () => {
    if (metrics) {
      exportToCSV([metrics], 'urwa_metrics');
      toast.success('Export Complete', 'Metrics exported to CSV');
    }
  };

  // Backend Offline State
  if (!isBackendOnline) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div
            className="w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center"
            style={{ background: 'var(--error-bg)' }}
          >
            <AlertTriangle className="w-8 h-8" style={{ color: 'var(--error)' }} />
          </div>

          <h2
            className="text-xl font-bold mb-2"
            style={{ color: 'var(--text-primary)' }}
          >
            Backend Unavailable
          </h2>
          <p
            className="text-sm mb-6"
            style={{ color: 'var(--text-muted)' }}
          >
            Cannot connect to URWA Brain backend at localhost:8000.
            Please ensure the server is running.
          </p>

          <div className="space-y-3">
            <button onClick={fetchData} className="btn btn-primary w-full">
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Retry Connection
            </button>

            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary w-full"
            >
              <ExternalLink className="w-4 h-4" />
              Open API Docs
            </a>
          </div>
        </div>
      </div>
    );
  }

  // Loading State
  if (isLoading && !metrics) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <div
            className="w-12 h-12 mx-auto rounded-xl flex items-center justify-center"
            style={{ background: 'var(--primary-bg)' }}
          >
            <RefreshCw className="w-6 h-6 animate-spin" style={{ color: 'var(--primary)' }} />
          </div>
          <p style={{ color: 'var(--text-muted)' }}>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="h-full overflow-y-auto"
      style={{ background: 'var(--bg-base)' }}
    >
      <div className="p-8 max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex justify-between items-start">
          <div>
            <h1
              className="text-2xl font-bold font-display mb-1"
              style={{ color: 'var(--text-primary)' }}
            >
              Dashboard
            </h1>
            <p style={{ color: 'var(--text-muted)' }}>
              Monitor your web intelligence operations
            </p>
          </div>

          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span
                className="text-xs"
                style={{ color: 'var(--text-muted)' }}
              >
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={fetchData}
              disabled={isLoading}
              className="btn btn-secondary btn-sm"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={handleExportMetrics}
              className="btn btn-primary btn-sm"
            >
              Export
            </button>
          </div>
        </header>

        {/* Stats Grid */}
        {metrics && (
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <StatCard
              title="Total Requests"
              value={metrics.total_requests?.toLocaleString() ?? '0'}
              icon={Activity}
              trend={{ value: '+12.5%', up: true }}
              color="primary"
            />
            <StatCard
              title="Success Rate"
              value={`${metrics.scraping_success_rate ?? 0}%`}
              icon={Zap}
              color="success"
              subtitle="Last 24 hours"
            />
            <StatCard
              title="Active Tasks"
              value={metrics.active_tasks ?? 0}
              icon={Globe}
              color="warning"
              subtitle="Processing now"
            />
            <StatCard
              title="Est. Cost"
              value={`$${metrics.cost_estimate?.toFixed(2) ?? '0.00'}`}
              icon={DollarSign}
              trend={{ value: '+4%', up: false }}
              color="error"
              subtitle="This cycle"
            />
          </section>
        )}

        {/* Quick Actions */}
        <section>
          <h2
            className="text-lg font-semibold mb-4"
            style={{ color: 'var(--text-primary)' }}
          >
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <QuickAction
              title="Start Research"
              description="Deep web analysis with AI synthesis"
              icon={Search}
              color="var(--primary)"
              onClick={() => navigate(AppRoute.RESEARCH)}
            />
            <QuickAction
              title="Talk to Agent"
              description="Unified AI for any task"
              icon={Bot}
              color="var(--accent)"
              onClick={() => navigate(AppRoute.AGENT)}
            />
            <QuickAction
              title="Scrape Website"
              description="Extract data with stealth strategies"
              icon={Globe}
              color="var(--warning)"
              onClick={() => navigate(AppRoute.SCRAPER)}
            />
          </div>
        </section>

        {/* Two Column Layout */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Infrastructure Health */}
          <div className="lg:col-span-2 saas-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div
                className="p-2 rounded-lg"
                style={{ background: 'var(--primary-bg)' }}
              >
                <Server className="w-5 h-5" style={{ color: 'var(--primary)' }} />
              </div>
              <div>
                <h3
                  className="font-semibold"
                  style={{ color: 'var(--text-primary)' }}
                >
                  System Resources
                </h3>
                <p
                  className="text-xs"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Infrastructure utilization
                </p>
              </div>
            </div>

            {metrics && (
              <div className="space-y-5">
                <ProgressBar
                  label="CPU Usage"
                  value={metrics.cpu_usage}
                  color="var(--primary)"
                />
                <ProgressBar
                  label="Memory"
                  value={metrics.memory_usage}
                  color="var(--accent)"
                />
                <ProgressBar
                  label="Token Budget"
                  value={(metrics.tokens_used / 1000000) * 100}
                  color="var(--success)"
                />
              </div>
            )}
          </div>

          {/* Circuit Breakers */}
          <div className="saas-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div
                className="p-2 rounded-lg"
                style={{ background: 'var(--warning-bg)' }}
              >
                <Activity className="w-5 h-5" style={{ color: 'var(--warning)' }} />
              </div>
              <div>
                <h3
                  className="font-semibold"
                  style={{ color: 'var(--text-primary)' }}
                >
                  Service Status
                </h3>
                <p
                  className="text-xs"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Circuit breakers
                </p>
              </div>
            </div>

            <div className="space-y-2">
              {circuits.length === 0 ? (
                <p
                  className="text-sm text-center py-4"
                  style={{ color: 'var(--text-muted)' }}
                >
                  No services monitored
                </p>
              ) : (
                circuits.map((circuit) => (
                  <CircuitCard key={circuit.service} circuit={circuit} />
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;