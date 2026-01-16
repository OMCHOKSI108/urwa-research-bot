"""
Hybrid scraper that intelligently chooses between multiple strategies.
ENHANCED with production-grade strategy integration.

Strategy Pipeline:
1. Compliance Check → robots.txt, blacklist
2. Site Profiler → Bot detection, protection level
3. Adaptive Learning → Learned success rates
4. Rate Control → Dynamic throttling  
5. Strategy Selection → lightweight/stealth/ultra
6. Intelligent Retry → Failure-specific retries
7. Evidence Capture → On failure: save diagnostics
"""
from app.agents.lightweight_scraper import LightweightScraper
from app.agents.scraper import StealthScraper
from app.agents.ultra_stealth_scraper import UltraStealthScraper
from loguru import logger
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
import asyncio
import time
import threading


class HybridScraper:
    """
    Production-grade intelligent multi-strategy scraper with:
    - Site profiling before scraping
    - Adaptive strategy learning
    - Intelligent failure-specific retries
    - Dynamic rate limiting
    - Evidence capture for debugging
    - Compliance checking (robots.txt)
    """

    # Sites that are known to require heavy scraping
    HEAVY_SITES = [
        'linkedin.com', 'facebook.com', 'instagram.com', 'twitter.com',
        'amazon.com', 'ebay.com', 'google.com', 'cloudflare.com',
        'zillow.com', 'indeed.com', 'glassdoor.com'
    ]

    # Sites that need ultra stealth
    ULTRA_STEALTH_SITES = [
        'linkedin.com', 'facebook.com', 'instagram.com', 'twitter.com',
        'cloudflare.com', 'datadome.com', 'akamai.com', 'perimeterx.com'
    ]
    
    # Strategy name mapping
    STRATEGY_MAP = {
        'lightweight': 'lightweight',
        'stealth': 'playwright',
        'ultra_stealth': 'ultra_stealth'
    }

    def __init__(self, use_strategies: bool = True):
        """
        Initialize HybridScraper.
        
        Args:
            use_strategies: Enable production strategy integration (default: True)
        """
        self.lightweight = LightweightScraper()
        self.stealth = StealthScraper()
        self.ultra_stealth = UltraStealthScraper()
        self.use_strategies = use_strategies

        # Stats tracking (thread-safe)
        self._stats_lock = threading.Lock()
        self.stats = {
            "lightweight_success": 0,
            "playwright_success": 0,
            "ultra_stealth_success": 0,
            "total_failures": 0,
            "total_requests": 0
        }
        
        # Import strategy components (lazy to avoid circular imports)
        self._strategies_loaded = False
        self._site_profiler = None
        self._strategy_learner = None
        self._rate_controller = None
        self._evidence_capture = None
        self._compliance_checker = None
    
    def _load_strategies(self):
        """Lazy load strategy components."""
        if self._strategies_loaded:
            return
        
        try:
            from app.strategies import (
                site_profiler, strategy_learner, rate_controller,
                evidence_capture, compliance_checker
            )
            self._site_profiler = site_profiler
            self._strategy_learner = strategy_learner
            self._rate_controller = rate_controller
            self._evidence_capture = evidence_capture
            self._compliance_checker = compliance_checker
            self._strategies_loaded = True
            logger.info("[Hybrid] Production strategies loaded successfully")
        except ImportError as e:
            logger.warning(f"[Hybrid] Strategy import failed, using basic mode: {e}")
            self.use_strategies = False

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    def _needs_heavy_scraping(self, url: str) -> bool:
        """Check if URL requires heavy scraping strategy."""
        return any(site in url.lower() for site in self.HEAVY_SITES)

    def _needs_ultra_stealth(self, url: str) -> bool:
        """Check if URL requires ultra stealth mode."""
        return any(site in url.lower() for site in self.ULTRA_STEALTH_SITES)

    async def scrape(self, url: str, force_playwright: bool = False, 
                    force_ultra_stealth: bool = False) -> str:
        """
        Scrape URL with automatic strategy selection.
        
        Enhanced flow:
        1. Check compliance (robots.txt)
        2. Profile site for protection
        3. Get learned strategy recommendation  
        4. Apply rate limiting
        5. Execute with selected strategy
        6. Record results for learning
        7. Capture evidence on failure

        Args:
            url: Target URL
            force_playwright: Skip lightweight and go straight to Playwright
            force_ultra_stealth: Use ultra stealth mode directly

        Returns:
            Markdown/JSON content or empty string if failed
        """
        with self._stats_lock:
            self.stats["total_requests"] += 1
        start_time = time.time()
        domain = self._get_domain(url)
        
        logger.info(f"[Hybrid] Processing: {url[:60]}...")
        
        # Load strategies if enabled
        if self.use_strategies:
            self._load_strategies()
        
        # ===== STEP 1: Compliance Check =====
        if self.use_strategies and self._compliance_checker:
            try:
                compliance = await self._compliance_checker.check(url)
                if not compliance.get("allowed", True):
                    logger.warning(f"[Hybrid] Blocked by compliance: {compliance.get('reason')}")
                    return ""
                
                if compliance.get("warnings"):
                    for warning in compliance["warnings"]:
                        logger.info(f"[Hybrid] ⚠️ Compliance warning: {warning}")
            except Exception as e:
                logger.debug(f"[Hybrid] Compliance check error: {e}")
        
        # ===== STEP 2: Site Profiling =====
        profile = None
        if self.use_strategies and self._site_profiler:
            try:
                profile = await self._site_profiler.profile(url)
                logger.info(f"[Hybrid] Profile: risk={profile.get('risk')}, "
                           f"protection={profile.get('bot_wall', 'none')}, "
                           f"recommended={profile.get('recommended_strategy')}")
            except Exception as e:
                logger.debug(f"[Hybrid] Profiling error: {e}")
        
        # ===== STEP 3: Strategy Selection =====
        selected_strategy = self._select_strategy(
            url, profile, force_playwright, force_ultra_stealth
        )
        logger.info(f"[Hybrid] Selected strategy: {selected_strategy}")
        
        # ===== STEP 4: Rate Limiting =====
        if self.use_strategies and self._rate_controller:
            try:
                await self._rate_controller.acquire(domain)
            except Exception as e:
                logger.debug(f"[Hybrid] Rate control error: {e}")
        
        # ===== STEP 5: Execute Scraping =====
        content = ""
        strategy_used = selected_strategy
        status_code = None
        
        try:
            content, strategy_used = await self._execute_with_fallback(
                url, selected_strategy, force_ultra_stealth
            )
        except Exception as e:
            logger.error(f"[Hybrid] Scrape error: {e}")
            content = ""
        
        duration = time.time() - start_time
        success = bool(content and len(content) > 100)
        
        # ===== STEP 6: Record Results for Learning =====
        if self.use_strategies and self._strategy_learner:
            try:
                self._strategy_learner.record(domain, strategy_used, success, duration)
            except Exception as e:
                logger.debug(f"[Hybrid] Learning record error: {e}")
        
        # Rate controller feedback
        if self.use_strategies and self._rate_controller:
            try:
                if success:
                    self._rate_controller.record_success(domain)
                else:
                    self._rate_controller.record_error(domain, status_code)
            except Exception as e:
                logger.debug(f"[Hybrid] Rate feedback error: {e}")
        
        # ===== STEP 7: Evidence Capture on Failure =====
        if not success and self.use_strategies and self._evidence_capture:
            try:
                self._evidence_capture.capture(
                    url=url,
                    failure_type=self._diagnose_failure(content),
                    status_code=status_code,
                    html_content=content[:50000] if content else "",
                    request_context={
                        "strategy": strategy_used,
                        "profile_risk": profile.get("risk") if profile else None,
                        "duration": duration
                    }
                )
            except Exception as e:
                logger.debug(f"[Hybrid] Evidence capture error: {e}")
        
        if success:
            logger.info(f"[Hybrid] ✓ Success with {strategy_used} ({duration:.1f}s)")
        else:
            logger.warning(f"[Hybrid] ✗ Failed after {duration:.1f}s")
        
        return content

    def _select_strategy(self, url: str, profile: dict = None,
                        force_playwright: bool = False,
                        force_ultra_stealth: bool = False) -> str:
        """
        Select best strategy using all available signals.
        
        Priority:
        1. Force flags (if set)
        2. Learned success rates (if available)
        3. Profile recommendation
        4. URL-based heuristics
        """
        domain = self._get_domain(url)
        
        # Honor force flags
        if force_ultra_stealth:
            return "ultra_stealth"
        if force_playwright:
            return "stealth"
        
        # Safety Override: If site is known extreme risk, always use ultra_stealth
        if profile and profile.get("risk") == "extreme":
            logger.info(f"[Hybrid] Extreme risk site detected. Forcing ultra_stealth strategy.")
            return "ultra_stealth"
        
        # Check learned recommendations
        if self.use_strategies and self._strategy_learner:
            try:
                learned = self._strategy_learner.recommend(domain)
                
                if learned and learned != "lightweight":
                    logger.info(f"[Hybrid] Using learned strategy: {learned}")
                    return learned
            except Exception:
                pass
        
        # Use profile recommendation
        if profile:
            rec = profile.get("recommended_strategy", "lightweight")
            if rec in ["ultra_stealth", "stealth"]:
                return rec
        
        # URL-based heuristics
        if self._needs_ultra_stealth(url):
            return "ultra_stealth"
        if self._needs_heavy_scraping(url):
            return "stealth"
        
        return "lightweight"

    async def _execute_with_fallback(self, url: str, strategy: str,
                                     force_ultra_stealth: bool = False) -> Tuple[str, str]:
        """
        Execute scraping with automatic fallback to heavier strategies.
        
        Returns:
            (content, strategy_used)
        """
        strategies_to_try = []
        
        # Build priority list based on selected strategy
        # Always include fallbacks - start with lighter strategies when possible
        if strategy == "ultra_stealth":
            # high risk site - go straight to heavy artillery to avoid IP bans from lighter attempts
            strategies_to_try = ["ultra_stealth"]
        elif strategy == "stealth":
            strategies_to_try = ["stealth", "ultra_stealth"]
        else:  # lightweight
            strategies_to_try = ["lightweight", "stealth", "ultra_stealth"]
        
        for strat in strategies_to_try:
            content = await self._execute_strategy(url, strat)
            
            # success criteria:
            # 1. Content exists and has reasonable length
            # 2. Content is NOT a known block page (Cloudflare, Captcha, etc.)
            failure_reason = self._diagnose_failure(content)
            is_valid = bool(content and len(content) > 100 and failure_reason in ["unknown", "minimal_content"])
            
            # Special case: minimal content is acceptable if we are in ultra_stealth (might be small JSON/API response)
            if strat == "ultra_stealth" and failure_reason == "minimal_content" and content:
                 is_valid = True

            if is_valid:
                # Update stats (thread-safe)
                with self._stats_lock:
                    if strat == "lightweight":
                        self.stats["lightweight_success"] += 1
                    elif strat == "stealth":
                        self.stats["playwright_success"] += 1
                    else:
                        self.stats["ultra_stealth_success"] += 1
                
                return content, strat
            
            logger.info(f"[Hybrid] {strat} failed (reason: {failure_reason}), trying next...")
        
        # All failed (thread-safe)
        with self._stats_lock:
            self.stats["total_failures"] += 1
        return "", strategies_to_try[-1]

    async def _execute_strategy(self, url: str, strategy: str) -> str:
        """Execute a specific scraping strategy."""
        raw_result = ""
        try:
            if strategy == "lightweight":
                logger.info(f"[Hybrid] Trying lightweight...")
                raw_result = await self.lightweight.scrape(url)
                if raw_result and len(raw_result.split()) > 20:
                     pass
                else:
                    raw_result = ""
            
            elif strategy == "stealth":
                logger.info(f"[Hybrid] Trying Playwright stealth...")
                raw_result = await self.stealth.scrape(url, max_retries=2)
            
            elif strategy == "ultra_stealth":
                logger.info(f"[Hybrid] Trying Ultra Stealth...")
                raw_result = await self.ultra_stealth.scrape(url, max_retries=3)
            
        except Exception as e:
            logger.warning(f"[Hybrid] Strategy {strategy} error: {e}")
            return ""

        # Global JSON Unpacking (for stealth/ultra_stealth which return JSON strings)
        if raw_result and len(raw_result) > 10:
            # More robust JSON detection - check if it's valid JSON first
            stripped = raw_result.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    import json
                    data = json.loads(stripped)
                    if isinstance(data, dict):
                        # Extract text content from various keys used by our scrapers
                        text = data.get("raw_html_content", "") or data.get("content", "") or data.get("text_content", "")
                        
                        # If text implies empty body but we have structured data, format it
                        items = data.get("structured_data", {}).get("items", [])
                        
                        if items:
                            text += "\n\n### Extracted Items:\n"
                            for item in items[:20]:
                                 title = item.get('title') or item.get('name')
                                 if title:
                                     text += f"- {title} {item.get('price', '')}\n"
                        
                        if text:
                            return text
                except (json.JSONDecodeError, ValueError) as e:
                    # Not valid JSON, return raw result
                    logger.debug(f"[Hybrid] Content looks like JSON but isn't valid, using as-is: {e}")
                except Exception as e:
                    logger.warning(f"[Hybrid] Unexpected error in JSON unpacking: {e}")
        
        return raw_result

    def _diagnose_failure(self, content: str) -> str:
        """Diagnose failure type from content."""
        if not content:
            return "empty_content"
        
        content_lower = content.lower()
        
        if any(s in content_lower for s in ['captcha', 'recaptcha', 'hcaptcha']):
            return "captcha"
        if any(s in content_lower for s in ['cloudflare', 'cf-ray']):
            return "cloudflare"
        if 'access denied' in content_lower or 'forbidden' in content_lower:
            return "blocked"
        if len(content) < 500:
            return "minimal_content"
        
        return "unknown"

    async def scrape_with_retry(self, url: str, max_total_attempts: int = 5) -> str:
        """
        Scrape with multiple attempts across all strategies.
        """
        for attempt in range(max_total_attempts):
            content = await self.scrape(url)
            if content:
                return content
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return ""

    def get_stats(self) -> dict:
        """Return scraping strategy statistics (thread-safe)."""
        with self._stats_lock:
            total = self.stats["total_requests"] or 1
            return {
                **self.stats,
                "success_rate": (self.stats["lightweight_success"] + 
                               self.stats["playwright_success"] + 
                               self.stats["ultra_stealth_success"]) / total,
                "lightweight_rate": self.stats["lightweight_success"] / total,
                "playwright_rate": self.stats["playwright_success"] / total,
                "ultra_stealth_rate": self.stats["ultra_stealth_success"] / total
            }

    def get_session_history(self) -> list:
        """Return combined session history from all scrapers."""
        history = []
        history.extend(self.stealth.get_session_history())
        history.extend(self.ultra_stealth.get_session_history())
        return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)[:100]

    def clear_cache(self):
        """Clear caches from all scrapers."""
        self.stealth.clear_cache()
        self.ultra_stealth.clear_cache()

    @property
    def cache(self):
        """Access to stealth scraper cache."""
        return self.stealth.cache

    @property
    def session_history(self):
        """Access to combined session history."""
        return self.get_session_history()
