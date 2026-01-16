// API Response Types matching the URWA Brain Backend

export interface AgentResponse {
  intent: string;
  action_taken: string;
  result: {
    answer: string;
    sources?: Array<{ title: string; url: string }>;
    confidence: number;
  };
  follow_up_suggestions: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    intent?: string;
    action?: string;
    sources?: Array<{ title: string; url: string }>;
    confidence?: number;
  };
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_tasks: number;
  scraping_success_rate: number;
  total_requests: number;
  tokens_used: number;
  cost_estimate: number;
}

export interface CircuitStatus {
  service: string;
  status: 'OPEN' | 'CLOSED' | 'HALF-OPEN';
  failures: number;
}

export enum AppRoute {
  DASHBOARD = '/',
  AGENT = '/agent',
  RESEARCH = '/research',
  MONITOR = '/monitor',
  SETTINGS = '/settings'
}