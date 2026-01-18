/**
 * URWA Brain - TypeScript Types & Interfaces
 * Comprehensive type definitions for the frontend
 */

// ═══════════════════════════════════════════════════════════════════════════
// ROUTING
// ═══════════════════════════════════════════════════════════════════════════

export enum AppRoute {
  DASHBOARD = '/',
  AGENT = '/agent',
  RESEARCH = '/research',
  SCRAPER = '/scraper',
  MONITOR = '/monitor',
  SETTINGS = '/settings',
}

// ═══════════════════════════════════════════════════════════════════════════
// AI AGENT TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface AgentResponse {
  intent: string;
  action_taken: string;
  result: {
    answer: string;
    sources?: Array<{ title: string; url: string }>;
    confidence: number;
    data?: any;
  };
  follow_up_suggestions: string[];
  llm_used?: string;
  execution_time?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  status?: 'pending' | 'success' | 'error';
  metadata?: {
    intent?: string;
    action?: string;
    sources?: Array<{ title: string; url: string }>;
    confidence?: number;
    executionTime?: number;
    llmUsed?: string;
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// SYSTEM TYPES
// ═══════════════════════════════════════════════════════════════════════════

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
  last_failure?: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: {
    [key: string]: {
      status: string;
      latency?: number;
    };
  };
  timestamp: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// SCRAPING TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface SiteProfile {
  domain: string;
  protection_level: 'none' | 'low' | 'medium' | 'high' | 'extreme';
  bot_detection: string[];
  requires_js: boolean;
  recommended_strategy: string;
  estimated_success_rate: number;
  warnings?: string[];
}

export interface ScrapeResult {
  success: boolean;
  url: string;
  content?: string;
  content_length?: number;
  extracted_data?: any;
  execution_time?: number;
  strategy_used?: string;
  error?: string;
}

export interface ScraperStats {
  strategies: {
    lightweight: { success_count: number; success_rate: string };
    playwright: { success_count: number; success_rate: string };
    ultra_stealth: { success_count: number; success_rate: string };
  };
  totals: {
    total_requests: number;
    total_failures: number;
    overall_success_rate: string;
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// RESEARCH TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface ResearchResult {
  status: string;
  answer: string;
  sources: Array<{
    url: string;
    title: string;
    snippet?: string;
  }>;
  follow_up_questions: string[];
  confidence: number;
  research_time: number;
  llm_used: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// UI STATE TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export interface ModalState {
  isOpen: boolean;
  title?: string;
  content?: React.ReactNode;
  onConfirm?: () => void;
  onCancel?: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════
// FORM TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface ScrapeFormData {
  url: string;
  instruction?: string;
  forceStrategy?: 'auto' | 'lightweight' | 'playwright' | 'ultra_stealth';
  useOllama?: boolean;
}

export interface ResearchFormData {
  query: string;
  deep: boolean;
  useOllama: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// LOG TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'WARN' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
  source?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// TABLE / DATA TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface TableColumn<T> {
  key: keyof T | string;
  header: string;
  width?: string;
  render?: (value: any, row: T) => React.ReactNode;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}