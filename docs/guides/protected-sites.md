# Protected Sites Guide

How to scrape sites with strong bot protection.

---

## Understanding Protection

Modern websites use multiple layers to block scrapers:

| Layer | Examples |
|-------|----------|
| IP-based | Rate limiting, blacklisting |
| Browser detection | WebDriver detection, fingerprinting |
| Behavior analysis | Mouse tracking, timing patterns |
| Challenge pages | CAPTCHA, JavaScript challenges |
| Authentication | Login walls, session validation |

---

## Site-Specific Strategies

### LinkedIn

LinkedIn has aggressive anti-scraping measures.

**Direct scraping status:** Not possible without login

**Alternative approaches:**

1. Google Cache
```bash
POST /api/v1/protected-scrape?url=https://linkedin.com/in/username
```

2. Search engine results
```bash
POST /api/v1/smart_scrape
{"query": "site:linkedin.com username"}
```

3. Web Archive
```bash
# System automatically tries archive.org
```

**Available data:**
- Name
- Headline
- Location
- Recent cached content

---

### Amazon

Amazon uses bot detection with CAPTCHA challenges.

**Protection level:** High

**Strategies:**

1. Mobile URLs (less protected)
```bash
POST /api/v1/protected-scrape?url=https://amazon.com/dp/ASIN
```

2. Search result extraction
```bash
# Falls back to search results if product page blocked
```

3. ASIN-based lookup
```bash
# Constructs optimized URLs from product ID
```

**Tips:**
- Use ultra stealth mode
- Add random delays (5-10 seconds)
- Rotate browser profiles
- Limit to 10-20 products per session

---

### Indeed

Indeed has Cloudflare protection.

**Strategies:**

1. RSS feeds (recommended)
```bash
POST /api/v1/protected-scrape?url=https://indeed.com&instruction=python+developer
```

2. Google Jobs integration
```bash
# Searches Google for Indeed listings
```

**Available data:**
- Job title
- Company name
- Location
- (From RSS) Full description

---

### Twitter/X

Twitter requires authentication for most content.

**Strategies:**

1. oEmbed API (official)
```bash
POST /api/v1/protected-scrape?url=https://twitter.com/user/status/123
```

2. Nitter mirrors
```bash
# Tries nitter.net as fallback
```

**Available data:**
- Tweet text (via oEmbed HTML)
- Author name
- Author URL

---

### Instagram

Instagram blocks all non-authenticated access.

**Strategies:**

1. oEmbed API
```bash
POST /api/v1/protected-scrape?url=https://instagram.com/p/ABC123
```

**Available data:**
- Post thumbnail
- Author name
- Caption (sometimes)

---

## Browser Profile Management

Persistent browser profiles help bypass detection.

### Create Profile

```bash
POST /api/v1/browser-profiles/create?name=amazon_scraper
```

Response includes unique fingerprint:
- Screen resolution
- User agent
- WebGL properties
- Canvas hash
- Timezone

### Use Profiles

Profiles persist:
- Cookies
- localStorage
- Session data

This makes subsequent visits appear as a returning user.

### Best Practices

1. Use one profile per site category
2. Warm up profiles before scraping
3. Maintain realistic session patterns
4. Clear profiles if detected

---

## CAPTCHA Handling

### Automatic Detection

The system detects CAPTCHAs and:
1. Captures screenshot
2. Adds to human queue
3. Waits for solution

### API Integration

Configure CAPTCHA service:

```env
CAPTCHA_API_KEY=your_2captcha_key
CAPTCHA_SERVICE=2captcha
```

Supported services:
- 2Captcha
- Anti-Captcha
- CapMonster

### Manual Queue

If no CAPTCHA service:

1. Task added to `/api/v1/human-queue`
2. Get task with screenshot
3. Solve manually
4. Submit solution via `/api/v1/human-queue/{id}/complete`

---

## Cloudflare Bypass

### Challenge Types

| Type | Auto-solvable |
|------|---------------|
| JS Challenge | Yes (wait) |
| Managed Challenge | Needs CAPTCHA service |
| Block | No |

### Handling

1. System waits for JS challenges (up to 30s)
2. Detects Turnstile and extracts site key
3. Submits to CAPTCHA service if configured
4. Stores clearance cookie for reuse

---

## Proxy Usage

### Add Proxies

```python
# Via API or configuration
proxy_intelligence.add_proxy("http://user:pass@proxy.example.com:8080")
```

### Smart Rotation

System automatically:
- Scores proxies by success rate
- Tracks banned domains per proxy
- Selects best proxy for each domain
- Retires poorly performing proxies

### Proxy Types

| Type | Use Case |
|------|----------|
| Datacenter | General scraping |
| Residential | Protected sites |
| Mobile | Maximum stealth |

---

## Rate Limiting

### Per-domain Throttling

```python
# Automatic based on:
# 1. robots.txt Crawl-delay
# 2. Response time patterns
# 3. Historical blocks
```

### Recommended Delays

| Site Type | Delay |
|-----------|-------|
| Low protection | 1-2 seconds |
| Medium protection | 3-5 seconds |
| High protection | 5-10 seconds |
| Extreme protection | 10-30 seconds |

---

## Failure Recovery

### Intelligent Retry

| Failure | Action |
|---------|--------|
| Timeout | Increase timeout, retry |
| 403 | Switch to stealth mode |
| 429 | Wait, respect Retry-After |
| CAPTCHA | Queue for solving |
| Block | Change proxy, notify |

### Evidence Capture

On failure, system captures:
- Screenshot
- HTML source
- Response headers
- Cookies

Location: `app/static/evidence/`

Use for debugging and improving strategies.

---

## Best Practices

### Do

1. Profile site before scraping
2. Start with least aggressive strategy
3. Respect rate limits
4. Use browser profiles
5. Monitor circuit breakers
6. Handle failures gracefully

### Do Not

1. Hammer sites with requests
2. Ignore robots.txt warnings
3. Use same fingerprint everywhere
4. Retry forever on blocks
5. Scrape login-required content without auth
