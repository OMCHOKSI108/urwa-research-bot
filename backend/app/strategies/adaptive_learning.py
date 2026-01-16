"""
Strategy 2: Adaptive Strategy Learning
Tracks success rates per domain and learns which strategy works best.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger


class AdaptiveStrategyLearner:
    """
    Learns from scraping attempts and remembers what works for each domain.
    
    Features:
    - Tracks success/failure per domain per strategy
    - Recommends optimal strategy based on history
    - Decays old data over time
    - Persists learning to disk
    """
    
    STRATEGIES = ["lightweight", "stealth", "ultra_stealth"]
    PERSISTENCE_FILE = "app/static/strategy_learning.json"
    
    def __init__(self):
        self.domain_stats: Dict[str, Dict[str, Dict]] = {}
        self.load()
    
    def record(self, domain: str, strategy: str, success: bool, duration: float = 0):
        """
        Record a scraping attempt result.
        
        Args:
            domain: The domain that was scraped
            strategy: Which strategy was used
            success: Whether it succeeded
            duration: How long it took (seconds)
        """
        domain = self._normalize_domain(domain)
        
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {}
        
        if strategy not in self.domain_stats[domain]:
            self.domain_stats[domain][strategy] = {
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "avg_duration": 0,
                "last_success": None,
                "last_failure": None,
                "success_rate": 0.0
            }
        
        stats = self.domain_stats[domain][strategy]
        stats["attempts"] += 1
        
        if success:
            stats["successes"] += 1
            stats["last_success"] = datetime.now().isoformat()
        else:
            stats["failures"] += 1
            stats["last_failure"] = datetime.now().isoformat()
        
        # Update average duration
        if duration > 0:
            old_avg = stats["avg_duration"]
            stats["avg_duration"] = (old_avg * (stats["attempts"] - 1) + duration) / stats["attempts"]
        
        # Calculate success rate
        stats["success_rate"] = stats["successes"] / stats["attempts"] if stats["attempts"] > 0 else 0
        
        logger.debug(f"[Learn] {domain} + {strategy}: {'✓' if success else '✗'} (rate: {stats['success_rate']:.0%})")
        
        # Persist periodically
        if sum(s["attempts"] for s in self.domain_stats.get(domain, {}).values()) % 10 == 0:
            self.save()
    
    def recommend(self, domain: str, default: str = "lightweight") -> str:
        """
        Recommend the best strategy for a domain based on historical success.
        
        Args:
            domain: The domain to scrape
            default: Default strategy if no history exists
            
        Returns:
            Best strategy name
        """
        domain = self._normalize_domain(domain)
        
        if domain not in self.domain_stats:
            logger.debug(f"[Learn] No history for {domain}, using default: {default}")
            return default
        
        stats = self.domain_stats[domain]
        
        # Find strategy with highest success rate (minimum 3 attempts)
        best_strategy = default
        best_rate = 0.0
        
        for strategy, data in stats.items():
            if data["attempts"] >= 3 and data["success_rate"] > best_rate:
                best_rate = data["success_rate"]
                best_strategy = strategy
        
        # If best rate is still low, escalate
        if best_rate < 0.5:
            # Try the next heavier strategy
            current_idx = self.STRATEGIES.index(best_strategy) if best_strategy in self.STRATEGIES else 0
            if current_idx < len(self.STRATEGIES) - 1:
                best_strategy = self.STRATEGIES[current_idx + 1]
        
        logger.info(f"[Learn] Recommend {best_strategy} for {domain} (success rate: {best_rate:.0%})")
        return best_strategy
    
    def get_domain_stats(self, domain: str) -> Optional[Dict]:
        """Get statistics for a specific domain."""
        domain = self._normalize_domain(domain)
        return self.domain_stats.get(domain)
    
    def get_all_stats(self) -> Dict:
        """Get all domain statistics."""
        return {
            "domains": len(self.domain_stats),
            "total_attempts": sum(
                sum(s["attempts"] for s in stats.values())
                for stats in self.domain_stats.values()
            ),
            "top_domains": self._get_top_domains(10),
            "strategy_effectiveness": self._get_strategy_effectiveness()
        }
    
    def _get_top_domains(self, limit: int) -> list:
        """Get domains with most scraping attempts."""
        domain_totals = [
            (domain, sum(s["attempts"] for s in stats.values()))
            for domain, stats in self.domain_stats.items()
        ]
        domain_totals.sort(key=lambda x: x[1], reverse=True)
        return [{"domain": d, "attempts": a} for d, a in domain_totals[:limit]]
    
    def _get_strategy_effectiveness(self) -> Dict:
        """Calculate overall effectiveness per strategy."""
        effectiveness = {s: {"successes": 0, "attempts": 0} for s in self.STRATEGIES}
        
        for stats in self.domain_stats.values():
            for strategy, data in stats.items():
                if strategy in effectiveness:
                    effectiveness[strategy]["successes"] += data["successes"]
                    effectiveness[strategy]["attempts"] += data["attempts"]
        
        return {
            s: {
                "success_rate": d["successes"] / d["attempts"] if d["attempts"] > 0 else 0,
                "total_attempts": d["attempts"]
            }
            for s, d in effectiveness.items()
        }
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain name."""
        from urllib.parse import urlparse
        
        if domain.startswith("http"):
            domain = urlparse(domain).netloc
        
        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain.lower()
    
    def save(self):
        """Persist learning data to disk."""
        try:
            os.makedirs(os.path.dirname(self.PERSISTENCE_FILE), exist_ok=True)
            with open(self.PERSISTENCE_FILE, 'w') as f:
                json.dump(self.domain_stats, f, indent=2, default=str)
            logger.debug(f"[Learn] Saved {len(self.domain_stats)} domain profiles")
        except Exception as e:
            logger.warning(f"[Learn] Failed to save: {e}")
    
    def load(self):
        """Load learning data from disk."""
        try:
            if os.path.exists(self.PERSISTENCE_FILE):
                with open(self.PERSISTENCE_FILE, 'r') as f:
                    self.domain_stats = json.load(f)
                logger.info(f"[Learn] Loaded {len(self.domain_stats)} domain profiles")
        except Exception as e:
            logger.warning(f"[Learn] Failed to load: {e}")
            self.domain_stats = {}
    
    def decay_old_data(self, days: int = 30):
        """Remove data older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        for domain in list(self.domain_stats.keys()):
            for strategy in list(self.domain_stats[domain].keys()):
                stats = self.domain_stats[domain][strategy]
                last_activity = stats.get("last_success") or stats.get("last_failure")
                
                if last_activity and last_activity < cutoff_str:
                    del self.domain_stats[domain][strategy]
            
            # Remove domain if no strategies left
            if not self.domain_stats[domain]:
                del self.domain_stats[domain]
        
        self.save()


# Singleton instance
strategy_learner = AdaptiveStrategyLearner()
