# Core APIs

The core APIs provide web scraping, search, and analysis functionality.

---

## Smart Scrape

AI-powered web research that combines search, scraping, and analysis.

**Endpoint:** `POST /api/v1/smart_scrape`

### Request

```json
{
  "query": "best programming languages 2024",
  "use_local_llm": true,
  "max_results": 5
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Research query |
| `use_local_llm` | boolean | No | Use local LLM (default: true) |
| `max_results` | integer | No | Maximum results (default: 10) |

### Response

```json
{
  "task_id": "abc123def456",
  "status": "processing"
}
```

### Task Result

Poll `/api/v1/tasks/{task_id}` for completion:

```json
{
  "status": "completed",
  "result": {
    "summary": "Analysis of programming language trends...",
    "sources": [
      {
        "url": "https://example.com/article",
        "title": "Programming Languages 2024",
        "relevance": 0.95
      }
    ],
    "key_points": [
      "Python remains most popular",
      "Rust growing rapidly"
    ]
  }
}
```

---

## Chat

Natural language interface for web research.

**Endpoint:** `POST /api/chat`

### Request

```json
{
  "message": "Find me the latest news about AI",
  "session_id": "optional-session-id"
}
```

### Response

```json
{
  "task_id": "abc123",
  "status": "processing"
}
```

---

## Search

Web search with result analysis.

**Endpoint:** `POST /api/search`

### Request

```json
{
  "query": "machine learning tutorials",
  "max_results": 10,
  "analyze": true
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `max_results` | integer | No | Maximum results |
| `analyze` | boolean | No | Analyze results with LLM |

### Response

```json
{
  "task_id": "abc123",
  "status": "processing"
}
```

---

## Analyze URLs

Analyze specific URLs directly.

**Endpoint:** `POST /api/analyze-urls`

### Request

```json
{
  "urls": [
    "https://example.com/article1",
    "https://example.com/article2"
  ],
  "instruction": "Compare these articles"
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | array | Yes | List of URLs to analyze |
| `instruction` | string | No | Analysis instructions |

---

## Custom Scrape

Extract specific data from a URL using custom instructions.

**Endpoint:** `POST /api/v1/custom-scrape`

### Request

```json
{
  "url": "https://news.ycombinator.com",
  "instruction": "Extract top 10 stories with title, points, and comments"
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Target URL |
| `instruction` | string | Yes | Extraction instructions |
| `format` | string | No | Output format: json, text |

### Response

```json
{
  "status": "success",
  "data": {
    "stories": [
      {
        "title": "Story Title",
        "points": 342,
        "comments": 156
      }
    ]
  },
  "confidence": 0.85
}
```

---

## Web Search Pipeline

Comprehensive 11-step web search pipeline.

**Endpoint:** `POST /api/v1/websearch`

### Request

```json
{
  "query": "climate change research 2024",
  "deep": true
}
```

### Pipeline Steps

1. Query analysis
2. Search execution
3. URL extraction
4. Page profiling
5. Content scraping
6. Text extraction
7. Relevance scoring
8. Deduplication
9. LLM analysis
10. Source attribution
11. Response formatting

---

## Targeted Scrape

9-step targeted scraping pipeline.

**Endpoint:** `POST /api/v1/targeted-scrape`

### Request

```json
{
  "url": "https://example.com/article",
  "extraction_type": "article"
}
```

### Extraction Types

| Type | Description |
|------|-------------|
| `article` | News article extraction |
| `product` | E-commerce product data |
| `job` | Job listing details |
| `profile` | Profile information |
| `generic` | General content |

---

## Get Task Status

Poll for task completion.

**Endpoint:** `GET /api/v1/tasks/{task_id}`

### Response (Processing)

```json
{
  "task_id": "abc123",
  "status": "processing",
  "progress": 45,
  "message": "Analyzing content..."
}
```

### Response (Completed)

```json
{
  "task_id": "abc123",
  "status": "completed",
  "result": { ... },
  "duration_ms": 3500
}
```

### Response (Failed)

```json
{
  "task_id": "abc123",
  "status": "failed",
  "error": "Connection timeout",
  "code": "TIMEOUT_ERROR"
}
```

---

## Fact Check

Verify claims against multiple sources.

**Endpoint:** `POST /api/v1/fact-check`

### Request

```json
{
  "claim": "Python is the most popular programming language",
  "deep_check": true,
  "max_sources": 5
}
```

### Response

```json
{
  "claim": "Python is the most popular programming language",
  "verdict": "mostly_true",
  "confidence": 0.82,
  "evidence": [
    {
      "source": "https://tiobe.com",
      "supports": true,
      "quote": "Python ranks #1..."
    }
  ],
  "analysis": "Multiple sources confirm..."
}
```

---

## Source Intelligence

Evaluate source credibility.

**Endpoint:** `POST /api/v1/source-intelligence`

### Request

```json
{
  "url": "https://example.com/article"
}
```

### Response

```json
{
  "url": "https://example.com/article",
  "domain": "example.com",
  "credibility_score": 0.75,
  "factors": {
    "domain_age": "5 years",
    "https": true,
    "author_attribution": true,
    "citations": 3
  },
  "category": "news"
}
```
