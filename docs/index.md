# URWA Brain

**Universal Research Web Agent - Production-Grade Web Intelligence Platform**

Version: 3.0.0

---

## Overview

URWA Brain is a production-grade web scraping and research platform that combines intelligent scraping strategies with AI-powered analysis. It is designed to handle real-world challenges including bot detection, rate limiting, and dynamic content.

---

## Key Features

### Intelligent Scraping
- Multi-strategy scraper (Lightweight, Stealth, Ultra Stealth)
- Automatic strategy selection based on site protection
- Adaptive learning from successes and failures

### Protected Site Handling
- Site-specific scrapers for LinkedIn, Amazon, Indeed
- CAPTCHA solving integration
- Browser profile persistence
- Human-in-the-loop for blockers

### Production Infrastructure
- Circuit breakers to prevent cascading failures
- Prometheus-compatible metrics
- Health checks with self-healing
- Cost control and usage limits

### Data Quality
- Automatic data normalization (prices, dates, locations)
- Versioned extractors with rollback support
- Confidence scoring on all outputs

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/urwa-brain.git
cd urwa-brain/backend

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running the Server

```bash
python run.py
```

The API will be available at `http://localhost:8000`

### First Request

```bash
curl -X POST "http://localhost:8000/api/v1/smart_scrape" \
  -H "Content-Type: application/json" \
  -d '{"query": "best programming languages 2024"}'
```

---

## Documentation Sections

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started/installation.md) | Installation and setup |
| [API Reference](api/overview.md) | Complete API documentation |
| [Architecture](architecture/overview.md) | System design and components |
| [Guides](guides/protected-sites.md) | How-to guides for specific tasks |

---

## API Endpoints Summary

| Category | Endpoints | Description |
|----------|-----------|-------------|
| Core | 7 | Web scraping and research |
| Strategy | 5 | Protection detection and learning |
| Advanced | 7 | Protected site bypass |
| System | 10 | Monitoring and operations |
| Data | 1 | Data normalization |

**Total: 45+ API endpoints**

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Scraping | Playwright, aiohttp |
| LLM | Groq, Google Gemini |
| Search | DuckDuckGo |
| Monitoring | Prometheus-compatible |
| Logging | Structured JSON (Loguru) |

---

## Project Structure

```
urwa-brain/
├── backend/
│   ├── app/
│   │   ├── core/           # Production infrastructure
│   │   ├── strategies/     # Scraping strategies
│   │   ├── agents/         # Scraper implementations
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt
│   └── run.py
├── docs/                   # Documentation
└── mkdocs.yml              # Documentation config
```

---

## License

MIT License - See LICENSE file for details.
