# API Overview

URWA Brain provides a comprehensive REST API for web scraping, research, and data extraction.

---

## Base URL

```
http://localhost:8000
```

---

## API Versioning

All endpoints are versioned under `/api/v1/`:

```
http://localhost:8000/api/v1/smart_scrape
```

---

## Authentication

Currently, the API is open by default. Optional API key authentication can be enabled via configuration.

When enabled, include the API key in the header:

```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/v1/smart_scrape
```

---

## Response Format

All responses follow a consistent format:

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "task_id": "abc123"
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

---

## Async Operations

Long-running operations return a `task_id` immediately:

```json
{
  "task_id": "abc123def456",
  "status": "processing"
}
```

Poll the task endpoint for results:

```bash
GET /api/v1/tasks/{task_id}
```

Task statuses:

| Status | Description |
|--------|-------------|
| `processing` | Task is running |
| `completed` | Task finished successfully |
| `failed` | Task failed with error |

---

## Rate Limiting

Default rate limits:

| Endpoint Type | Limit |
|--------------|-------|
| Scraping | 5/minute |
| Search | 10/minute |
| System | 60/minute |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1705320000
```

---

## API Categories

### Core APIs

Web scraping and research endpoints.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/smart_scrape` | POST | AI-powered web research |
| `/api/chat` | POST | Natural language interface |
| `/api/search` | POST | Web search with analysis |
| `/api/analyze-urls` | POST | Analyze specific URLs |
| `/api/v1/custom-scrape` | POST | Custom extraction |

[Full Core API Reference](core.md)

---

### Strategy APIs

Protection detection and learning.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/strategy/profile-site` | GET | Detect site protection |
| `/api/v1/strategy/compliance-check` | GET | Check robots.txt |
| `/api/v1/strategy/stats` | GET | Strategy statistics |
| `/api/v1/strategy/learning` | GET | Learning data |

[Full Strategy API Reference](strategy.md)

---

### System APIs

Monitoring and operations.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/system/health` | GET | Health check |
| `/api/v1/system/metrics` | GET | Prometheus metrics |
| `/api/v1/system/circuits` | GET | Circuit breakers |
| `/api/v1/system/cost` | GET | Usage tracking |

[Full System API Reference](system.md)

---

### Advanced APIs

Protected site bypass.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/protected-scrape` | POST | Site-specific scraping |
| `/api/v1/human-queue` | GET | Human intervention queue |
| `/api/v1/browser-profiles` | GET | Session profiles |

[Full Advanced API Reference](advanced.md)

---

## Common Parameters

### Scraping Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | - | Target URL |
| `query` | string | - | Search query |
| `instruction` | string | - | Extraction instructions |
| `force_ultra_stealth` | boolean | false | Force stealth mode |
| `use_local_llm` | boolean | true | Use local LLM |

### Pagination

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Results per page |
| `offset` | integer | 0 | Skip N results |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_URL` | 400 | Malformed URL |
| `SCRAPE_FAILED` | 500 | Scraping error |
| `TASK_NOT_FOUND` | 404 | Task ID not found |
| `BLOCKED` | 403 | Blocked by target site |
| `CAPTCHA_REQUIRED` | 403 | CAPTCHA detected |

---

## Interactive Documentation

FastAPI provides interactive documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
