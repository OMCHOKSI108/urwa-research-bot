"""
Lightweight HTTP-based scraper for sites that don't require JavaScript rendering.
Faster and less detectable than Playwright for static content.
"""
import requests
from bs4 import BeautifulSoup
import random
import asyncio
from loguru import logger
from typing import Optional
import html2text

class LightweightScraper:
    """Fast HTTP-based scraper using requests + BeautifulSoup"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = True
        
    def _get_headers(self) -> dict:
        """Generate realistic request headers"""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.google.com/",
            "Cache-Control": "max-age=0",
        }
    
    async def scrape(self, url: str, timeout: int = 20) -> Optional[str]:
        """
        Scrape a URL using simple HTTP requests (async wrapper).
        Returns markdown content or None if failed.
        """
        try:
            logger.info(f"[Lightweight] Scraping {url}")
            
            # Random delay to appear human (now async)
            await asyncio.sleep(random.uniform(1, 2))
            
            # Use asyncio.to_thread for blocking requests call
            response = await asyncio.to_thread(
                self.session.get,
                url,
                headers=self._get_headers(),
                timeout=timeout,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                logger.warning(f"[Lightweight] HTTP {response.status_code} for {url}")
                return None
            
            # Check for common block indicators
            content_lower = response.text.lower()
            if any(indicator in content_lower for indicator in ["captcha", "access denied", "forbidden", "unusual traffic"]):
                logger.warning(f"[Lightweight] Block detected in {url}")
                return None
            
            # Convert HTML to markdown
            markdown = self.converter.handle(response.text)
            
            if len(markdown) < 100:
                logger.warning(f"[Lightweight] Content too short for {url}")
                return None
            
            logger.info(f"[Lightweight] ✓ Successfully scraped {url} ({len(markdown)} chars)")
            return markdown
            
        except requests.Timeout:
            logger.error(f"[Lightweight] Timeout for {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"[Lightweight] Request failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"[Lightweight] Unexpected error for {url}: {e}")
            return None
