# Monitoring Guide

How to monitor URWA Brain in production.

---

## Overview

URWA provides multiple monitoring interfaces:

| Interface | Use Case |
|-----------|----------|
| Health endpoint | Service availability |
| Metrics endpoint | Prometheus integration |
| Logs endpoint | Debugging and analysis |
| Circuit status | Failure tracking |
| Cost tracking | Resource management |

---

## Health Monitoring

### Basic Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "3.0.0"
}
```

### Detailed Health Check

```bash
curl http://localhost:8000/api/v1/system/health
```

Response:
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

### Status Meanings

| Status | Action |
|--------|--------|
| healthy | No action needed |
| degraded | Monitor closely |
| unhealthy | Investigate immediately |

---

## Prometheus Integration

### Metrics Endpoint

```bash
curl http://localhost:8000/api/v1/system/metrics/prometheus
```

Response (plain text):
```
urwa_scrape_total{status="success"} 150
urwa_scrape_total{status="error"} 12
urwa_cache_hits 45
urwa_active_tasks 3
```

### Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'urwa'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/system/metrics/prometheus'
    scrape_interval: 30s
```

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `scrape_total` | Counter | Total scrape attempts |
| `cache_hits` | Counter | Cache hit count |
| `active_tasks` | Gauge | Currently running tasks |
| `scrape_duration_seconds` | Histogram | Scrape latency |

---

## Grafana Dashboard

### Key Panels

1. Success Rate
```
rate(urwa_scrape_total{status="success"}[5m]) / rate(urwa_scrape_total[5m])
```

2. Scrape Latency (p95)
```
histogram_quantile(0.95, urwa_scrape_duration_seconds)
```

3. Error Rate
```
rate(urwa_scrape_total{status="error"}[5m])
```

4. Resource Usage
```
urwa_cpu_percent
urwa_memory_percent
```

---

## Logging

### View Recent Logs

```bash
curl "http://localhost:8000/api/v1/system/logs?limit=100"
```

### Filter by Level

```bash
curl "http://localhost:8000/api/v1/system/logs?level=error"
```

### Log Format

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

### Log Levels

| Level | Use |
|-------|-----|
| DEBUG | Detailed debugging |
| INFO | Normal operations |
| WARNING | Potential issues |
| ERROR | Failures |
| METRIC | Performance data |

---

## Circuit Breaker Monitoring

### View All Circuits

```bash
curl http://localhost:8000/api/v1/system/circuits
```

Response:
```json
{
  "circuits": [
    {
      "name": "amazon.com",
      "state": "closed",
      "failure_count": 2,
      "success_count": 15
    },
    {
      "name": "linkedin.com",
      "state": "open",
      "failure_count": 10,
      "last_failure": "2024-01-15T10:25:00"
    }
  ],
  "open_circuits": ["linkedin.com"]
}
```

### Alerting on Open Circuits

```python
import requests

response = requests.get("http://localhost:8000/api/v1/system/circuits")
data = response.json()

if data["open_circuits"]:
    send_alert(f"Circuits open: {data['open_circuits']}")
```

---

## Cost Monitoring

### View Usage

```bash
curl http://localhost:8000/api/v1/system/cost
```

Response:
```json
{
  "usage": {
    "current_hour": {
      "llm_tokens": 15000,
      "browser_minutes": 12.5,
      "estimated_cost_usd": 0.35
    },
    "limits_status": {
      "llm_exceeded": false,
      "cost_exceeded": false,
      "any_exceeded": false
    }
  }
}
```

### Set Alerts

Monitor when approaching limits:

```python
response = requests.get("http://localhost:8000/api/v1/system/cost")
usage = response.json()["usage"]

current = usage["current_hour"]["estimated_cost_usd"]
limit = usage["limits"]["cost_per_hour_usd"]

if current > limit * 0.8:
    send_alert(f"Cost at {current/limit*100:.0f}% of limit")
```

---

## Strategy Performance

### View Strategy Stats

```bash
curl http://localhost:8000/api/v1/strategy/stats
```

### Key Metrics

| Metric | Good | Warning |
|--------|------|---------|
| Success rate | > 80% | < 60% |
| Retry rate | < 20% | > 40% |
| Cache hit rate | > 30% | < 10% |

---

## Alerting Setup

### Health-based Alerts

```python
import requests
import time

while True:
    try:
        r = requests.get("http://localhost:8000/api/v1/system/health", timeout=5)
        data = r.json()
        
        if data["status"] != "healthy":
            send_alert(f"URWA status: {data['status']}")
            
    except requests.exceptions.Timeout:
        send_alert("URWA not responding")
        
    time.sleep(60)
```

### Metric-based Alerts

Using Prometheus Alertmanager:

```yaml
groups:
- name: urwa
  rules:
  - alert: HighErrorRate
    expr: rate(urwa_scrape_total{status="error"}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High scraping error rate"
      
  - alert: CircuitOpen
    expr: urwa_circuits_open > 0
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Circuit breaker open"
```

---

## Dashboard Recommendations

### Operations Dashboard

1. Health status (big number)
2. Success rate (gauge)
3. Active tasks (number)
4. Error rate (line chart)
5. Open circuits (list)
6. Cost usage (progress bar)

### Performance Dashboard

1. Latency percentiles (line chart)
2. Throughput (requests/min)
3. Cache hit rate (gauge)
4. Strategy distribution (pie chart)
5. Top domains (table)

### Debug Dashboard

1. Recent errors (log view)
2. Failed domains (table)
3. Retry counts (bar chart)
4. Evidence captures (count)

---

## Best Practices

1. Set up health checks in load balancer
2. Configure alerts for degraded status
3. Monitor circuit breakers for repeated issues
4. Track cost to prevent overruns
5. Review logs daily for patterns
6. Keep metrics retention for trend analysis
