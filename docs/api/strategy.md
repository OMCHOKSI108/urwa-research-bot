# Strategy APIs

APIs for site profiling, compliance checking, and adaptive learning.

---

## Profile Site

Detect site protection before scraping.

**Endpoint:** `GET /api/v1/strategy/profile-site`

### Request

```bash
GET /api/v1/strategy/profile-site?url=https://amazon.com
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | URL to profile |

### Response

```json
{
  "status": "success",
  "profile": {
    "url": "https://amazon.com",
    "domain": "amazon.com",
    "risk_level": "high",
    "risk_score": 75,
    "protection": {
      "bot_detection": true,
      "cloudflare": false,
      "captcha_likely": true,
      "javascript_required": true
    },
    "recommended_strategy": "ultra_stealth",
    "recommended_delay": 5.0,
    "cached": false
  }
}
```

### Risk Levels

| Level | Score | Description |
|-------|-------|-------------|
| `low` | 0-25 | Basic sites, no protection |
| `medium` | 26-50 | Some protection, stealth recommended |
| `high` | 51-75 | Strong protection, ultra stealth needed |
| `extreme` | 76-100 | Very aggressive protection |

---

## Compliance Check

Check if a URL can be scraped compliantly.

**Endpoint:** `GET /api/v1/strategy/compliance-check`

### Request

```bash
GET /api/v1/strategy/compliance-check?url=https://linkedin.com
```

### Response

```json
{
  "status": "success",
  "compliance": {
    "url": "https://linkedin.com",
    "domain": "linkedin.com",
    "allowed": false,
    "robots_txt": {
      "status": "disallowed",
      "user_agent": "*",
      "path": "/"
    },
    "crawl_delay": 10,
    "blacklisted": false,
    "warnings": [
      "Site has strict ToS against scraping",
      "Login wall detected"
    ]
  }
}
```

### Compliance Statuses

| Status | Description |
|--------|-------------|
| `allowed` | robots.txt permits access |
| `disallowed` | robots.txt blocks access |
| `unknown` | No robots.txt found |
| `blacklisted` | Domain is blacklisted |

---

## Get Strategy Stats

Get statistics from all strategy components.

**Endpoint:** `GET /api/v1/strategy/stats`

### Response

```json
{
  "status": "success",
  "stats": {
    "profiler": {
      "profiles_cached": 45,
      "profiles_today": 12
    },
    "learner": {
      "domains_tracked": 28,
      "total_attempts": 156,
      "overall_success_rate": 0.78
    },
    "rate_controller": {
      "domains_rate_limited": 3,
      "total_delays_applied": 89
    },
    "retry_controller": {
      "total_retries": 23,
      "success_after_retry": 18
    },
    "evidence": {
      "captures_total": 15,
      "captures_today": 5
    }
  }
}
```

---

## Get Learning Data

Get domain-specific learning data.

**Endpoint:** `GET /api/v1/strategy/learning`

### Request (Specific Domain)

```bash
GET /api/v1/strategy/learning?domain=amazon.com
```

### Response (Specific Domain)

```json
{
  "status": "success",
  "domain": "amazon.com",
  "learning": {
    "total_attempts": 25,
    "successful": 18,
    "success_rate": 0.72,
    "strategies": {
      "lightweight": {
        "attempts": 5,
        "success": 1,
        "rate": 0.20
      },
      "stealth": {
        "attempts": 10,
        "success": 7,
        "rate": 0.70
      },
      "ultra_stealth": {
        "attempts": 10,
        "success": 10,
        "rate": 1.00
      }
    },
    "best_strategy": "ultra_stealth",
    "avg_response_time": 4.5,
    "last_success": "2024-01-15T10:30:00"
  }
}
```

### Request (All Domains)

```bash
GET /api/v1/strategy/learning
```

### Response (All Domains)

```json
{
  "status": "success",
  "summary": {
    "total_domains": 28,
    "overall_success_rate": 0.78,
    "top_domains": [
      {
        "domain": "wikipedia.org",
        "success_rate": 0.98
      },
      {
        "domain": "github.com",
        "success_rate": 0.95
      }
    ],
    "problem_domains": [
      {
        "domain": "linkedin.com",
        "success_rate": 0.15
      }
    ]
  }
}
```

---

## Clear Strategy Data

Reset all strategy data.

**Endpoint:** `POST /api/v1/strategy/clear`

### Request

```bash
POST /api/v1/strategy/clear
```

### Response

```json
{
  "status": "success",
  "message": "All strategy data cleared",
  "cleared": {
    "profiles": 45,
    "learning": 28,
    "evidence": 15
  }
}
```

Warning: This resets all learned behaviors and cached profiles.

---

## Scraper Stats

Get scraping strategy statistics.

**Endpoint:** `GET /api/v1/scraper-stats`

### Response

```json
{
  "status": "success",
  "stats": {
    "lightweight": {
      "attempts": 100,
      "success": 85,
      "rate": 0.85
    },
    "stealth": {
      "attempts": 75,
      "success": 60,
      "rate": 0.80
    },
    "ultra_stealth": {
      "attempts": 25,
      "success": 22,
      "rate": 0.88
    }
  },
  "total_scrapes": 200,
  "cache_hits": 45,
  "cache_hit_rate": 0.225
}
```

---

## Clear Scraper Cache

Clear the scraping cache.

**Endpoint:** `POST /api/v1/scraper-cache/clear`

### Response

```json
{
  "status": "success",
  "message": "Cache cleared",
  "items_cleared": 45
}
```
