"""
URWA Advanced Stealth Scraper - Ultra Anti-Bot Bypass Module

This module implements enterprise-grade anti-detection techniques to bypass:
- Cloudflare, Akamai, PerimeterX, DataDome
- Bot detection via fingerprinting
- Rate limiting and IP bans
- JavaScript challenges
- CAPTCHA detection

Techniques used:
1. Browser fingerprint spoofing (Canvas, WebGL, Audio, Fonts)
2. Human behavior simulation (mouse movements, scroll patterns)
3. Distributed request timing with jitter
4. Automatic proxy rotation
5. Cookie/session persistence
6. TLS fingerprint randomization
7. Multiple fallback strategies
"""

import asyncio
import random
import time
import hashlib
import json
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from loguru import logger

# External imports
try:
    from playwright.sync_api import sync_playwright
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - advanced scraping disabled")

try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class UltraStealthScraper:
    """
    Enterprise-grade stealth scraper with maximum anti-bot bypass capabilities.
    Uses multiple techniques in combination for maximum success rate.
    """

    # Extended User-Agent pool (latest browsers, mobile, etc.)
    USER_AGENTS = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        # Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]

    # Viewport sizes to randomize (realistic screen sizes)
    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 1366, "height": 768},
        {"width": 2560, "height": 1440},
        {"width": 1280, "height": 720},
        {"width": 1680, "height": 1050},
    ]

    # Common screen resolutions for spoofing
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (2560, 1440), (1536, 864), (1440, 900), (1366, 768),
        (3840, 2160), (1680, 1050), (1280, 1024), (1600, 900)
    ]

    # Timezone IDs for rotation
    TIMEZONES = [
        'America/New_York', 'America/Los_Angeles', 'America/Chicago',
        'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Singapore',
        'Australia/Sydney', 'America/Toronto', 'Europe/Berlin'
    ]

    # Locales for rotation
    LOCALES = ['en-US', 'en-GB', 'en-CA', 'en-AU', 'de-DE', 'fr-FR', 'ja-JP']

    def __init__(self):
        if HTML2TEXT_AVAILABLE:
            self.converter = html2text.HTML2Text()
            self.converter.ignore_links = False
            self.converter.ignore_images = True

        # Cache: URL -> (content, timestamp)
        self.cache: Dict[str, Tuple[str, datetime]] = {}
        self.cache_ttl = timedelta(minutes=30)

        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 1.5
        self.max_delay = 4.0

        # Session tracking
        self.session_history = []
        self.success_count = 0
        self.failure_count = 0

        # Cookies storage (domain -> cookies)
        self.cookie_jar: Dict[str, List[dict]] = {}

        # Proxy pool (add your proxies here)
        self.proxy_pool: List[str] = []
        self.current_proxy_index = 0
        
        # Advanced stealth techniques integration
        self._load_advanced_techniques()
    
    def _load_advanced_techniques(self):
        """Load advanced stealth technique modules."""
        try:
            from app.strategies.stealth_techniques import (
                cookie_persistence, trust_builder, behavior_sim, low_and_slow
            )
            self.cookie_persistence = cookie_persistence
            self.trust_builder = trust_builder
            self.behavior_sim = behavior_sim
            self.low_and_slow = low_and_slow
            self.use_advanced_techniques = True
            logger.info("[UltraStealth] Advanced techniques loaded")
        except ImportError as e:
            logger.warning(f"[UltraStealth] Advanced techniques not available: {e}")
            self.use_advanced_techniques = False


    def _get_cache_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _get_from_cache(self, url: str) -> Optional[str]:
        key = self._get_cache_key(url)
        if key in self.cache:
            content, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.info(f"[Cache] HIT for {url[:50]}...")
                return content
            del self.cache[key]
        return None

    def _store_in_cache(self, url: str, content: str):
        key = self._get_cache_key(url)
        self.cache[key] = (content, datetime.now())

    def _generate_fingerprint(self) -> dict:
        """Generate a realistic browser fingerprint."""
        screen = random.choice(self.SCREEN_RESOLUTIONS)
        return {
            'screen_width': screen[0],
            'screen_height': screen[1],
            'color_depth': random.choice([24, 32]),
            'pixel_ratio': random.choice([1, 1.25, 1.5, 2]),
            'timezone_offset': random.choice([-480, -420, -360, -300, -240, 0, 60, 120, 540]),
            'session_storage': True,
            'local_storage': True,
            'indexed_db': True,
            'cpu_class': 'unknown',
            'platform': random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
            'do_not_track': random.choice(['1', 'unspecified']),
            'plugins_hash': hashlib.md5(str(random.random()).encode()).hexdigest()[:8],
            'canvas_hash': hashlib.md5(str(random.random()).encode()).hexdigest()[:12],
            'webgl_hash': hashlib.md5(str(random.random()).encode()).hexdigest()[:10],
            'audio_hash': hashlib.md5(str(random.random()).encode()).hexdigest()[:8],
        }

    def _get_stealth_script(self, fingerprint: dict) -> str:
        """Generate comprehensive stealth JavaScript injection script."""
        return f"""
        (() => {{
            // ==================== CORE WEBDRIVER HIDING ====================
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                configurable: true
            }});

            // Delete webdriver traces
            delete navigator.__proto__.webdriver;

            // ==================== CHROME DETECTION BYPASS ====================
            window.chrome = {{
                runtime: {{
                    connect: () => {{}},
                    sendMessage: () => {{}},
                    onMessage: {{ addListener: () => {{}} }}
                }},
                loadTimes: () => ({{}}),
                csi: () => ({{}})
            }};

            // ==================== PLUGINS SPOOFING ====================
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = [
                        {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                        {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
                        {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }}
                    ];
                    plugins.refresh = () => {{}};
                    plugins.item = (i) => plugins[i];
                    plugins.namedItem = (n) => plugins.find(p => p.name === n);
                    return plugins;
                }},
                configurable: true
            }});

            // ==================== LANGUAGES ====================
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['en-US', 'en', 'es'],
                configurable: true
            }});

            Object.defineProperty(navigator, 'language', {{
                get: () => 'en-US',
                configurable: true
            }});

            // ==================== PLATFORM ====================
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint["platform"]}',
                configurable: true
            }});

            // ==================== HARDWARE CONCURRENCY ====================
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {random.choice([4, 8, 12, 16])},
                configurable: true
            }});

            // ==================== DEVICE MEMORY ====================
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {random.choice([4, 8, 16, 32])},
                configurable: true
            }});

            // ==================== SCREEN PROPERTIES ====================
            Object.defineProperty(screen, 'width', {{ get: () => {fingerprint['screen_width']} }});
            Object.defineProperty(screen, 'height', {{ get: () => {fingerprint['screen_height']} }});
            Object.defineProperty(screen, 'availWidth', {{ get: () => {fingerprint['screen_width']} }});
            Object.defineProperty(screen, 'availHeight', {{ get: () => {fingerprint['screen_height'] - 40} }});
            Object.defineProperty(screen, 'colorDepth', {{ get: () => {fingerprint['color_depth']} }});
            Object.defineProperty(screen, 'pixelDepth', {{ get: () => {fingerprint['color_depth']} }});

            // ==================== CANVAS FINGERPRINT RANDOMIZATION ====================
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, attributes) {{
                const context = originalGetContext.call(this, type, attributes);
                if (type === '2d' && context) {{
                    const originalGetImageData = context.getImageData;
                    context.getImageData = function(...args) {{
                        const imageData = originalGetImageData.apply(this, args);
                        // Add subtle noise to prevent fingerprinting
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + (Math.random() - 0.5) * 2));
                        }}
                        return imageData;
                    }};
                }}
                return context;
            }};

            // ==================== WEBGL FINGERPRINT SPOOFING ====================
            const getParameterProto = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(param) {{
                const vendors = ['Intel Inc.', 'NVIDIA Corporation', 'AMD', 'Google Inc.'];
                const renderers = ['Intel Iris OpenGL Engine', 'NVIDIA GeForce GTX 1080', 'AMD Radeon RX 580', 'ANGLE (Intel)'];
                if (param === 37445) return vendors[{random.randint(0, 3)}];
                if (param === 37446) return renderers[{random.randint(0, 3)}];
                return getParameterProto.call(this, param);
            }};

            // WebGL2
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                const getParameterProto2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(param) {{
                    const vendors = ['Intel Inc.', 'NVIDIA Corporation', 'AMD', 'Google Inc.'];
                    const renderers = ['Intel Iris OpenGL Engine', 'NVIDIA GeForce RTX 3080', 'AMD Radeon RX 6800'];
                    if (param === 37445) return vendors[{random.randint(0, 3)}];
                    if (param === 37446) return renderers[{random.randint(0, 2)}];
                    return getParameterProto2.call(this, param);
                }};
            }}

            // ==================== AUDIO FINGERPRINT SPOOFING ====================
            const originalGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function(channel) {{
                const data = originalGetChannelData.call(this, channel);
                for (let i = 0; i < data.length; i += 100) {{
                    data[i] = data[i] + (Math.random() - 0.5) * 0.0001;
                }}
                return data;
            }};

            // ==================== PERMISSIONS API ====================
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (params) => {{
                if (params.name === 'notifications') {{
                    return Promise.resolve({{ state: 'prompt', onchange: null }});
                }}
                return originalQuery.call(navigator.permissions, params);
            }};

            // ==================== BATTERY API (often used for tracking) ====================
            if (navigator.getBattery) {{
                navigator.getBattery = () => Promise.resolve({{
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1.0,
                    addEventListener: () => {{}},
                    removeEventListener: () => {{}}
                }});
            }}

            // ==================== WEBRTC LEAK PREVENTION ====================
            const originalRTCPeerConnection = window.RTCPeerConnection;
            window.RTCPeerConnection = function(...args) {{
                const pc = new originalRTCPeerConnection(...args);
                pc.createDataChannel = () => null;
                return pc;
            }};

            // ==================== IFRAME DETECTION BYPASS ====================
            Object.defineProperty(window, 'parent', {{ get: () => window }});
            Object.defineProperty(window, 'top', {{ get: () => window }});

            // ==================== AUTOMATION FLAGS ====================
            Object.defineProperty(navigator, 'automationController', {{ get: () => undefined }});
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

            // ==================== HEADLESS DETECTION BYPASS ====================
            Object.defineProperty(navigator, 'headless', {{ get: () => false }});
            Object.defineProperty(document, 'hidden', {{ get: () => false }});
            Object.defineProperty(document, 'visibilityState', {{ get: () => 'visible' }});

            console.log('[URWA Stealth] All anti-detection measures applied');
        }})();
        """

    async def _simulate_human_behavior(self, page) -> None:
        """Simulate realistic human behavior on the page."""
        try:
            # Random scroll behavior
            scroll_times = random.randint(2, 5)
            for _ in range(scroll_times):
                scroll_amount = random.randint(100, 500)
                page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await asyncio.sleep(random.uniform(0.3, 1.0))

            # Random mouse movements (via JavaScript)
            page.evaluate("""
                () => {
                    const event = new MouseEvent('mousemove', {
                        clientX: Math.random() * window.innerWidth,
                        clientY: Math.random() * window.innerHeight,
                        bubbles: true
                    });
                    document.dispatchEvent(event);
                }
            """)

            # Small random delay as "reading time"
            await asyncio.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logger.debug(f"Human behavior simulation error (non-critical): {e}")

    async def _rate_limit_with_jitter(self) -> None:
        """Intelligent rate limiting with random jitter."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        # Dynamic delay based on recent failures
        base_delay = self.min_delay
        if self.failure_count > 3:
            base_delay = self.max_delay

        target_delay = random.uniform(base_delay, base_delay * 1.5)

        if time_since_last < target_delay:
            wait_time = target_delay - time_since_last
            logger.debug(f"[RateLimit] Waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    def _get_next_proxy(self) -> Optional[str]:
        """Rotate through proxy pool."""
        if not self.proxy_pool:
            return None
        proxy = self.proxy_pool[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_pool)
        return proxy

    async def scrape(self, url: str, max_retries: int = 3, force_playwright: bool = False) -> str:
        """
        Main scraping method with full stealth capabilities.

        Args:
            url: Target URL
            max_retries: Maximum retry attempts
            force_playwright: Skip lightweight attempts

        Returns:
            JSON string with extracted content
        """
        logger.info(f"[UltraStealth] Starting scrape: {url[:80]}...")

        # Check cache first
        cached = self._get_from_cache(url)
        if cached:
            return cached

        # Rate limiting
        await self._rate_limit_with_jitter()

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                # Generate unique fingerprint for this attempt
                fingerprint = self._generate_fingerprint()

                # Attempt scrape
                content = await self._execute_stealth_scrape(url, fingerprint)

                if content and len(content) > 100:
                    self._store_in_cache(url, content)
                    self.success_count += 1
                    self.session_history.append({
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "attempt": attempt + 1
                    })
                    return content

                raise ValueError("Empty or insufficient content")

            except Exception as e:
                wait_time = (2 ** attempt) + random.uniform(0.5, 2.0)
                logger.warning(f"[UltraStealth] Attempt {attempt + 1}/{max_retries} failed: {e}")

                if attempt < max_retries - 1:
                    logger.info(f"[UltraStealth] Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    self.failure_count += 1
                    self.session_history.append({
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "status": "failed",
                        "error": str(e)
                    })

        return ""

    async def _execute_stealth_scrape(self, url: str, fingerprint: dict) -> str:
        """Execute the actual stealth scrape."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available")

        user_agent = random.choice(self.USER_AGENTS)
        viewport = random.choice(self.VIEWPORTS)
        timezone = random.choice(self.TIMEZONES)
        locale = random.choice(self.LOCALES)

        return await asyncio.to_thread(
            self._sync_stealth_scrape,
            url, user_agent, viewport, timezone, locale, fingerprint
        )

    def _sync_stealth_scrape(self, url: str, user_agent: str, viewport: dict,
                              timezone: str, locale: str, fingerprint: dict) -> str:
        """Synchronous stealth scrape implementation."""
        try:
            with sync_playwright() as p:
                # Browser launch with maximum stealth args
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--ignore-certificate-errors',
                        '--ignore-ssl-errors',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-popup-blocking',
                        '--disable-translate',
                        '--disable-background-networking',
                        '--disable-sync',
                        '--metrics-recording-only',
                        '--disable-default-apps',
                        '--mute-audio',
                        '--no-default-browser-check',
                        '--autoplay-policy=user-gesture-required',
                        f'--window-size={viewport["width"]},{viewport["height"]}',
                        f'--user-agent={user_agent}',
                    ]
                )

                try:
                    # Create context with full stealth settings
                    context = browser.new_context(
                        user_agent=user_agent,
                        viewport=viewport,
                        locale=locale,
                        timezone_id=timezone,
                        ignore_https_errors=True,
                        java_script_enabled=True,
                        extra_http_headers={
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Sec-Fetch-User': '?1',
                            'Cache-Control': 'max-age=0',
                            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="122", "Chromium";v="122"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                        }
                    )

                    page = context.new_page()

                    # Inject stealth script BEFORE navigation
                    page.add_init_script(self._get_stealth_script(fingerprint))

                    # Random pre-navigation delay
                    time.sleep(random.uniform(0.3, 0.8))

                    # Navigate with fallback strategies
                    try:
                        page.goto(url, wait_until="load", timeout=60000)
                    except Exception:
                        try:
                            # Try waiting only for DOM (faster)
                            page.goto(url, wait_until="domcontentloaded", timeout=40000)
                        except Exception:
                            try:
                                # Last resort: just ensure connection is made
                                page.goto(url, wait_until="commit", timeout=30000)
                            except Exception as e:
                                logger.warning(f"Navigation timeout, continuing... {e}")

                    # Site-Specific Intelligent Wait Logic
                    if "github.com" in url:
                        try:
                            # Wait for key profile/repo elements
                            page.wait_for_selector('.vcard-names, .PinnedRepo-list, #readme, .Layout-main', timeout=8000)
                            logger.info("[UltraStealth] GitHub content detected")
                        except:
                            logger.debug("[UltraStealth] GitHub specific selector not found")
                            
                    elif "msn.com" in url:
                        try:
                            # Wait for article content
                            page.wait_for_selector('article, .article-content, main', timeout=15000)
                            # Scroll down to trigger lazy load
                            page.evaluate("window.scrollBy(0, 500)")
                            time.sleep(2)
                            logger.info("[UltraStealth] MSN content detected")
                        except Exception:
                            logger.debug("[UltraStealth] MSN specific selectors not found, continuing...")
                        
                    elif "goodreturns.in" in url:
                        try:
                            page.wait_for_selector('.content-area, .story-section', timeout=15000)
                            logger.info("[UltraStealth] GoodReturns content detected")
                        except Exception:
                            logger.debug("[UltraStealth] GoodReturns specific selectors not found, continuing...")

                    # Wait for content stabilization
                    time.sleep(random.uniform(2.0, 4.0))
                    
                    # Check for redirects to login (common Soft Block)
                    if "login" in page.url or "signin" in page.url:
                        if "return_to" in page.url or "auth" in page.url:
                            logger.warning(f"[UltraStealth] Redirected to login page: {page.url}")
                            raise ValueError("Redirected to Login Page (Soft Block)")

                    # Simulate human behavior
                    self._sync_human_behavior(page)

                    # Check for bot detection
                    if self._detect_block(page):
                        raise ValueError("Bot detection triggered - trying different strategy")

                    # Extract content
                    content = self._extract_content(page, url)

                    return json.dumps(content, ensure_ascii=False, indent=2)

                finally:
                    browser.close()

        except Exception as e:
            logger.error(f"[UltraStealth] Error scraping {url}: {e}")
            raise

    def _sync_human_behavior(self, page) -> None:
        """Synchronous human behavior simulation."""
        try:
            # Scroll
            for _ in range(random.randint(2, 4)):
                page.evaluate(f"window.scrollBy(0, {random.randint(100, 400)})")
                time.sleep(random.uniform(0.2, 0.6))

            # Mouse movement simulation
            page.evaluate("""
                const event = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight,
                    bubbles: true
                });
                document.dispatchEvent(event);
            """)

            time.sleep(random.uniform(0.3, 0.8))

        except Exception:
            pass

    def _detect_block(self, page) -> bool:
        """Detect if we've been blocked or challenged."""
        try:
            title = page.title().lower()
            content = page.content().lower()[:5000]

            # Only check TITLE for block indicators (content has too many false positives)
            title_block_indicators = [
                'access denied', 'blocked', 'captcha', 
                'just a moment', 'attention required',
                'checking your browser', 'please wait',
                'ddos protection', 'security check'
            ]
            
            for indicator in title_block_indicators:
                if indicator in title:
                    logger.warning(f"Block indicator in title: {indicator}")
                    return True
            
            # Check for Cloudflare challenge page specifically
            if 'just a moment' in title or 'attention required' in title:
                return True
            
            # Check for very short content that suggests a block page
            if len(content) < 500 and any(x in content for x in ['captcha', 'verify you are human', 'unusual traffic']):
                logger.warning("Block page detected (short content with block keywords)")
                return True

            return False

        except Exception:
            return False

    def _extract_content(self, page, url: str) -> dict:
        """Extract structured content from page."""
        try:
            # 1. Get raw HTML and convert to Markdown (Better for LLM)
            html = page.content()
            markdown_content = ""
            
            if HTML2TEXT_AVAILABLE:
                try:
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    h.ignore_images = True
                    h.body_width = 0
                    markdown_content = h.handle(html)
                except Exception as e:
                    logger.warning(f"Markdown conversion failed: {e}")
            
            # 2. Extract structured data via JS
            data = page.evaluate("""
                () => {
                    const result = {
                        title: document.title,
                        items: [],
                        headings: [],
                        links: [],
                        text_content: ''
                    };

                    // Extract headings
                    document.querySelectorAll('h1, h2, h3').forEach(h => {
                        const text = h.textContent?.trim();
                        if (text) result.headings.push({ level: h.tagName, text });
                    });

                    // Extract links
                    document.querySelectorAll('a[href]').forEach(a => {
                        const text = a.textContent?.trim();
                        const href = a.href;
                        if (text && href && !href.startsWith('javascript:')) {
                            result.links.push({ text: text.slice(0, 100), url: href });
                        }
                    });

                    // Extract main text (fallback if markdown fails)
                    const mainContent = document.querySelector('main, article, .content, #content, .main') 
                        || document.body;
                    result.text_content = mainContent.innerText?.slice(0, 20000) || '';

                    // Try to find list items (products, companies, etc.)
                    const listSelectors = [
                        '.product', '.item', '.card', '.company', '[class*="item"]',
                        'li', 'article', '[class*="card"]', '.listing-card', '.job-card'
                    ];

                    for (const selector of listSelectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 3) {
                            elements.forEach((el, i) => {
                                if (i >= 50) return;
                                const title = el.querySelector('h1, h2, h3, h4, .title, .name, a')?.textContent?.trim();
                                const desc = el.querySelector('p, .description, .summary')?.textContent?.trim();
                                const price = el.querySelector('[class*="price"], .cost')?.textContent?.trim();
                                
                                if (title) {
                                    result.items.push({
                                        title,
                                        description: desc?.slice(0, 200),
                                        price,
                                        source: window.location.hostname
                                    });
                                }
                            });
                            if (result.items.length > 0) break;
                        }
                    }

                    return result;
                }
            """)

            # 3. Combine and Format
            
            # Prefer Markdown if available and sufficient
            final_content = markdown_content if len(markdown_content) > 100 else data.get("text_content", "")
            
            return {
                "url": url,
                "structured_data": {
                    "title": data.get("title", ""),
                    "items": data.get("items", []),
                    "headings": data.get("headings", [])[:20],
                    "links": data.get("links", [])[:30],
                    "total_items": len(data.get("items", []))
                },
                "raw_html_content": final_content[:30000],  # Increased limit
                "metadata": {
                    "extraction_method": "ultra_stealth",
                    "timestamp": datetime.now().isoformat(),
                    "items_found": len(data.get("items", [])),
                    "markdown_available": bool(markdown_content)
                }
            }

        except Exception as e:
            logger.error(f"Content extraction error: {e}")
            return {
                "url": url,
                "structured_data": {},
                "raw_html_content": "",
                "metadata": {"extraction_method": "failed", "error": str(e)}
            }

    def get_stats(self) -> dict:
        """Return scraping statistics."""
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count),
            "cache_size": len(self.cache),
            "session_history_count": len(self.session_history)
        }

    def clear_cache(self):
        """Clear the content cache."""
        self.cache.clear()

    def get_session_history(self) -> list:
        """Return session history."""
        return self.session_history[-50:]  # Last 50 entries
