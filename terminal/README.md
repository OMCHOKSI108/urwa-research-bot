# URWA Brain Terminal CLI

Beautiful command-line interface for URWA Brain that connects to the FastAPI backend.

## Architecture

The CLI is a **client** to the FastAPI server. This ensures:
- ✅ Same code path as the API
- ✅ Proper web research with scraping
- ✅ Consistent results
- ✅ Production-ready behavior

## Prerequisites

1. **Start the API server first** (in a separate terminal):
```bash
cd backend
python run.py
```

2. Then run the CLI:
```bash
# Windows
urwa.bat

# Linux/Mac
./urwa.sh
```

## Quick Start

### Two-Terminal Setup (Recommended)

**Terminal 1 - API Server:**
```bash
cd backend
python run.py
```

**Terminal 2 - CLI:**
```bash
urwa.bat
```

### Single Terminal (CLI starts server)
If the API server is not running, the CLI will offer to start it for you.

## Features

- **API-Powered**: Calls FastAPI endpoints for real web research
- **Live Progress**: See what's happening with progress indicators
- **Colored Output**: Beautiful rich text formatting
- **Multiple Modes**: Chat, Scrape, Research, Fact-Check, Site Analysis

## Modes

### 1. Chat Mode
Interactive Q&A powered by web research.
- Uses `/api/v1/agent` endpoint
- Searches the web for current information
- Returns AI-synthesized answers with citations

### 2. Scrape Mode
Extract data from any URL.
- Uses `/api/v1/agent` endpoint with scrape intent
- Supports JavaScript-heavy sites via Playwright

### 3. Research Mode (Deep)
Comprehensive research on any topic.
- Uses `/api/v1/research?deep=true` endpoint
- Scrapes multiple sources
- Returns detailed analysis with sources

### 4. Fact Check Mode
Verify claims and statements.
- Uses `/api/v1/agent` endpoint
- Cross-references multiple sources
- Returns verdict with evidence

### 5. Site Analysis Mode
Check if a website can be scraped.
- Uses `/api/v1/agent` endpoint
- Profiles site protection
- Recommends scraping strategy

### 6. Start API Server
Launch the FastAPI server from within the CLI.

## Technical Notes

- CLI makes HTTP calls to `http://localhost:8000`
- Timeout is set to 300 seconds for complex research queries
- Results match exactly what the API returns

## Requirements

- Python 3.9+
- FastAPI server running
- Internet connection for web research
