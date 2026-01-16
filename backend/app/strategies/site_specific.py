"""
SITE-SPECIFIC SCRAPERS
Custom strategies for the hardest-to-scrape sites.

Each site has its own tailored approach based on how its protection works.
"""

import asyncio
import random
import json
import re
from typing import Dict, Optional, List
from datetime import datetime
from loguru import logger
from urllib.parse import urlparse, urljoin


class LinkedInScraper:
    """
    LinkedIn-specific scraping strategy.
    
    LinkedIn is one of the hardest sites to scrape due to:
    - Aggressive rate limiting
    - Device fingerprinting
    - Session tracking
    - Login walls
    
    Strategy:
    1. Use Google cache/web archive as fallback
    2. Parse public profile URLs without login
    3. Extract from search engine results
    """
    
    # Alternative sources for LinkedIn data
    FALLBACK_SOURCES = [
        "https://webcache.googleusercontent.com/search?q=cache:",
        "https://web.archive.org/web/",
        "https://www.bing.com/search?q=site:linkedin.com+",
    ]
    
    @classmethod
    async def scrape_profile(cls, profile_url: str, scraper) -> Dict:
        """
        Scrape LinkedIn profile using fallback strategies.
        """
        result = {
            "url": profile_url,
            "source": None,
            "data": {},
            "success": False
        }
        
        # Extract username from URL
        match = re.search(r'linkedin\.com/in/([^/\?]+)', profile_url)
        if not match:
            return result
        
        username = match.group(1)
        
        # Strategy 1: Try Google Cache
        try:
            cache_url = f"https://webcache.googleusercontent.com/search?q=cache:linkedin.com/in/{username}"
            content = await scraper.scrape(cache_url)
            if content and "linkedin" in content.lower():
                result["data"] = cls._parse_profile_content(content)
                result["source"] = "google_cache"
                result["success"] = True
                return result
        except Exception as e:
            logger.debug(f"[LinkedIn] Google cache failed: {e}")
        
        # Strategy 2: Try Bing search results
        try:
            bing_url = f"https://www.bing.com/search?q=site:linkedin.com/in/{username}"
            content = await scraper.scrape(bing_url)
            if content:
                result["data"] = cls._parse_search_results(content, username)
                result["source"] = "bing_search"
                result["success"] = bool(result["data"])
                return result
        except Exception as e:
            logger.debug(f"[LinkedIn] Bing search failed: {e}")
        
        # Strategy 3: Try Web Archive
        try:
            archive_url = f"https://web.archive.org/web/2024/linkedin.com/in/{username}"
            content = await scraper.scrape(archive_url)
            if content:
                result["data"] = cls._parse_profile_content(content)
                result["source"] = "web_archive"
                result["success"] = bool(result["data"])
                return result
        except Exception as e:
            logger.debug(f"[LinkedIn] Web archive failed: {e}")
        
        return result
    
    @classmethod
    def _parse_profile_content(cls, content: str) -> Dict:
        """Parse LinkedIn profile from cached/archived content."""
        data = {}
        
        # Extract name
        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        if name_match:
            data["name"] = name_match.group(1).strip()
        
        # Extract headline
        headline_match = re.search(r'headline["\s:>]+([^<]+)', content, re.IGNORECASE)
        if headline_match:
            data["headline"] = headline_match.group(1).strip()
        
        # Extract location
        location_match = re.search(r'location["\s:>]+([^<]+)', content, re.IGNORECASE)
        if location_match:
            data["location"] = location_match.group(1).strip()
        
        return data
    
    @classmethod
    def _parse_search_results(cls, content: str, username: str) -> Dict:
        """Parse profile info from search results."""
        data = {}
        
        # Extract from meta descriptions in search results
        title_match = re.search(rf'{username}[^|]*\|[^-]*-([^<]+)', content, re.IGNORECASE)
        if title_match:
            data["headline"] = title_match.group(1).strip()
        
        return data


class AmazonScraper:
    """
    Amazon-specific scraping strategy.
    
    Amazon uses:
    - IP-based rate limiting
    - CAPTCHA on suspicious behavior
    - Dynamic pricing/content
    
    Strategy:
    1. Use product API alternatives
    2. Parse search results instead of product pages
    3. Slow, randomized scraping
    """
    
    # Amazon domains
    AMAZON_DOMAINS = {
        "us": "amazon.com",
        "uk": "amazon.co.uk",
        "de": "amazon.de",
        "in": "amazon.in",
    }
    
    @classmethod
    async def scrape_product(cls, product_url: str, scraper) -> Dict:
        """
        Scrape Amazon product with anti-ban strategies.
        """
        result = {
            "url": product_url,
            "data": {},
            "success": False
        }
        
        # Extract ASIN
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
        if not asin_match:
            asin_match = re.search(r'/product/([A-Z0-9]{10})', product_url)
        
        if not asin_match:
            return result
        
        asin = asin_match.group(1)
        
        # Strategy 1: Try mobile URL (often less protected)
        try:
            mobile_url = f"https://www.amazon.com/dp/{asin}?th=1&psc=1"
            content = await scraper.scrape(
                mobile_url,
                force_ultra_stealth=True
            )
            if content and len(content) > 1000:
                result["data"] = cls._parse_product(content, asin)
                result["success"] = bool(result["data"].get("title"))
                return result
        except Exception as e:
            logger.debug(f"[Amazon] Mobile URL failed: {e}")
        
        # Strategy 2: Try price API endpoint
        try:
            api_url = f"https://www.amazon.com/gp/product/ajax/get-price/{asin}"
            # This usually requires cookies but sometimes works
            pass
        except:
            pass
        
        # Strategy 3: Search and extract from results
        try:
            search_url = f"https://www.amazon.com/s?k={asin}"
            content = await scraper.scrape(search_url, force_ultra_stealth=True)
            if content:
                result["data"] = cls._parse_from_search(content, asin)
                result["success"] = bool(result["data"].get("title"))
                return result
        except Exception as e:
            logger.debug(f"[Amazon] Search failed: {e}")
        
        return result
    
    @classmethod
    def _parse_product(cls, content: str, asin: str) -> Dict:
        """Parse product details from page content."""
        data = {"asin": asin}
        
        # Title
        title_match = re.search(r'id="productTitle"[^>]*>([^<]+)', content)
        if title_match:
            data["title"] = title_match.group(1).strip()
        
        # Price
        price_match = re.search(r'\$[\d,]+\.?\d*', content)
        if price_match:
            data["price"] = price_match.group(0)
        
        # Rating
        rating_match = re.search(r'([\d.]+) out of 5', content)
        if rating_match:
            data["rating"] = float(rating_match.group(1))
        
        # Reviews count
        reviews_match = re.search(r'([\d,]+)\s*(?:global\s*)?ratings?', content, re.IGNORECASE)
        if reviews_match:
            data["reviews_count"] = reviews_match.group(1).replace(",", "")
        
        return data
    
    @classmethod
    def _parse_from_search(cls, content: str, asin: str) -> Dict:
        """Parse product from search results."""
        data = {"asin": asin}
        
        # Find the specific ASIN in search results
        asin_pattern = rf'data-asin="{asin}"[^>]*>(.*?)</div>'
        match = re.search(asin_pattern, content, re.DOTALL)
        
        if match:
            block = match.group(1)
            
            # Extract title
            title_match = re.search(r'<span[^>]*>([^<]{20,})</span>', block)
            if title_match:
                data["title"] = title_match.group(1).strip()
            
            # Extract price
            price_match = re.search(r'\$[\d,]+\.?\d*', block)
            if price_match:
                data["price"] = price_match.group(0)
        
        return data


class IndeedScraper:
    """
    Indeed job scraping strategy.
    
    Indeed blocks aggressively with:
    - Cloudflare protection
    - Rate limiting
    - CAPTCHA
    
    Strategy:
    1. Use RSS feeds (less protected)
    2. Parse Google Jobs results
    3. Use API-like endpoints
    """
    
    @classmethod
    async def scrape_jobs(cls, query: str, location: str, scraper) -> Dict:
        """
        Scrape Indeed job listings.
        """
        result = {
            "query": query,
            "location": location,
            "jobs": [],
            "source": None,
            "success": False
        }
        
        # Strategy 1: RSS feed (often less protected)
        try:
            rss_url = f"https://www.indeed.com/rss?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
            content = await scraper.scrape(rss_url)
            if content and "<item>" in content:
                result["jobs"] = cls._parse_rss(content)
                result["source"] = "rss"
                result["success"] = len(result["jobs"]) > 0
                return result
        except Exception as e:
            logger.debug(f"[Indeed] RSS failed: {e}")
        
        # Strategy 2: Google Jobs API endpoint
        try:
            google_url = f"https://www.google.com/search?q={query}+jobs+{location}+site:indeed.com"
            content = await scraper.scrape(google_url)
            if content:
                result["jobs"] = cls._parse_google_jobs(content)
                result["source"] = "google"
                result["success"] = len(result["jobs"]) > 0
                return result
        except Exception as e:
            logger.debug(f"[Indeed] Google jobs failed: {e}")
        
        # Strategy 3: Direct with ultra stealth
        try:
            indeed_url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
            content = await scraper.scrape(indeed_url, force_ultra_stealth=True)
            if content and len(content) > 2000:
                result["jobs"] = cls._parse_indeed_page(content)
                result["source"] = "direct"
                result["success"] = len(result["jobs"]) > 0
                return result
        except Exception as e:
            logger.debug(f"[Indeed] Direct failed: {e}")
        
        return result
    
    @classmethod
    def _parse_rss(cls, content: str) -> List[Dict]:
        """Parse jobs from RSS feed."""
        jobs = []
        
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        for item in items[:20]:
            job = {}
            
            title_match = re.search(r'<title>([^<]+)', item)
            if title_match:
                job["title"] = title_match.group(1)
            
            link_match = re.search(r'<link>([^<]+)', item)
            if link_match:
                job["url"] = link_match.group(1)
            
            company_match = re.search(r'<source[^>]*>([^<]+)', item)
            if company_match:
                job["company"] = company_match.group(1)
            
            if job.get("title"):
                jobs.append(job)
        
        return jobs
    
    @classmethod
    def _parse_google_jobs(cls, content: str) -> List[Dict]:
        """Parse Indeed jobs from Google search results."""
        jobs = []
        
        patterns = [
            r'indeed\.com/viewjob[^"]*"[^>]*>([^<]+)',
            r'indeed\.com/rc/clk[^"]*"[^>]*>([^<]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches[:20]:
                jobs.append({"title": match.strip()})
        
        return jobs
    
    @classmethod
    def _parse_indeed_page(cls, content: str) -> List[Dict]:
        """Parse Indeed job listings from direct page."""
        jobs = []
        
        # Find job cards
        job_blocks = re.findall(r'data-jk="([^"]+)"(.*?)</td>', content, re.DOTALL)
        
        for job_id, block in job_blocks[:20]:
            job = {"id": job_id}
            
            title_match = re.search(r'jobTitle[^>]*>([^<]+)', block)
            if title_match:
                job["title"] = title_match.group(1).strip()
            
            company_match = re.search(r'companyName[^>]*>([^<]+)', block)
            if company_match:
                job["company"] = company_match.group(1).strip()
            
            location_match = re.search(r'companyLocation[^>]*>([^<]+)', block)
            if location_match:
                job["location"] = location_match.group(1).strip()
            
            if job.get("title"):
                jobs.append(job)
        
        return jobs


class SocialMediaScraper:
    """
    Social media scraping via alternative endpoints.
    
    Direct scraping of Facebook/Instagram/Twitter is very difficult.
    We use:
    1. Public embed endpoints
    2. oEmbed API
    3. Search engine caches
    """
    
    @classmethod
    async def get_twitter_post(cls, tweet_url: str, scraper) -> Dict:
        """Get Twitter/X post content via oEmbed."""
        result = {"url": tweet_url, "data": {}, "success": False}
        
        # Strategy 1: oEmbed endpoint (public API)
        try:
            oembed_url = f"https://publish.twitter.com/oembed?url={tweet_url}"
            content = await scraper.scrape(oembed_url)
            if content and "{" in content:
                data = json.loads(content)
                result["data"] = {
                    "html": data.get("html"),
                    "author": data.get("author_name"),
                    "author_url": data.get("author_url")
                }
                result["success"] = True
                return result
        except Exception as e:
            logger.debug(f"[Twitter] oEmbed failed: {e}")
        
        # Strategy 2: Nitter instance (Twitter mirror)
        try:
            # Extract tweet ID
            tweet_id = re.search(r'/status/(\d+)', tweet_url)
            if tweet_id:
                nitter_url = f"https://nitter.net/i/status/{tweet_id.group(1)}"
                content = await scraper.scrape(nitter_url)
                if content:
                    result["data"] = cls._parse_nitter(content)
                    result["success"] = bool(result["data"])
                    result["source"] = "nitter"
                    return result
        except Exception as e:
            logger.debug(f"[Twitter] Nitter failed: {e}")
        
        return result
    
    @classmethod
    async def get_instagram_post(cls, post_url: str, scraper) -> Dict:
        """Get Instagram post via embed endpoint."""
        result = {"url": post_url, "data": {}, "success": False}
        
        # oEmbed endpoint
        try:
            oembed_url = f"https://api.instagram.com/oembed?url={post_url}"
            content = await scraper.scrape(oembed_url)
            if content and "{" in content:
                data = json.loads(content)
                result["data"] = {
                    "html": data.get("html"),
                    "title": data.get("title"),
                    "author": data.get("author_name"),
                    "thumbnail": data.get("thumbnail_url")
                }
                result["success"] = True
        except Exception as e:
            logger.debug(f"[Instagram] oEmbed failed: {e}")
        
        return result
    
    @classmethod
    async def get_facebook_post(cls, post_url: str, scraper) -> Dict:
        """Get Facebook post via embed."""
        result = {"url": post_url, "data": {}, "success": False}
        
        # oEmbed endpoint
        try:
            oembed_url = f"https://www.facebook.com/plugins/post/oembed.json/?url={post_url}"
            content = await scraper.scrape(oembed_url)
            if content and "{" in content:
                data = json.loads(content)
                result["data"] = {"html": data.get("html")}
                result["success"] = True
        except Exception as e:
            logger.debug(f"[Facebook] oEmbed failed: {e}")
        
        return result
    
    @classmethod
    def _parse_nitter(cls, content: str) -> Dict:
        """Parse tweet from Nitter."""
        data = {}
        
        text_match = re.search(r'class="tweet-content[^>]*>([^<]+)', content)
        if text_match:
            data["text"] = text_match.group(1).strip()
        
        return data


# Registry of site-specific scrapers
SITE_SCRAPERS = {
    "linkedin.com": LinkedInScraper,
    "amazon.com": AmazonScraper,
    "amazon.co.uk": AmazonScraper,
    "amazon.de": AmazonScraper,
    "amazon.in": AmazonScraper,
    "indeed.com": IndeedScraper,
    "twitter.com": SocialMediaScraper,
    "x.com": SocialMediaScraper,
    "instagram.com": SocialMediaScraper,
    "facebook.com": SocialMediaScraper,
}


def get_site_scraper(url: str):
    """Get the appropriate site-specific scraper for a URL."""
    domain = urlparse(url).netloc.lower()
    
    # Remove www.
    if domain.startswith("www."):
        domain = domain[4:]
    
    return SITE_SCRAPERS.get(domain)
