# Scraping Strategies

URWA Brain uses a layered strategy system that adapts to site protection.

---

## Strategy Selection

The system automatically selects the appropriate strategy based on:

1. Site profiling results
2. Historical success rates
3. Compliance requirements
4. Resource constraints

```
            Site Profiling
                  |
                  v
        +------------------+
        | Risk Assessment  |
        +--------+---------+
                 |
    +------------+------------+
    |            |            |
    v            v            v
  Low Risk   Medium Risk  High Risk
    |            |            |
    v            v            v
Lightweight   Stealth    Ultra Stealth
```

---

## Strategy Types

### Lightweight Strategy

Fast HTTP-only scraping without browser.

Best for:
- Static HTML pages
- APIs and JSON endpoints
- Sites with no JavaScript
- High-volume scraping

Techniques:
- aiohttp async requests
- Session persistence
- Header rotation
- Gzip handling

```python
# Example usage
result = await hybrid_scraper.scrape(url, force_strategy="lightweight")
```

---

### Stealth Strategy

Playwright browser with stealth patches.

Best for:
- JavaScript-rendered content
- Sites with basic bot detection
- Single Page Applications
- Dynamic content loading

Techniques:
- Playwright browser automation
- Navigator webdriver removal
- Plugin spoofing
- Chrome runtime injection

```python
# Example usage
result = await hybrid_scraper.scrape(url, force_strategy="stealth")
```

---

### Ultra Stealth Strategy

Maximum anti-detection measures.

Best for:
- Sites with Cloudflare
- Sites with CAPTCHA
- Aggressive bot detection
- High-value targets

Techniques:
- Full fingerprint spoofing
- Canvas noise injection
- WebGL vendor spoofing
- Human behavior simulation
- Session trust building
- Low-and-slow pacing

```python
# Example usage
result = await hybrid_scraper.scrape(url, force_ultra_stealth=True)
```

---

## Strategy Components

### Site Profiler

Analyzes sites before scraping.

File: `strategies/site_profiler.py`

Detects:
- Bot protection systems (Cloudflare, Akamai, DataDome)
- JavaScript requirements
- CAPTCHA presence
- Login walls
- Rate limit indicators

Output:
```json
{
  "risk_level": "high",
  "risk_score": 75,
  "protection": {
    "cloudflare": true,
    "javascript_required": true
  },
  "recommended_strategy": "ultra_stealth"
}
```

---

### Adaptive Learning

Learns from successful and failed attempts.

File: `strategies/adaptive_learning.py`

Tracks:
- Per-domain success rates
- Per-strategy effectiveness
- Response times
- Failure patterns

Uses:
- Updates strategy selection based on history
- Automatically escalates on repeated failures
- Remembers what works for each domain

---

### Intelligent Retry

Failure-specific retry logic.

File: `strategies/intelligent_retry.py`

Failure types and actions:

| Failure Type | Action |
|--------------|--------|
| Timeout | Retry with longer timeout |
| 403 Forbidden | Switch to stealth mode |
| 429 Rate Limit | Wait and retry |
| CAPTCHA | Queue for solving |
| JavaScript Error | Use Playwright |
| Connection Error | Change proxy |

---

### Rate Controller

Per-domain request throttling.

File: `strategies/rate_control.py`

Features:
- Respects Crawl-delay from robots.txt
- Adaptive delay based on response times
- Domain-specific rate limits
- Burst protection

---

### Evidence Capture

Debug information on failures.

File: `strategies/evidence_capture.py`

Captures:
- Screenshots
- HTML source
- Network logs
- Headers
- Cookies

Stored in: `app/static/evidence/`

---

## Stealth Techniques

### Fingerprint Masking

File: `strategies/stealth_techniques.py`

Spoofs:
- Navigator properties (platform, languages)
- Screen dimensions
- Hardware concurrency
- Device memory
- WebGL vendor/renderer
- Canvas fingerprint
- Audio fingerprint

---

### Session Trust Building

Warms up sessions before target access:

1. Visit homepage first
2. Navigate to intermediate pages
3. Simulate reading time
4. Scroll naturally
5. Access target page

---

### Behavior Simulation

Mimics human actions:

- Random mouse movements
- Natural scrolling patterns
- Variable typing speed
- Click delays
- Page focus/blur events

---

### Cookie Persistence

Maintains sessions across requests:

- Stores cookies per domain
- Reuses sessions for returning visitor appearance
- Manages cookie expiration
- Handles consent cookies

---

## Strategy Pipeline

The complete scraping pipeline:

```
1. Receive URL
       |
2. Check cache (skip if cached)
       |
3. Profile site protection
       |
4. Check compliance (robots.txt)
       |
5. Check circuit breaker
       |
6. Select strategy (adaptive)
       |
7. Apply rate limiting
       |
8. Execute scrape
       |
   +---+---+
   |       |
Success  Failure
   |       |
   v       v
9. Cache  10. Intelligent retry
   |           |
   v           v
11. Extract content
       |
12. Normalize data
       |
13. Score confidence
       |
14. Record metrics
       |
15. Return result
```

---

## Configuration

### Strategy Priorities

```python
STRATEGY_PRIORITY = {
    "lightweight": 1,  # Try first
    "stealth": 2,      # Try second
    "ultra_stealth": 3 # Last resort
}
```

### Risk Score Thresholds

```python
RISK_THRESHOLDS = {
    "low": 25,      # Use lightweight
    "medium": 50,   # Use stealth
    "high": 75,     # Use ultra_stealth
    "extreme": 100  # May need manual intervention
}
```

### Retry Limits

```python
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 2,
    "max_delay": 60
}
```

---

## Adding Custom Strategies

To add a new strategy:

1. Create strategy class:

```python
# strategies/my_strategy.py

class MyCustomStrategy:
    async def scrape(self, url: str) -> Optional[str]:
        # Implementation
        pass
```

2. Register in HybridScraper:

```python
# agents/hybrid_scraper.py

self.strategies["my_strategy"] = MyCustomStrategy()
```

3. Add selection logic:

```python
if site_profile.special_protection:
    return "my_strategy"
```
