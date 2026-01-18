
<div align="center">

╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                          URWA BRAIN v3.5                             ║
║               AI-Powered Autonomous Research Engine                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-000000?style=for-the-badge&logo=ollama&logoColor=white)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-MkDocs-blue.svg)](docs/index.md)

**URWA Brain is an intelligent autonomous research and scraping engine that understands intent, adapts its strategy, and delivers structured intelligence — not raw HTML.**

[Quick Start](#quick-start) • [Docs](docs/index.md) • [API](http://localhost:8000/docs) • [CLI](terminal/README.md)

</div>

---

# What Makes URWA Different?

URWA Brain is **not just a scraper**.  
It is an **agentic research system** that decides *how* to solve a task.

### Core Capabilities

- **Intent-Aware Agent** – understands whether you want to research, scrape, analyze, or compare
- **Ultra-Stealth Scraping** – bypasses Cloudflare & bot detection safely
- **Deep Research Mode** – multi-source search + AI synthesis + citations
- **Local & Cloud AI** – Ollama for privacy, Groq/Gemini for speed
- **Strategy Learning** – adapts scraping method per domain
- **CLI + REST API** – terminal-first + production-ready backend

---

# Quick Start

### One Command

**Windows**
```powershell
urwa sans start

```

**Linux / macOS**

```bash
./urwa sans start

```

Starts:

* FastAPI backend
* Interactive CLI
* Strategy learning engine

---

# Try It

```bash
urwa research "Latest AI agent frameworks"
urwa scrape [https://example.com](https://example.com)
urwa profile [https://amazon.com](https://amazon.com)

```

---

# Screenshots & Demo

## Terminal Interface

<div align="center">
  <img src="docs/terminal.png" alt="URWA Brain Terminal Interface" width="800"/>
  <p><em>Professional CLI with Master AI mode, research capabilities, and real-time status</em></p>
</div>

## Frontend Dashboard

<div align="center">
  <img src="docs/frontend_ui_dashboard.png" alt="Frontend Dashboard" width="800"/>
  <p><em>Modern web interface with system metrics, agent console, and monitoring</em></p>
</div>

## System Monitoring

<div align="center">
  <img src="docs/system_monitor.png" alt="System Health Monitor" width="800"/>
  <p><em>Real-time system health, circuit breakers, and performance metrics</em></p>
</div>

## API Documentation

<div align="center">
  <img src="docs/fastapi.png" alt="FastAPI Swagger Documentation" width="800"/>
  <p><em>Interactive API documentation with Swagger UI</em></p>
</div>

<div align="center">
  <img src="docs/redoc.png" alt="ReDoc API Documentation" width="800"/>
  <p><em>Beautiful API documentation with ReDoc</em></p>
</div>

---

# Architecture (High Level)

```mermaid
flowchart TD
    User --> UI[CLI / API / Frontend]
    UI --> Router{Unified Agent Router}
    
    Router -- Research --> RE[Research Engine]
    Router -- Scrape --> SE[Scraper Engine]
    Router -- Profile --> PE[Profiler Engine]

    RE & SE & PE --> LLM[LLM Processing Layer\nOllama / Groq / Gemini]
    
    LLM --> Out[Structured Intelligence\nJSON • CSV • PDF • API]

```

---

# Installation

## Prerequisites

* Python 3.11+
* 4GB RAM minimum
* Git

## Setup

```bash
git clone [https://github.com/OMCHOKSI108/urwa-brain.git](https://github.com/OMCHOKSI108/urwa-brain.git)
cd urwa-brain

python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

cd backend
pip install -r requirements.txt
playwright install chromium

```

### Optional: Local AI

```bash
ollama pull phi3:mini

```

---

# Configuration

Create `backend/.env`

```env
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini

PORT=8000
RATE_LIMIT=20/minute
MAX_RETRIES=3

```

---

# Three-Level Scraping Strategy

| Level | Mode | Use Case | Success Rate |
| --- | --- | --- | --- |
| 1 | Lightweight | Blogs, docs | ~60% |
| 2 | Stealth | Protected sites | ~85% |
| 3 | Ultra-Stealth | Heavy bot walls | ~95% |

URWA **automatically escalates** if a strategy fails.

---

# API Overview

Base URL → `http://localhost:8000`

## Unified Agent

```http
POST /api/v1/agent

```

```json
{
  "input": "Compare iPhone 15 prices on Amazon and Apple",
  "use_ollama": true
}

```

### Response

```json
{
  "status": "success",
  "intent": "scrape",
  "confidence": 0.95,
  "action_taken": "Ultra-stealth scraping",
  "result": {
    "amazon_price": "$1199",
    "apple_price": "$1199"
  }
}

```

---

# Core Endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/v1/agent` | POST | Unified AI agent |
| `/api/v1/research` | POST | Deep research |
| `/api/v1/scrape` | POST | Direct scraping |
| `/api/v1/profile` | GET | Site protection |
| `/api/v1/stats` | GET | System metrics |
| `/docs` | GET | Swagger UI |

---

# CLI Power Features

```bash
urwa stats
urwa logs --tail
urwa research "AI regulation" --export pdf
urwa scrape [https://site.com](https://site.com) --export json

```

---

# System Architecture

```mermaid
flowchart TD
    UI[CLI / API / Web UI] --> AG[Unified Agent Core]

    AG --> RE[Research Engine]
    AG --> SE[Scraping Engine]
    AG --> PE[Profiling Engine]

    subgraph Strategies
        SE --> LW[Lightweight]
        SE --> ST[Stealth]
        SE --> US[Ultra Stealth]
    end

    RE --> SRCH[Search + Synthesis]
    PE --> BOT[Bot + Risk Scan]

    LW & ST & US --> SL[Strategy Learning]
    SL --> SE

    RE & SE & PE --> LLM[LLM Layer\nOllama / Groq / Gemini]

    LLM --> OUT[Structured Intelligence]
    OUT --> FILES[JSON / CSV / PDF]
    OUT --> API_OUT[API Response]

```

---

# Roadmap

* [ ] RAG memory store
* [ ] Workflow automation
* [ ] Browser extension
* [ ] Multi-agent collaboration
* [ ] Cloud deployment templates

---

# License

MIT — see [LICENSE](https://www.google.com/search?q=LICENSE)

---

<div align="center">

**Built for Speed. Engineered for Stealth. Designed for Intelligence.**

</div>

```

