"""
Advanced Stealth Techniques for Highly Protected Sites
Implements survival strategies for scraping protected sites.

Strategies:
- Fingerprint Masking
- Session Trust Building  
- Behavior Simulation
- Cookie Persistence
- Low-and-Slow Pacing
"""

import asyncio
import random
import json
import os
import hashlib
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from loguru import logger


class FingerprintMasker:
    """
    Strategy 2: Fingerprint Masking
    Masks automation fingerprints that sites use to detect bots.
    """
    
    # Common screen resolutions (weighted by popularity)
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
        (1280, 720), (2560, 1440), (1600, 900), (1280, 800)
    ]
    
    # Realistic timezones
    TIMEZONES = [
        "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Kolkata"
    ]
    
    # Common languages
    LANGUAGES = [
        ["en-US", "en"], ["en-GB", "en"], ["en-IN", "en"],
        ["de-DE", "de", "en"], ["fr-FR", "fr", "en"]
    ]
    
    # WebGL vendors
    WEBGL_VENDORS = [
        ("Intel Inc.", "Intel Iris OpenGL Engine"),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce GTX 1080)"),
        ("Google Inc. (Intel)", "ANGLE (Intel UHD Graphics 630)"),
        ("Google Inc. (AMD)", "ANGLE (AMD Radeon RX 580)")
    ]
    
    @classmethod
    def generate_fingerprint(cls, seed: str = None) -> Dict:
        """
        Generate a consistent fingerprint for a session.
        
        Args:
            seed: Optional seed for reproducible fingerprints
        """
        if seed:
            random.seed(hashlib.md5(seed.encode()).hexdigest())
        
        resolution = random.choice(cls.SCREEN_RESOLUTIONS)
        webgl = random.choice(cls.WEBGL_VENDORS)
        
        fingerprint = {
            "screen": {
                "width": resolution[0],
                "height": resolution[1],
                "availWidth": resolution[0],
                "availHeight": resolution[1] - 40,  # Taskbar
                "colorDepth": 24,
                "pixelDepth": 24
            },
            "timezone": random.choice(cls.TIMEZONES),
            "languages": random.choice(cls.LANGUAGES),
            "webgl": {
                "vendor": webgl[0],
                "renderer": webgl[1]
            },
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "hardwareConcurrency": random.choice([4, 8, 12, 16]),
            "deviceMemory": random.choice([4, 8, 16, 32]),
            "maxTouchPoints": 0,  # Desktop
            "plugins": cls._generate_plugins()
        }
        
        # Reset random seed
        random.seed()
        
        return fingerprint
    
    @classmethod
    def _generate_plugins(cls) -> List[Dict]:
        """Generate realistic browser plugins."""
        return [
            {"name": "Chrome PDF Plugin", "filename": "internal-pdf-viewer"},
            {"name": "Chrome PDF Viewer", "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai"},
            {"name": "Native Client", "filename": "internal-nacl-plugin"}
        ]
    
    @classmethod
    def get_stealth_scripts(cls, fingerprint: Dict) -> str:
        """
        Generate JavaScript to mask fingerprints.
        Inject this before page load.
        """
        return f"""
        // Override navigator properties
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => {json.dumps(fingerprint['languages'])}
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fingerprint["platform"]}'
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fingerprint['hardwareConcurrency']}
        }});
        
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {fingerprint['deviceMemory']}
        }});
        
        // Override screen properties
        Object.defineProperty(screen, 'width', {{
            get: () => {fingerprint['screen']['width']}
        }});
        
        Object.defineProperty(screen, 'height', {{
            get: () => {fingerprint['screen']['height']}
        }});
        
        // WebGL fingerprint masking
        const getParameterProxy = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{fingerprint["webgl"]["vendor"]}';
            if (parameter === 37446) return '{fingerprint["webgl"]["renderer"]}';
            return getParameterProxy.call(this, parameter);
        }};
        
        // Mask automation detection
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        console.log('[Stealth] Fingerprint masking applied');
        """


class SessionTrustBuilder:
    """
    Strategy 3: Session Trust Building
    Warms up sessions before accessing target pages.
    """
    
    # Warmup paths for common sites
    WARMUP_PATHS = {
        "default": ["/", "/about", "/contact"],
        "amazon.com": ["/", "/gp/help/customer/display.html"],
        "linkedin.com": ["/", "/feed/"],
        "indeed.com": ["/", "/career-advice"],
        "glassdoor.com": ["/", "/about-us.htm"],
    }
    
    @classmethod
    async def warmup_session(cls, page, base_url: str, duration: float = 5.0) -> bool:
        """
        Warm up a session by simulating human navigation.
        
        Args:
            page: Playwright page object
            base_url: Base URL of the site
            duration: How long to spend warming up
            
        Returns:
            True if warmup was successful
        """
        from urllib.parse import urlparse
        
        domain = urlparse(base_url).netloc.lower()
        
        # Get warmup paths for this domain
        paths = cls.WARMUP_PATHS.get(domain, cls.WARMUP_PATHS["default"])
        
        logger.info(f"[TrustBuild] Warming up session for {domain}...")
        
        try:
            # Visit homepage first
            homepage = f"{urlparse(base_url).scheme}://{domain}"
            await page.goto(homepage, wait_until="domcontentloaded", timeout=15000)
            
            # Wait and scroll
            await asyncio.sleep(random.uniform(1, 2))
            await cls._human_scroll(page)
            
            # Visit 1-2 warmup pages
            for path in random.sample(paths, min(2, len(paths))):
                if path == "/":
                    continue
                    
                try:
                    warmup_url = f"{homepage}{path}"
                    await asyncio.sleep(random.uniform(1, 3))
                    await page.goto(warmup_url, wait_until="domcontentloaded", timeout=10000)
                    await cls._human_scroll(page)
                except:
                    pass  # Warmup failures are OK
            
            # Final wait
            await asyncio.sleep(random.uniform(1, 2))
            
            logger.info(f"[TrustBuild] Session warmed up successfully")
            return True
            
        except Exception as e:
            logger.warning(f"[TrustBuild] Warmup failed: {e}")
            return False
    
    @classmethod
    async def _human_scroll(cls, page, scrolls: int = 2):
        """Simulate human-like scrolling."""
        for _ in range(scrolls):
            scroll_amount = random.randint(200, 500)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.3, 0.8))


class BehaviorSimulator:
    """
    Strategy 7: Behavior Simulation
    Mimics human behavior patterns.
    """
    
    @classmethod
    async def simulate_human_behavior(cls, page, duration: float = 3.0):
        """
        Simulate human-like behavior on a page.
        
        Includes:
        - Random scrolling
        - Mouse movements
        - Reading pauses
        - Focus/blur events
        """
        start = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start < duration:
            action = random.choice(["scroll", "pause", "mouse", "focus"])
            
            try:
                if action == "scroll":
                    direction = random.choice([1, 1, 1, -1])  # Mostly down
                    amount = random.randint(100, 400) * direction
                    await page.evaluate(f"window.scrollBy(0, {amount})")
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                    
                elif action == "pause":
                    # Reading pause
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                elif action == "mouse":
                    # Random mouse movement
                    x = random.randint(100, 800)
                    y = random.randint(100, 600)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                elif action == "focus":
                    # Simulate focus/blur
                    await page.evaluate("document.body.click()")
                    await asyncio.sleep(random.uniform(0.1, 0.2))
                    
            except:
                pass  # Behavior simulation failures are OK
    
    @classmethod
    async def human_type(cls, page, selector: str, text: str):
        """Type text with human-like delays."""
        element = await page.query_selector(selector)
        if not element:
            return
            
        for char in text:
            await element.type(char, delay=random.randint(50, 150))
            if random.random() < 0.1:  # Occasional pause
                await asyncio.sleep(random.uniform(0.1, 0.3))
    
    @classmethod
    def get_human_wait(cls, min_sec: float = 1.0, max_sec: float = 3.0) -> float:
        """Get a human-like random wait time."""
        # Use a distribution that feels more natural
        base = random.uniform(min_sec, max_sec)
        # Occasionally add extra "thinking" time
        if random.random() < 0.2:
            base += random.uniform(0.5, 1.5)
        return base


class CookiePersistence:
    """
    Strategy 6: Cookie Persistence
    Saves and reuses browser sessions across scrapes.
    """
    
    STORAGE_DIR = "app/static/browser_sessions"
    SESSION_MAX_AGE = 24 * 60 * 60  # 24 hours
    
    def __init__(self):
        os.makedirs(self.STORAGE_DIR, exist_ok=True)
    
    def get_session_path(self, domain: str) -> str:
        """Get storage path for a domain's session."""
        safe_domain = domain.replace(".", "_").replace(":", "_")
        return os.path.join(self.STORAGE_DIR, f"{safe_domain}_session.json")
    
    async def save_session(self, context, domain: str):
        """
        Save browser context (cookies, storage) for reuse.
        
        Args:
            context: Playwright browser context
            domain: Domain to associate session with
        """
        try:
            path = self.get_session_path(domain)
            
            # Get cookies
            cookies = await context.cookies()
            
            # Get storage state if available
            storage = await context.storage_state()
            
            session_data = {
                "domain": domain,
                "saved_at": datetime.now().isoformat(),
                "cookies": cookies,
                "storage": storage
            }
            
            with open(path, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"[Session] Saved {len(cookies)} cookies for {domain}")
            
        except Exception as e:
            logger.warning(f"[Session] Failed to save: {e}")
    
    async def load_session(self, context, domain: str) -> bool:
        """
        Load a saved session into browser context.
        
        Returns:
            True if session was loaded successfully
        """
        try:
            path = self.get_session_path(domain)
            
            if not os.path.exists(path):
                return False
            
            with open(path, 'r') as f:
                session_data = json.load(f)
            
            # Check age
            saved_at = datetime.fromisoformat(session_data["saved_at"])
            age = (datetime.now() - saved_at).total_seconds()
            
            if age > self.SESSION_MAX_AGE:
                logger.info(f"[Session] Session for {domain} expired")
                os.remove(path)
                return False
            
            # Load cookies
            cookies = session_data.get("cookies", [])
            if cookies:
                await context.add_cookies(cookies)
            
            logger.info(f"[Session] Loaded {len(cookies)} cookies for {domain} (age: {age/3600:.1f}h)")
            return True
            
        except Exception as e:
            logger.warning(f"[Session] Failed to load: {e}")
            return False
    
    def clear_session(self, domain: str):
        """Clear saved session for a domain."""
        path = self.get_session_path(domain)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"[Session] Cleared session for {domain}")
    
    def list_sessions(self) -> List[Dict]:
        """List all saved sessions."""
        sessions = []
        
        for filename in os.listdir(self.STORAGE_DIR):
            if filename.endswith("_session.json"):
                path = os.path.join(self.STORAGE_DIR, filename)
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    saved_at = datetime.fromisoformat(data["saved_at"])
                    age = (datetime.now() - saved_at).total_seconds()
                    
                    sessions.append({
                        "domain": data["domain"],
                        "cookies": len(data.get("cookies", [])),
                        "age_hours": round(age / 3600, 1),
                        "expired": age > self.SESSION_MAX_AGE
                    })
                except:
                    pass
        
        return sessions


class LowAndSlow:
    """
    Strategy 4: Low-and-Slow Pacing
    Extremely conservative scraping for maximum stealth.
    """
    
    # Timing ranges (seconds)
    TIMING = {
        "between_requests": (10, 30),
        "between_pages": (5, 15),
        "after_error": (30, 60),
        "reading_time": (3, 8)
    }
    
    @classmethod
    async def wait_between_requests(cls):
        """Wait a random time between requests."""
        wait = random.uniform(*cls.TIMING["between_requests"])
        logger.debug(f"[LowSlow] Waiting {wait:.1f}s between requests")
        await asyncio.sleep(wait)
    
    @classmethod
    async def wait_for_reading(cls):
        """Simulate reading/processing time."""
        wait = random.uniform(*cls.TIMING["reading_time"])
        await asyncio.sleep(wait)
    
    @classmethod
    async def wait_after_error(cls):
        """Extended wait after an error."""
        wait = random.uniform(*cls.TIMING["after_error"])
        logger.info(f"[LowSlow] Cooling down for {wait:.1f}s after error")
        await asyncio.sleep(wait)
    
    @classmethod
    def should_back_off(cls, consecutive_errors: int) -> bool:
        """Check if we should pause scraping entirely."""
        if consecutive_errors >= 3:
            logger.warning(f"[LowSlow] {consecutive_errors} consecutive errors - backing off")
            return True
        return False


# Export singleton instances
fingerprint_masker = FingerprintMasker()
trust_builder = SessionTrustBuilder()
behavior_sim = BehaviorSimulator()
cookie_persistence = CookiePersistence()
low_and_slow = LowAndSlow()
