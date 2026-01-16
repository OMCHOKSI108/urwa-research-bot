"""
Strategy 1: Site Profiler
Detects site protection BEFORE scraping to select the right strategy.
"""

import aiohttp
import asyncio
import re
from typing import Dict, Any, Tuple
from urllib.parse import urlparse
from loguru import logger


class SiteProfiler:
    """
    Profiles a website to determine:
    - Protection level (Cloudflare, Akamai, DataDome, etc.)
    - JavaScript requirements
    - Bot detection signals
    - Recommended scraping strategy
    """
    
    # Known bot protection signatures
    BOT_PROTECTION_SIGNATURES = {
        'cloudflare': [
            'cf-ray', 'cf-cache-status', '__cf_bm', 'cf_clearance',
            'cloudflare', 'checking your browser', 'ray id'
        ],
        'akamai': [
            'akamai', 'akamai-grn', 'x-akamai', 'ak_bmsc'
        ],
        'datadome': [
            'datadome', 'dd_s', 'datadome.co'
        ],
        'perimeterx': [
            'perimeterx', '_px', 'px-captcha'
        ],
        'incapsula': [
            'incapsula', 'incap_ses', 'visid_incap'
        ],
        'distil': [
            'distil', 'x-distil'
        ],
        'shape': [
            'shape', 'f5'
        ]
    }
    
    # JS-heavy site indicators
    JS_FRAMEWORKS = [
        'react', 'angular', 'vue', 'next', 'nuxt', 'gatsby',
        '__NEXT_DATA__', '__NUXT__', 'ng-app', 'data-reactroot'
    ]
    
    # CAPTCHA indicators
    CAPTCHA_SIGNATURES = [
        'captcha', 'recaptcha', 'hcaptcha', 'funcaptcha',
        'g-recaptcha', 'h-captcha', 'challenge-form',
        'verify you are human', 'prove you are not a robot'
    ]
    
    def __init__(self):
        self.profile_cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def profile(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Profile a website to determine protection level and recommended strategy.
        
        Returns:
            {
                "url": str,
                "domain": str,
                "risk": "low" | "medium" | "high" | "extreme",
                "needs_rendering": bool,
                "bot_wall": str | None,
                "captcha_detected": bool,
                "redirect_count": int,
                "recommended_strategy": str,
                "details": {...}
            }
        """
        domain = urlparse(url).netloc.lower()
        
        # Check cache first
        # Check cache first
        if domain in self.profile_cache:
            cached = self.profile_cache[domain]
            logger.info(f"[Profiler] Using cached profile for {domain}")
            return cached
        
        logger.info(f"[Profiler] Profiling {domain}...")

        # Known High Risk Domains force override
        KNOWN_HIGH_RISK = {
             "linkedin.com": "extreme",
             "facebook.com": "extreme",
             "instagram.com": "extreme",
             "twitter.com": "extreme",
             "x.com": "extreme",
             "github.com": "extreme",
             "ambitionbox.com": "extreme",
             "glassdoor.com": "extreme",
             "trustpilot.com": "extreme",
             "amazon.com": "high",
             "yelp.com": "high",
             "tripadvisor.com": "high",
             "g2.com": "extreme"
        }

        for known, risk in KNOWN_HIGH_RISK.items():
            if known in domain:
                logger.info(f"[Profiler] {domain} is a KNOWN {risk} risk site -> Forcing Ultra Stealth")
                
                strategy = "ultra_stealth" if risk == "extreme" else "stealth"
                
                forced_profile = {
                    "url": url,
                    "domain": domain,
                    "risk": risk,
                    "needs_rendering": True,
                    "bot_wall": "known_protection",
                    "captcha_detected": True,
                    "redirect_count": 0,
                    "recommended_strategy": strategy,
                    "details": {"reason": "Known high-risk domain"}
                }
                self.profile_cache[domain] = forced_profile
                return forced_profile
        
        profile = {
            "url": url,
            "domain": domain,
            "risk": "low",
            "needs_rendering": False,
            "bot_wall": None,
            "captcha_detected": False,
            "redirect_count": 0,
            "recommended_strategy": "lightweight",
            "details": {
                "status_code": None,
                "headers": {},
                "protection_signals": [],
                "js_signals": [],
                "warnings": []
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
                
                async with session.get(
                    url, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
                    max_redirects=5
                ) as response:
                    profile["details"]["status_code"] = response.status
                    profile["redirect_count"] = len(response.history)
                    
                    # Store relevant headers
                    for header in ['server', 'x-powered-by', 'cf-ray', 'x-cache']:
                        if header in response.headers:
                            profile["details"]["headers"][header] = response.headers[header]
                    
                    # Get content for analysis
                    content = await response.text()
                    content_lower = content.lower()
                    headers_str = str(response.headers).lower()
                    
                    # Detect bot protection - check HEADERS only for protection signatures
                    # (many pages mention "cloudflare" in content without being protected)
                    for protection, signatures in self.BOT_PROTECTION_SIGNATURES.items():
                        for sig in signatures:
                            # Only check headers for cloudflare/akamai detection
                            if sig in headers_str:
                                profile["bot_wall"] = protection
                                profile["details"]["protection_signals"].append(f"{sig} (header)")
                                break
                        if profile["bot_wall"]:
                            break
                    
                    # Check for challenge page content (these are specific to block pages)
                    challenge_indicators = [
                        'checking your browser before accessing',
                        'please wait while we verify',
                        'this process is automatic',
                        'ray id:',
                        'performance & security by cloudflare'
                    ]
                    for indicator in challenge_indicators:
                        if indicator in content_lower:
                            profile["bot_wall"] = "cloudflare"
                            profile["details"]["protection_signals"].append(f"{indicator[:30]}...")
                            break
                    
                    # Detect JS requirements
                    for framework in self.JS_FRAMEWORKS:
                        if framework in content_lower:
                            profile["needs_rendering"] = True
                            profile["details"]["js_signals"].append(framework)
                    
                    # Detect CAPTCHA (only in short content - challenge pages)
                    for captcha_sig in self.CAPTCHA_SIGNATURES:
                        if captcha_sig in content_lower and len(content) < 10000:
                            profile["captcha_detected"] = True
                            profile["details"]["warnings"].append(f"CAPTCHA detected: {captcha_sig}")
                            break
                    
                    # Check for minimal content (likely JS-rendered)
                    if len(content) < 5000 and '<noscript>' in content_lower:
                        profile["needs_rendering"] = True
                        profile["details"]["warnings"].append("Minimal HTML, likely JS-rendered")
                    
                    # Calculate risk level
                    profile["risk"] = self._calculate_risk(profile)
                    
                    # Determine recommended strategy
                    profile["recommended_strategy"] = self._recommend_strategy(profile)
                    
        except asyncio.TimeoutError:
            profile["details"]["warnings"].append("Profile timeout - assuming high risk")
            profile["risk"] = "high"
            profile["recommended_strategy"] = "stealth"
        except Exception as e:
            profile["details"]["warnings"].append(f"Profile error: {str(e)[:50]}")
            profile["risk"] = "medium"
            profile["recommended_strategy"] = "stealth"
        
        # Cache the profile
        self.profile_cache[domain] = profile
        
        logger.info(f"[Profiler] {domain}: risk={profile['risk']}, strategy={profile['recommended_strategy']}")
        return profile
    
    def _calculate_risk(self, profile: Dict) -> str:
        """Calculate risk level based on detected signals."""
        score = 0
        
        if profile["bot_wall"]:
            score += 40
            if profile["bot_wall"] in ['cloudflare', 'akamai', 'datadome']:
                score += 20
        
        if profile["captcha_detected"]:
            score += 30
        
        if profile["needs_rendering"]:
            score += 15
        
        if profile["redirect_count"] > 2:
            score += 10
        
        if profile["details"]["status_code"] and profile["details"]["status_code"] >= 400:
            score += 25
        
        if score >= 70:
            return "extreme"
        elif score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        else:
            return "low"
    
    def _recommend_strategy(self, profile: Dict) -> str:
        """Recommend scraping strategy based on profile."""
        risk = profile["risk"]
        
        if risk == "extreme" or profile["captcha_detected"]:
            return "ultra_stealth"
        elif risk == "high" or profile["bot_wall"]:
            return "ultra_stealth"
        elif risk == "medium" or profile["needs_rendering"]:
            return "stealth"
        else:
            return "lightweight"
    
    def get_cached_profiles(self) -> Dict[str, Dict]:
        """Return all cached profiles."""
        return self.profile_cache.copy()
    
    def clear_cache(self):
        """Clear the profile cache."""
        self.profile_cache.clear()


# Singleton instance
site_profiler = SiteProfiler()
