import { AgentResponse, SystemMetrics, CircuitStatus } from '../types';

const API_BASE = 'http://localhost:8000/api/v1';

// Helper to simulate network delay for polished feel
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Sends a prompt to the Unified AI Agent.
 * Wraps the fetch call with a mock fallback if the backend is offline.
 */
export const sendAgentMessage = async (input: string): Promise<AgentResponse> => {
  try {
    const response = await fetch(`${API_BASE}/agent?input=${encodeURIComponent(input)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) throw new Error('API Unavailable');
    return await response.json();
  } catch (error) {
    console.warn("Backend unavailable, using mock data for demo.");
    await delay(1500); // Fake thinking time
    
    // Mock response based on input keywords
    let intent = "research";
    let action = "Searched the web and analyzed sources";
    let answer = "I found several insights regarding your query. According to recent market analysis, this trend is growing significantly.";
    
    if (input.toLowerCase().includes("scrape")) {
      intent = "scraping";
      action = "Executed Playwright Stealth Scraper";
      answer = "Successfully extracted data from the target URL. The protection level was bypassed using Strategy A.";
    }

    return {
      intent: intent,
      action_taken: action,
      result: {
        answer: `## Analysis Result\n\n${answer}\n\n**Key Findings:**\n- Point 1: Data indicates strong correlation.\n- Point 2: Source credibility is high.\n\n`,
        sources: [
          { title: "TechCrunch Analysis", url: "https://techcrunch.com" },
          { title: "MarketWatch Report", url: "https://marketwatch.com" }
        ],
        confidence: 0.89
      },
      follow_up_suggestions: [
        "Analyze the competitors",
        "Export this data to CSV",
        "Monitor this topic for changes"
      ]
    };
  }
};

/**
 * Fetches system metrics for the dashboard.
 */
export const getSystemMetrics = async (): Promise<SystemMetrics> => {
  try {
    const response = await fetch(`${API_BASE}/system/metrics`);
    if (!response.ok) throw new Error('API Unavailable');
    return await response.json();
  } catch (e) {
    // Mock metrics
    return {
      cpu_usage: 42,
      memory_usage: 65,
      active_tasks: 3,
      scraping_success_rate: 98.5,
      total_requests: 12450,
      tokens_used: 450000,
      cost_estimate: 12.45
    };
  }
};

export const getCircuitStatus = async (): Promise<CircuitStatus[]> => {
    // Mock Data for Circuits
    return [
        { service: 'Groq API', status: 'CLOSED', failures: 0 },
        { service: 'Google Gemini', status: 'CLOSED', failures: 0 },
        { service: 'Scraper (Linkedin)', status: 'HALF-OPEN', failures: 2 },
        { service: 'DuckDuckGo', status: 'CLOSED', failures: 0 },
    ];
}