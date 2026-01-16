# Codebase Audit Report: Bugs, Logic Errors, and Improvements

## 1. Critical Bugs & Logic Errors

### A. Memory Leaks in `CostController`
**File:** `backend/app/core/production_infra.py` (Line 612-617)
The `_maybe_reset_hourly` method performs **nothing** to clean up old data.
```python
612:     def _maybe_reset_hourly(self):
613:         """Reset hourly counters if new hour."""
614:         hour_key = self._get_current_hour_key()
615:         if hour_key not in self.hourly_usage:
616:             # New hour, old data stays for history
617:             pass  # <-- BUG: Old keys are never removed, dict grows forever
```
**Fix:** Implement logic to remove hour keys older than X hours (e.g., 24 hours).

### B. O(N) Performance Degradation in Metrics
**File:** `backend/app/core/production_infra.py` (Line 118)
```python
118:         if len(self.histograms[key]) > 1000:
119:             self.histograms[key] = self.histograms[key][-1000:]
```
This slice operation creates a copy of the list every single time an observation is added after the 1000th data point. This is O(N) complexity for every insert.
**Fix:** Use `collections.deque(maxlen=1000)` which is O(1) for appending and popping.

### C. Logic Error in Smart Scrape Limit
**File:** `backend/app/services/orchestrator.py` (Line 211)
```python
211:                 if not request.urls and len(collected_data) >= 15: 
212:                     break
```
Logic flaw: `request.urls` is a user input. If it is None, the system goes into "Auto-Discovery" mode. The break condition `len(collected_data) >= 15` is intended to stop after getting enough data. However, `collected_data` is appended to *inside* the loop. If the first URL yields 20 items, the loop breaks immediately, even if 2 more high-quality URLs were found in search.
**Improvement:** Should probably check source count, not item count, or ensure diversity.

### D. Race Condition in Global State (Multi-Worker)
**File:** `backend/app/main.py`
Objects like `limiter`, `scraper`, `orchestrator`, and `recent_logs` are global variables instantiated at module level.
If the application is run with multiple Uvicorn workers (standard production setup), **each worker has its own copy**.
- **Rate Limits** will be per-worker (not effective globally).
- **Circuit Breakers** will be per-worker (one worker might block a domain while others spam it).
- **Logs** (`recent_logs`) will be fragmented; `GET /logs` will return random results depending on which worker handles the request.
**Fix:** Use Redis for distributed Rate Limiting and Circuit state.

## 2. Security Vulnerabilities

### A. SSRF (Server-Side Request Forgery) Risk
**File:** `backend/app/services/orchestrator.py`
The `run_smart_scrape` and `run_websearch` functions take arbitrary URLs from user input and blindly feed them to `scraper.scrape(url)`.
A user could input `http://localhost:8000/system/metrics` or `http://169.254.169.254/latest/meta-data/` (AWS Metadata) to extract internal infrastructure data.
**Fix:** Implement a `validate_url` function that resolves the IP and blocks private ranges (127.0.0.0/8, 10.0.0.0/8, etc.) before scraping.

### B. Unbounded File Creation
**File:** `backend/app/services/orchestrator.py`
Session files are created with `uuid`. History files are created with timestamps.
There is **no cleanup mechanism**. `app/static/sessions` and `app/static/history` will fill up the disk indefinitely.
**Fix:** Add a background task (cron) to delete files older than 24 hours.

## 3. Code Quality & Maintenance Issues

### A. Cyclomatic Complexity
**File:** `backend/app/services/orchestrator.py`
The `run_smart_scrape` method is ~500 lines long (Lines 163-686). It handles:
- Orchestration
- Scraping logic
- Data parsing (JSON/Markdown)
- Logic branching (AmbitionBox vs Generic)
- Smart extraction fallback
- Playwright retry logic
- LLM processing
- File generation
- Response construction
**Fix:** Decompose into `_discover_urls`, `_process_url`, `_synthesize_results`, etc.

### B. Regex Heavy Extraction
**File:** `backend/app/utils/smart_extractor.py`
The extractor relies entirely on dozens of complex Regex patterns.
While fast, this is brittle. A small HTML change on a target site breaks extraction.
**Fix:** Use `BeautifulSoup` or `selectolax` for robust CSS selector/XPath extraction combined with Regex for text cleaning.

### C. Hardcoded Paths
**File:** `backend/app/main.py`
```python
58: EXPORT_DIR = "app/static/exports"
```
Hardcoded relative paths breaks if the app is run from a different directory (e.g. `python backend/app/main.py` vs `python app/main.py`).
**Fix:** Use `pathlib` with `__file__` anchor.

## 4. Logical Inconsistencies

### A. Hybrid Scraper Strategy Fallback
**File:** `backend/app/agents/hybrid_scraper.py`
In `_execute_with_fallback`:
If `strategy == "lightweight"`, it tries `lightweight` -> `stealth` -> `ultra_stealth`.
If `strategy == "stealth"`, it tries `stealth` -> `ultra_stealth`.
However, `ultra_stealth` often uses third-party APIs or heavy resources.
The logic assumes "heavier is better reliability", which is generally true, but lacks cost awareness in the retry loop itself (though cost controller exists separately).

### B. "Smart" Pagination Detector
**File:** `backend/app/services/orchestrator.py`
The code calls `IntelligentRanker.smart_pagination_detector` inside the loop, but it only checks `if 'list-of-' in url`.
This is a very specific heuristic (`list-of-`) that misses 99% of pagination cases (e.g. `?page=2`, `/page/2`).

## 5. Missing Features for "Industry Grade"

1.  **Distributed Task Queue:** Currently uses `BackgroundTasks` (in-memory). If server restarts, tasks are lost. Should use `Celery` or `RQ` with Redis.
2.  **Centralized Configuration:** Settings are scattered across `production_infra.py`, `main.py`, and `hybrid_scraper.py`. Move to `config.py` using `pydantic-settings`.
3.  **Structured Error Handling:** Many bare `except Exception as e:` blocks just log errors. Should catch specific exceptions and handle them (e.g., `requests.exceptions.Timeout`).
