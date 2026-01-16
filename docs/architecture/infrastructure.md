# Production Infrastructure

Core production infrastructure components for system reliability.

---

## Observability

### Structured Logging

All logs are written as JSON for easy parsing.

File: `core/production_infra.py`

Log format:
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

Usage:
```python
from app.core import structured_logger

structured_logger.set_trace_id()  # Creates unique ID for request
structured_logger.info("Starting scrape", component="scraper", url=url)
```

Log file location: `app/static/logs/urwa.jsonl`

---

### Metrics Collection

Prometheus-compatible metrics.

Metric types:

| Type | Description | Example |
|------|-------------|---------|
| Counter | Cumulative count | `scrape_total` |
| Gauge | Current value | `active_tasks` |
| Histogram | Distribution | `scrape_duration_seconds` |

Usage:
```python
from app.core import metrics_collector

metrics_collector.increment("scrape_total", status="success")
metrics_collector.set_gauge("active_tasks", 5)
metrics_collector.observe("scrape_duration_seconds", 2.5)
```

---

### Request Tracing

Every request gets a unique trace_id for correlation.

```python
# In request handler
trace_id = structured_logger.set_trace_id()

# All subsequent logs include this trace_id
structured_logger.info("Processing request")
# {"trace_id": "abc123", "message": "Processing request", ...}
```

---

## Circuit Breakers

Prevent cascading failures by stopping requests to failing services.

File: `core/production_infra.py`

### States

| State | Description |
|-------|-------------|
| Closed | Normal operation |
| Open | Blocked (too many failures) |
| Half-Open | Testing recovery |

### Flow

```
        Closed
           |
     Failures > threshold
           |
           v
         Open -----(timeout)-----> Half-Open
           ^                           |
           |                           |
       Failure                     Success
           |                           |
           +---------------------------+
                                       |
                                       v
                                    Closed
```

### Configuration

```python
CircuitBreaker(
    name="amazon.com",
    failure_threshold=5,     # Open after 5 failures
    recovery_timeout=300,    # Wait 5 minutes before retry
    half_open_max=3          # Allow 3 test requests
)
```

### Usage

```python
from app.core import circuit_breakers

breaker = circuit_breakers.get_breaker("amazon.com")

if breaker.can_execute():
    try:
        result = await scrape()
        breaker.record_success()
    except Exception:
        breaker.record_failure()
else:
    # Circuit is open, fail fast
    raise CircuitOpenError()
```

---

## Confidence Scoring

Quality ratings for all outputs.

File: `core/production_infra.py`

### Score Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Content Length | 25% | More content = higher confidence |
| Source Count | 20% | More sources = higher confidence |
| Extraction Method | 20% | Structured > semantic > raw |
| Response Quality | 15% | HTTP status code |
| Structured Data | 10% | Has JSON/schema |
| Speed | 10% | Faster = more likely successful |

### Output

```json
{
  "overall": 0.78,
  "extraction_quality": "medium",
  "source_count": 3,
  "factors": {
    "content_length": 0.7,
    "source_count": 0.7,
    "extraction": 0.8
  },
  "warnings": []
}
```

### Usage

```python
from app.core import confidence_calculator

score = confidence_calculator.calculate(
    content=scraped_content,
    sources=[url1, url2],
    extraction_method="semantic",
    response_time=2.5
)

print(score.overall)  # 0.78
print(score.extraction_quality)  # "medium"
```

---

## Health Checks

Monitor system health.

File: `core/production_infra.py`

### Components Checked

| Component | Checks |
|-----------|--------|
| System | CPU, Memory, Disk usage |
| Playwright | Browser availability |

### Status Levels

| Status | Description |
|--------|-------------|
| Healthy | All components operational |
| Degraded | Some components have issues |
| Unhealthy | Critical components failing |

### Thresholds

| Metric | Degraded | Unhealthy |
|--------|----------|-----------|
| CPU | > 80% | > 95% |
| Memory | > 85% | > 95% |
| Disk | > 90% | > 98% |

### Usage

```python
from app.core import health_checker

status = await health_checker.check_all()
# Returns dict of component -> ComponentHealth
```

---

## Self-Healing

Automatic recovery from failures.

### Recovery Actions

| Issue | Action |
|-------|--------|
| Browser crash | Restart browser instance |
| Memory leak | Trigger garbage collection |
| Stuck task | Timeout and cancel |
| High CPU | Pause new tasks |

### Implementation

```python
health_checker.register_component(
    name="playwright",
    check_func=check_playwright,
    recovery_func=restart_playwright
)
```

---

## Cost Control

Track and limit resource usage.

File: `core/production_infra.py`

### Tracked Resources

| Resource | Cost Estimate |
|----------|--------------|
| LLM Token | $0.00001 |
| Browser Minute | $0.001 |
| Proxy Request | $0.0001 |
| Search Request | $0.001 |

### Limits

| Limit | Default |
|-------|---------|
| LLM tokens/hour | 100,000 |
| Browser minutes/hour | 60 |
| Requests/hour | 1,000 |
| Cost/hour (USD) | $1.00 |

### Usage

```python
from app.core import cost_controller

# Track usage
cost_controller.track_llm(tokens=500)
cost_controller.track_browser(seconds=30)

# Check limits
limits = cost_controller.check_limits()
if limits["any_exceeded"]:
    raise RateLimitError()

# Get stats
stats = cost_controller.get_usage_stats()
```

---

## Data Normalization

Standardize extracted data.

File: `core/data_quality.py`

### Supported Types

| Type | Input | Output |
|------|-------|--------|
| Price | "$1,234.56" | `{amount: 1234.56, currency: "USD"}` |
| Date | "Jan 15, 2024" | `{iso: "2024-01-15"}` |
| Location | "NYC, NY, USA" | `{city, state, country}` |
| Company | "Google LLC" | `{name: "Google", suffix: "LLC"}` |
| Rating | "4.5/5 stars" | `{value: 4.5, max: 5, percent: 90}` |
| Phone | "(555) 123-4567" | `{e164: "+15551234567"}` |

### Usage

```python
from app.core import data_normalizer

price = data_normalizer.normalize_price("$1,234.56")
# {"amount": 1234.56, "currency": "USD", "raw": "$1,234.56"}

date = data_normalizer.normalize_date("January 15, 2024")
# {"iso": "2024-01-15", "timestamp": 1705276800}
```

---

## Versioned Extractors

Rollback-capable CSS selectors.

File: `core/data_quality.py`

### Features

- Version tracking for selectors
- Changelog for each version
- Hash for integrity
- Rollback capability

### Built-in Extractors

| Name | Fields |
|------|--------|
| `amazon_product` | title, price, rating, reviews |
| `linkedin_profile` | name, headline, location |
| `job_listing` | title, company, location, salary |
| `ecommerce_product` | title, price, rating, image |

### Usage

```python
from app.core import extractor_registry

# Get extractor
extractor = extractor_registry.get_extractor("amazon_product")

# Get selectors for a field
selectors = extractor.get_selectors("price")
# ["#priceblock_ourprice", ".a-price-whole", ...]

# Add new version
extractor.add_version("1.1.0", new_selectors, "Fixed price selector")

# Rollback
extractor.rollback("1.0.0")
```
