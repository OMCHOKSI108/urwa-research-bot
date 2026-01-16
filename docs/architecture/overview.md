# Architecture Overview

URWA Brain is designed as a production-grade web intelligence platform with a layered architecture.

---

## High-Level Architecture

```
                     +------------------+
                     |   API Gateway    |
                     |    (FastAPI)     |
                     +--------+---------+
                              |
              +---------------+---------------+
              |               |               |
      +-------v------+ +------v------+ +------v------+
      |   Strategy   | |  Execution  | |   System    |
      |    Engine    | |   Engine    | |   Monitor   |
      +--------------+ +-------------+ +-------------+
              |               |               |
      +-------v---------------v---------------v------+
      |              Data Layer                      |
      |     (Caching, Storage, Evidence)             |
      +----------------------------------------------+
```

---

## Layer Descriptions

### Layer 1: API Gateway

The FastAPI application that handles all HTTP requests.

Components:
- Request routing
- Rate limiting (SlowAPI)
- Request tracing
- Response formatting
- Authentication (optional)

Files:
- `app/main.py`

---

### Layer 2: Intelligence Layer

Makes decisions about how to scrape and what strategies to use.

Components:
- Site Profiler: Detects protection before scraping
- Adaptive Learning: Learns from successes and failures
- Compliance Checker: Validates robots.txt and ToS
- Confidence Calculator: Scores output quality

Files:
- `app/strategies/site_profiler.py`
- `app/strategies/adaptive_learning.py`
- `app/strategies/compliance.py`
- `app/core/production_infra.py`

---

### Layer 3: Execution Layer

Performs the actual scraping operations.

Components:
- Hybrid Scraper: Orchestrates scraping strategies
- Lightweight Scraper: Fast HTTP-only scraping
- Stealth Scraper: Playwright with stealth patches
- Ultra Stealth Scraper: Maximum anti-detection

Files:
- `app/agents/hybrid_scraper.py`
- `app/agents/scraper.py`
- `app/agents/ultra_stealth_scraper.py`

---

### Layer 4: Resilience Layer

Handles failures and ensures system stability.

Components:
- Circuit Breakers: Prevent cascading failures
- Intelligent Retry: Failure-specific retry logic
- Rate Controller: Per-domain throttling
- Evidence Capture: Debug information on failures

Files:
- `app/core/production_infra.py`
- `app/strategies/intelligent_retry.py`
- `app/strategies/rate_control.py`
- `app/strategies/evidence_capture.py`

---

### Layer 5: Data Quality Layer

Ensures output data is clean and consistent.

Components:
- Data Normalizer: Standardizes prices, dates, etc.
- Versioned Extractors: Rollback-capable selectors
- Semantic Extractor: Multi-selector fallback

Files:
- `app/core/data_quality.py`
- `app/strategies/semantic_extractor.py`

---

### Layer 6: Operations Layer

Provides visibility and control over the system.

Components:
- Metrics Collector: Prometheus-compatible metrics
- Health Checker: System health monitoring
- Cost Controller: Resource usage tracking
- Structured Logger: JSON logging with tracing

Files:
- `app/core/production_infra.py`

---

## Request Flow

```
1. Request arrives at API Gateway
          |
2. Rate limiting check
          |
3. Site profiling (if scraping)
          |
4. Strategy selection (adaptive learning)
          |
5. Compliance check (robots.txt)
          |
6. Circuit breaker check
          |
7. Scraping execution
          |
8. Retry on failure (intelligent retry)
          |
9. Data normalization
          |
10. Confidence scoring
          |
11. Response formatting
          |
12. Metrics recording
```

---

## Data Flow

```
+------------+     +------------+     +------------+
|   Search   |     |   Scrape   |     |  Analyze   |
|  (DuckDuckGo)    | (Playwright)|     |  (LLM)     |
+-----+------+     +-----+------+     +-----+------+
      |                  |                  |
      v                  v                  v
+--------------------------------------------------+
|                  Task Queue                       |
|           (Background Processing)                 |
+--------------------------------------------------+
      |                  |                  |
      v                  v                  v
+------------+     +------------+     +------------+
|   Cache    |     |  Storage   |     |  Evidence  |
+------------+     +------------+     +------------+
```

---

## Dependency Diagram

```
main.py
    |
    +-- services/orchestrator.py
    |       |
    |       +-- agents/hybrid_scraper.py
    |       |       |
    |       |       +-- agents/scraper.py (stealth)
    |       |       +-- agents/ultra_stealth_scraper.py
    |       |
    |       +-- services/llm_service.py
    |
    +-- strategies/
    |       |
    |       +-- site_profiler.py
    |       +-- adaptive_learning.py
    |       +-- intelligent_retry.py
    |       +-- compliance.py
    |       +-- stealth_techniques.py
    |       +-- advanced_bypass.py
    |
    +-- core/
            |
            +-- production_infra.py
            +-- data_quality.py
```

---

## Scalability Considerations

### Current State (Single Server)

- All components run in one process
- In-memory caching
- File-based storage
- Suitable for light to moderate load

### Future State (Distributed)

For high-traffic deployments:

```
                    +------------------+
                    |  Load Balancer   |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
+--------v-------+   +-------v--------+   +------v--------+
| API Server 1   |   | API Server 2   |   | API Server N  |
+--------+-------+   +-------+--------+   +------+--------+
         |                   |                   |
         +-------------------+-------------------+
                             |
                    +--------v---------+
                    |     Redis        |
                    | (Cache, Queue)   |
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Worker Pool    |
                    | (Scraping Tasks) |
                    +------------------+
```

Required changes for scaling:
- Replace in-memory cache with Redis
- Use task queue (Celery/RQ) for scraping
- Move storage to S3/database
- Add shared session storage

---

## Security Model

```
+--------------------------------------------------+
|                  API Gateway                      |
|  +--------------------------------------------+  |
|  |  Rate Limiting  |  API Key Auth  | CORS    |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
                         |
                         v
+--------------------------------------------------+
|               Request Validation                  |
|  +--------------------------------------------+  |
|  |  URL Validation | Input Sanitization       |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
                         |
                         v
+--------------------------------------------------+
|               Compliance Layer                    |
|  +--------------------------------------------+  |
|  |  robots.txt  |  Blacklist  |  ToS Check    |  |
|  +--------------------------------------------+  |
+--------------------------------------------------+
```
