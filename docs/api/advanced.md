# Advanced APIs

APIs for protected site bypass, human intervention, and browser profiles.

---

## Protected Scrape

Scrape protected sites using site-specific strategies.

**Endpoint:** `POST /api/v1/protected-scrape`

### Request

```bash
POST /api/v1/protected-scrape?url=https://linkedin.com/in/billgates
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Target URL |
| `instruction` | string | No | Additional instructions |

### Supported Sites

| Site | Strategy |
|------|----------|
| LinkedIn | Google Cache, Bing Search, Web Archive |
| Amazon | Mobile URLs, Search extraction, ASIN parsing |
| Indeed | RSS feeds, Google Jobs integration |
| Twitter/X | oEmbed API, Nitter mirrors |
| Instagram | oEmbed API |
| Facebook | oEmbed API |

### Response (LinkedIn)

```json
{
  "status": "success",
  "url": "https://linkedin.com/in/billgates",
  "result": {
    "success": true,
    "source": "google_cache",
    "data": {
      "name": "Bill Gates",
      "headline": "Co-chair, Bill & Melinda Gates Foundation",
      "location": "Seattle, Washington"
    }
  }
}
```

### Response (Amazon)

```json
{
  "status": "success",
  "url": "https://amazon.com/dp/B0BSHF7WHW",
  "result": {
    "success": true,
    "data": {
      "asin": "B0BSHF7WHW",
      "title": "Product Name",
      "price": "$29.99",
      "rating": 4.5,
      "reviews_count": "1,234"
    }
  }
}
```

### Response (Indeed)

```json
{
  "status": "success",
  "url": "https://indeed.com",
  "result": {
    "success": true,
    "source": "rss",
    "jobs": [
      {
        "title": "Python Developer",
        "company": "Tech Corp",
        "location": "Remote"
      }
    ]
  }
}
```

---

## Human Queue

Get pending tasks requiring human intervention.

**Endpoint:** `GET /api/v1/human-queue`

### Response

```json
{
  "status": "success",
  "pending_tasks": [
    {
      "id": "task_abc123",
      "type": "captcha",
      "url": "https://protected-site.com",
      "screenshot": "base64_encoded_image",
      "created_at": "2024-01-15T10:30:00",
      "expires_at": "2024-01-15T11:30:00"
    }
  ],
  "total_pending": 1
}
```

### Task Types

| Type | Description |
|------|-------------|
| `captcha` | CAPTCHA needs solving |
| `login` | Login required |
| `verification` | Verification challenge |
| `block` | IP or account blocked |

---

## Complete Human Task

Submit solution for a human queue task.

**Endpoint:** `POST /api/v1/human-queue/{task_id}/complete`

### Request

```json
{
  "cookies": [
    {
      "name": "session",
      "value": "abc123",
      "domain": ".example.com"
    }
  ],
  "token": "solved_captcha_token",
  "session_id": "browser_session_id"
}
```

### Response

```json
{
  "status": "success",
  "task_id": "task_abc123"
}
```

---

## List Browser Profiles

List all persistent browser profiles.

**Endpoint:** `GET /api/v1/browser-profiles`

### Response

```json
{
  "status": "success",
  "profiles": [
    {
      "name": "profile_a1b2c3d4",
      "created_at": "2024-01-10T08:00:00",
      "last_used": "2024-01-15T10:30:00",
      "sites_count": 15
    }
  ],
  "total": 1
}
```

---

## Create Browser Profile

Create a new browser profile with unique fingerprint.

**Endpoint:** `POST /api/v1/browser-profiles/create`

### Request

```bash
POST /api/v1/browser-profiles/create?name=my_custom_profile
```

### Response

```json
{
  "status": "success",
  "profile": {
    "name": "my_custom_profile",
    "fingerprint": {
      "screen_width": 1920,
      "screen_height": 1080,
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "platform": "Win32",
      "language": "en-US",
      "timezone": "America/New_York",
      "webgl_vendor": "Intel Inc.",
      "webgl_renderer": "Intel Iris OpenGL Engine",
      "canvas_hash": "a1b2c3d4e5f6",
      "hardware_concurrency": 8,
      "device_memory": 8
    }
  }
}
```

### Fingerprint Properties

| Property | Description |
|----------|-------------|
| `screen_width/height` | Spoofed screen resolution |
| `user_agent` | Browser user agent |
| `platform` | OS platform (Win32, MacIntel, Linux) |
| `language` | Browser language |
| `timezone` | Timezone identifier |
| `webgl_vendor` | GPU vendor string |
| `webgl_renderer` | GPU renderer string |
| `canvas_hash` | Canvas fingerprint hash |
| `hardware_concurrency` | CPU core count |
| `device_memory` | Device RAM in GB |

---

## CAPTCHA Stats

Get CAPTCHA solving statistics.

**Endpoint:** `GET /api/v1/captcha-stats`

### Response

```json
{
  "status": "success",
  "stats": {
    "solved": 45,
    "failed": 3,
    "service": "2captcha",
    "configured": true
  }
}
```

---

## Proxy Stats

Get proxy intelligence statistics.

**Endpoint:** `GET /api/v1/proxy-stats`

### Response

```json
{
  "status": "success",
  "stats": {
    "total_proxies": 10,
    "banned_count": 2,
    "scores": {
      "proxy_1": {
        "success_rate": 0.85,
        "latency": 250,
        "banned_domains": 1
      },
      "proxy_2": {
        "success_rate": 0.92,
        "latency": 180,
        "banned_domains": 0
      }
    }
  }
}
```

---

## Add Monitor

Add a URL to monitor for changes.

**Endpoint:** `POST /api/v1/monitor/add`

### Request

```json
{
  "url": "https://example.com/page",
  "check_interval": 3600,
  "notify_on_change": true
}
```

### Response

```json
{
  "status": "success",
  "monitor_id": "mon_abc123",
  "url": "https://example.com/page",
  "next_check": "2024-01-15T11:30:00"
}
```

---

## List Monitors

List all monitored URLs.

**Endpoint:** `GET /api/v1/monitor/list`

### Response

```json
{
  "status": "success",
  "monitors": [
    {
      "id": "mon_abc123",
      "url": "https://example.com/page",
      "last_check": "2024-01-15T10:30:00",
      "last_change": "2024-01-14T15:00:00",
      "check_count": 24,
      "change_count": 2
    }
  ]
}
```

---

## Check Monitor

Check a specific monitor for changes.

**Endpoint:** `GET /api/v1/monitor/{monitor_id}/check`

### Response

```json
{
  "status": "success",
  "monitor_id": "mon_abc123",
  "changed": true,
  "changes": {
    "added": ["New paragraph about..."],
    "removed": ["Old content that was..."],
    "modified": 2
  },
  "current_hash": "abc123def456",
  "previous_hash": "xyz789uvw012"
}
```
