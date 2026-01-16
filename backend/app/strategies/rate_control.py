"""
Strategy 4: Rate Control
Dynamic throttling based on response patterns.
"""

import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from loguru import logger


class RateController:
    """
    Dynamic rate limiting that adapts to site responses.
    
    Features:
    - Per-domain rate limits
    - Automatic slowdown after errors
    - Speed up after success streaks
    - Respects Retry-After headers
    """
    
    # Default rate limits (requests per second)
    DEFAULT_RATES = {
        "aggressive": 0.5,     # 1 request per 2 seconds
        "normal": 0.2,         # 1 request per 5 seconds
        "conservative": 0.1,   # 1 request per 10 seconds
        "ultra_safe": 0.05     # 1 request per 20 seconds
    }
    
    # Known site rate limits
    SITE_SPECIFIC_RATES = {
        "amazon.com": 0.1,
        "linkedin.com": 0.05,
        "facebook.com": 0.05,
        "indeed.com": 0.1,
        "glassdoor.com": 0.1,
        "ebay.com": 0.1,
        "twitter.com": 0.05,
        "instagram.com": 0.05,
    }
    
    def __init__(self):
        self.domain_stats: Dict[str, Dict] = defaultdict(lambda: {
            "last_request": 0,
            "success_streak": 0,
            "error_streak": 0,
            "current_rate": 0.2,  # Default: 1 req per 5 seconds
            "total_requests": 0,
            "total_errors": 0,
            "retry_after": None
        })
        self.global_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        self.domain_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def acquire(self, domain: str) -> None:
        """
        Wait for rate limit before making request.
        
        Args:
            domain: Domain being accessed
        """
        domain = self._normalize_domain(domain)
        stats = self.domain_stats[domain]
        
        # Get domain-specific or default rate
        base_rate = self.SITE_SPECIFIC_RATES.get(domain, stats["current_rate"])
        
        # Check Retry-After
        if stats["retry_after"] and datetime.now() < stats["retry_after"]:
            wait_time = (stats["retry_after"] - datetime.now()).total_seconds()
            logger.info(f"[Rate] Waiting {wait_time:.1f}s for Retry-After on {domain}")
            await asyncio.sleep(wait_time)
            stats["retry_after"] = None
        
        async with self.domain_locks[domain]:
            # Calculate minimum wait time
            min_interval = 1.0 / base_rate
            elapsed = time.time() - stats["last_request"]
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                # Add jitter
                wait_time += wait_time * 0.1 * (hash(domain) % 10) / 10
                logger.debug(f"[Rate] Waiting {wait_time:.2f}s for {domain}")
                await asyncio.sleep(wait_time)
            
            stats["last_request"] = time.time()
            stats["total_requests"] += 1
    
    def record_success(self, domain: str) -> None:
        """Record successful request, potentially speeding up."""
        domain = self._normalize_domain(domain)
        stats = self.domain_stats[domain]
        
        stats["success_streak"] += 1
        stats["error_streak"] = 0
        
        # Speed up after 5 consecutive successes
        if stats["success_streak"] >= 5:
            old_rate = stats["current_rate"]
            # Don't exceed site-specific rate
            max_rate = self.SITE_SPECIFIC_RATES.get(domain, 0.5)
            stats["current_rate"] = min(stats["current_rate"] * 1.2, max_rate)
            if stats["current_rate"] != old_rate:
                logger.info(f"[Rate] Speeding up {domain}: {old_rate:.2f} → {stats['current_rate']:.2f} req/s")
            stats["success_streak"] = 0
    
    def record_error(self, domain: str, status_code: Optional[int] = None, 
                     retry_after: Optional[int] = None) -> None:
        """Record failed request, slowing down."""
        domain = self._normalize_domain(domain)
        stats = self.domain_stats[domain]
        
        stats["error_streak"] += 1
        stats["success_streak"] = 0
        stats["total_errors"] += 1
        
        # Handle Retry-After header
        if retry_after:
            stats["retry_after"] = datetime.now() + timedelta(seconds=retry_after)
            logger.info(f"[Rate] Retry-After {retry_after}s for {domain}")
        
        # Slow down after errors
        if status_code in [429, 503]:
            # Aggressive slowdown for rate limits
            stats["current_rate"] = max(stats["current_rate"] * 0.5, 0.02)
            logger.warning(f"[Rate] Rate limited on {domain}, slowing to {stats['current_rate']:.3f} req/s")
        elif status_code in [403]:
            # Moderate slowdown for blocks
            stats["current_rate"] = max(stats["current_rate"] * 0.7, 0.05)
            logger.warning(f"[Rate] Blocked on {domain}, slowing to {stats['current_rate']:.3f} req/s")
        elif stats["error_streak"] >= 3:
            # General slowdown after 3 consecutive errors
            stats["current_rate"] = max(stats["current_rate"] * 0.8, 0.05)
            logger.warning(f"[Rate] Error streak on {domain}, slowing to {stats['current_rate']:.3f} req/s")
    
    def get_stats(self) -> Dict:
        """Get rate control statistics."""
        return {
            "domains_tracked": len(self.domain_stats),
            "domain_rates": {
                domain: {
                    "rate": f"{stats['current_rate']:.3f} req/s",
                    "total_requests": stats["total_requests"],
                    "total_errors": stats["total_errors"],
                    "success_streak": stats["success_streak"],
                    "error_streak": stats["error_streak"]
                }
                for domain, stats in list(self.domain_stats.items())[:20]
            },
            "site_specific_limits": self.SITE_SPECIFIC_RATES
        }
    
    def set_rate(self, domain: str, rate: float) -> None:
        """Manually set rate limit for a domain."""
        domain = self._normalize_domain(domain)
        self.domain_stats[domain]["current_rate"] = rate
        logger.info(f"[Rate] Set {domain} rate to {rate:.3f} req/s")
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain name."""
        from urllib.parse import urlparse
        
        if domain.startswith("http"):
            domain = urlparse(domain).netloc
        
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain.lower()
    
    def reset(self, domain: Optional[str] = None) -> None:
        """Reset rate limits for a domain or all domains."""
        if domain:
            domain = self._normalize_domain(domain)
            if domain in self.domain_stats:
                del self.domain_stats[domain]
        else:
            self.domain_stats.clear()


# Singleton instance
rate_controller = RateController()
