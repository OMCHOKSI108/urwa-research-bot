from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from datetime import datetime
import datetime as dt

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
    title="URWA Brain v3.5",
    description="""
# 🧠 Universal Research Web Agent (URWA Brain)

## AI-Powered Autonomous Research & Web Intelligence Platform

URWA Brain is an intelligent web scraping and research platform that combines the power of AI with advanced stealth techniques to extract structured intelligence from any website.

### 🎯 Key Features

* **Intent-Aware Agent** - Understands natural language and automatically routes requests
* **Ultra-Stealth Scraping** - Bypasses Cloudflare, bot detection, and CAPTCHA challenges
* **Deep Research Mode** - Multi-source web search with AI synthesis and citations
* **Local & Cloud AI** - Supports both Ollama (private) and Groq/Gemini (cloud)
* **Adaptive Learning** - Learns successful strategies per domain
* **Production-Grade** - Rate limiting, compliance checking, and evidence capture

### 🚀 Getting Started

1. **Unified Agent** - Use `/api/v1/agent` for any request (research, scrape, analyze)
2. **Research** - Use `/api/v1/research` for deep web research with citations
3. **Scraping** - Use `/api/v1/scrape` for direct URL extraction

### 📚 Documentation

* [GitHub Repository](https://github.com/OMCHOKSI108/urwa-brain)
* [Full Documentation](https://urwa-brain.docs.io)
* [CLI Guide](https://github.com/OMCHOKSI108/urwa-brain/tree/main/terminal)

### ⚖️ Legal Notice

This API is designed for ethical and legal web data collection. Users are responsible for compliance with applicable laws and website terms of service.
    """,
    version="3.5.0",
    terms_of_service="https://github.com/OMCHOKSI108/urwa-brain/blob/main/LICENSE",
    contact={
        "name": "URWA Team",
        "url": "https://github.com/OMCHOKSI108/urwa-brain",
        "email": "support@urwa-brain.dev"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Status",
            "description": "Health checks and system status endpoints"
        },
        {
            "name": "AI Agent",
            "description": "Unified AI agent that handles any request intelligently - research, scraping, or analysis"
        },
        {
            "name": "Research",
            "description": "Deep web research with multi-source search, AI synthesis, and citations"
        },
        {
            "name": "Scraping",
            "description": "Advanced web scraping with multi-level stealth strategies"
        },
        {
            "name": "Site Intelligence",
            "description": "Site profiling, protection detection, and compliance checking"
        },
        {
            "name": "Chat Mode",
            "description": "Natural language chat interface with intelligent URL detection"
        },
        {
            "name": "Search Mode",
            "description": "Traditional web search with AI-powered analysis"
        },
        {
            "name": "Analysis",
            "description": "Batch analysis and data quality assessment"
        },
        {
            "name": "System",
            "description": "System metrics, logs, and statistics"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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

@app.get(
    "/",
    tags=["Status"],
    summary="Root endpoint",
    response_description="System status and version info"
)
async def root():
    """
    **System Status**
    
    Returns the current status of the URWA Brain API.
    """
    return {
        "status": "URWA Brain Online",
        "version": "3.5.0",
        "ai_agent": "enabled",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get(
    "/health",
    tags=["Status"],
    summary="Health check",
    response_description="Health status"
)
async def health_check():
    """
    **Health Check Endpoint**
    
    Returns the health status of the API. Used by monitoring systems and load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# UNIFIED AI AGENT - ONE ENDPOINT FOR EVERYTHING
# ============================================================================

class AgentRequest(BaseModel):
    input: str
    use_ollama: bool = False
    llm_provider: str = "gemini"  # "gemini", "groq", or "ollama"
    model: str = "gemini-2.5-flash"

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
    - **llm_provider**: The LLM provider to use ("gemini", "groq", or "ollama")
    - **model**: The specific model to use
    
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
        # use_ollama is a simpler flag, but llm_provider gives more control
        use_local = body.use_ollama or body.llm_provider == "ollama"
        agent = ai_agent_ollama if use_local else ai_agent
        
        logger.info(f"Using LLM provider: {body.llm_provider}, model: {body.model}, use_ollama: {use_local}")
        
        result = await agent.process(body.input)
        result["llm_used"] = body.llm_provider if body.llm_provider else ("ollama" if use_local else "gemini/groq")
        result["model_used"] = body.model
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
    llm_provider: str = "gemini"  # "gemini", "groq", or "ollama"
    model: str = "gemini-2.5-flash"

@app.post(
    "/api/v1/research",
    tags=["Research"],
    summary="AI-powered deep research",
    response_description="Comprehensive research results with citations"
)
@limiter.limit("10/minute")
async def research_query(
    request: Request,
    body: ResearchChatRequest
):
    """
    **Perplexity-Style AI Research Chat**
    
    Takes a question, searches the web, scrapes sources, and returns
    a comprehensive AI-generated answer with citations.
    
    **Example Queries:**
    - "What are the current bitcoin market conditions?"
    - "Top 10 economies and their GDP"
    - "Latest AI trends in healthcare 2024"
    - "Compare Python vs JavaScript for backend development"
    
    **Response:**
    ```json
    {
        "status": "success",
        "answer": "Based on current market data...",
        "sources": [
            {"url": "https://...", "title": "..."}
        ],
        "follow_up_questions": ["What about Ethereum?"],
        "confidence": 0.85,
        "research_time": 5.2,
        "llm_used": "gemini"
    }
    ```
    
    **Parameters:**
    - **query**: Your research question (natural language)
    - **deep**: Enable deep research mode (scrapes more sources, slower but comprehensive)
    - **use_ollama**: Use local Ollama LLM instead of cloud Gemini/Groq
    - **llm_provider**: The LLM provider to use ("gemini", "groq", or "ollama")
    - **model**: The specific model to use
    
    **Rate Limit:** 10 requests per minute
    """
    try:
        # Choose LLM based on parameter
        use_local = body.use_ollama or body.llm_provider == "ollama"
        chat_service = research_chat_ollama if use_local else research_chat
        
        logger.info(f"Research using LLM provider: {body.llm_provider}, model: {body.model}, use_ollama: {use_local}")
        
        result = await chat_service.chat(body.query, deep_research=body.deep)
        return {
            "status": "success",
            "llm_used": body.llm_provider if body.llm_provider else ("ollama" if use_local else "gemini/groq"),
            "model_used": body.model,
            **result
        }
    except Exception as e:
        logger.error(f"Research error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "query": body.query
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


# ============================================================================
# DIRECT SCRAPE ENDPOINT
# ============================================================================

class ScrapeRequest(BaseModel):
    url: str
    instruction: str = None

@app.post("/api/v1/scrape", tags=["Scrape"])
@limiter.limit("20/minute")
async def direct_scrape(
    request: Request,
    body: ScrapeRequest
):
    """
    **Direct Web Scraping**
    
    Extract content from any URL using intelligent strategy selection.
    If 'instruction' is provided, uses AI to extract specific data.
    
    **Parameters:**
    - **url**: Target URL to scrape
    - **instruction**: Optional extraction instructions (e.g., "extract all prices")
    
    **Response:**
    ```json
    {
        "status": "success",
        "url": "https://...",
        "content": "Extracted content...",
        "extracted_data": { ... },
        "strategy_used": "lightweight|stealth|ultra_stealth",
        "execution_time": 2.3
    }
    ```
    """
    import time
    start_time = time.time()
    
    try:
        # 1. Scrape the content
        logger.info(f"Direct scraping: {body.url}")
        result = await scraper.scrape(body.url)
        
        # 2. Check if scraping failed
        if result.get("status") == "error" and not result.get("content"):
             return {
                "status": "error",
                "url": body.url,
                "message": result.get("error", "Failed to scrape URL"),
                "execution_time": round(time.time() - start_time, 2)
            }
            
        content = result.get("content", "")
        strategy = result.get("strategy", "auto")
        
        # 3. Process with AI if instruction is provided
        extracted_data = None
        if body.instruction and content and len(content) > 100:
            try:
                logger.info(f"Processing content with instruction: {body.instruction}")
                # Use synthesizer to extract structured data
                extraction_result = await processor.synthesize(
                    query=body.instruction,
                    all_contents=[content]
                )
                extracted_data = extraction_result
            except Exception as e:
                logger.error(f"AI Extraction failed: {e}")
                extracted_data = {"error": str(e)}

        execution_time = time.time() - start_time
        
        return {
            "status": "success",
            "url": body.url,
            "content": content,
            "content_length": len(content),
            "extracted_data": extracted_data,
            "strategy_used": strategy,
            "execution_time": round(execution_time, 2)
        }

    except Exception as e:
        logger.error(f"Scrape error: {e}")
        return {
            "status": "error",
            "url": body.url,
            "message": str(e)
        }


@app.get(
    "/api/v1/scraper-stats",
    tags=["System"],
    summary="Scraper performance statistics",
    response_description="Detailed scraping stats by strategy"
)
async def scraper_stats():
    """
    **Scraping Strategy Performance Statistics**
    
    Returns success rates and counts for each scraping strategy.
    
    **Strategies:**
    - **Lightweight HTTP**: Fast HTTP requests for static pages
    - **Playwright Stealth**: Browser-based scraping for JavaScript-rendered pages
    - **Ultra Stealth**: Maximum anti-bot bypass for heavily protected sites
    
    **Response:**
    ```json
    {
        "status": "success",
        "strategies": {
            "lightweight": {
                "name": "Lightweight HTTP",
                "success_count": 150,
                "success_rate": "85.5%"
            },
            "playwright": {
                "name": "Stealth Playwright",
                "success_count": 75,
                "success_rate": "68.2%"
            },
            "ultra_stealth": {
                "name": "Ultra Stealth Mode",
                "success_count": 30,
                "success_rate": "90.9%"
            }
        },
        "totals": {
            "total_requests": 300,
            "total_failures": 45,
            "overall_success_rate": "85.0%"
        },
        "protected_sites": ["linkedin.com", "facebook.com", ...]
    }
    ```
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


@app.post(
    "/api/v1/scraper-cache/clear",
    tags=["System"],
    summary="Clear scraper cache",
    response_description="Cache cleared confirmation"
)
async def clear_scraper_cache():
    """
    **Clear Scraper Cache & Reset Statistics**
    
    Clears the scraper cache and resets all statistics.
    Useful for testing or when you want fresh scrapes.
    
    **Use Cases:**
    - Testing strategy effectiveness
    - Forcing fresh content retrieval
    - Resetting statistics after configuration changes
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

@app.get(
    "/api/v1/strategy/profile-site",
    tags=["Site Intelligence"],
    summary="Profile website protection level",
    response_description="Site protection profile"
)
async def profile_site(url: str):
    """
    **Website Protection Profiler**
    
    Analyzes a website before scraping to detect protection mechanisms.
    
    **Detects:**
    - Bot protection (Cloudflare, Akamai, DataDome, PerimeterX)
    - JavaScript rendering requirements
    - CAPTCHA presence
    - Rate limiting strategies
    - Recommended scraping strategy
    
    **Example:**
    ```
    GET /api/v1/strategy/profile-site?url=https://linkedin.com
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "profile": {
            "domain": "linkedin.com",
            "protection_level": "extreme",
            "bot_detection": ["cloudflare", "captcha"],
            "requires_js": true,
            "recommended_strategy": "ultra_stealth",
            "estimated_success_rate": 0.75
        }
    }
    ```
    """
    profile = await site_profiler.profile(url)
    return {
        "status": "success",
        "profile": profile
    }


@app.get(
    "/api/v1/strategy/compliance-check",
    tags=["Site Intelligence"],
    summary="Check scraping compliance",
    response_description="Compliance check result"
)
async def check_compliance(url: str):
    """
    **Website Scraping Compliance Checker**
    
    Checks if a URL can be scraped compliantly according to website rules.
    
    **Checks:**
    - robots.txt rules
    - Crawl-delay requirements
    - Blacklist status
    - Terms of Service warnings
    
    **Example:**
    ```
    GET /api/v1/strategy/compliance-check?url=https://example.com
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "compliance": {
            "can_scrape": true,
            "robots_txt_allowed": true,
            "crawl_delay": 1,
            "blacklisted": false,
            "warnings": []
        }
    }
    ```
    """
    result = await compliance_checker.check(url)
    return {
        "status": "success",
        "compliance": result
    }


@app.get(
    "/api/v1/strategy/stats",
    tags=["System"],
    summary="Strategy statistics",
    response_description="Comprehensive strategy stats"
)
async def strategy_stats():
    """
    **Scraping Strategy Statistics**
    
    Get comprehensive statistics from all scraping strategies.
    
    **Includes:**
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

@app.post(
    "/api/v1/protected-scrape",
    tags=["Scraping"],
    summary="Scrape protected sites",
    response_description="Scraping result from protected site"
)
async def protected_scrape(url: str, instruction: str = None):
    """
    **Protected Site Scraper**
    
    Scrape heavily protected sites using site-specific strategies and bypass techniques.
    
    **Supported Sites:**
    - **LinkedIn**: via Google Cache, Bing, Web Archive
    - **Amazon**: via mobile URLs, search extraction
    - **Indeed**: via RSS feeds, Google Jobs API
    - **Twitter/X**: via oEmbed API
    - **Instagram**: via oEmbed API
    - **Facebook**: via oEmbed API
    
    **Parameters:**
    - **url**: The protected URL to scrape
    - **instruction**: Additional context (e.g., for Indeed: "software engineer")
    
    **Examples:**
    ```
    POST /api/v1/protected-scrape?url=https://linkedin.com/in/username
    POST /api/v1/protected-scrape?url=https://amazon.com/dp/B0BSHF7WHW
    POST /api/v1/protected-scrape?url=https://indeed.com&instruction=python developer remote
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "url": "https://...",
        "result": {
            "success": true,
            "data": {...},
            "method": "google_cache"
        }
    }
    ```
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


@app.get(
    "/api/v1/human-queue",
    tags=["Scraping"],
    summary="Get human intervention queue",
    response_description="List of tasks requiring human help"
)
async def get_human_queue():
    """
    **Human Intervention Queue**
    
    Get pending tasks requiring human intervention.
    
    **Task Types:**
    - CAPTCHA solving
    - Login requirements
    - Verification challenges
    - Two-factor authentication
    
    **Response:**
    ```json
    {
        "status": "success",
        "pending_tasks": [
            {
                "task_id": "abc123",
                "type": "captcha",
                "url": "https://...",
                "created_at": "2024-01-16T10:30:00Z"
            }
        ],
        "total_pending": 1
    }
    ```
    """
    from app.strategies.advanced_bypass import human_queue
    
    return {
        "status": "success",
        "pending_tasks": human_queue.get_pending_tasks(),
        "total_pending": len(human_queue.get_pending_tasks())
    }


@app.post(
    "/api/v1/human-queue/{task_id}/complete",
    tags=["Scraping"],
    summary="Complete human intervention task",
    response_description="Task completion status"
)
async def complete_human_task(task_id: str, result: dict):
    """
    **Complete Human Intervention Task**
    
    Provide solution for a human queue task.
    
    **Result Format:**
    - For CAPTCHA: `{"captcha_solution": "answer"}`
    - For Login: `{"cookies": {...}, "session_token": "..."}`
    - For 2FA: `{"verification_code": "123456"}`
    
    **Example:**
    ```
    POST /api/v1/human-queue/abc123/complete
    Body: {"captcha_solution": "XJKL8P"}
    ```
    """
    from app.strategies.advanced_bypass import human_queue
    
    success = human_queue.complete_task(task_id, result)
    
    return {
        "status": "success" if success else "not_found",
        "task_id": task_id
    }


@app.get(
    "/api/v1/browser-profiles",
    tags=["Scraping"],
    summary="List browser profiles",
    response_description="List of persistent browser profiles"
)
async def list_browser_profiles():
    """
    **Browser Profile Manager**
    
    List all persistent browser profiles.
    
    **Profiles Maintain:**
    - Cookies across sessions
    - Consistent fingerprints
    - Site visit history
    - LocalStorage/SessionStorage data
    
    **Response:**
    ```json
    {
        "status": "success",
        "profiles": [
            {
                "name": "default",
                "fingerprint": {...},
                "created_at": "2024-01-10T08:00:00Z"
            }
        ],
        "total": 1
    }
    ```
    """
    from app.strategies.browser_profiles import profile_manager
    
    return {
        "status": "success",
        "profiles": profile_manager.list_profiles(),
        "total": len(profile_manager.profiles)
    }


@app.post(
    "/api/v1/browser-profiles/create",
    tags=["Scraping"],
    summary="Create new browser profile",
    response_description="Created profile details"
)
async def create_browser_profile(name: str = None):
    """
    **Create New Browser Profile**
    
    Generate a new browser profile with unique fingerprint.
    
    **Use Cases:**
    - Multiple identities for different sites
    - Avoiding detection through profile rotation
    - Persistent sessions across scraping runs
    
    **Example:**
    ```
    POST /api/v1/browser-profiles/create?name=amazon_scraper
    ```
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


@app.get(
    "/api/v1/captcha-stats",
    tags=["System"],
    summary="CAPTCHA solving statistics",
    response_description="CAPTCHA solver stats"
)
async def get_captcha_stats():
    """
    **CAPTCHA Solving Statistics**
    
    Get statistics on CAPTCHA encounters and solving success.
    """
    from app.strategies.advanced_bypass import captcha_solver
    
    return {
        "status": "success",
        "stats": captcha_solver.get_stats()
    }


@app.get(
    "/api/v1/proxy-stats",
    tags=["System"],
    summary="Proxy intelligence statistics",
    response_description="Proxy usage stats"
)
async def get_proxy_stats():
    """
    **Proxy Intelligence Statistics**
    
    Get proxy rotation and intelligence statistics.
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

@app.post(
    "/api/v1/smart_scrape",
    response_model=TaskResponse,
    tags=["Scraping"],
    summary="Intelligent research scraper",
    response_description="Background task started"
)
@limiter.limit("5/minute")
async def smart_scrape(
    request: Request,
    scrape_req: SmartScrapeRequest, 
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    **Intelligent Research Scraper**
    
    Smart scraping with research capabilities. Combines web search, URL scraping,
    and AI analysis to answer complex research questions.
    
    **Features:**
    - Automatic web search if URLs not provided
    - Multi-strategy scraping (lightweight → stealth → ultra-stealth)
    - AI-powered data extraction and analysis
    - Support for multiple output formats
    
    **Request Body:**
    ```json
    {
        "query": "What are the top JavaScript frameworks in 2024?",
        "urls": [],  // Optional: provide specific URLs or let it search
        "output_format": "json",  // json | markdown | csv
        "use_local_llm": false  // Use Ollama instead of Gemini/Groq
    }
    ```
    
    **Response:**
    ```json
    {
        "task_id": "abc-123-def",
        "status": "processing",
        "message": "Research task started in background"
    }
    ```
    
    **Poll Status:**
    ```
    GET /api/v1/tasks/{task_id}
    ```
    
    **Rate Limit:** 5 requests per minute
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Queuing Request {request_id} from {request.client.host}: {scrape_req.query}")
    
    background_tasks.add_task(service.run_smart_scrape, request_id, scrape_req)
    
    return TaskResponse(
        task_id=request_id,
        status="processing",
        message="Research task started in background"
    )

@app.get(
    "/api/v1/tasks/{task_id}",
    tags=["Status"],
    summary="Get task status",
    response_description="Task status and results"
)
@limiter.limit("60/minute")
async def get_task_status(
    request: Request,
    task_id: str
):
    """
    **Poll Task Status**
    
    Check the status and retrieve results of a background task.
    
    **Task States:**
    - `processing`: Task is running
    - `completed`: Task finished successfully
    - `failed`: Task encountered an error
    
    **Example:**
    ```
    GET /api/v1/tasks/abc-123-def
    ```
    
    **Response (Processing):**
    ```json
    {
        "task_id": "abc-123-def",
        "status": "processing",
        "progress": 45,
        "message": "Scraping 2 of 5 URLs..."
    }
    ```
    
    **Response (Completed):**
    ```json
    {
        "task_id": "abc-123-def",
        "status": "completed",
        "result": {
            "answer": "...",
            "sources": [...],
            "export_url": "/exports/abc-123-def.json"
        }
    }
    ```
    
    **Rate Limit:** 60 requests per minute
    """
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

@app.post(
    "/api/chat",
    response_model=TaskResponse,
    tags=["Chat Mode"],
    summary="Intelligent chat interface",
    response_description="Task started in background"
)
@limiter.limit("5/minute")
async def chat_mode(
    request: Request,
    chat_req: ChatRequest,
    background_tasks: BackgroundTasks,
    service: OrchestratorService = Depends(get_orchestrator)
):
    """
    **Intelligent Natural Language Chat Interface**
    
    Uses the Unified Agent to intelligently process your message. Automatically determines
    whether to scrape URLs, do research, or answer questions directly.
    
    **How It Works:**
    - **URL Scraping**: Only scrapes when you explicitly request it with keywords like:
      - "scrape https://example.com"
      - "extract data from https://example.com"
      - "analyze these sites: https://..."
      - "get data from https://..."
      
    - **Research Mode**: For questions that mention URLs without scraping intent:
      - "What is the latest on example.com?" → Research, don't scrape
      - "Tell me about example.com features" → Research, don't scrape
      
    - **Direct Questions**: For general questions without URLs:
      - "What is Python?" → Direct answer
      - "How does photosynthesis work?" → Research if needed
    
    **Example Messages:**
    ```
    # Scraping (explicit):
    "scrape https://news.ycombinator.com and summarize top stories"
    
    # Research (implicit):
    "what are the top stories on hackernews today?"
    
    # Question:
    "compare python vs javascript"
    ```
    
    **Rate Limit:** 5 requests per minute
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Chat Request {request_id} from {request.client.host}: {chat_req.message[:100]}...")

    # Check if user explicitly wants to scrape/extract
    import re
    scrape_keywords = ['scrape', 'extract', 'get data from', 'analyze these sites', 'pull from']
    wants_scraping = any(keyword in chat_req.message.lower() for keyword in scrape_keywords)
    
    # Only extract and scrape URLs if user explicitly wants scraping
    if wants_scraping:
        urls = re.findall(r'https?://[^\s,]+', chat_req.message)
        query = re.sub(r'https?://[^\s,]+', '', chat_req.message).strip()
        
        if urls:
            # User wants to scrape specific URLs
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
                message=f"Scraping {len(urls)} URL(s) and analyzing content"
            )
    
    # Otherwise, treat as research question (don't scrape mentioned URLs)
    scrape_req = SmartScrapeRequest(
        query=chat_req.message,
        urls=[],  # No URLs to scrape - just research
        output_format=chat_req.output_format,
        use_local_llm=chat_req.use_local_llm
    )
    
    background_tasks.add_task(service.run_smart_scrape, request_id, scrape_req)
    
    return TaskResponse(
        task_id=request_id,
        status="processing",
        message="Researching your question (URLs mentioned but not scraped)"
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




