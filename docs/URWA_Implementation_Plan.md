# URWA Implementation Plan & Architecture

## 1. System Overview
**URWA (Universal Reasoning & Web Agent)** is an advanced autonomous research and analysis platform. The system consists of a modern, high-performance React frontend (Perplexity-style) and a robust FastAPI backend powered by Hybrid Scraping and LLM orchestration.

---

## 2. Frontend Architecture (URWA Brain)
**Tech Stack:** React 18, Vite, Tailwind CSS (Zinc Dark Theme), Lucide React.

### 2.1 UI Design System (Perplexity Clone)
- **Theme**: "Matte Dark" (`#191A1A`) with Teal Accents (`#30BFCC`).
- **Layout**:
  - **Sidebar**: Minimalist navigation (User, Search, Library).
  - **Hero Interface**: Centered input with "Focus" modes.
  - **Chat Interface**: Sources-first display, followed by detailed markdown answers.
- **Components**:
  - `Chat.tsx`: Main orchestration component managing state, messages, and modes.
  - `SourceCard`: Visual representation of cited URLs.
  - `ModePill`: Rounded pills for toggling active agents (Pro Search, Data Scraper).

### 2.2 Mode Mapping (Frontend → Backend)
The frontend "Focus Modes" map directly to backend strategies:
| Frontend Mode | Backend Param (`mode`) | Description |
| :--- | :--- | :--- |
| **Auto** | `"auto"` | Intelligent routing based on query complexity. |
| **Pro Search** | `"research"` | Triggers Multi-Agent Deep Research (Search + Scrape + Synthesize). |
| **Data Scraper** | `"scrape"` | Forces heavy scraping of specific URLs to extract structured data. |
| **Reasoning** | `"analysis"` | Activates "Deep Analysis" for logic puzzles or code breakdown. |

---

## 3. Dedicated Backend Connections
**Tech Stack:** FastAPI, Playwright (UltraStealth), Ollama (Local LLM), DuckDuckGo.

### 3.1 API Contracts
- **Endpoint**: `POST /api/v1/agent`
- **Request Structure**:
  ```json
  {
    "query": "Compare GitHub profiles...",
    "mode": "research",
    "stream": false
  }
  ```
- **Response Structure (Standard)**:
  ```json
  {
    "status": "success",
    "result": {
      "answer": "Markdown formatted answer...",
      "sources": ["https://github.com/..."],
      "scraped_data": [...]
    }
  }
  ```

### 3.2 Hybrid Scraping Pipeline
1.  **Compliance Check**: Verifies `robots.txt`.
2.  **Site Profiling**: Detects high-risk sites (e.g., GitHub, LinkedIn).
3.  **Strategy Selection**:
    - *Low Risk*: `Requests` / `BeautifulSoup` (Fast).
    - *High Risk*: `UltraStealth` (Headless Browser + Evasion).
4.  **Extraction**: Smart Parsing (JSON-LD, HTML5 Semantic) -> LLM Structuring.

---

## 4. Roadmap: "Dedicated Connections" (Streaming)
To achieve true "Perplexity-like" real-time feedback, the connection will be upgraded from **HTTP Polling** to **Server-Sent Events (SSE)**.

### Phase 1: Real-Time Progress (Current Priority)
- **Goal**: Show "Searching...", "Reading content...", "Generating..." steps in real-time.
- **Implementation**:
  - Backend: `yield` progress events from `Orchestrator`.
  - Frontend: `EventSource` to listen for status updates.

### Phase 2: Token Streaming
- **Goal**: Stream the answer text character-by-character.
- **Implementation**:
  - Enable `stream=True` in Ollama.
  - Backend proxies the stream to Frontend via SSE.

### Phase 3: Persistent History
- **Goal**: Save threads to database.
- **Implementation**:
  - SQLite/PostgreSQL database for `Conversation` and `Message` tables.
  - Sidebar "Library" loads past chats from API.

---

## 5. Deployment Strategy
1.  **Frontend**: Build with `npm run build` -> Serve static files via Nginx or Backend.
2.  **Backend**: `uvicorn run:app --host 0.0.0.0 --port 8000`.
3.  **Environment**: Ensure `Ollama` is running on port 11434.
