# Installation

This guide covers the installation of URWA Brain on your local machine.

---

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Git

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-repo/urwa-brain.git
cd urwa-brain
```

---

## Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

---

## Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Core Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| playwright | Browser automation |
| aiohttp | Async HTTP client |
| groq | LLM integration |
| loguru | Logging |
| psutil | System metrics |

---

## Step 4: Install Playwright Browsers

```bash
playwright install chromium
```

This downloads the Chromium browser used for JavaScript rendering.

---

## Step 5: Configure Environment

Create a `.env` file in the backend directory:

```env
# LLM Configuration
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key

# Optional: CAPTCHA Solving
CAPTCHA_API_KEY=your_2captcha_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

---

## Step 6: Verify Installation

```bash
python run.py
```

You should see:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 7: Test the API

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "3.0.0"
}
```

---

## Troubleshooting

### Playwright Installation Fails

If Playwright fails to install browsers:

```bash
# Install system dependencies (Linux)
playwright install-deps

# Then retry
playwright install chromium
```

### Port Already in Use

Change the port in `run.py` or set the `PORT` environment variable:

```bash
PORT=8080 python run.py
```

### Missing API Keys

The system works without API keys but with limited LLM functionality:

- Without GROQ_API_KEY: Falls back to local processing
- Without CAPTCHA_API_KEY: CAPTCHA solving disabled

---

## Next Steps

- [Quick Start Guide](quickstart.md) - Basic usage examples
- [Configuration](configuration.md) - Advanced configuration options
