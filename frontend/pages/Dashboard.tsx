import React, { useEffect, useState } from 'react';
import { getSystemMetrics, getCircuitStatus } from '../services/api';
import { SystemMetrics, CircuitStatus } from '../types';
import { 
    Activity, 
    Server, 
    Globe, 
    Cpu, 
    DollarSign,
    Zap,
    CheckCircle2,
    AlertTriangle
} from 'lucide-react';

const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  trend?: string;
  color?: string;
}> = ({ title, value, subtitle, icon: Icon, trend, color = "blue" }) => (
  <div className="bg-surface border border-slate-700/50 rounded-xl p-5 hover:border-slate-600 transition-colors">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-2 rounded-lg bg-${color}-500/10`}>
        <Icon className={`w-5 h-5 text-${color}-500`} />
      </div>
      {trend && (
        <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full">
          {trend}
        </span>
      )}
    </div>
    <div className="text-2xl font-bold text-white mb-1">{value}</div>
    <div className="text-sm text-slate-400 font-medium">{title}</div>
    {subtitle && <div className="text-xs text-slate-500 mt-2">{subtitle}</div>}
  </div>
);

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [circuits, setCircuits] = useState<CircuitStatus[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const [m, c] = await Promise.all([getSystemMetrics(), getCircuitStatus()]);
      setMetrics(m);
      setCircuits(c);
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return <div className="p-8 text-slate-400">Loading system telemetry...</div>;

  return (
    <div className="p-8 space-y-8 h-full overflow-y-auto">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Platform Overview</h1>
        <p className="text-slate-400">Real-time telemetry and operational status.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
            title="Total Requests" 
            value={metrics.total_requests?.toLocaleString() ?? '0'} 
            icon={Activity} 
            trend="+12% this week"
            color="blue"
        />
        <StatCard 
            title="Scraping Success" 
            value={`${metrics.scraping_success_rate ?? 0}%`} 
            icon={Globe} 
            color="emerald"
            subtitle="Last 24 hours"
        />
        <StatCard 
            title="Active Tasks" 
            value={metrics.active_tasks ?? 0} 
            icon={Zap} 
            color="amber"
            subtitle="Processing now"
        />
         <StatCard 
            title="Est. Cost" 
            value={`$${metrics.cost_estimate?.toFixed(2) ?? '0.00'}`} 
            icon={DollarSign} 
            color="indigo"
            subtitle="Current billing cycle"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health */}
        <div className="lg:col-span-2 bg-surface border border-slate-700/50 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <Server className="w-5 h-5 text-blue-500" />
                Infrastructure Health
            </h2>
            <div className="space-y-6">
                <div>
                    <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-400">CPU Load</span>
                        <span className="text-white font-mono">{metrics.cpu_usage}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                        <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-500" 
                            style={{ width: `${metrics.cpu_usage}%` }}
                        ></div>
                    </div>
                </div>
                <div>
                    <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-400">Memory Usage</span>
                        <span className="text-white font-mono">{metrics.memory_usage}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                        <div 
                            className="bg-purple-500 h-2 rounded-full transition-all duration-500" 
                            style={{ width: `${metrics.memory_usage}%` }}
                        ></div>
                    </div>
                </div>
                <div>
                    <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-400">Token Budget</span>
                        <span className="text-white font-mono">{(metrics.tokens_used / 1000000 * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                        <div 
                            className="bg-emerald-500 h-2 rounded-full transition-all duration-500" 
                            style={{ width: `${(metrics.tokens_used / 1000000 * 100)}%` }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>

        {/* Circuit Breakers */}
        <div className="bg-surface border border-slate-700/50 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-rose-500" />
                Circuit Status
            </h2>
            <div className="space-y-4">
                {circuits.map((c) => (
                    <div key={c.service} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                        <span className="text-sm font-medium text-slate-300">{c.service}</span>
                        <div className="flex items-center gap-2">
                            {c.status === 'CLOSED' ? (
                                <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
                                    <CheckCircle2 className="w-3 h-3" /> Operational
                                </span>
                            ) : (
                                <span className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-500/10 px-2 py-1 rounded">
                                    <AlertTriangle className="w-3 h-3" /> Degraded
                                </span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;