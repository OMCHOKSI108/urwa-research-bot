from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import datetime

from app.models.schemas import (
    SmartScrapeRequest, ScrapeResponse, TaskResponse, ChatRequest, SearchRequest, 
    AnalyzeUrlsRequest, WebSearchRequest, TargetedScrapeRequest, CustomScrapeRequest,
    SourceIntelligenceRequest, FactCheckRequest, KnowledgeBaseAddRequest,
    KnowledgeBaseSearchRequest, PlannerRequest, MonitoringAddRequest
)
from app.agents.hybrid_scraper import HybridScraper
from app.agents.llm_processor import LLMProcessor
from app.agents.ollama_processor import OllamaProcessor
from app.utils.html_parser_advanced import AdvancedHTMLParser
from app.utils.context_manager import AdvancedContextManager
from app.services.orchestrator import OrchestratorService
from app.strategies import strategy_engine, site_profiler, compliance_checker
import os
import sys
import asyncio
import nest_asyncio
import uuid
import json
from loguru import logger
from dotenv import load_dotenv
from collections import deque

# Log Capture
recent_logs = deque(maxlen=100)
logger.add(lambda msg: recent_logs.append(str(msg).strip()))

# Load Environment
load_dotenv()

# Windows Proactor Loop Fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

nest_asyncio.apply()

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)

# --- App Initialization ---
app = FastAPI(
    title="URWA Brain - Smart Agent",
    description="Universal Research Web Agent - AI-powered web scraping with stealth capabilities",
    version="2.2.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Dirs
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = str(BASE_DIR / "app/static/exports")
SESSION_DIR = str(BASE_DIR / "app/static/sessions")
HISTORY_DIR = str(BASE_DIR / "app/static/history")
for d in [EXPORT_DIR, SESSION_DIR, HISTORY_DIR]:
    os.makedirs(d, exist_ok=True)

app.mount("/exports", StaticFiles(directory=EXPORT_DIR), name="exports")
# Serve frontend UI (SPA) under /ui
frontend_path = Path("../../frontend")
if frontend_path.exists():
    try:
        app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
        logger.info("Frontend mounted at /ui")
    except Exception as e:
        logger.warning(f"Failed to mount frontend UI: {e}")
else:
    # Quietly skip if frontend not found (headless mode)
    pass

# --- CORS ---
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Services ---
scraper = HybridScraper()
processor = LLMProcessor()
ollama_processor = OllamaProcessor(model="phi3:mini")
html_parser = AdvancedHTMLParser()
context_manager = AdvancedContextManager()

orchestrator = OrchestratorService(
    scraper=scraper, 
    processor=processor, 
    ollama_processor=ollama_processor, 
    html_parser=html_parser,
    context_manager=context_manager
)

# Research Chat (Perplexity-style) - Cloud LLM (Gemini/Groq)
from app.services.research_chat import get_research_chat
research_chat = get_research_chat(orchestrator, processor)

# Research Chat with Local Ollama
research_chat_ollama = get_research_chat(orchestrator, ollama_processor)

# Unified AI Agent - Cloud LLM (Gemini/Groq)
from app.services.unified_agent import get_unified_agent
ai_agent = get_unified_agent(orchestrator, processor, research_chat)

# Unified AI Agent - Local Ollama
ai_agent_ollama = get_unified_agent(orchestrator, ollama_processor, research_chat_ollama)

def get_orchestrator():
    return orchestrator

# --- Routes ---

@app.get("/", tags=["Status"])
async def root():
    return {"status": "URWA Brain Online", "version": "3.0.0", "ai_agent": "enabled"}

@app.get("/health", tags=["Status"])
async def health_check():
    return {"status": "healthy"}


# ============================================================================
# UNIFIED AI AGENT - ONE ENDPOINT FOR EVERYTHING
# ============================================================================

class AgentRequest(BaseModel):
    input: str
    use_ollama: bool = False

@app.post("/api/v1/agent", tags=["AI Agent"])
@limiter.limit("20/minute")
async def unified_ai_agent(
    request: Request,
    body: AgentRequest
):
    """
    UNIFIED AI AGENT - One endpoint that does everything.
    
    Just tell it what you want in natural language, and it will:
    - Understand your intent
    - Decide which tools to use
    - Execute the appropriate actions
    - Return comprehensive results
    
    **Examples:**
    
    Research:
    ```
    "What are the current bitcoin market conditions and impact on Indian economy?"
    "Tell me about the latest AI trends in healthcare"
    "Compare Python vs JavaScript for web development"
    ```
    
    Scrape:
    ```
    "Extract the top stories from https://news.ycombinator.com"
    "Get product details from https://amazon.com/dp/B0BSHF7WHW"
    ```
    
    Fact Check:
    ```
    "Is it true that Python is the most popular programming language?"
    "Verify: Electric cars are better for the environment"
    ```
    
    Site Analysis:
    ```
    "Can I scrape linkedin.com?"
    "What protection does amazon.com have?"
    ```
    
    **Parameters:**
    - **input**: Your natural language request
    - **use_ollama**: If true, uses local Ollama LLM instead of cloud Gemini/Groq
    
    **Response:**
    ```json
    {
        "intent": "research",
        "action_taken": "Searched the web and analyzed multiple sources",
        "result": {
            "answer": "Comprehensive analysis...",
            "sources": [...]
        },
        "follow_up_suggestions": [...]
    }
    ```
    """
    try:
        # Choose agent based on LLM preference
        agent = ai_agent_ollama if body.use_ollama else ai_agent
        result = await agent.process(body.input)
        result["llm_used"] = "ollama" if body.use_ollama else "gemini/groq"
        return result
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "input": body.input
        }


@app.get("/api/v1/agent/history", tags=["AI Agent"])
async def get_agent_history():
    """Get AI agent conversation history."""
    return {
        "status": "success",
        "history": ai_agent.get_history()
    }


@app.post("/api/v1/agent/clear", tags=["AI Agent"])
async def clear_agent_history():
    """Clear AI agent conversation history."""
    ai_agent.clear_history()
    return {"status": "success", "message": "History cleared"}


# ============================================================================
# PERPLEXITY-STYLE RESEARCH CHAT
# ============================================================================

class ResearchChatRequest(BaseModel):
    query: str
    deep: bool = False
    use_ollama: bool = False

@app.post("/api/v1/research", tags=["Research"])
@limiter.limit("10/minute")
async def research_query(
    request: Request,
    body: ResearchChatRequest
):
    """
    Perplexity-style AI Research Chat.
    
    Takes a question, searches the web, scrapes sources, and returns
    a comprehensive AI-generated answer with citations.
    """
    try:
        # Choose chat service based on LLM preference
        chat_service = research_chat_ollama if body.use_ollama else research_chat
        return await chat_service.chat(body.query, deep_research=body.deep)
    except Exception as e:
        logger.error(f"Research error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    """
    
    **Example:**
    ```
    POST /api/v1/research?query=what is current bitcoin market conditions
    POST /api/v1/research?query=top 10 economies&use_ollama=true  # Use local Ollama
    ```
    
    **Response:**
    ```json
    {
        "answer": "Based on current market data...",
        "sources": [{"url": "...", "title": "..."}],
        "follow_up_questions": ["What about Ethereum?", ...],
        "confidence": 0.85,
        "research_time": 5.2
    }
    ```
    
    Parameters:
    - **query**: Your question (natural language)
    - **deep**: If true, scrapes more sources (slower but more comprehensive)
    - **use_ollama**: If true, uses local Ollama LLM instead of cloud Gemini/Groq
    """
    try:
        # Choose LLM based on parameter
        chat_service = research_chat_ollama if use_ollama else research_chat
        result = await chat_service.chat(query, deep_research=deep)
        return {
            "status": "success",
            "llm_used": "ollama" if use_ollama else "gemini/groq",
            **result
        }
    except Exception as e:
        logger.error(f"Research error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "query": query
        }


@app.get("/api/v1/research/history", tags=["Research"])
async def get_research_history():
    """Get conversation history from research chat."""
    return {
        "status": "success",
        "history": research_chat.get_history()
    }


@app.post("/api/v1/research/clear", tags=["Research"])
async def clear_research_history():
    """Clear research chat history."""
    research_chat.clear_history()
    return {"status": "success", "message": "History cleared"}

@app.get("/api/v1/scraper-stats", tags=["Status"])
async def scraper_stats():
    """
    Get scraping strategy statistics.
    
    Returns success rates and counts for each scraping strategy:
    - Lightweight HTTP (fastest)
    - Playwright Stealth (JavaScript rendering)
    - Ultra Stealth (anti-bot bypass)
    """
    stats = scraper.get_stats()
    
    return {
        "status": "success",
        "strategies": {
            "lightweight": {
                "name": "Lightweight HTTP",
                "description": "Fast HTTP requests for static pages",
                "success_count": stats.get("lightweight_success", 0),
                "success_rate": f"{stats.get('lightweight_rate', 0) * 100:.1f}%"
            },
            "playwright": {
                "name": "Stealth Playwright",
                "description": "Browser-based scraping for JavaScript-rendered pages",
                "success_count": stats.get("playwright_success", 0),
                "success_rate": f"{stats.get('playwright_rate', 0) * 100:.1f}%"
            },
            "ultra_stealth": {
                "name": "Ultra Stealth Mode",
                "description": "Maximum anti-bot bypass for protected sites",
                "success_count": stats.get("ultra_stealth_success", 0),
                "success_rate": f"{stats.get('ultra_stealth_rate', 0) * 100:.1f}%"
            }
        },
        "totals": {
            "total_requests": stats.get("total_requests", 0),
            "total_failures": stats.get("total_failures", 0),
            "overall_success_rate": f"{stats.get('success_rate', 0) * 100:.1f}%"
        },
        "protected_sites": [
            "linkedin.com", "facebook.com", "instagram.com", "twitter.com",
            "amazon.com", "ebay.com", "cloudflare.com", "indeed.com"
        ]
    }


@app.post("/api/v1/scraper-cache/clear", tags=["Status"])
async def clear_scraper_cache():
    """
    Clear the scraper cache and reset statistics.
    Useful for testing or when you want fresh scrapes.
    """
    scraper.clear_cache()
    return {
        "status": "success",
        "message": "Scraper cache cleared successfully",
        "cache_cleared": True
    }


# ============================================================================
# STRATEGY ENDPOINTS - Production-grade scraping intelligence
# ============================================================================

@app.get("/api/v1/strategy/profile-site", tags=["Strategy"])
async def profile_site(url: str):
    """
    Profile a website to detect protection level before scraping.
    
    Detects:
    - Bot protection (Cloudflare, Akamai, DataDome, etc.)
    - JavaScript rendering requirements
    - CAPTCHA presence
    - Recommended scraping strategy
    """
    profile = await site_profiler.profile(url)
    return {
        "status": "success",
        "profile": profile
    }


@app.get("/api/v1/strategy/compliance-check", tags=["Strategy"])
async def check_compliance(url: str):
    """
    Check if a URL can be scraped compliantly.
    
    Checks:
    - robots.txt rules
    - Crawl-delay requirements
    - Blacklist status
    - ToS warnings
    """
    result = await compliance_checker.check(url)
    return {
        "status": "success",
        "compliance": result
    }


@app.get("/api/v1/strategy/stats", tags=["Strategy"])
async def strategy_stats():
    """
    Get comprehensive statistics from all scraping strategies.
    
    Includes:
    - Learning data (success rates per domain)
    - Rate control status
    - Failure evidence summary
    - Retry statistics
    """
    return {
        "status": "success",
        "stats": strategy_engine.get_stats()
    }


@app.get("/api/v1/scraper-stats", tags=["System"])
async def get_scraper_stats():
    """Get statistics from the core HybridScraper."""
    return {
        "status": "success",
        "stats": scraper.get_stats()
    }


@app.get("/api/v1/strategy/learning", tags=["Strategy"])
async def strategy_learning(domain: str = None):
    """
    Get domain-specific learning data.
    
    Shows what strategies work best for each domain based on historical success.
    """
    from app.strategies import strategy_learner
    
    if domain:
        stats = strategy_learner.get_domain_stats(domain)
        recommendation = strategy_learner.recommend(domain)
        return {
            "status": "success",
            "domain": domain,
            "stats": stats,
            "recommendation": recommendation
        }
    else:
        return {
            "status": "success",
            "summary": strategy_learner.get_all_stats()
        }


@app.post("/api/v1/strategy/clear", tags=["Strategy"])
async def clear_strategy_data():
    """
    Clear all strategy data (caches, learning, evidence).
    Use with caution - this resets all learned behaviors.
    """
    strategy_engine.clear_all()
    return {
        "status": "success",
        "message": "All strategy data cleared"
    }


# ============================================================================
# ADVANCED BYPASS ENDPOINTS - For protected sites
# ============================================================================

@app.post("/api/v1/protected-scrape", tags=["Advanced"])
async def protected_scrape(url: str, instruction: str = None):
    """
    Scrape protected sites using site-specific strategies.
    
    Supports:
    - LinkedIn (via Google Cache, Bing, Web Archive)
    - Amazon (via mobile URLs, search extraction)
    - Indeed (via RSS feeds, Google Jobs)
    - Twitter/Instagram/Facebook (via oEmbed)
    """
    from app.strategies.site_specific import get_site_scraper
    
    site_scraper = get_site_scraper(url)
    
    if site_scraper:
        # Use site-specific scraper
        if "linkedin" in url.lower():
            result = await site_scraper.scrape_profile(url, scraper)
        elif "amazon" in url.lower():
            result = await site_scraper.scrape_product(url, scraper)
        elif "indeed" in url.lower():
            # Parse query from URL or instruction
            query = instruction or "software engineer"
            result = await site_scraper.scrape_jobs(query, "remote", scraper)
        elif any(s in url.lower() for s in ["twitter", "x.com"]):
            result = await site_scraper.get_twitter_post(url, scraper)
        elif "instagram" in url.lower():
            result = await site_scraper.get_instagram_post(url, scraper)
        elif "facebook" in url.lower():
            result = await site_scraper.get_facebook_post(url, scraper)
        else:
            result = {"error": "Site not yet supported"}
        
        return {
            "status": "success" if result.get("success") else "partial",
            "url": url,
            "result": result
        }
    else:
        # Fall back to standard scraping
        content = await scraper.scrape(url, force_ultra_stealth=True)
        return {
            "status": "success" if content else "failed",
            "url": url,
            "content": content[:10000] if content else "",  # Include actual content (truncated)
            "content_length": len(content) if content else 0,
            "message": "Used standard ultra-stealth scraping"
        }


@app.get("/api/v1/human-queue", tags=["Advanced"])
async def get_human_queue():
    """
    Get pending tasks requiring human intervention.
    
    Tasks include:
    - CAPTCHA solving
    - Login requirements
    - Verification challenges
    """
    from app.strategies.advanced_bypass import human_queue
    
    return {
        "status": "success",
        "pending_tasks": human_queue.get_pending_tasks(),
        "total_pending": len(human_queue.get_pending_tasks())
    }


@app.post("/api/v1/human-queue/{task_id}/complete", tags=["Advanced"])
async def complete_human_task(task_id: str, result: dict):
    """
    Complete a human queue task with solution.
    
    The result should contain cookies, tokens, or other session data
    obtained from manual intervention.
    """
    from app.strategies.advanced_bypass import human_queue
    
    success = human_queue.complete_task(task_id, result)
    
    return {
        "status": "success" if success else "not_found",
        "task_id": task_id
    }


@app.get("/api/v1/browser-profiles", tags=["Advanced"])
async def list_browser_profiles():
    """
    List all browser profiles.
    
    Profiles maintain persistent sessions with:
    - Cookies across sessions
    - Consistent fingerprints
    - Site visit history
    """
    from app.strategies.browser_profiles import profile_manager
    
    return {
        "status": "success",
        "profiles": profile_manager.list_profiles(),
        "total": len(profile_manager.profiles)
    }


@app.post("/api/v1/browser-profiles/create", tags=["Advanced"])
async def create_browser_profile(name: str = None):
    """
    Create a new browser profile with unique fingerprint.
    """
    from app.strategies.browser_profiles import profile_manager
    
    profile = profile_manager.create_profile(name)
    
    return {
        "status": "success",
        "profile": {
            "name": profile.name,
            "fingerprint": profile.fingerprint
        }
    }


@app.get("/api/v1/captcha-stats", tags=["Advanced"])
async def get_captcha_stats():
    """
    Get CAPTCHA solving statistics.
    """
    from app.strategies.advanced_bypass import captcha_solver
    
    return {
        "status": "success",
        "stats": captcha_solver.get_stats()
    }


@app.get("/api/v1/proxy-stats", tags=["Advanced"])
async def get_proxy_stats():
    """
    Get proxy intelligence statistics.
    """
    from app.strategies.advanced_bypass import proxy_intelligence
    
    return {
        "status": "success",
        "stats": proxy_intelligence.get_stats()
    }


# ============================================================================
# PRODUCTION INFRASTRUCTURE ENDPOINTS
# ============================================================================

@app.get("/api/v1/system/metrics", tags=["System"])
async def get_system_metrics():
    """
    Get system metrics (Prometheus-compatible).
    
    Returns:
    - Counters (requests, errors, cache hits)
    - Gauges (active connections, queue size)
    - Histograms (latency percentiles)
    """
    from app.core.production_infra import metrics_collector
    
    return metrics_collector.get_metrics()


@app.get("/api/v1/system/metrics/prometheus", tags=["System"])
async def get_prometheus_metrics():
    """Export metrics in Prometheus format for scraping."""
    from app.core.production_infra import metrics_collector
    from fastapi.responses import PlainTextResponse
    
    return PlainTextResponse(
        content=metrics_collector.export_prometheus(),
        media_type="text/plain"
    )


@app.get("/api/v1/system/circuits", tags=["System"])
async def get_circuit_breakers():
    """
    Get circuit breaker status for all domains/services.
    
    Shows which domains are currently blocked due to repeated failures.
    """
    from app.core.production_infra import circuit_breakers
    
    return {
        "status": "success",
        "circuits": circuit_breakers.get_all_status(),
        "open_circuits": circuit_breakers.get_open_circuits()
    }


@app.get("/api/v1/system/health", tags=["System"])
async def system_health_check():
    """
    Comprehensive system health check.
    
    Checks:
    - CPU/Memory/Disk usage
    - Playwright availability
    - External service connectivity
    """
    from app.core.production_infra import health_checker
    
    components = await health_checker.check_all()
    
    # Determine overall status
    statuses = [c.status.value for c in components.values()]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "unhealthy"
    else:
        overall = "degraded"
    
    return {
        "status": overall,
        "components": {
            name: {
                "status": c.status.value,
                "message": c.message,
                "metrics": c.metrics
            }
            for name, c in components.items()
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/system/logs", tags=["System"])
async def get_system_logs(limit: int = 20):
    """
    Get recent system logs.
    """
    return {
        "status": "success",
        "logs": list(recent_logs)[-limit:],
        "total_cached": len(recent_logs)
    }


@app.get("/api/v1/system/cost", tags=["System"])
async def get_cost_usage():
    """
    Get resource usage and cost tracking.
    
    Shows:
    - LLM token usage
    - Browser time
    - Proxy requests
    - Estimated costs
    """
    from app.core.production_infra import cost_controller
    
    return {
        "status": "success",
        "usage": cost_controller.get_usage_stats()
    }


@app.post("/api/v1/system/cost/limits", tags=["System"])
async def set_cost_limits(limit_name: str, value: float):
    """
    Set resource usage limits.
    
    Available limits:
    - llm_tokens_per_hour
    - browser_minutes_per_hour
    - requests_per_hour
    - cost_per_hour_usd
    """
    from app.core.production_infra import cost_controller
    
    cost_controller.set_limit(limit_name, value)
    
    return {
        "status": "success",
        "message": f"Limit {limit_name} set to {value}",
        "current_limits": cost_controller.limits
    }


@app.get("/api/v1/system/extractors", tags=["System"])
async def list_extractors():
    """
    List all versioned extractors.
    
    Shows registered extractors with their current versions.
    """
    from app.core.data_quality import extractor_registry
    
    return {
        "status": "success",
        "extractors": extractor_registry.list_extractors()
    }


@app.post("/api/v1/system/extractors/rollback", tags=["System"])
async def rollback_extractor(name: str, version: str):
    """
    Rollback an extractor to a previous version.
    
    Use when a site changes and new selectors break extraction.
    """
    from app.core.data_quality import extractor_registry
    
    extractor = extractor_registry.get_extractor(name)
    if not extractor:
        return {"status": "error", "message": f"Extractor {name} not found"}
    
    success = extractor.rollback(version)
    
    return {
        "status": "success" if success else "error",
        "message": f"Rolled back {name} to v{version}" if success else "Version not found"
    }


@app.post("/api/v1/normalize", tags=["Data"])
async def normalize_data(data_type: str, value: str):
    """
    Normalize raw data to structured format.
    
    Types:
    - price: "$1,234.56" → {"amount": 1234.56, "currency": "USD"}
    - date: "Jan 15, 2024" → {"iso": "2024-01-15"}
    - location: "New York, NY" → {"city": "New York", "state": "NY"}
    - company: "Google LLC" → {"name": "Google", "legal_suffix": "LLC"}
    - rating: "4.5/5" → {"value": 4.5, "max": 5, "percent": 90}
    """
    from app.core.data_quality import data_normalizer
    
    normalizers = {
        "price": data_normalizer.normalize_price,
        "date": data_normalizer.normalize_date,
        "location": data_normalizer.normalize_location,
        "company": data_normalizer.normalize_company_name,
        "rating": data_normalizer.normalize_rating,
        "phone": data_normalizer.normalize_phone,
    }
    
    if data_type not in normalizers:
        return {
            "status": "error",
            "message": f"Unknown type: {data_type}",
            "available_types": list(normalizers.keys())
        }
    
    result = normalizers[data_type](value)
    
    return {
        "status": "success",
        "input": value,
        "normalized": result
    }


@app.get("/api/v1/system/logs", tags=["System"])
async def get_recent_logs(limit: int = 100, level: str = None):
    """
    Get recent structured logs.
    
    Filter by level: info, warning, error, metric
    """
    import os
    import json
    
    log_file = "app/static/logs/urwa.jsonl"
    logs = []
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()[-limit:]
            for line in lines:
                try:
                    entry = json.loads(line)
                    if level is None or entry.get("level", "").lower() == level.lower():
                        logs.append(entry)
                except:
                    pass
    
    return {
        "status": "success",
        "count": len(logs),
        "logs": logs[-limit:]
    }

@app.post("/api/v1/smart_scrape", response_model=TaskResponse, tags=["Core"])
@limiter.limit("5/minute")
async def smart_scrape(
    request: Request,
    scrape_req: SmartScrapeRequest, 
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    request_id = str(uuid.uuid4())
    logger.info(f"Queuing Request {request_id} from {request.client.host}: {scrape_req.query}")
    
    background_tasks.add_task(service.run_smart_scrape, request_id, scrape_req)
    
    return TaskResponse(
        task_id=request_id,
        status="processing",
        message="Research task started in background"
    )

@app.get("/api/v1/tasks/{task_id}", tags=["Core"])
@limiter.limit("60/minute")
async def get_task_status(
    request: Request,
    task_id: str
):
    """Poll this endpoint to get task status and final results"""
    session_file = os.path.join(SESSION_DIR, f"{task_id}.json")
    
    if not os.path.exists(session_file):
        raise HTTPException(status_code=404, detail="Task not found")
        
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error reading session file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read task data")

# --- Specialized Endpoints for Different Modes ---

@app.post("/api/chat", response_model=TaskResponse, tags=["Chat Mode"])
@limiter.limit("5/minute")
async def chat_mode(
    request: Request,
    chat_req: ChatRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """Chat mode: Natural language processing with automatic URL extraction"""
    request_id = str(uuid.uuid4())
    logger.info(f"Chat Request {request_id} from {request.client.host}: {chat_req.message[:100]}...")

    # Parse URLs from the message
    import re
    urls = re.findall(r'https?://[^\s,]+', chat_req.message)
    query = re.sub(r'https?://[^\s,]+', '', chat_req.message).strip()

    # Create SmartScrapeRequest from chat input
    scrape_req = SmartScrapeRequest(
        query=query or "Analyze the provided URLs",
        urls=urls,
        output_format=chat_req.output_format,
        use_local_llm=chat_req.use_local_llm
    )

    background_tasks.add_task(service.run_smart_scrape, request_id, scrape_req)

    return TaskResponse(
        task_id=request_id,
        status="processing",
        message="Chat analysis started - extracting URLs and processing query"
    )

@app.post("/api/search", response_model=TaskResponse, tags=["Search Mode"])
@limiter.limit("5/minute")
async def search_mode(
    request: Request,
    search_req: SearchRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """Search mode: Traditional web search with AI analysis"""
    request_id = str(uuid.uuid4())
    logger.info(f"Search Request {request_id} from {request.client.host}: {search_req.query}")

    # Create SmartScrapeRequest for search
    scrape_req = SmartScrapeRequest(
        query=search_req.query,
        urls=[],  # No specific URLs, let the system search
        output_format=search_req.output_format,
        use_local_llm=search_req.use_local_llm
    )

    background_tasks.add_task(service.run_smart_scrape, request_id, scrape_req)

    return TaskResponse(
        task_id=request_id,
        status="processing",
        message="Web search started - discovering and analyzing relevant content"
    )

@app.post("/api/analyze-urls", response_model=TaskResponse, tags=["URL Analysis Mode"])
@limiter.limit("5/minute")
async def analyze_urls_mode(
    request: Request,
    urls_req: AnalyzeUrlsRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """URL Analysis mode: Direct analysis of specified URLs"""
    request_id = str(uuid.uuid4())
    logger.info(f"URL Analysis Request {request_id} from {request.client.host}: {len(urls_req.urls)} URLs")

    # Create SmartScrapeRequest for URL analysis
    scrape_req = SmartScrapeRequest(
        query=urls_req.query or f"Analyze {len(urls_req.urls)} provided URLs",
        urls=urls_req.urls,
        output_format=urls_req.output_format,
        use_local_llm=urls_req.use_local_llm
    )

    background_tasks.add_task(service.run_smart_scrape, request_id, scrape_req)

    return TaskResponse(
        task_id=request_id,
        status="processing",
        message=f"URL analysis started - processing {len(urls_req.urls)} websites"
    )


# ============================================================================
# WEB SEARCH API - 11-Step Workflow
# ============================================================================

@app.post("/api/v1/websearch", response_model=TaskResponse, tags=["Web Search"])
@limiter.limit("5/minute")
async def websearch(
    request: Request,
    websearch_req: WebSearchRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    Comprehensive Web Search API following the 11-step workflow:
    
    1. **User Input** - Submit your research query
    2. **Web Search** - Fetch top 10-20 relevant results from search engines
    3. **Scraping** - Collect raw HTML content from each result
    4. **HTML Parsing** - Convert HTML to clean, structured text
    5. **AI Processing** - Analyze content using local Ollama LLM
    6. **Data Storage** - Store all sources in tabular format
    7. **Quality Selection** - Identify most reliable and relevant sources
    8. **Answer Generation** - Generate concise, high-quality answer
    9. **Source Attribution** - Include cited top sources
    10. **Schema Assembly** - Optional structured JSON/DB export
    11. **Transparency** - Full traceability of all scraped references
    
    Returns a task_id to poll for results via GET /api/v1/tasks/{task_id}
    """
    request_id = str(uuid.uuid4())
    logger.info(f"🔍 WebSearch Request {request_id} from {request.client.host}: {websearch_req.query}")

    background_tasks.add_task(service.run_websearch, request_id, websearch_req)

    return TaskResponse(
        task_id=request_id,
        status="processing",
        message=f"Web search started - fetching and analyzing {websearch_req.max_results} sources"
    )


# ============================================================================
# TARGETED SCRAPING API - 9-Step Workflow
# ============================================================================

@app.post("/api/v1/targeted-scrape", response_model=TaskResponse, tags=["Targeted Scraping"])
@limiter.limit("10/minute")
async def targeted_scrape(
    request: Request,
    scrape_req: TargetedScrapeRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    Targeted Scraping API following the 9-step workflow:
    
    1. **User Input** - Provide one or more website URLs
    2. **URL Validation** - Validate and prepare URLs for processing
    3. **Smart Scraping** - Intelligent strategy (lightweight first, advanced if needed)
    4. **Content Extraction** - Extract text, tables, lists, metadata
    5. **Format Detection** - Check if data is in clean, usable structure
    6. **LLM Assistance** - Use AI to normalize complex/inconsistent content
    7. **Multi-Source Handling** - Process all URLs independently, then consolidate
    8. **Structured Output** - Return well-defined JSON format
    9. **Response Delivery** - Deliver structured data for each URL
    
    Returns a task_id to poll for results via GET /api/v1/tasks/{task_id}
    """
    request_id = str(uuid.uuid4())
    logger.info(f"🎯 Targeted Scrape Request {request_id} from {request.client.host}: {len(scrape_req.urls)} URLs")

    background_tasks.add_task(service.run_targeted_scrape, request_id, scrape_req)

    return TaskResponse(
        task_id=request_id,
        status="processing",
        message=f"Targeted scraping started - processing {len(scrape_req.urls)} URL(s)"
    )


# ============================================================================
# CUSTOM WEB SCRAPE API - Advanced Prompt-Driven Extraction
# ============================================================================

@app.post("/api/v1/custom-scrape", response_model=TaskResponse, tags=["Custom Scrape"])
@limiter.limit("5/minute")
async def custom_scrape(
    request: Request,
    scrape_req: CustomScrapeRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    Advanced Custom Web Scrape API - The most powerful scraping endpoint.
    
    Designed for prompt-driven extraction from protected or dynamic websites.
    
    **Input:** A target URL + natural language instruction
    
    **Processing Flow:**
    1. **Input Understanding** - Parse URL and instruction, identify intent
    2. **Adaptive Scraping** - Lightweight first, escalate to stealth if needed
    3. **Anti-Bot Handling** - Browser fingerprints, behavior simulation, retries
    4. **Content Extraction** - Raw data → clean, structured text
    5. **LLM-Assisted Reasoning** - Interpret, rank, filter, transform results
    6. **Result Structuring** - JSON with answer, entities, confidence scores
    7. **Metadata & Provenance** - Source URLs, scrape method, timestamps
    
    Returns a task_id to poll for results via GET /api/v1/tasks/{task_id}
    """
    request_id = str(uuid.uuid4())
    logger.info(f"🔮 Custom Scrape Request {request_id} from {request.client.host}: {scrape_req.url}")
    logger.info(f"   Instruction: {scrape_req.instruction[:80]}...")

    background_tasks.add_task(service.run_custom_scrape, request_id, scrape_req)

    return TaskResponse(
        task_id=request_id,
        status="processing",
        message=f"Custom scraping started with instruction: {scrape_req.instruction[:50]}..."
    )


# ============================================================================
# SOURCE INTELLIGENCE API - Source Evaluation
# ============================================================================

@app.post("/api/v1/source-intelligence", response_model=TaskResponse, tags=["Source Intelligence"])
@limiter.limit("10/minute")
async def source_intelligence(
    request: Request,
    intel_req: SourceIntelligenceRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    Source Intelligence API - Evaluate source credibility + bias + freshness.
    
    Analyzes URLs for:
    - **Credibility Score** (0-100)
    - **Bias Indicator** (left, center, right)
    - **Freshness** (fresh, recent, outdated)
    - **Domain Authority**
    - **SSL Validation**
    """
    request_id = str(uuid.uuid4())
    logger.info(f"🔍 Source Intelligence {request_id}: {len(intel_req.urls)} URLs")
    background_tasks.add_task(service.run_source_intelligence, request_id, intel_req)
    return TaskResponse(task_id=request_id, status="processing", message=f"Evaluating {len(intel_req.urls)} sources")


# ============================================================================
# FACT-CHECK API - Verification
# ============================================================================

@app.post("/api/v1/fact-check", response_model=TaskResponse, tags=["Fact-Check"])
@limiter.limit("5/minute")
async def fact_check(
    request: Request,
    fact_req: FactCheckRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    Fact-Check API - Verify claims by searching multiple sources.
    
    Returns:
    - **Verdict** (true, false, partially_true, unverified, misleading)
    - **Confidence** (0-100)
    - **Evidence** from multiple sources
    - **Explanation** of the analysis
    """
    request_id = str(uuid.uuid4())
    logger.info(f"✓ Fact-Check {request_id}: {fact_req.claim[:60]}...")
    background_tasks.add_task(service.run_fact_check, request_id, fact_req)
    return TaskResponse(task_id=request_id, status="processing", message=f"Verifying claim...")


# ============================================================================
# KNOWLEDGE BASE API - Knowledge Store
# ============================================================================

@app.post("/api/v1/knowledge/add", response_model=TaskResponse, tags=["Knowledge Base"])
@limiter.limit("20/minute")
async def knowledge_add(
    request: Request,
    kb_req: KnowledgeBaseAddRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """Add a new entry to the knowledge base."""
    request_id = str(uuid.uuid4())
    logger.info(f"📚 Knowledge Add {request_id}: {kb_req.title}")
    background_tasks.add_task(service.run_knowledge_add, request_id, kb_req)
    return TaskResponse(task_id=request_id, status="processing", message=f"Adding '{kb_req.title}'")


@app.post("/api/v1/knowledge/search", response_model=TaskResponse, tags=["Knowledge Base"])
@limiter.limit("30/minute")
async def knowledge_search(
    request: Request,
    search_req: KnowledgeBaseSearchRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """Search the knowledge base."""
    request_id = str(uuid.uuid4())
    logger.info(f"🔍 Knowledge Search {request_id}: {search_req.query}")
    background_tasks.add_task(service.run_knowledge_search, request_id, search_req)
    return TaskResponse(task_id=request_id, status="processing", message=f"Searching for '{search_req.query}'")


# ============================================================================
# PLANNER API - Task Automation
# ============================================================================

@app.post("/api/v1/planner", response_model=TaskResponse, tags=["Planner"])
@limiter.limit("5/minute")
async def planner(
    request: Request,
    plan_req: PlannerRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    Planner API - Create and optionally execute research plans.
    
    Generates a step-by-step plan to achieve research objectives:
    - Search → Analyze → Scrape → Compare → Summarize
    
    Set `auto_execute: true` to run the plan automatically.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"📋 Planner {request_id}: {plan_req.objective[:60]}...")
    background_tasks.add_task(service.run_planner, request_id, plan_req)
    return TaskResponse(task_id=request_id, status="processing", message=f"Creating research plan...")


# ============================================================================
# MONITORING API - Change Alerts
# ============================================================================

@app.post("/api/v1/monitor/add", response_model=TaskResponse, tags=["Monitoring"])
@limiter.limit("10/minute")
async def monitor_add(
    request: Request,
    monitor_req: MonitoringAddRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    Monitoring API - Add a URL to watch for changes.
    
    Monitors for:
    - **Content changes**
    - **Price changes**
    - **New items**
    - **Keyword appearances**
    """
    request_id = str(uuid.uuid4())
    logger.info(f"👁️ Monitor Add {request_id}: {monitor_req.url}")
    background_tasks.add_task(service.run_monitoring_add, request_id, monitor_req)
    return TaskResponse(task_id=request_id, status="processing", message=f"Setting up monitoring for {monitor_req.url}")


@app.get("/api/v1/monitor/list", response_model=TaskResponse, tags=["Monitoring"])
@limiter.limit("30/minute")
async def monitor_list(
    request: Request,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """List all monitored URLs and recent alerts."""
    request_id = str(uuid.uuid4())
    background_tasks.add_task(service.run_monitoring_list, request_id)
    return TaskResponse(task_id=request_id, status="processing", message="Fetching monitors...")


@app.get("/api/v1/monitor/{monitor_id}/check", response_model=TaskResponse, tags=["Monitoring"])
@limiter.limit("10/minute")
async def monitor_check(
    request: Request,
    monitor_id: str,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """Check a specific monitor for changes."""
    request_id = str(uuid.uuid4())
    background_tasks.add_task(service.run_monitoring_check, request_id, monitor_id)
    return TaskResponse(task_id=request_id, status="processing", message="Checking for changes...")




