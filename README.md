<div align="center">

# ╔══════════════════════════════════════════════════════════════╗
# ║                       URWA BRAIN v3.5                        ║
# ╚══════════════════════════════════════════════════════════════╝

### [ AI-Powered Autonomous Research & Scraping Engine ]

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-000000?style=for-the-badge&logo=ollama&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<br>

</div>

---

## ┏ Quick Start ┓

The fastest way to launch the **URWA Terminal Interface**:

```bash
# Windows
urwa sans start
```

```bash
# Linux / Mac / Git Bash
./urwa sans start
```

*> This will automatically set up the environment, check dependencies, and launch the AI Agent.*

---

## ┏ Key Features ┓

| Feature | Status | Description |
|:---|:---:|:---|
| **Autonomous Agent** | [ACTIVE] | Understands natural language intent (Research vs Scrape vs Analyze) |
| **Ultra Stealth Scraper** | [ACTIVE] | Bypasses Cloudflare, 403s, and CAPTCHAs using browser fingerprinting |
| **Deep Research** | [ACTIVE] | Multi-step web searching, synthesizing, and citing sources |
| **Site Analysis** | [ACTIVE] | Profiles target websites for protection levels before attacking |
| **Private AI** | [ACTIVE] | Full local LLM support via **Ollama** (Phi-3, Llama-3) |
| **API First** | [ACTIVE] | Full REST API with Swagger documentation |

---

## ┏ Architecture ┓

```mermaid
graph TD
    User[User Input] --> Router{Intent Router}
    Router -->|Question| Research[Research Engine]
    Router -->|URL| Scraper[Stealth Scraper]
    Router -->|Analysis| Profiler[Site Profiler]
    
    Research --> Search[DuckDuckGo (DDGS)]
    Scraper --> Browser[Playwright/Stealth]
    
    Search --> LLM[LLM Analysis]
    Browser --> LLM
    
    LLM --> JSON[Structured Output]
```

---

## ┏ Installation & Setup ┓

### Option 1: The "Pro" Way (CLI)
Just run the command above. It handles everything.

### Option 2: Manual Setup

**1. Clone & Prep**
```bash
git clone https://github.com/yourusername/urwa-brain.git
cd urwa-brain
python -m venv venv
# Windows: venv\Scripts\activate
# Linux: source venv/bin/activate
```

**2. Install Core**
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

**3. Configure AI**
*   **Local (Private):** Install [Ollama](https://ollama.ai) and run `ollama pull phi3:mini`.
*   **Cloud (Fast):** Set `GROQ_API_KEY` in your environment.

---

## ┏ API Usage ┓

The backend runs on port `8000`.

### **Agent Endpoint (The Brain)**
`POST /api/v1/agent`

**Request:**
```json
{
  "input": "Find the pricing of iPhone 15 Pro Max on amazon.com and compare with apple.com",
  "use_ollama": true
}
```

**Response:**
```json
{
  "intent": "scrape",
  "action_taken": "Scraped 2 sources",
  "result": {
    "structured_data": {
      "amazon_price": "$1199",
      "apple_price": "$1199",
      "verdict": "Prices are identical"
    }
  }
}
```

---

## ┏ Project Structure ┓

```text
urwa-brain/
├── backend/               # Core API Logic
│   ├── app/
│   │   ├── main.py        # FastAPI Application
│   │   ├── agents/        # Scraper & Research Agents
│   │   └── services/      # Orchestrator Logic
│   └── requirements.txt   # Python Dependencies
├── terminal/              # CLI Interface
│   └── cli.py             # Rich Terminal UI
├── urwa.cmd               # Windows Launcher
├── urwa                   # Linux/Unix Launcher
└── README.md              # Documentation
```

---

<div align="center">

**Built for Speed, Stealth, and Intelligence.**
<br>
[Report Bug] • [Request Feature]

</div>
