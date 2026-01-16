<div align="center">

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                          URWA BRAIN v3.5                             ║
║              AI-Powered Autonomous Research Engine                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-000000?style=for-the-badge&logo=ollama&logoColor=white)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](docs/index.md)

**An intelligent web scraping and research platform that understands intent, adapts strategies, and delivers structured intelligence - not just raw HTML.**

[Quick Start](#quick-start) • [Documentation](docs/index.md) • [API Docs](http://localhost:8000/docs) • [CLI Guide](terminal/README.md)

</div>

---

## What It Does

- **Intent-Aware Agent** - Ask in natural language, it figures out what to do
- **Ultra-Stealth Scraping** - Bypasses Cloudflare, bot detection, and protections
- **Deep Research** - Multi-source web search with AI synthesis and citations
- **Local & Cloud AI** - Ollama (private) or Groq/Gemini (fast)
- **Smart Strategy Selection** - Learns which approach works best per site
- **CLI & API** - Rich terminal interface + REST API with Swagger

---

## Quick Start

### One-Command Launch

**Windows:**
```powershell
urwa sans start
```

**Linux / macOS:**
```bash
./urwa sans start
```

This automatically starts the backend API and launches the interactive CLI.

### Try It Out

```bash
# Research anything
urwa research "What are the latest AI trends?"

# Scrape any website
urwa scrape https://example.com

# Check if a site is protected
urwa profile https://amazon.com
```

---

## Installation

### Prerequisites
- Python 3.11+
- 4GB RAM minimum

### Setup

```bash
# Clone repository
git clone https://github.com/OMCHOKSI08/urwa-brain.git
cd urwa-brain

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
playwright install chromium

# (Optional) Install Ollama for local AI
ollama pull phi3:mini
```

### Configuration

Create `backend/.env`:
```env
# Choose one or both
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Optional: Ollama for local AI
OLLAMA_BASE_URL=http://localhost:11434
```

**[Full Installation Guide](docs/getting-started/installation.md)**

---

## Usage Examples

### CLI Interface

```bash
# Interactive mode
urwa sans start

# Direct commands
urwa research "Compare Python vs JavaScript for web development"
urwa scrape https://news.ycombinator.com --output json
urwa profile https://linkedin.com
```

### API Usage

```python
# Start server
uvicorn app.main:app --reload

# Make requests
import requests

response = requests.post('http://localhost:8000/api/v1/agent', json={
    "input": "Get latest tech news from HackerNews",
    "use_ollama": false
})

print(response.json())
```

**[Complete API Documentation](docs/api/overview.md)**  
**[CLI Command Reference](terminal/README.md)**

---

## Architecture

```
User Input → Intent Router → Strategy Selection → Execution → AI Analysis → Output
                ↓                    ↓                ↓
          [Research]          [Lightweight]    [Local/Cloud LLM]
          [Scrape]            [Stealth]        [Structured Data]
          [Analyze]           [Ultra-Stealth]  [Citations]
```

**Three-Level Scraping Strategy:**
1. **Lightweight** - Fast, simple requests (60% sites)
2. **Stealth** - Playwright with anti-detection (85% sites)
3. **Ultra-Stealth** - Advanced fingerprinting (95% sites)

**[Detailed Architecture](docs/architecture/overview.md)**a logs --tail                       # Follow logs in real-time
urwa stats                             # Show scraping statistics
```

### Advanced CLI Features

**Site Profiling:**
```bash
# Check if a site is scrapable
urwa profile https://example.com

Output:
┌─────────────────────────────────────────┐
│  Site: example.com                      │
│  Risk Level: Medium                     │
│  Protection: Cloudflare detected        │
│  Recommended: Stealth mode              │
│  Robots.txt: Allowed                    │
└─────────────────────────────────────────┘
```

**Export Options:**
```bash
# Export research to different formats
urwa research "query" --export pdf
urwa research "query" --export csv
urwa scrape URL --export json
```

---

## API Usage

```
╔═══════════════════════════════════════════════════════════════════════╗
║                          REST API ENDPOINTS                           ║
╚═══════════════════════════════════════════════════════════════════════╝
```

Backend runs on **`http://localhost:8000`**

### Interactive API Documentation

Visit `http://localhost:8000/docs` for the full Swagger UI with:
- Interactive request testing
- Schema documentation
- Example responses
- Authentication setup

### Core Endpoints

#### 1. Unified Agent Endpoint

**The main brain** - handles any request intelligently.

```http
POST /api/v1/agent

```http
POST /api/v1/agent
Content-Type: application/json

{
  "input": "Find the pricing of iPhone 15 Pro Max on amazon.com and compare with apple.com",
  "use_ollama": true
}
```

**Response:**
```json
{
  "status": "success",
  "intent": "scrape",
  "confidence": 0.95,
  "action_taken": "Scraped 2 sources using ultra-stealth mode",
  "result": {
    "type": "scrape_result",
    "structured_data": {
      "amazon_price": "$1199",
      "apple_price": "$1199",
      "comparison": "Prices are identical across both platforms"
    }
  },
  "processing_time": 12.4
}
```

#### 2. Research Endpoint

**Deep web research** with AI synthesis.

```http
POST /api/v1/research
Content-Type: application/json

{
  "query": "What are the implications of quantum computing on cybersecurity?",
  "deep": true,
  "use_ollama": false
}
```

**Response:**
```json
{
  "answer": "Quantum computing poses both opportunities and threats...",
  "sources": [
    {
      "url": "https://example.com/article",
      "title": "Quantum Computing Security",
      "snippet": "..."
    }
  ],
  "confidence": 0.87,
  "sources_scraped": 8,
  "research_time": 8.2
}
```

#### 3. Site Profile Endpoint

**Check protection level** before scraping.

```http
GET /api/v1/profile?url=https://example.com
```

**Response:**
```json
{
  "domain": "example.com",
  "risk": "medium",
  "bot_wall": "cloudflare",
  "recommended_strategy": "stealth",
  "robots_txt_allowed": true,
  "estimated_success_rate": 0.85
}
```

### Complete API Reference

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/api/v1/agent` | POST | Unified agent (handles any request) |
| `/api/v1/research` | POST | Deep research with citations |
| `/api/v1/scrape` | POST | Direct URL scraping |
| `/api/v1/profile` | GET | Site protection analysis |
| `/api/v1/health` | GET | System health check |
| `/api/v1/stats` | GET | Scraping statistics |
| `/docs` | GET | Interactive Swagger UI |

---

## Installation

```
╔═══════════════════════════════════════════════════════════════════════╗
║                      INSTALLATION GUIDE                               ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### Prerequisites

- Python 3.11 or higher
- Node.js 16+ (for frontend, optional)
- Git
- 4GB RAM minimum
- Internet connection

### Step 1: Clone Repository

```bash
git clone https://github.com/OMCHOKSI108/urwa-brain.git
cd urwa-brain
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### Step 4: Configure Environment

Create a `.env` file in the `backend` directory:

```env
# API Keys (Optional - choose one or both)
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here

# Ollama Settings (for local AI)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini

# Server Settings
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=*

# Scraping Settings
MAX_RETRIES=3
TIMEOUT=180
RATE_LIMIT=20/minute
```

### Step 5: Install Ollama (Optional - for local AI)

**Windows:**
```powershell
# Download from https://ollama.ai
# Then pull models:
ollama pull phi3:mini
ollama pull llama3.2-vision:11b
```

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
ollama pull phi3:mini
```

### Step 6: Start the Application

```bash
# From project root
urwa sans start

# Or manually:
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Configuration

```
╔═══════════════════════════════════════════════════════════════════════╗
║                        CONFIGURATION OPTIONS                          ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `GROQ_API_KEY` | None | Groq Cloud API key for fast LLM |
| `GEMINI_API_KEY` | None | Google Gemini API key |
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama server URL |
| `OLLAMA_MODEL` | phi3:mini | Default Ollama model |
| `PORT` | 8000 | Backend server port |
| `ALLOWED_ORIGINS` | * | CORS allowed origins |
| `MAX_RETRIES` | 3 | Maximum scraping retry attempts |
| `TIMEOUT` | 180 | Request timeout in seconds |
| `RATE_LIMIT` | 20/minute | API rate limiting |

### Strategy Configuration

Edit `backend/app/static/strategy_learning.json` to customize scraping strategies per domain.

```json
{
  "amazon.com": {
    "preferred_strategy": "ultra_stealth",
    "success_rate": 0.92,
    "avg_response_time": 8.5
  }
}
```

---

## Architecture

```
╔═══════════════════════════════════════════════════════════════════════╗
║                       SYSTEM ARCHITECTURE                             ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### High-Level Overview

```
                    ┌─────────────────────────────┐
                    │      User Interface         │
                    │  (CLI / API / Frontend)     │
                    └────────────┬────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │   Unified Agent Router      │
                    │  (Intent Classification)    │
                    └────────────┬────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼────────┐  ┌────────▼────────┐  ┌──────▼──────┐
    │    Research    │  │    Scraper      │  │  Profiler   │
    │    Engine      │  │    Engine       │  │   Engine    │
    └───────┬────────┘  └────────┬────────┘  └──────┬──────┘
            │                    │                    │
    ┌───────▼────────┐  ┌────────▼────────┐  ┌──────▼──────┐
    │  Search APIs   │  │   Playwright    │  │  Compliance │
    │  (Google/DDG)  │  │  (Stealth Mode) │  │   Checker   │
    └───────┬────────┘  └────────┬────────┘  └──────┬──────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │    LLM Processing Layer     │
                    │  (Ollama / Groq / Gemini)   │
                    └────────────┬────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │   Structured JSON Output    │
                    └─────────────────────────────┘
```

### Component Breakdown

**1. Intent Router (`unified_agent.py`)**
- Natural language understanding
- Automatic task classification
- Context-aware decision making

**2. Scraping Engine (`hybrid_scraper.py`)**
- Three-level strategy: Lightweight to Stealth to Ultra
- Automatic fallback on failure
- Domain-specific learning

**3. Research Engine (`research_chat.py`)**
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Backend README](backend/README.md) - Technical details
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community standards

---

## License

MIT License - see [LICENSE](LICENSE) for details.

**Built with:** FastAPI • Playwright • Ollama • BeautifulSoup • Loguru╗
║                                                                      ║
║        Built for Speed. Engineered for Stealth.                      ║
║              Designed for Intelligence.                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

[![GitHub Stars](https://img.shields.io/github/stars/OMCHOKSI108/urwa-brain?style=social)](https://github.com/OMCHOKSI108/urwa-brain)
[![GitHub Issues](https://img.shields.io/github/issues/OMCHOKSI108/urwa-brain)](https://github.com/OMCHOKSI108/urwa-brain/issues)

**Made with love by the URWA Team**