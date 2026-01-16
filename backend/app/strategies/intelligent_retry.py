"""
Strategy 3: Intelligent Retry
Retries with variation, not repetition.
"""

import asyncio
import random
from typing import Optional, Callable, Any, Dict
from enum import Enum
from loguru import logger


class FailureType(Enum):
    """Types of failures that require different retry strategies."""
    BLOCKED_403 = "blocked_403"
    RATE_LIMITED_429 = "rate_limited_429"
    CLOUDFLARE = "cloudflare"
    CAPTCHA = "captcha"
    TIMEOUT = "timeout"
    EMPTY_CONTENT = "empty_content"
    CONNECTION_ERROR = "connection_error"
    UNKNOWN = "unknown"


class IntelligentRetry:
    """
    Intelligent retry system that adapts based on failure type.
    
    Instead of blindly retrying the same way, it:
    - Diagnoses the failure type
    - Applies targeted fixes
    - Escalates strategies progressively
    """
    
    # Retry configuration per failure type
    RETRY_MATRIX = {
        FailureType.BLOCKED_403: {
            "action": "rotate_identity",
            "wait": (2, 5),
            "escalate_strategy": True,
            "max_retries": 3
        },
        FailureType.RATE_LIMITED_429: {
            "action": "slow_down",
            "wait": (10, 30),
            "escalate_strategy": False,
            "max_retries": 2
        },
        FailureType.CLOUDFLARE: {
            "action": "ultra_stealth",
            "wait": (3, 7),
            "escalate_strategy": True,
            "max_retries": 2
        },
        FailureType.CAPTCHA: {
            "action": "human_in_loop",
            "wait": (0, 0),
            "escalate_strategy": False,
            "max_retries": 1
        },
        FailureType.TIMEOUT: {
            "action": "reduce_concurrency",
            "wait": (1, 3),
            "escalate_strategy": False,
            "max_retries": 3
        },
        FailureType.EMPTY_CONTENT: {
            "action": "enable_rendering",
            "wait": (1, 2),
            "escalate_strategy": True,
            "max_retries": 2
        },
        FailureType.CONNECTION_ERROR: {
            "action": "retry_simple",
            "wait": (2, 5),
            "escalate_strategy": False,
            "max_retries": 3
        },
        FailureType.UNKNOWN: {
            "action": "escalate",
            "wait": (2, 5),
            "escalate_strategy": True,
            "max_retries": 2
        }
    }
    
    # User agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    ]
    
    def __init__(self):
        self.retry_counts: Dict[str, Dict[str, int]] = {}
        self.current_user_agent_idx = 0
    
    def diagnose_failure(self, 
                         status_code: Optional[int] = None,
                         content: str = "",
                         error: Optional[Exception] = None) -> FailureType:
        """
        Diagnose the type of failure to determine retry strategy.
        """
        content_lower = content.lower() if content else ""
        
        # Check status codes
        if status_code == 403:
            return FailureType.BLOCKED_403
        elif status_code == 429:
            return FailureType.RATE_LIMITED_429
        elif status_code == 503:
            if 'cloudflare' in content_lower:
                return FailureType.CLOUDFLARE
            return FailureType.RATE_LIMITED_429
        
        # Check content for protection signals
        if any(sig in content_lower for sig in ['captcha', 'recaptcha', 'hcaptcha']):
            return FailureType.CAPTCHA
        
        if any(sig in content_lower for sig in ['cloudflare', 'cf-ray', 'checking your browser']):
            return FailureType.CLOUDFLARE
        
        # Check for empty/minimal content
        if len(content) < 500:
            return FailureType.EMPTY_CONTENT
        
        # Check error types
        if error:
            error_str = str(error).lower()
            if 'timeout' in error_str:
                return FailureType.TIMEOUT
            if 'connection' in error_str or 'refused' in error_str:
                return FailureType.CONNECTION_ERROR
        
        return FailureType.UNKNOWN
    
    async def execute_with_retry(self,
                                  scrape_func: Callable,
                                  url: str,
                                  url_key: str = None,
                                  **kwargs) -> tuple[str, Dict]:
        """
        Execute a scraping function with intelligent retries.
        
        Args:
            scrape_func: Async function to call
            url: URL being scraped
            url_key: Unique key for tracking retries (uses domain if not provided)
            **kwargs: Arguments to pass to scrape_func
            
        Returns:
            (content, metadata) tuple
        """
        from urllib.parse import urlparse
        
        url_key = url_key or urlparse(url).netloc
        
        if url_key not in self.retry_counts:
            self.retry_counts[url_key] = {}
        
        current_strategy = kwargs.get('strategy', 'lightweight')
        strategies = ['lightweight', 'stealth', 'ultra_stealth']
        
        metadata = {
            "attempts": 0,
            "failure_types": [],
            "final_strategy": current_strategy,
            "success": False
        }
        
        for attempt in range(5):  # Max 5 total attempts
            metadata["attempts"] = attempt + 1
            
            try:
                logger.info(f"[Retry] Attempt {attempt + 1} for {url_key} using {current_strategy}")
                
                # Execute the scrape
                content = await scrape_func(url, **kwargs)
                
                # Check if content is valid
                if content and len(content) > 500:
                    metadata["success"] = True
                    metadata["final_strategy"] = current_strategy
                    return content, metadata
                
                # Diagnose failure
                failure_type = self.diagnose_failure(content=content)
                
            except asyncio.TimeoutError:
                failure_type = FailureType.TIMEOUT
            except Exception as e:
                failure_type = self.diagnose_failure(error=e)
            
            metadata["failure_types"].append(failure_type.value)
            
            # Get retry configuration
            config = self.RETRY_MATRIX.get(failure_type, self.RETRY_MATRIX[FailureType.UNKNOWN])
            
            # Check if we've exceeded retries for this failure type
            failure_key = failure_type.value
            self.retry_counts[url_key][failure_key] = self.retry_counts[url_key].get(failure_key, 0) + 1
            
            if self.retry_counts[url_key][failure_key] > config["max_retries"]:
                logger.warning(f"[Retry] Max retries for {failure_type.value} on {url_key}")
                continue
            
            # Apply action based on failure type
            action = config["action"]
            
            if action == "rotate_identity":
                self.current_user_agent_idx = (self.current_user_agent_idx + 1) % len(self.USER_AGENTS)
                kwargs['user_agent'] = self.USER_AGENTS[self.current_user_agent_idx]
                logger.info(f"[Retry] Rotated user agent")
            
            elif action == "slow_down":
                wait_time = random.uniform(*config["wait"])
                logger.info(f"[Retry] Rate limited, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            
            elif action == "ultra_stealth":
                kwargs['force_ultra_stealth'] = True
                current_strategy = 'ultra_stealth'
            
            elif action == "enable_rendering":
                kwargs['force_playwright'] = True
                current_strategy = 'stealth'
            
            elif action == "human_in_loop":
                logger.warning(f"[Retry] CAPTCHA detected - would trigger human-in-loop")
                metadata["captcha_detected"] = True
                break
            
            elif action == "escalate" and config["escalate_strategy"]:
                # Move to next heavier strategy
                current_idx = strategies.index(current_strategy) if current_strategy in strategies else 0
                if current_idx < len(strategies) - 1:
                    current_strategy = strategies[current_idx + 1]
                    logger.info(f"[Retry] Escalating to {current_strategy}")
            
            # Wait before retry
            if config["wait"][1] > 0:
                wait_time = random.uniform(*config["wait"])
                await asyncio.sleep(wait_time)
        
        return "", metadata
    
    def get_stats(self) -> Dict:
        """Get retry statistics."""
        return {
            "tracked_urls": len(self.retry_counts),
            "retry_breakdown": {
                url: dict(counts) 
                for url, counts in list(self.retry_counts.items())[:20]
            }
        }
    
    def clear(self):
        """Clear retry tracking."""
        self.retry_counts.clear()


# Singleton instance
intelligent_retry = IntelligentRetry()
