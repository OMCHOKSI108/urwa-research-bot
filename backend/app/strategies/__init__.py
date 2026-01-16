"""
URWA Brain Strategy Engine
Production-grade scraping strategies for real-world survival.

Strategies included:
1. Site Profiler - Detects protection before scraping
2. Adaptive Learning - Learns what works per domain
3. Intelligent Retry - Retries with variation, not repetition
4. Rate Control - Dynamic throttling based on responses
5. Evidence Capture - Saves failure data for debugging
6. Semantic Extractor - Multi-fallback extraction for any site
7. Compliance - Respects robots.txt and legal requirements
"""

from .site_profiler import SiteProfiler, site_profiler
from .adaptive_learning import AdaptiveStrategyLearner, strategy_learner
from .intelligent_retry import IntelligentRetry, intelligent_retry, FailureType
from .rate_control import RateController, rate_controller
from .evidence_capture import EvidenceCapture, evidence_capture
from .semantic_extractor import SemanticExtractor, semantic_extract
from .compliance import ComplianceChecker, compliance_checker
from .stealth_techniques import (
    FingerprintMasker, fingerprint_masker,
    SessionTrustBuilder, trust_builder,
    BehaviorSimulator, behavior_sim,
    CookiePersistence, cookie_persistence,
    LowAndSlow, low_and_slow
)

__all__ = [
    # Classes
    'SiteProfiler',
    'AdaptiveStrategyLearner',
    'IntelligentRetry',
    'RateController',
    'EvidenceCapture',
    'SemanticExtractor',
    'ComplianceChecker',
    'FailureType',
    
    # Stealth Technique Classes
    'FingerprintMasker',
    'SessionTrustBuilder',
    'BehaviorSimulator',
    'CookiePersistence',
    'LowAndSlow',
    
    # Singleton instances
    'site_profiler',
    'strategy_learner',
    'intelligent_retry',
    'rate_controller',
    'evidence_capture',
    'compliance_checker',
    
    # Stealth technique instances
    'fingerprint_masker',
    'trust_builder',
    'behavior_sim',
    'cookie_persistence',
    'low_and_slow',
    
    # Functions
    'semantic_extract',
    
    # Main engine
    'StrategyEngine',
]


class StrategyEngine:
    """
    Master orchestrator that combines all strategies.
    
    Usage:
        engine = StrategyEngine()
        
        # Profile site before scraping
        profile = await engine.profile(url)
        
        # Get recommended strategy
        strategy = engine.recommend_strategy(url, profile)
        
        # Scrape with all protections
        content, metadata = await engine.scrape(url, scraper)
    """
    
    def __init__(self):
        self.profiler = site_profiler
        self.learner = strategy_learner
        self.retry = intelligent_retry
        self.rate = rate_controller
        self.evidence = evidence_capture
        self.compliance = compliance_checker
    
    async def profile(self, url: str) -> dict:
        """Profile a site to determine protection level."""
        return await self.profiler.profile(url)
    
    async def check_compliance(self, url: str) -> dict:
        """Check if URL can be scraped compliantly."""
        return await self.compliance.check(url)
    
    def recommend_strategy(self, url: str, profile: dict = None) -> str:
        """
        Recommend best strategy based on profile and learning.
        
        Priority:
        1. Learned success rates (if available)
        2. Profile recommendation
        3. Default
        """
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        # Check learning first
        known_domain = self.learner.get_domain_stats(domain)
        if known_domain:
            return self.learner.recommend(domain)
        
        # Use profile recommendation
        if profile:
            return profile.get("recommended_strategy", "lightweight")
        
        return "lightweight"
    
    async def acquire_rate_limit(self, url: str):
        """Wait for rate limit before scraping."""
        await self.rate.acquire(url)
    
    def record_result(self, url: str, strategy: str, success: bool, 
                      duration: float = 0, status_code: int = None,
                      content: str = "", error: Exception = None):
        """Record scraping result for all strategies."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Record for learning
        self.learner.record(domain, strategy, success, duration)
        
        # Update rate controller
        if success:
            self.rate.record_success(domain)
        else:
            self.rate.record_error(domain, status_code)
            
            # Capture evidence on failure
            failure_type = self.retry.diagnose_failure(status_code, content, error)
            self.evidence.capture(
                url=url,
                failure_type=failure_type.value,
                status_code=status_code,
                html_content=content[:50000] if content else "",
                error=error,
                request_context={
                    "strategy": strategy,
                    "duration": duration
                }
            )
    
    def get_stats(self) -> dict:
        """Get comprehensive statistics from all strategies."""
        return {
            "learning": self.learner.get_all_stats(),
            "rate_control": self.rate.get_stats(),
            "evidence": self.evidence.get_failure_stats(),
            "retry": self.retry.get_stats(),
            "profiles_cached": len(self.profiler.get_cached_profiles())
        }
    
    def clear_all(self):
        """Clear all caches and data."""
        self.profiler.clear_cache()
        self.rate.reset()
        self.retry.clear()
        self.evidence.clear_all()


# Global strategy engine instance
strategy_engine = StrategyEngine()
