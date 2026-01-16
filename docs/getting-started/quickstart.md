# Quick Start

Get started with URWA Brain in minutes.

---

## Basic Web Search

Search the web and get AI-analyzed results:

```bash
curl -X POST "http://localhost:8000/api/v1/smart_scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "best programming languages 2024",
    "use_local_llm": true
  }'
```

Response includes a `task_id`. Poll for results:

```bash
curl "http://localhost:8000/api/v1/tasks/{task_id}"
```

---

## Scrape a Specific URL

Extract content from any website:

```bash
curl -X POST "http://localhost:8000/api/v1/custom-scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.ycombinator.com",
    "instruction": "Extract the top 10 stories with titles and points"
  }'
```

---

## Profile Site Protection

Check what protection a site uses before scraping:

```bash
curl "http://localhost:8000/api/v1/strategy/profile-site?url=https://amazon.com"
```

Response:

```json
{
  "url": "https://amazon.com",
  "risk": "high",
  "bot_wall": "cloudflare",
  "recommended_strategy": "ultra_stealth"
}
```

---

## Scrape Protected Sites

Use site-specific strategies for difficult sites:

```bash
# LinkedIn profile
curl -X POST "http://localhost:8000/api/v1/protected-scrape?url=https://linkedin.com/in/billgates"

# Amazon product
curl -X POST "http://localhost:8000/api/v1/protected-scrape?url=https://amazon.com/dp/B0BSHF7WHW"

# Indeed jobs
curl -X POST "http://localhost:8000/api/v1/protected-scrape?url=https://indeed.com&instruction=python+developer"
```

---

## Fact-Check a Claim

Verify claims against multiple sources:

```bash
curl -X POST "http://localhost:8000/api/v1/fact-check" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Python is the most popular programming language",
    "deep_check": true
  }'
```

---

## Normalize Data

Convert messy data to structured format:

```bash
# Normalize price
curl -X POST "http://localhost:8000/api/v1/normalize?data_type=price&value=\$1,234.56"

# Response
{
  "normalized": {
    "amount": 1234.56,
    "currency": "USD",
    "raw": "$1,234.56"
  }
}
```

Supported types: `price`, `date`, `location`, `company`, `rating`, `phone`

---

## Check System Health

Monitor system status:

```bash
curl "http://localhost:8000/api/v1/system/health"
```

Response:

```json
{
  "status": "healthy",
  "components": {
    "system": {
      "status": "healthy",
      "metrics": {
        "cpu_percent": 15.2,
        "memory_percent": 45.8
      }
    },
    "playwright": {
      "status": "healthy"
    }
  }
}
```

---

## View Metrics

Get Prometheus-compatible metrics:

```bash
curl "http://localhost:8000/api/v1/system/metrics"
```

---

## Common Patterns

### Async Task Pattern

All long-running operations return a `task_id`:

```bash
# Step 1: Start task
response=$(curl -X POST "http://localhost:8000/api/v1/smart_scrape" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI news"}')

task_id=$(echo $response | jq -r '.task_id')

# Step 2: Poll for completion
while true; do
  status=$(curl -s "http://localhost:8000/api/v1/tasks/$task_id" | jq -r '.status')
  echo "Status: $status"
  if [ "$status" = "completed" ]; then
    break
  fi
  sleep 2
done

# Step 3: Get results
curl "http://localhost:8000/api/v1/tasks/$task_id"
```

### Error Handling

All responses include a `status` field:

```json
{
  "status": "success",
  "data": { ... }
}
```

Or on error:

```json
{
  "status": "error",
  "message": "Error description"
}
```

---

## Next Steps

- [API Reference](../api/overview.md) - Complete API documentation
- [Protected Sites Guide](../guides/protected-sites.md) - Advanced scraping techniques
- [Configuration](configuration.md) - Customize behavior
