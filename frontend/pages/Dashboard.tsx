import React, { useEffect, useState, useCallback } from 'react';
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
  ExternalLink,
  Wifi,
  Shield,
  Database,
  Loader2
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
   LIVE ACTIVITY FEED - Shows real-time scraping activity with animations
   ═══════════════════════════════════════════════════════════════════════════ */

interface ActivityItem {
  id: string;
  url: string;
  status: 'scraping' | 'success' | 'analyzing' | 'queued';
  strategy: string;
  timestamp: Date;
}

const SAMPLE_URLS = [
  'news.ycombinator.com/front',
  'github.com/trending',
  'techcrunch.com/latest',
  'producthunt.com/posts',
  'reddit.com/r/technology',
  'medium.com/popular',
  'dev.to/top',
  'arxiv.org/list/cs.AI',
  'stackoverflow.com/questions',
  'bbc.com/news/technology',
];

const STRATEGIES = ['Lightweight', 'Stealth', 'Ultra Stealth'];

const LiveActivityFeed: React.FC<{ isActive?: boolean }> = ({ isActive = true }) => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);

  // Simulate live activity for demonstration
  useEffect(() => {
    if (!isActive) return;

    // Initial activities
    const initialActivities: ActivityItem[] = [
      { id: '1', url: SAMPLE_URLS[0], status: 'success', strategy: 'Lightweight', timestamp: new Date(Date.now() - 5000) },
      { id: '2', url: SAMPLE_URLS[1], status: 'scraping', strategy: 'Stealth', timestamp: new Date(Date.now() - 2000) },
      { id: '3', url: SAMPLE_URLS[2], status: 'analyzing', strategy: 'Ultra Stealth', timestamp: new Date(Date.now() - 1000) },
    ];
    setActivities(initialActivities);

    // Add new activities periodically
    const interval = setInterval(() => {
      setActivities(prev => {
        // Update existing scraping items to success
        const updated = prev.map(item => {
          if (item.status === 'scraping') return { ...item, status: 'success' as const };
          if (item.status === 'analyzing') return { ...item, status: 'scraping' as const };
          if (item.status === 'queued') return { ...item, status: 'analyzing' as const };
          return item;
        });

        // Add new activity
        const newActivity: ActivityItem = {
          id: Date.now().toString(),
          url: SAMPLE_URLS[Math.floor(Math.random() * SAMPLE_URLS.length)],
          status: 'queued',
          strategy: STRATEGIES[Math.floor(Math.random() * STRATEGIES.length)],
          timestamp: new Date(),
        };

        return [newActivity, ...updated].slice(0, 5);
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [isActive]);

  const getStatusConfig = (status: ActivityItem['status']) => {
    switch (status) {
      case 'scraping':
        return { color: 'var(--primary)', bg: 'var(--primary-bg)', label: 'Scraping', pulse: true };
      case 'success':
        return { color: 'var(--success)', bg: 'var(--success-bg)', label: 'Complete', pulse: false };
      case 'analyzing':
        return { color: 'var(--warning)', bg: 'var(--warning-bg)', label: 'Analyzing', pulse: true };
      case 'queued':
        return { color: 'var(--text-muted)', bg: 'var(--bg-muted)', label: 'Queued', pulse: false };
    }
  };

  return (
    <div className="saas-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Wifi className="w-5 h-5" style={{ color: 'var(--primary)' }} />
            <span
              className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full animate-ping"
              style={{ background: 'var(--success)' }}
            />
            <span
              className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full"
              style={{ background: 'var(--success)' }}
            />
          </div>
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
            Live Activity
          </h3>
        </div>
        <span
          className="text-xs px-2 py-1 rounded-full font-medium"
          style={{ background: 'var(--success-bg)', color: 'var(--success)' }}
        >
          Active
        </span>
      </div>

      <div className="space-y-3">
        {activities.map((activity, index) => {
          const config = getStatusConfig(activity.status);
          return (
            <div
              key={activity.id}
              className="flex items-center gap-3 p-3 rounded-lg transition-all duration-300"
              style={{
                background: 'var(--bg-muted)',
                animationDelay: `${index * 100}ms`,
                opacity: 1 - (index * 0.15),
              }}
            >
              {/* Status Indicator */}
              <div className="relative">
                <div
                  className={`w-2.5 h-2.5 rounded-full ${config.pulse ? 'animate-pulse' : ''}`}
                  style={{ background: config.color }}
                />
                {config.pulse && (
                  <div
                    className="absolute inset-0 rounded-full animate-ping"
                    style={{ background: config.color, opacity: 0.4 }}
                  />
                )}
              </div>

              {/* URL & Strategy */}
              <div className="flex-1 min-w-0">
                <p
                  className="text-sm font-medium truncate"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {activity.url}
                </p>
                <p
                  className="text-xs"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {activity.strategy} • {new Date(activity.timestamp).toLocaleTimeString()}
                </p>
              </div>

              {/* Status Badge */}
              <span
                className="text-xs px-2 py-1 rounded-full font-medium shrink-0"
                style={{ background: config.bg, color: config.color }}
              >
                {activity.status === 'scraping' && (
                  <Loader2 className="w-3 h-3 inline mr-1 animate-spin" />
                )}
                {config.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Progress Bar */}
      <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--border-light)' }}>
        <div className="flex justify-between text-xs mb-2">
          <span style={{ color: 'var(--text-muted)' }}>Session Progress</span>
          <span className="font-mono" style={{ color: 'var(--primary)' }}>
            {activities.filter(a => a.status === 'success').length} / {activities.length}
          </span>
        </div>
        <div
          className="h-1.5 rounded-full overflow-hidden"
          style={{ background: 'var(--bg-subtle)' }}
        >
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${(activities.filter(a => a.status === 'success').length / Math.max(activities.length, 1)) * 100}%`,
              background: 'linear-gradient(90deg, var(--primary), var(--success))'
            }}
          />
        </div>
      </div>
    </div>
  );
};

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

        {/* Quick Actions + Live Activity */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
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
          </div>

          {/* Live Activity Feed */}
          <div>
            <LiveActivityFeed isActive={isBackendOnline} />
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