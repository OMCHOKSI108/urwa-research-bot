# System APIs

APIs for monitoring, health checks, and system operations.

---

## System Health

Comprehensive health check.

**Endpoint:** `GET /api/v1/system/health`

### Response

```json
{
  "status": "healthy",
  "components": {
    "system": {
      "status": "healthy",
      "message": "All systems operational",
      "metrics": {
        "cpu_percent": 15.2,
        "memory_percent": 45.8,
        "disk_percent": 62.3
      }
    },
    "playwright": {
      "status": "healthy",
      "message": "Playwright available"
    }
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### Health Statuses

| Status | Description |
|--------|-------------|
| `healthy` | All components operational |
| `degraded` | Some components have issues |
| `unhealthy` | Critical components failing |

---

## System Metrics

Get Prometheus-compatible metrics.

**Endpoint:** `GET /api/v1/system/metrics`

### Response

```json
{
  "uptime_seconds": 3600,
  "counters": {
    "scrape_total{status=\"success\"}": 150,
    "scrape_total{status=\"error\"}": 12,
    "cache_hits": 45
  },
  "gauges": {
    "active_tasks": 3,
    "browser_instances": 2
  },
  "histograms": {
    "scrape_duration_seconds": {
      "count": 162,
      "sum": 486.5,
      "avg": 3.0,
      "p50": 2.5,
      "p95": 8.2,
      "p99": 12.1
    }
  },
  "collected_at": "2024-01-15T10:30:00"
}
```

---

## Prometheus Format

Export metrics for Prometheus scraping.

**Endpoint:** `GET /api/v1/system/metrics/prometheus`

### Response (Plain Text)

```
urwa_scrape_total{status="success"} 150
urwa_scrape_total{status="error"} 12
urwa_cache_hits 45
urwa_active_tasks 3
urwa_browser_instances 2
```

---

## Circuit Breakers

Get circuit breaker status for all domains.

**Endpoint:** `GET /api/v1/system/circuits`

### Response

```json
{
  "status": "success",
  "circuits": [
    {
      "name": "amazon.com",
      "state": "closed",
      "failure_count": 2,
      "success_count": 15,
      "last_failure": null
    },
    {
      "name": "linkedin.com",
      "state": "open",
      "failure_count": 10,
      "success_count": 0,
      "last_failure": "2024-01-15T10:25:00"
    }
  ],
  "open_circuits": ["linkedin.com"]
}
```

### Circuit States

| State | Description |
|-------|-------------|
| `closed` | Normal operation, requests allowed |
| `open` | Blocked, too many failures |
| `half_open` | Testing if recovered |

---

## Cost and Usage

Get resource usage and cost tracking.

**Endpoint:** `GET /api/v1/system/cost`

### Response

```json
{
  "status": "success",
  "usage": {
    "current_hour": {
      "llm_tokens": 15000,
      "llm_requests": 25,
      "browser_minutes": 12.5,
      "search_requests": 30,
      "proxy_requests": 45,
      "estimated_cost_usd": 0.35
    },
    "total": {
      "llm_tokens": 250000,
      "browser_minutes": 180.5,
      "bytes_downloaded": 52428800,
      "estimated_cost_usd": 5.25
    },
    "limits": {
      "llm_tokens_per_hour": 100000,
      "browser_minutes_per_hour": 60,
      "requests_per_hour": 1000,
      "cost_per_hour_usd": 1.0
    },
    "limits_status": {
      "llm_exceeded": false,
      "browser_exceeded": false,
      "cost_exceeded": false,
      "any_exceeded": false
    }
  }
}
```

---

## Set Cost Limits

Update resource usage limits.

**Endpoint:** `POST /api/v1/system/cost/limits`

### Request

```bash
POST /api/v1/system/cost/limits?limit_name=llm_tokens_per_hour&value=50000
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit_name` | string | Limit to update |
| `value` | float | New limit value |

### Available Limits

| Limit | Default | Description |
|-------|---------|-------------|
| `llm_tokens_per_hour` | 100000 | LLM tokens per hour |
| `browser_minutes_per_hour` | 60 | Browser usage minutes |
| `requests_per_hour` | 1000 | Total requests |
| `cost_per_hour_usd` | 1.0 | Maximum cost in USD |

### Response

```json
{
  "status": "success",
  "message": "Limit llm_tokens_per_hour set to 50000",
  "current_limits": {
    "llm_tokens_per_hour": 50000,
    "browser_minutes_per_hour": 60,
    "requests_per_hour": 1000,
    "cost_per_hour_usd": 1.0
  }
}
```

---

## List Extractors

List all versioned extractors.

**Endpoint:** `GET /api/v1/system/extractors`

### Response

```json
{
  "status": "success",
  "extractors": [
    {
      "name": "amazon_product",
      "current_version": "1.0.0",
      "hash": "a1b2c3d4",
      "fields": ["title", "price", "rating", "reviews_count"]
    },
    {
      "name": "linkedin_profile",
      "current_version": "1.0.0",
      "hash": "e5f6g7h8",
      "fields": ["name", "headline", "location"]
    }
  ]
}
```

---

## Rollback Extractor

Rollback an extractor to a previous version.

**Endpoint:** `POST /api/v1/system/extractors/rollback`

### Request

```bash
POST /api/v1/system/extractors/rollback?name=amazon_product&version=1.0.0
```

### Response

```json
{
  "status": "success",
  "message": "Rolled back amazon_product to v1.0.0"
}
```

---

## Normalize Data

Convert raw data to structured format.

**Endpoint:** `POST /api/v1/normalize`

### Request

```bash
POST /api/v1/normalize?data_type=price&value=$1,234.56
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data_type` | string | Type of data to normalize |
| `value` | string | Raw value to normalize |

### Supported Types

| Type | Input Example | Output |
|------|---------------|--------|
| `price` | "$1,234.56" | `{"amount": 1234.56, "currency": "USD"}` |
| `date` | "Jan 15, 2024" | `{"iso": "2024-01-15"}` |
| `location` | "New York, NY" | `{"city": "New York", "state": "NY"}` |
| `company` | "Google LLC" | `{"name": "Google", "legal_suffix": "LLC"}` |
| `rating` | "4.5/5" | `{"value": 4.5, "max": 5, "percent": 90}` |
| `phone` | "(555) 123-4567" | `{"e164": "+15551234567"}` |

### Response

```json
{
  "status": "success",
  "input": "$1,234.56",
  "normalized": {
    "amount": 1234.56,
    "currency": "USD",
    "raw": "$1,234.56"
  }
}
```

---

## Get Logs

Get recent structured logs.

**Endpoint:** `GET /api/v1/system/logs`

### Request

```bash
GET /api/v1/system/logs?limit=50&level=error
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Maximum logs to return (default: 100) |
| `level` | string | Filter by level: info, warning, error |

### Response

```json
{
  "status": "success",
  "count": 5,
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "level": "ERROR",
      "trace_id": "abc123",
      "component": "scraper",
      "message": "Connection timeout",
      "url": "https://example.com"
    }
  ]
}
```
