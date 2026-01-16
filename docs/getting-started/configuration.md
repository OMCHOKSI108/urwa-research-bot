# Configuration

Configure URWA Brain for your specific needs.

---

## Environment Variables

Create a `.env` file in the `backend` directory:

```env
# ===========================================
# LLM Configuration
# ===========================================

# Groq API (recommended for speed)
GROQ_API_KEY=gsk_xxxxxxxxxxxx

# Google Gemini (alternative)
GOOGLE_API_KEY=AIzaxxxxxxxxxxxx

# ===========================================
# CAPTCHA Solving (optional)
# ===========================================

# 2Captcha service
CAPTCHA_API_KEY=your_2captcha_key
CAPTCHA_SERVICE=2captcha

# Or Anti-Captcha
# CAPTCHA_API_KEY=your_anticaptcha_key
# CAPTCHA_SERVICE=anticaptcha

# ===========================================
# Server Configuration
# ===========================================

HOST=0.0.0.0
PORT=8000
DEBUG=false

# ===========================================
# Rate Limiting
# ===========================================

# Requests per minute per IP
RATE_LIMIT=60

# ===========================================
# Resource Limits
# ===========================================

# LLM tokens per hour
LLM_TOKENS_PER_HOUR=100000

# Browser minutes per hour
BROWSER_MINUTES_PER_HOUR=60

# Max cost per hour (USD)
MAX_COST_PER_HOUR=1.0
```

---

## Configuration Options

### Scraping Behavior

| Setting | Default | Description |
|---------|---------|-------------|
| `SCRAPE_TIMEOUT` | 30 | Request timeout in seconds |
| `MAX_RETRIES` | 3 | Maximum retry attempts |
| `RATE_LIMIT_DELAY` | 2 | Seconds between requests |

### Strategy Selection

| Setting | Default | Description |
|---------|---------|-------------|
| `DEFAULT_STRATEGY` | auto | lightweight, stealth, ultra_stealth, auto |
| `FORCE_STEALTH` | false | Always use stealth mode |
| `ENABLE_LEARNING` | true | Enable adaptive learning |

### Caching

| Setting | Default | Description |
|---------|---------|-------------|
| `CACHE_ENABLED` | true | Enable response caching |
| `CACHE_TTL` | 3600 | Cache time-to-live in seconds |
| `CACHE_MAX_SIZE` | 1000 | Maximum cached items |

---

## Runtime Configuration

Some settings can be changed at runtime via API:

### Set Cost Limits

```bash
curl -X POST "http://localhost:8000/api/v1/system/cost/limits" \
  -d "limit_name=llm_tokens_per_hour&value=50000"
```

### Clear Caches

```bash
curl -X POST "http://localhost:8000/api/v1/scraper-cache/clear"
```

---

## Proxy Configuration

Configure proxies for IP rotation:

```python
# In app config or environment
PROXY_LIST = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
]
```

Or via API:

```bash
curl -X POST "http://localhost:8000/api/v1/proxies/add" \
  -H "Content-Type: application/json" \
  -d '{"proxy": "http://user:pass@proxy.example.com:8080"}'
```

---

## Browser Profile Configuration

### Create Persistent Profile

```bash
curl -X POST "http://localhost:8000/api/v1/browser-profiles/create?name=my_profile"
```

### Profile Fingerprint Options

Profiles automatically generate:

- Screen resolution
- User agent
- WebGL renderer
- Canvas hash
- Timezone
- Language

---

## Logging Configuration

### Log Levels

Set in environment:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Structured Logging

Logs are written as JSON to `app/static/logs/urwa.jsonl`:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "trace_id": "abc123",
  "component": "scraper",
  "message": "Scrape completed",
  "url": "https://example.com",
  "duration_ms": 1500
}
```

---

## Security Settings

### API Key Authentication (optional)

```env
REQUIRE_API_KEY=true
API_KEYS=key1,key2,key3
```

Then include in requests:

```bash
curl -H "X-API-Key: key1" "http://localhost:8000/api/v1/smart_scrape"
```

### CORS Configuration

```env
CORS_ORIGINS=http://localhost:3000,https://myapp.com
```

---

## Performance Tuning

### Worker Configuration

For high-traffic deployments:

```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Memory Management

```env
# Limit browser instances
MAX_BROWSER_INSTANCES=5

# Auto-cleanup interval (seconds)
CLEANUP_INTERVAL=300
```

---

## Next Steps

- [API Reference](../api/overview.md) - Complete API documentation
- [Monitoring Guide](../guides/monitoring.md) - Set up monitoring
