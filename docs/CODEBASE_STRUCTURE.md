# 🧠 URWA Brain - Codebase Structure Overview

> **Last Updated:** January 17, 2026  
> **Version:** 3.5.0  
> **Purpose:** Complete architectural guide for developers

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Directory Structure](#directory-structure)
4. [Backend Architecture](#backend-architecture)
5. [Terminal CLI Architecture](#terminal-cli-architecture)
6. [Key Components Deep Dive](#key-components-deep-dive)
7. [Data Flow](#data-flow)
8. [API Endpoints Summary](#api-endpoints-summary)
9. [Technology Stack](#technology-stack)
10. [Development Workflow](#development-workflow)

---

## 🎯 Project Overview

**URWA Brain** is an **agentic AI-powered web intelligence platform** that combines:

- **Intelligent Intent Classification** - Understands what users want
- **Multi-Strategy Web Scraping** - Adapts to site protection levels
- **Deep Research Capabilities** - Perplexity-style research with citations
- **Adaptive Learning** - Improves scraping strategies based on success/failure
- **Production-Ready Infrastructure** - Metrics, circuit breakers, health checks

### Core Philosophy

**NOT just a scraper** → An autonomous research system that decides *how* to solve tasks.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACES                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │   CLI    │  │ REST API │  │ Frontend (deprecated)   │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬──────────────┘  │
└───────┼────────────┼────────────────────┼─────────────────┘
        │            │                    │
        └────────────┴────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   FastAPI Backend       │
        │   (app/main.py)         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────────────────────┐
        │        UNIFIED AGENT CORE                   │
        │  (services/unified_agent.py)                │
        │  - Intent Classification                    │
        │  - Tool Selection                           │
        │  - Execution Orchestration                  │
        └────────────┬────────────────────────────────┘
                     │
        ┌────────────┴──────────────┬──────────────┐
        │                           │              │
┌───────▼────────┐     ┌───────────▼──────┐  ┌───▼─────────┐
│ Research Engine│     │ Scraping Engine  │  │  Profiler   │
│ (research_chat)│     │ (orchestrator)   │  │   Engine    │
└───────┬────────┘     └───────────┬──────┘  └───┬─────────┘
        │                          │              │
        └──────────────┬───────────┴──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │    LLM Processing Layer     │
        │  - Ollama (Local/Privacy)   │
        │  - Groq (Cloud/Speed)       │
        │  - Gemini (Cloud/Quality)   │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │   Structured Intelligence   │
        │   JSON • CSV • PDF • API    │
        └─────────────────────────────┘
```

---

## 📁 Directory Structure

```
urwa-brain/
├── backend/                      # FastAPI backend application
│   ├── app/
│   │   ├── agents/              # Scraper implementations
│   │   │   ├── hybrid_scraper.py          # Main orchestrator (routes to strategies)
│   │   │   ├── lightweight_scraper.py     # Level 1: Simple HTTP scraping
│   │   │   ├── scraper.py                 # Level 2: Stealth Playwright
│   │   │   ├── ultra_stealth_scraper.py   # Level 3: Maximum stealth
│   │   │   ├── llm_processor.py           # Cloud LLM (Groq/Gemini)
│   │   │   └── ollama_processor.py        # Local LLM (Ollama)
│   │   │
│   │   ├── core/                # Production infrastructure
│   │   │   ├── production_infra.py        # Metrics, circuits, health
│   │   │   └── data_quality.py            # Normalization, extractors
│   │   │
│   │   ├── services/            # Business logic orchestration
│   │   │   ├── unified_agent.py           # Main AI agent (intent → action)
│   │   │   ├── research_chat.py           # Perplexity-style research
│   │   │   └── orchestrator.py            # Complex workflows (128KB!)
│   │   │
│   │   ├── strategies/          # Intelligent scraping strategies
│   │   │   ├── site_profiler.py           # Detect protection level
│   │   │   ├── adaptive_learning.py       # Learn from success/failure
│   │   │   ├── intelligent_retry.py       # Smart retry with backoff
│   │   │   ├── rate_control.py            # Rate limiting per domain
│   │   │   ├── compliance.py              # robots.txt / ToS checker
│   │   │   ├── semantic_extractor.py      # LLM-based extraction
│   │   │   ├── advanced_bypass.py         # CAPTCHA, fingerprint evasion
│   │   │   ├── site_specific.py           # LinkedIn, Amazon, etc.
│   │   │   ├── browser_profiles.py        # Persistent sessions
│   │   │   ├── evidence_capture.py        # Screenshots, HAR files
│   │   │   └── stealth_techniques.py      # Anti-detection tricks
│   │   │
│   │   ├── models/              # Pydantic request/response models
│   │   ├── utils/               # Helper utilities
│   │   ├── static/              # Static files, exports, sessions
│   │   └── main.py              # FastAPI app definition (1801 lines!)
│   │
│   ├── requirements.txt         # Python dependencies
│   ├── run.py                   # Server startup script
│   └── .env                     # Environment configuration
│
├── terminal/                    # CLI Interface
│   ├── cli.py                   # Main CLI (1640 lines!)
│   ├── handlers.py              # Strategy stats, settings handlers
│   ├── planner_logic.py         # Automated research planner
│   └── README.md                # CLI documentation
│
├── docs/                        # Documentation (MkDocs)
│   ├── getting-started/
│   ├── api/
│   ├── architecture/
│   ├── guides/
│   ├── logs/                    # CLI execution logs saved here
│   ├── PROJECT_INFO.txt         # Comprehensive API list
│   └── index.md
│
├── frontend/                    # Web UI (deprecated, use CLI)
├── urwa / urwa.cmd             # CLI launcher scripts
├── README.md                    # Main project README
├── docker-compose.yml           # Docker orchestration
└── mkdocs.yml                   # Documentation config
```

---

## 🔧 Backend Architecture

### Core Components

#### 1. **FastAPI Application** (`app/main.py`)
- **1801 lines** of production-grade API code
- **50+ endpoints** across 8 categories
- Rate limiting, CORS, logging, error handling
- OpenAPI/Swagger documentation

#### 2. **Unified Agent** (`services/unified_agent.py`)
The **heart of URWA Brain** - a single AI agent that:

```python
class UnifiedAgent:
    def process(user_input: str) -> Dict:
        """
        1. Classify intent (research, scrape, analyze, compare, etc.)
        2. Extract parameters (URLs, keywords, depth)
        3. Execute appropriate action
        4. Return comprehensive result
        """
```

**Intents Handled:**
- `research` - Deep web research with citations
- `scrape` - Extract data from URLs
- `profile` - Analyze site protection
- `compare` - Compare multiple sources
- `fact_check` - Verify claims
- `explain` - Educational queries
- `status` - System health

#### 3. **Orchestrator Service** (`services/orchestrator.py`)
- **2618 lines** - the largest file in the codebase
- Handles complex multi-step workflows
- Multi-engine search (DuckDuckGo, Bing, Brave, Google, Yahoo)
- SSRF protection, validation, session management

**Key Methods:**
```python
run_smart_scrape()       # AI-powered research with query
run_websearch()          # 11-step comprehensive search
run_targeted_scrape()    # 9-step URL scraping
run_custom_scrape()      # 7-step prompt-driven extraction
```

#### 4. **Research Chat** (`services/research_chat.py`)
Perplexity-style research engine:
- Web search → Scrape sources → Synthesize with LLM
- Returns answer + citations + follow-ups
- Deep mode for comprehensive analysis

### Scraping Architecture

**Three-Level Strategy System:**

| Level | File | Mode | Use Case | Success Rate |
|-------|------|------|----------|--------------|
| 1 | `lightweight_scraper.py` | HTTP requests | Blogs, docs, simple sites | ~60% |
| 2 | `scraper.py` | Playwright stealth | Protected sites | ~85% |
| 3 | `ultra_stealth_scraper.py` | Maximum evasion | Heavy bot walls (Cloudflare) | ~95% |

**Hybrid Scraper** (`agents/hybrid_scraper.py`):
- Automatically escalates if strategy fails
- Site profiler detects protection level
- Adaptive learning improves over time

### Strategy Intelligence

Located in `strategies/`:

1. **Site Profiler** - Detects Cloudflare, reCAPTCHA, rate limits
2. **Adaptive Learning** - Remembers best strategy per domain
3. **Intelligent Retry** - Exponential backoff with jitter
4. **Rate Control** - Per-domain rate limiting
5. **Compliance** - Checks robots.txt and ToS
6. **Semantic Extractor** - LLM-based data extraction when CSS fails
7. **Advanced Bypass** - CAPTCHA solving, fingerprint randomization
8. **Site Specific** - Custom logic for LinkedIn, Amazon, etc.

### LLM Processing

**Two processors for flexibility:**

```python
# Cloud LLMs (Fast, powerful)
llm_processor.py:
  - Groq API (llama3-70b-8192)
  - Google Gemini (gemini-1.5-flash)

# Local LLM (Private, free)
ollama_processor.py:
  - Ollama (phi3:mini)
  - Runs on localhost:11434
```

### Production Infrastructure (`core/`)

**Production Infra** (`production_infra.py`):
- Prometheus metrics
- Circuit breakers (prevent cascading failures)
- Health checks with self-healing
- Cost tracking and limits

**Data Quality** (`data_quality.py`):
- Normalization (prices, dates, locations)
- Versioned extractors (rollback support)
- Confidence scoring

---

## 🖥️ Terminal CLI Architecture

**Files:**
- `cli.py` - 1640 lines, main CLI logic
- `handlers.py` - Strategy stats, settings, interactive AI
- `planner_logic.py` - Automated research planner

### CLI Features

**8 Main Modes:**

```
1. 🤖 Master AI        → Unified agent (handles everything)
2. 💬 Chat/Research    → Quick research queries
3. 🔬 Deep Research    → Comprehensive analysis
4. 🌐 URL Scraper      → Extract from specific URLs
5. 🔍 Site Analyzer    → Protection detection
6. 📊 System Status    → Health + metrics
7. 📈 Strategy Stats   → Learning insights
8. ⚙️  Settings        → Toggle Ollama/Cloud AI
```

### Key Functions

```python
check_api_server()              # Auto-check backend status
start_backend()                 # Launch backend in new window
master_ai_handler(query)        # Route to unified agent
deep_research_handler(query)    # Full research workflow
site_analyzer_handler(url)      # Profile site protection
strategy_stats_handler()        # Display learning data
interactive_master_ai()         # Continuous conversation loop
```

### Planner Logic (`planner_logic.py`)

Automated research planner that breaks complex goals into steps:

```python
class ResearchPlanner:
    create_plan(goal)    # Generate 3-phase plan
    display_plan()       # Rich table visualization
    execute_plan(callbacks)  # Run steps sequentially
```

**Phases:**
1. **Discovery** - Multi-engine search
2. **Deep Scanning** - Scrape 5-20 sources
3. **Analysis** - Synthesize with LLM

---

## 🔑 Key Components Deep Dive

### 1. Intent Classification (`unified_agent.py`)

**Pattern-based + LLM fallback:**

```python
def _classify_intent(user_input: str) -> str:
    # Pattern matching
    if "research" in input or "tell me about":
        return "research"
    if url_pattern.match(input):
        return "scrape"
    if "can i scrape" or "protection":
        return "profile"
    
    # LLM fallback for ambiguous cases
    return llm_classify(input)
```

### 2. Multi-Engine Search (`orchestrator.py`)

**5 search engines with fallback:**

```python
async def perform_search_multi_engine(query, max_results=5):
    # Try in order
    1. DuckDuckGo (duckduckgo_search library)
    2. Bing (ultra-stealth scraping)
    3. Brave (lightweight scraping)
    4. Google (googlesearch-python)
    5. Yahoo (ultra-stealth scraping)
    
    # Return first successful results
```

### 3. Adaptive Learning (`strategies/adaptive_learning.py`)

**Strategy success tracking:**

```python
class AdaptiveLearning:
    domain_strategies = {}  # domain → {strategy: success_rate}
    
    def record_success(domain, strategy):
        # Update success rate
        # Recommend best strategy next time
    
    def get_best_strategy(domain):
        # Return highest success rate strategy
```

### 4. Site Profiling (`strategies/site_profiler.py`)

**Protection detection:**

```python
async def profile_site(url):
    checks = {
        "cloudflare": check_cloudflare(),
        "recaptcha": check_recaptcha(),
        "rate_limit": check_rate_limit(),
        "login_required": check_login(),
        "javascript_heavy": check_js(),
    }
    return ProtectionLevel(1-3)
```

---

## 🔄 Data Flow

### Example: Research Query

```
User: "What are the latest AI trends in 2024?"
  ↓
CLI (cli.py) → POST /api/v1/agent
  ↓
FastAPI (main.py) → unified_agent.process()
  ↓
UnifiedAgent classifies intent: "research"
  ↓
Executes: research_chat.research(query, deep=False)
  ↓
ResearchChat:
  1. Multi-engine search → 10 URLs
  2. Scrape top 5 sources (hybrid scraper)
  3. Extract content (HTML parser)
  4. Synthesize with LLM (Groq/Gemini)
  5. Generate citations
  ↓
Return to CLI:
  - Markdown answer
  - Source list with titles
  - Follow-up suggestions
```

### Example: URL Scraping

```
User: "https://news.ycombinator.com"
  ↓
UnifiedAgent classifies intent: "scrape"
  ↓
Executes: orchestrator.run_custom_scrape()
  ↓
HybridScraper:
  1. SiteProfiler → Protection Level = 1
  2. Try lightweight_scraper (HTTP)
  3. Success! Extract content
  4. AdaptiveLearning.record_success("news.ycombinator.com", "lightweight")
  ↓
SemanticExtractor (LLM):
  - Extract structured data from HTML
  ↓
Return: {title, content, headlines, metadata}
```

---

## 📡 API Endpoints Summary

**Total: 50+ endpoints across 8 categories**

### Primary Endpoints (Most Used)

```http
POST /api/v1/agent              # Unified AI agent (MAIN)
POST /api/v1/research           # Perplexity-style research
POST /api/v1/smart_scrape       # AI-powered scraping
POST /api/v1/custom_scrape      # Prompt-driven extraction
GET  /api/v1/strategy/stats     # Strategy learning data
GET  /health                    # Quick health check
```

### Categories

1. **AI Agent** (3) - Unified agent, history, clear
2. **Research Chat** (3) - Research, history, clear
3. **Health & Status** (3) - Root, health, task polling
4. **Core Scraping** (7) - Smart scrape, search, analyze, websearch, targeted, custom
5. **Strategy Engine** (5) - Profile, compliance, stats, learning, clear
6. **Advanced Bypass** (7) - Protected scrape, human queue, browser profiles, CAPTCHA stats
7. **System/Production** (10) - Metrics, circuits, health, cost, extractors, logs, normalize
8. **Intelligence** (5) - Fact check, source intelligence, knowledge base, planner

See `docs/PROJECT_INFO.txt` for complete API documentation.

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI (async, fast, OpenAPI auto-docs)
- **Scraping:** Playwright (browser automation), BeautifulSoup4, aiohttp
- **LLM:** Groq API, Google Gemini, Ollama (local)
- **Search:** DuckDuckGo Search, Google Search (no API), manual scraping (Bing, Yahoo, Brave)
- **Data:** Pandas (CSV), FPDF2 (PDF), JSON
- **Monitoring:** Loguru (structured logs), psutil (metrics), custom Prometheus metrics
- **Production:** Circuit breakers, health checks, rate limiting (slowapi)

### CLI
- **Rich** - Beautiful terminal UI (tables, panels, spinners, markdown)
- **aiohttp** - Async HTTP client
- **asyncio** - Async execution

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **MkDocs** - Documentation site generator

---

## 🧑‍💻 Development Workflow

### Setup

```bash
# Clone repo
git clone https://github.com/OMCHOKSI108/urwa-brain.git
cd urwa-brain

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running

```bash
# Method 1: CLI launcher (recommended)
urwa sans start  # Windows: urwa.cmd sans start

# Method 2: Manual
cd backend
python run.py
```

### Testing

```bash
# Run tests
pytest

# Test specific API
curl -X POST "http://localhost:8000/api/v1/agent" \
  -H "Content-Type: application/json" \
  -d '{"input": "What is AI?", "use_ollama": false}'
```

### Logs Location

```
docs/logs/                  # CLI execution logs
backend/app/static/exports/ # Exported files (CSV, PDF)
backend/app/static/sessions/# Session data
```

---

## 📊 Code Statistics

| Component | File | Lines | Bytes | Complexity |
|-----------|------|-------|-------|------------|
| Main API | `app/main.py` | 1,801 | 59KB | High |
| Orchestrator | `services/orchestrator.py` | 2,618 | 128KB | Very High |
| CLI | `terminal/cli.py` | 1,640 | 68KB | High |
| Unified Agent | `services/unified_agent.py` | 662 | 30KB | Medium |
| Ultra Stealth | `agents/ultra_stealth_scraper.py` | 37,157 | 37KB | High |

**Total Backend:** ~89 files, ~200KB of Python code

---

## 🎯 Key Design Patterns

1. **Factory Pattern** - `get_unified_agent()`, `get_orchestrator()`
2. **Strategy Pattern** - Scraping strategies (Lightweight, Stealth, Ultra-Stealth)
3. **Adapter Pattern** - LLM processors (Ollama, Groq, Gemini)
4. **Circuit Breaker** - Prevent cascading failures
5. **Observer Pattern** - Adaptive learning from scraping outcomes
6. **Facade Pattern** - Unified Agent abstracts complexity

---

## 🚀 Future Enhancements (Roadmap)

From `README.md`:

- [ ] RAG memory store
- [ ] Workflow automation
- [ ] Browser extension
- [ ] Multi-agent collaboration
- [ ] Cloud deployment templates

---

## 📚 Additional Resources

- **Main README:** `/README.md`
- **API Docs:** `http://localhost:8000/docs`
- **Project Info:** `/docs/PROJECT_INFO.txt`
- **CLI Guide:** `/terminal/README.md`
- **Docker Guide:** `/docs/DOCKER.md`

---

## 🤝 Contributing

Key files to understand before contributing:

1. `app/main.py` - API endpoint definitions
2. `services/unified_agent.py` - Intent classification logic
3. `services/orchestrator.py` - Complex workflow orchestration
4. `strategies/` - Scraping intelligence
5. `terminal/cli.py` - CLI interface

**Architecture principle:** Keep the Unified Agent as the single entry point, delegate to specialized services.

---

## 📝 Notes

- **Duplicate code detected:** `cli.py` has duplicate `site_analyzer_handler()` and `interactive_mode()` functions (lines 862-985 and 1410-1518). Consider refactoring.
- **Large files:** `orchestrator.py` (128KB) could be split into smaller modules for better maintainability.
- **Deprecated:** `frontend/` directory exists but is no longer maintained. CLI is the primary interface.

---

**Built for Speed. Engineered for Stealth. Designed for Intelligence.**

*URWA Brain v3.5.0 - Production-Grade AI Web Intelligence Platform*
