"""
Strategy 10: Compliance
Respects robots.txt, ToS, and legal requirements.
"""

import aiohttp
import asyncio
from typing import Dict, Optional, Set
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from datetime import datetime, timedelta
from loguru import logger


class ComplianceChecker:
    """
    Ensures scraping respects legal and ethical boundaries.
    
    Features:
    - robots.txt parsing and enforcement
    - Rate limit detection from robots.txt
    - Sensitive site blacklist
    - ToS awareness
    """
    
    # Sites that should never be scraped
    BLACKLIST = {
        # Government/Military
        "gov", "mil",
        # Healthcare
        "hipaa", "healthcare.gov",
        # Financial (sensitive)
        "bank", "paypal.com", "stripe.com",
        # Password managers
        "lastpass.com", "1password.com", "bitwarden.com",
        # Email providers
        "mail.google.com", "outlook.live.com",
    }
    
    # Sites requiring extra caution
    CAUTION_LIST = {
        "linkedin.com": "Aggressive anti-scraping. Use carefully.",
        "facebook.com": "Strict ToS against scraping.",
        "instagram.com": "Meta ToS prohibits automated access.",
        "twitter.com": "API access preferred over scraping.",
    }
    
    USER_AGENT = "URWABot/1.0 (+https://github.com/your-repo)"
    
    def __init__(self):
        self.robots_cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def check(self, url: str) -> Dict:
        """
        Check if a URL can be scraped compliantly.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "crawl_delay": float,
                "warnings": list,
                "recommendations": list
            }
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path
        
        result = {
            "url": url,
            "domain": domain,
            "allowed": True,
            "reason": "Allowed",
            "crawl_delay": 0,
            "warnings": [],
            "recommendations": []
        }
        
        # Check blacklist
        for blocked in self.BLACKLIST:
            if blocked in domain:
                result["allowed"] = False
                result["reason"] = f"Domain matches blacklist: {blocked}"
                return result
        
        # Check caution list
        for site, warning in self.CAUTION_LIST.items():
            if site in domain:
                result["warnings"].append(warning)
        
        # Check robots.txt
        robots_result = await self._check_robots(url)
        if not robots_result["allowed"]:
            result["allowed"] = False
            result["reason"] = "Blocked by robots.txt"
        
        result["crawl_delay"] = robots_result.get("crawl_delay", 0)
        
        if robots_result.get("sitemap"):
            result["recommendations"].append(f"Sitemap available: {robots_result['sitemap']}")
        
        return result
    
    async def _check_robots(self, url: str) -> Dict:
        """Parse and check robots.txt for a URL."""
        parsed = urlparse(url)
        domain = parsed.netloc
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"
        
        # Check cache
        if domain in self.robots_cache:
            cached = self.robots_cache[domain]
            if datetime.now() < cached["expires"]:
                return self._evaluate_robots(cached["parser"], url)
        
        # Fetch robots.txt
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    robots_url, 
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        parser = self._parse_robots(content)
                        
                        self.robots_cache[domain] = {
                            "parser": parser,
                            "content": content,
                            "expires": datetime.now() + timedelta(seconds=self.cache_ttl)
                        }
                        
                        return self._evaluate_robots(parser, url)
                    else:
                        # No robots.txt = allowed
                        return {"allowed": True, "crawl_delay": 0}
                        
        except Exception as e:
            logger.debug(f"[Compliance] Could not fetch robots.txt for {domain}: {e}")
            return {"allowed": True, "crawl_delay": 0}
    
    def _parse_robots(self, content: str) -> Dict:
        """Parse robots.txt content."""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delay": 0
        }
        
        current_ua = "*"
        
        for line in content.split("\n"):
            line = line.strip().lower()
            
            if line.startswith("user-agent:"):
                current_ua = line.split(":", 1)[1].strip()
                if current_ua not in result["user_agents"]:
                    result["user_agents"][current_ua] = {"allow": [], "disallow": []}
            
            elif line.startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    result["user_agents"].setdefault(current_ua, {"allow": [], "disallow": []})
                    result["user_agents"][current_ua]["disallow"].append(path)
            
            elif line.startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    result["user_agents"].setdefault(current_ua, {"allow": [], "disallow": []})
                    result["user_agents"][current_ua]["allow"].append(path)
            
            elif line.startswith("crawl-delay:"):
                try:
                    result["crawl_delay"] = float(line.split(":", 1)[1].strip())
                except:
                    pass
            
            elif line.startswith("sitemap:"):
                sitemap = line.split(":", 1)[1].strip()
                if sitemap:
                    result["sitemaps"].append(sitemap)
        
        return result
    
    def _evaluate_robots(self, parser: Dict, url: str) -> Dict:
        """Evaluate if URL is allowed based on parsed robots.txt."""
        parsed = urlparse(url)
        path = parsed.path or "/"
        
        result = {
            "allowed": True,
            "crawl_delay": parser.get("crawl_delay", 0),
            "sitemap": parser.get("sitemaps", [None])[0] if parser.get("sitemaps") else None
        }
        
        # Check rules for our user agent and "*"
        for ua in ["urwabot", "*"]:
            rules = parser.get("user_agents", {}).get(ua, {})
            
            # Check disallow rules
            for disallowed in rules.get("disallow", []):
                if path.startswith(disallowed):
                    # Check if there's an explicit allow that overrides
                    allowed = False
                    for allow_path in rules.get("allow", []):
                        if path.startswith(allow_path):
                            allowed = True
                            break
                    
                    if not allowed:
                        result["allowed"] = False
                        return result
        
        return result
    
    def is_blacklisted(self, url: str) -> bool:
        """Quick check if URL is blacklisted."""
        domain = urlparse(url).netloc.lower()
        return any(blocked in domain for blocked in self.BLACKLIST)
    
    def get_caution_warning(self, url: str) -> Optional[str]:
        """Get caution warning for a URL if applicable."""
        domain = urlparse(url).netloc.lower()
        for site, warning in self.CAUTION_LIST.items():
            if site in domain:
                return warning
        return None
    
    def clear_cache(self):
        """Clear robots.txt cache."""
        self.robots_cache.clear()


# Singleton instance
compliance_checker = ComplianceChecker()
