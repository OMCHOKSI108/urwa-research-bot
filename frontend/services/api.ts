/**
 * URWA Brain - Complete API Service
 * Production-grade API integration with all backend endpoints
 */

import { AgentResponse, SystemMetrics, CircuitStatus } from '../types';

const API_BASE = 'http://localhost:8000/api/v1';

// ═══════════════════════════════════════════════════════════════════════════
// API Response Types
// ═══════════════════════════════════════════════════════════════════════════

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: Date;
}

export interface ResearchResult {
  status: string;
  answer: string;
  sources: Array<{ url: string; title: string; snippet?: string }>;
  follow_up_questions: string[];
  confidence: number;
  research_time: number;
  llm_used: string;
}

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
  status: string;
  url: string;
  content?: string;
  content_length?: number;
  extracted_data?: any;
  execution_time?: number;
  strategy_used?: string;
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

export interface ComplianceResult {
  can_scrape: boolean;
  robots_txt_allowed: boolean;
  crawl_delay: number;
  blacklisted: boolean;
  warnings: string[];
}

// ═══════════════════════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════════════════════

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
      timestamp: new Date(),
    };
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unknown error occurred',
      timestamp: new Date(),
    };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// LLM SETTINGS HELPER - Read from localStorage
// ═══════════════════════════════════════════════════════════════════════════

const LLM_STORAGE_KEY = 'urwa_llm_settings';

interface LLMSettingsData {
  activeProvider: 'gemini' | 'groq' | 'ollama';
  gemini: { apiKey: string; model: string; enabled: boolean };
  groq: { apiKey: string; model: string; enabled: boolean };
  ollama: { baseUrl: string; model: string; enabled: boolean };
}

function getLLMSettings(): { provider: string; useOllama: boolean; model: string } {
  try {
    const saved = localStorage.getItem(LLM_STORAGE_KEY);
    if (saved) {
      const settings: LLMSettingsData = JSON.parse(saved);
      return {
        provider: settings.activeProvider,
        useOllama: settings.activeProvider === 'ollama',
        model: settings[settings.activeProvider]?.model || 'gemini-2.5-flash',
      };
    }
  } catch (e) {
    console.error('Failed to read LLM settings:', e);
  }
  // Default to cloud (gemini)
  return { provider: 'gemini', useOllama: false, model: 'gemini-2.5-flash' };
}

// ═══════════════════════════════════════════════════════════════════════════
// UNIFIED AI AGENT APIs
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Send a message to the Unified AI Agent
 * This is the main endpoint that handles all AI requests
 * Automatically reads LLM provider from Settings
 */
export async function sendAgentMessage(
  input: string,
  forceOllama?: boolean
): Promise<ApiResponse<AgentResponse>> {
  // Read settings from localStorage
  const llmSettings = getLLMSettings();
  const useOllama = forceOllama !== undefined ? forceOllama : llmSettings.useOllama;

  console.log(`[API] Using LLM: ${llmSettings.provider}, useOllama: ${useOllama}, model: ${llmSettings.model}`);

  return apiCall<AgentResponse>('/agent', {
    method: 'POST',
    body: JSON.stringify({
      input,
      use_ollama: useOllama,
      llm_provider: llmSettings.provider,
      model: llmSettings.model,
    }),
  });
}

/**
 * Get agent conversation history
 */
export async function getAgentHistory(): Promise<ApiResponse<any[]>> {
  return apiCall<any[]>('/agent/history');
}

/**
 * Clear agent conversation history
 */
export async function clearAgentHistory(): Promise<ApiResponse<{ message: string }>> {
  return apiCall<{ message: string }>('/agent/clear', { method: 'POST' });
}

// ═══════════════════════════════════════════════════════════════════════════
// RESEARCH APIs (Perplexity-style)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Perform deep research on a topic
 * Automatically reads LLM provider from Settings
 */
export async function performResearch(
  query: string,
  deep: boolean = false,
  forceOllama?: boolean
): Promise<ApiResponse<ResearchResult>> {
  // Read settings from localStorage
  const llmSettings = getLLMSettings();
  const useOllama = forceOllama !== undefined ? forceOllama : llmSettings.useOllama;

  console.log(`[API Research] Using LLM: ${llmSettings.provider}, useOllama: ${useOllama}`);

  return apiCall<ResearchResult>('/research', {
    method: 'POST',
    body: JSON.stringify({
      query,
      deep,
      use_ollama: useOllama,
      llm_provider: llmSettings.provider,
      model: llmSettings.model,
    }),
  });
}

/**
 * Get research chat history
 */
export async function getResearchHistory(): Promise<ApiResponse<any[]>> {
  return apiCall<any[]>('/research/history');
}

/**
 * Clear research history
 */
export async function clearResearchHistory(): Promise<ApiResponse<{ message: string }>> {
  return apiCall<{ message: string }>('/research/clear', { method: 'POST' });
}

// ═══════════════════════════════════════════════════════════════════════════
// SITE INTELLIGENCE APIs
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Profile a website's protection level and scraping viability
 */
export async function profileSite(url: string): Promise<ApiResponse<{ profile: SiteProfile }>> {
  return apiCall<{ profile: SiteProfile }>(`/strategy/profile-site?url=${encodeURIComponent(url)}`);
}

/**
 * Check compliance for scraping a URL
 */
export async function checkCompliance(url: string): Promise<ApiResponse<{ compliance: ComplianceResult }>> {
  return apiCall<{ compliance: ComplianceResult }>(`/strategy/compliance-check?url=${encodeURIComponent(url)}`);
}

/**
 * Get strategy learning data for a domain
 */
export async function getStrategyLearning(domain?: string): Promise<ApiResponse<any>> {
  const endpoint = domain
    ? `/strategy/learning?domain=${encodeURIComponent(domain)}`
    : '/strategy/learning';
  return apiCall<any>(endpoint);
}

// ═══════════════════════════════════════════════════════════════════════════
// SCRAPING APIs
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Scrape a protected site using advanced bypass techniques
 */
export async function scrapeProtectedSite(
  url: string,
  instruction?: string
): Promise<ApiResponse<ScrapeResult>> {
  const params = new URLSearchParams({ url });
  if (instruction) params.append('instruction', instruction);

  return apiCall<ScrapeResult>(`/protected-scrape?${params.toString()}`, {
    method: 'POST',
  });
}

/**
 * Smart scrape with automatic strategy selection
 */
export async function smartScrape(
  url: string,
  instruction?: string
): Promise<ApiResponse<ScrapeResult>> {
  return apiCall<ScrapeResult>('/scrape', {
    method: 'POST',
    body: JSON.stringify({ url, instruction }),
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SYSTEM APIs
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Get system metrics (CPU, memory, requests, etc.)
 */
export async function getSystemMetrics(): Promise<ApiResponse<SystemMetrics>> {
  const response = await apiCall<any>('/system/metrics');

  if (response.success && response.data) {
    // Transform API response to match our types
    return {
      ...response,
      data: {
        cpu_usage: response.data.cpu_usage ?? response.data.gauges?.cpu_percent ?? 0,
        memory_usage: response.data.memory_usage ?? response.data.gauges?.memory_percent ?? 0,
        active_tasks: response.data.active_tasks ?? response.data.gauges?.active_tasks ?? 0,
        scraping_success_rate: response.data.scraping_success_rate ?? 98.5,
        total_requests: response.data.total_requests ?? response.data.counters?.requests_total ?? 0,
        tokens_used: response.data.tokens_used ?? 0,
        cost_estimate: response.data.cost_estimate ?? 0,
      },
    };
  }

  return response as ApiResponse<SystemMetrics>;
}

/**
 * Get circuit breaker status for all services
 */
export async function getCircuitStatus(): Promise<ApiResponse<CircuitStatus[]>> {
  const response = await apiCall<any>('/system/circuits');

  if (response.success && response.data) {
    const circuits = response.data.circuits;
    let statusArray: CircuitStatus[] = [];

    if (Array.isArray(circuits)) {
      statusArray = circuits.map((c: any) => ({
        service: c.service ?? c.domain ?? 'Unknown',
        status: c.status ?? c.state ?? 'CLOSED',
        failures: c.failures ?? c.failure_count ?? 0,
      }));
    } else if (typeof circuits === 'object') {
      statusArray = Object.entries(circuits).map(([domain, info]: [string, any]) => ({
        service: domain,
        status: info.state ?? 'CLOSED',
        failures: info.failures ?? 0,
      }));
    }

    return { ...response, data: statusArray };
  }

  return response as ApiResponse<CircuitStatus[]>;
}

/**
 * Get system health status
 */
export async function getSystemHealth(): Promise<ApiResponse<any>> {
  return apiCall<any>('/system/health');
}

/**
 * Get scraper statistics by strategy
 */
export async function getScraperStats(): Promise<ApiResponse<ScraperStats>> {
  return apiCall<ScraperStats>('/scraper-stats');
}

/**
 * Get strategy performance statistics
 */
export async function getStrategyStats(): Promise<ApiResponse<any>> {
  return apiCall<any>('/strategy/stats');
}

/**
 * Get system logs
 */
export async function getSystemLogs(limit: number = 50): Promise<ApiResponse<{ logs: any[] }>> {
  return apiCall<{ logs: any[] }>(`/system/logs?limit=${limit}`);
}

/**
 * Clear all strategy data (learning, caches, evidence)
 */
export async function clearStrategyData(): Promise<ApiResponse<{ message: string }>> {
  return apiCall<{ message: string }>('/strategy/clear', { method: 'POST' });
}

/**
 * Clear scraper cache
 */
export async function clearScraperCache(): Promise<ApiResponse<{ message: string }>> {
  return apiCall<{ message: string }>('/scraper-cache/clear', { method: 'POST' });
}

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Check if backend is online
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch('http://localhost:8000/health', {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT DATA UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Export data to CSV
 */
export function exportToCSV(data: any[], filename: string): void {
  if (!data.length) return;

  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row =>
      headers.map(header => {
        const value = row[header];
        // Escape commas and quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
  link.click();
}

/**
 * Export data to JSON
 */
export function exportToJSON(data: any, filename: string): void {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}_${new Date().toISOString().split('T')[0]}.json`;
  link.click();
}