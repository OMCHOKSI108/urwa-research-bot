import React from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from 'recharts';

const data = [
  { name: '00:00', requests: 400, success: 380, cost: 2.1 },
  { name: '04:00', requests: 300, success: 290, cost: 1.5 },
  { name: '08:00', requests: 1200, success: 1150, cost: 8.4 },
  { name: '12:00', requests: 2400, success: 2300, cost: 15.2 },
  { name: '16:00', requests: 1800, success: 1750, cost: 11.1 },
  { name: '20:00', requests: 900, success: 880, cost: 5.3 },
  { name: '23:59', requests: 500, success: 490, cost: 2.8 },
];

const SystemHealth: React.FC = () => {
  return (
    <div className="p-8 space-y-8 h-full overflow-y-auto">
      <div className="flex justify-between items-end">
        <div>
            <h1 className="text-2xl font-bold text-white mb-2">System Analytics</h1>
            <p className="text-slate-400">Detailed performance metrics and cost analysis.</p>
        </div>
        <div className="flex gap-2">
            <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-sm font-medium text-slate-300 rounded-lg transition-colors">Export CSV</button>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-sm font-medium text-white rounded-lg transition-colors">Generate Report</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Request Volume Chart */}
        <div className="bg-surface border border-slate-700/50 rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-white mb-6">Request Volume (24h)</h3>
            <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorReq" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                        <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }} 
                            itemStyle={{ color: '#94a3b8' }}
                        />
                        <Area type="monotone" dataKey="requests" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorReq)" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>

        {/* Cost Analysis Chart */}
        <div className="bg-surface border border-slate-700/50 rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-white mb-6">Cost Analysis ($)</h3>
             <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                        <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip 
                            cursor={{fill: '#334155', opacity: 0.2}}
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }} 
                        />
                        <Bar dataKey="cost" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
      </div>

      {/* Logs Preview */}
      <div className="bg-surface border border-slate-700/50 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700/50 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-white">System Logs</h3>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">LIVE</span>
        </div>
        <div className="p-0 bg-[#0c111c]">
            <div className="font-mono text-xs text-slate-400 p-4 space-y-1 h-64 overflow-y-auto">
                <div className="flex gap-3">
                    <span className="text-slate-500">[2023-10-27 10:42:01]</span>
                    <span className="text-blue-400">INFO</span>
                    <span>Orchestrator initialized successfully.</span>
                </div>
                <div className="flex gap-3">
                    <span className="text-slate-500">[2023-10-27 10:42:05]</span>
                    <span className="text-emerald-400">SUCCESS</span>
                    <span>Connected to Groq API (Latency: 45ms).</span>
                </div>
                <div className="flex gap-3">
                    <span className="text-slate-500">[2023-10-27 10:43:12]</span>
                    <span className="text-blue-400">INFO</span>
                    <span>Task #4922 (Smart Scrape) started for domain: news.ycombinator.com</span>
                </div>
                 <div className="flex gap-3">
                    <span className="text-slate-500">[2023-10-27 10:43:15]</span>
                    <span className="text-amber-400">WARN</span>
                    <span>Detected Cloudflare protection. Switching to Stealth Strategy B.</span>
                </div>
                 <div className="flex gap-3">
                    <span className="text-slate-500">[2023-10-27 10:43:18]</span>
                    <span className="text-emerald-400">SUCCESS</span>
                    <span>Task #4922 completed. Extracted 30 items.</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;