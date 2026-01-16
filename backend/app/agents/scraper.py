from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import html2text
from loguru import logger
import asyncio
import sys
import random
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib

# Windows ProactorLoop fix for python 3.8+ (and sub-processing issues)
# REMOVE the policy setting from here as it might conflict with uvicorn loop setup
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

class StealthScraper:
    # Pool of realistic user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    
    # Viewport sizes for randomization
    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 2560, "height": 1440},
    ]
    
    def __init__(self):
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = True
        
        # Cache: URL -> (content, timestamp)
        self.cache: Dict[str, tuple[str, datetime]] = {}
        self.cache_ttl = timedelta(minutes=30)  # Cache validity: 30 minutes
        
        # Rate limiting: Track last request time
        self.last_request_time = 0
        self.min_delay_between_requests = 2.0  # Minimum 2 seconds between requests
        
        # Session persistence
        self.session_history = []
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_from_cache(self, url: str) -> Optional[str]:
        """Retrieve from cache if valid"""
        key = self._get_cache_key(url)
        if key in self.cache:
            content, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.info(f"Cache HIT for {url}")
                return content
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def _store_in_cache(self, url: str, content: str):
        """Store content in cache"""
        key = self._get_cache_key(url)
        self.cache[key] = (content, datetime.now())
        logger.debug(f"Cached content for {url}")
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay_between_requests:
            wait_time = self.min_delay_between_requests - time_since_last
            # Add small random jitter (0-500ms)
            wait_time += random.uniform(0, 0.5)
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

    async def scrape(self, url: str, max_retries: int = 3) -> str:
        """
        Scrapes a URL with advanced features:
        - Caching with TTL
        - Retry logic with exponential backoff
        - Rate limiting
        - User agent rotation
        - Enhanced stealth
        """
        logger.info(f"Scraping URL: {url}")
        
        # Check cache first
        cached_content = self._get_from_cache(url)
        if cached_content:
            return cached_content
        
        # Rate limiting
        await self._rate_limit()
        
        # Retry loop with exponential backoff
        last_error = "Unknown error"
        for attempt in range(max_retries):
            try:
                content = await self._scrape_with_stealth(url)
                
                if content:
                    # Store in cache and session history
                    self._store_in_cache(url, content)
                    self.session_history.append({
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "content_length": len(content)
                    })
                    return content
                else:
                    raise ValueError("Empty content returned")
                    
            except Exception as e:
                last_error = str(e)
                wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {last_error}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait_time:.2f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed for {url}")
                    self.session_history.append({
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "status": "failed",
                        "error": last_error
                    })
                    return ""
        
        return ""
    
    async def _scrape_with_stealth(self, url: str) -> str:
        """
        Internal scraping method with full stealth capabilities
        """
        # Randomly select user agent and viewport
        user_agent = random.choice(self.USER_AGENTS)
        viewport = random.choice(self.VIEWPORTS)
        
        # Use sync playwright in a thread to avoid asyncio subprocess issues on Windows
        return await asyncio.to_thread(self._sync_scrape_with_stealth, url, user_agent, viewport)
    
    def _sync_scrape_with_stealth(self, url: str, user_agent: str, viewport: dict) -> str:
        """
        Synchronous scraping method using sync playwright with intelligent parsing
        """
        try:
            with sync_playwright() as p:
                # Enhanced stealth arguments - back to Chromium for reliability
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                        '--window-position=0,0',
                        '--ignore-certificate-errors',
                        '--ignore-ssl-errors',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        f'--user-agent={user_agent}'
                    ]
                )

                try:
                    # Create context with randomized properties
                    headers = {
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0',
                    }
                    context = browser.new_context(
                        user_agent=user_agent,
                        viewport=viewport,
                        locale='en-US',
                        timezone_id='America/New_York',
                        extra_http_headers=headers,
                        ignore_https_errors=True,
                    )

                    page = context.new_page()

                    # Headers already set on context above (line 206)

                    # Inject script to remove webdriver property and other detection vectors
                    page.add_init_script("""
                        // Remove webdriver property
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });

                        // Hide headless property
                        Object.defineProperty(navigator, 'headless', {
                            get: () => false
                        });

                        // ADVANCED: Realistic Chrome plugins
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [
                                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'}
                            ]
                        });

                        // Mock languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });

                        // Chrome runtime mock (common detection)
                        if (!window.chrome) window.chrome = {};
                        window.chrome.runtime = {connect: () => {}, sendMessage: () => {}};

                        // ADVANCED: Canvas fingerprint randomization (bypass canvas detection)
                        const shift = Math.random() * 0.0001;
                        const getImageData = CanvasRenderingContext2D.prototype.getImageData;
                        CanvasRenderingContext2D.prototype.getImageData = function() {
                            const imageData = getImageData.apply(this, arguments);
                            for (let i = 0; i < imageData.data.length; i++) {
                                imageData.data[i] = imageData.data[i] + shift;
                            }
                            return imageData;
                        };

                        // ADVANCED: WebGL vendor spoofing (bypass WebGL fingerprinting)
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(param) {
                            if (param === 37445) return 'Intel Inc.';
                            if (param === 37446) return 'Intel Iris OpenGL Engine';
                            return getParameter.apply(this, arguments);
                        };

                        // Permissions
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    """)

                    # Random human-like delay before navigation
                    time.sleep(random.uniform(0.3, 0.8))

                    # Navigate with short timeout
                    logger.info(f"Navigating to {url}...")
                    try:
                        page.goto(url, wait_until="load", timeout=35000)
                    except:
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        except:
                            logger.warning(f"Timeout for {url}, continuing...")

                    time.sleep(0.5)

                    # Intelligent content extraction based on website type
                    content_data = self._extract_structured_content(page, url)

                    # Check for blocks or CAPTCHAs
                    title = page.title()

                    # Strict bot detection - only title
                    title_lower = title.lower()

                    if 'captcha' in title_lower or 'challenge' in title_lower or 'unusual traffic' in title_lower:
                        logger.warning(f"Bot detection triggered for {url}")
                        raise ValueError("Bot detection/CAPTCHA detected")

                    # Return structured data as JSON string
                    import json
                    return json.dumps(content_data, ensure_ascii=False, indent=2)

                except Exception as e:
                    logger.error(f"Error in _sync_scrape_with_stealth for {url}: {e}")
                    raise
                finally:
                    browser.close()
        except Exception as outer_e:
            logger.error(f"Critical error in _sync_scrape_with_stealth for {url}: {outer_e}")
            return ""

    def _extract_structured_content(self, page, url: str) -> dict:
        """
        Universal structured content extraction using intelligent pattern recognition
        """
        try:
            # Use universal extraction that works with any website
            return self._extract_universal_data(page, url)
        except Exception as e:
            logger.error(f"Error extracting structured content from {url}: {e}")
            return self._extract_generic_content(page, url)

    def _extract_universal_data(self, page, url: str) -> dict:
        """
        Intelligent universal data extraction that works with any listing website
        """
        try:
            # Wait for content to load
            page.wait_for_timeout(2000)

            # Extract data using intelligent JavaScript that analyzes page structure
            extracted_data = page.evaluate("""
                () => {
                    const results = {
                        items: [],
                        detected_type: 'unknown',
                        confidence: 0,
                        total_found: 0
                    };

                    // Common selectors for different types of content
                    const patterns = [
                        // Company/Organization cards
                        {
                            type: 'companies',
                            selectors: [
                                'div.companyCardWrapper',
                                '[data-testid="company-card"]',
                                '.company-card',
                                '.company-item',
                                '[class*="company"]',
                                '.card:has(h2, h3)',
                                '.item:has(.rating, .review)'
                            ],
                            fields: {
                                name: ['h2', 'h3', '.company-name', '.name', 'a', '[class*="name"]'],
                                rating: ['.rating', '[class*="rating"]', '.stars', '[data-testid*="rating"]'],
                                reviews: ['.reviews', '[class*="review"]', '.review-count', '[data-testid*="review"]'],
                                description: ['p', '.description', '.summary', '[class*="desc"]'],
                                industry: ['.industry', '.category', '.sector', '[class*="industry"]'],
                                location: ['.location', '.city', '.address', '[class*="location"]']
                            }
                        },
                        // Product items
                        {
                            type: 'products',
                            selectors: [
                                '.product-card',
                                '.product-item',
                                '[data-testid="product"]',
                                '.item-card',
                                '.product',
                                '[class*="product"]'
                            ],
                            fields: {
                                name: ['h2', 'h3', '.product-name', '.name', '.title', 'a'],
                                price: ['.price', '[class*="price"]', '.cost', '.amount'],
                                description: ['p', '.description', '.summary'],
                                category: ['.category', '.type', '.brand'],
                                rating: ['.rating', '[class*="rating"]']
                            }
                        },
                        // Generic listings
                        {
                            type: 'listings',
                            selectors: [
                                'li',
                                '.list-item',
                                '.item',
                                '[class*="item"]',
                                'article',
                                '.card'
                            ],
                            fields: {
                                title: ['h1', 'h2', 'h3', 'h4', '.title', '.name', 'a'],
                                description: ['p', '.description', '.summary', '.content'],
                                link: ['a'],
                                metadata: ['.meta', '.info', '.details']
                            }
                        }
                    ];

                    // Try each pattern to find the best match
                    let bestMatch = null;
                    let maxItems = 0;

                    for (const pattern of patterns) {
                        for (const selector of pattern.selectors) {
                            try {
                                const elements = document.querySelectorAll(selector);
                                if (elements.length > maxItems && elements.length >= 3) {
                                    maxItems = elements.length;
                                    bestMatch = { pattern, selector, elements };
                                }
                            } catch (e) {
                                continue;
                            }
                        }
                    }

                    if (!bestMatch || maxItems < 3) {
                        // Fallback: try to find any repeating structure
                        const allElements = document.querySelectorAll('*');
                        const elementCounts = {};

                        for (const el of allElements) {
                            const tag = el.tagName.toLowerCase();
                            const className = el.className || '';
                            const key = `${tag}.${className.split(' ').join('.')}`;

                            if (!elementCounts[key]) elementCounts[key] = 0;
                            elementCounts[key]++;
                        }

                        // Find the most common element type
                        let mostCommon = null;
                        let maxCount = 0;
                        for (const [key, count] of Object.entries(elementCounts)) {
                            if (count > maxCount && count >= 5) {
                                maxCount = count;
                                mostCommon = key;
                            }
                        }

                        if (mostCommon) {
                            const [tagName, className] = mostCommon.split('.');
                            const selector = className ? `${tagName}.${className.split('.').join('.')}` : tagName;
                            const elements = document.querySelectorAll(selector);

                            bestMatch = {
                                pattern: patterns[2], // Use generic listings pattern
                                selector,
                                elements: Array.from(elements).slice(0, 50)
                            };
                        }
                    }

                    if (bestMatch) {
                        const { pattern, elements } = bestMatch;
                        results.detected_type = pattern.type;
                        results.confidence = Math.min(maxItems / 10, 1); // Confidence based on item count

                        // Extract data from each element
                        elements.forEach((element, index) => {
                            if (index >= 50) return; // Limit to 50 items

                            try {
                                const item = {};

                                // Extract each field
                                for (const [fieldName, fieldSelectors] of Object.entries(pattern.fields)) {
                                    for (const fieldSelector of fieldSelectors) {
                                        try {
                                            let value = null;

                                            if (fieldSelector === 'a' && fieldName === 'link') {
                                                value = element.querySelector(fieldSelector)?.href;
                                            } else {
                                                value = element.querySelector(fieldSelector)?.textContent?.trim();
                                            }

                                            if (value && value.length > 0) {
                                                // Clean up the value
                                                if (fieldName === 'reviews' || fieldName === 'rating') {
                                                    // Extract numbers
                                                    const numMatch = value.match(/\\d+(\\.\\d+)?/);
                                                    if (numMatch) value = numMatch[0];
                                                } else if (fieldName === 'price') {
                                                    // Clean price format
                                                    value = value.replace(/[^\\d.,]/g, '');
                                                }

                                                item[fieldName] = value;
                                                break; // Found a value, move to next field
                                            }
                                        } catch (e) {
                                            continue;
                                        }
                                    }
                                }

                                // Only add if we found at least a name/title
                                if (item.name || item.title) {
                                    // Add source and URL info
                                    item.source = window.location.hostname;
                                    item.page_url = window.location.href;

                                    results.items.push(item);
                                }

                            } catch (e) {
                                console.log('Error extracting item:', e);
                            }
                        });

                        results.total_found = results.items.length;
                    }

                    return results;
                }
            """)

            # Process the extracted data
            items = extracted_data.get('items', [])
            detected_type = extracted_data.get('detected_type', 'unknown')
            confidence = extracted_data.get('confidence', 0)

            # Format response based on detected type
            if detected_type == 'companies' and items:
                return {
                    "url": url,
                    "structured_data": {
                        "companies": items,
                        "total_companies": len(items),
                        "source": "universal_extraction"
                    },
                    "metadata": {
                        "extraction_method": "universal_intelligent",
                        "detected_type": detected_type,
                        "confidence": confidence,
                        "companies_found": len(items)
                    }
                }
            elif detected_type == 'products' and items:
                return {
                    "url": url,
                    "structured_data": {
                        "products": items,
                        "total_products": len(items),
                        "source": "universal_extraction"
                    },
                    "metadata": {
                        "extraction_method": "universal_intelligent",
                        "detected_type": detected_type,
                        "confidence": confidence,
                        "products_found": len(items)
                    }
                }
            elif items:
                return {
                    "url": url,
                    "structured_data": {
                        "items": items,
                        "total_items": len(items),
                        "source": "universal_extraction"
                    },
                    "metadata": {
                        "extraction_method": "universal_intelligent",
                        "detected_type": detected_type,
                        "confidence": confidence,
                        "items_found": len(items)
                    }
                }
            else:
                # Fallback to generic extraction
                return self._extract_generic_content(page, url)

        except Exception as e:
            logger.error(f"Error in universal data extraction: {e}")
            return self._extract_generic_content(page, url)

    def _extract_generic_content(self, page, url: str) -> dict:
        """
        Fallback generic content extraction
        """
        try:
            # Get basic page content
            title = page.title()
            content = page.content()

            # Try to extract some structured data
            headings = page.evaluate("""
                () => Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                    level: h.tagName.toLowerCase(),
                    text: h.textContent.trim()
                }))
            """)

            links = page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).slice(0, 20).map(a => ({
                    text: a.textContent.trim(),
                    url: a.href
                })).filter(link => link.text.length > 0)
                            } else if (interlinking) {
                                industry = interlinking;
                            }

                            const link = card.querySelector('a')?.href;

                            if (name) {
                                companies.push({
                                    name: name,
                                    rating: rating || 'N/A',
                                    reviews: cleanReviews || 'N/A',
                                    industry: industry || '',
                                    location: location || '',
                                    url: link || '',
                                    source: 'AmbitionBox'
                                });
                            }
                        } catch (e) {
                            console.log('Error parsing company card:', e);
                        }
                    });

                    return companies;
                }
            """)

            # Try to get all pages if this is the main companies page
            if '/companies' in url and len(companies_data) < 50:
                # Try to click "Load More" or navigate to next pages
                try:
                    # Look for pagination or load more button
                    load_more_selectors = [
                        '[data-testid="load-more"]',
                        'button:has-text("Load More")',
                        'button:has-text("Show More")',
                        '.load-more',
                        '.pagination-next'
                    ]

                    for selector in load_more_selectors:
                        try:
                            page.click(selector, timeout=5000)
                            page.wait_for_timeout(2000)
                            break
                        except:
                            continue

                    # Re-extract after loading more
                    updated_companies = page.evaluate("""
                        () => {
                            const companies = [];
                            const companyCards = document.querySelectorAll('div.companyCardWrapper');

                            companyCards.forEach(card => {
                                try {
                                    const name = card.querySelector('h2.companyCardWrapper__companyName')?.textContent?.trim();
                                    const rating = card.querySelector('div.rating_text')?.textContent?.trim();
                                    const reviews = card.querySelector('span.companyCardWrapper__companyRatingCount')?.textContent?.trim();
                                    const cleanReviews = reviews ? reviews.replace(/[()]/g, '') : null;

                                    const interlinking = card.querySelector('span.companyCardWrapper__interLinking')?.textContent?.trim();
                                    let industry = null;
                                    let location = null;
                                    if (interlinking && interlinking.includes(' | ')) {
                                        [industry, location] = interlinking.split(' | ', 2);
                                    } else if (interlinking) {
                                        industry = interlinking;
                                    }

                                    if (name && !companies.some(c => c.name === name)) {
                                        companies.push({
                                            name: name,
                                            rating: rating || 'N/A',
                                            reviews: cleanReviews || 'N/A',
                                            industry: industry || '',
                                            location: location || '',
                                            source: 'AmbitionBox'
                                        });
                                    }
                                } catch (e) {}
                            });

                            return companies;
                        }
                    """)

                    if len(updated_companies) > len(companies_data):
                        companies_data = updated_companies

                except Exception as e:
                    logger.info(f"Could not load more companies: {e}")

            return {
                "url": url,
                "structured_data": {
                    "companies": companies_data,
                    "total_companies": len(companies_data),
                    "source": "AmbitionBox"
                },
                "metadata": {
                    "extraction_method": "ambitionbox_specific",
                    "companies_found": len(companies_data)
                }
            }

        except Exception as e:
            logger.error(f"Error extracting AmbitionBox data: {e}")
            return self._extract_generic_content(page, url)

    def _extract_listing_data(self, page, url: str) -> dict:
        """
        Extract data from generic listing pages
        """
        try:
            # Wait for list items to load
            page.wait_for_selector('li, .item, .card, .product, .company', timeout=5000)

            items_data = page.evaluate("""
                () => {
                    const items = [];
                    const selectors = ['li', '.item', '.card', '.product', '.company', '[class*="item"]'];

                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 5) {  // Only if we find multiple items
                            elements.forEach(el => {
                                try {
                                    const title = el.querySelector('h1, h2, h3, h4, .title, .name, a')?.textContent?.trim();
                                    const description = el.querySelector('p, .description, .summary')?.textContent?.trim();
                                    const link = el.querySelector('a')?.href;
                                    const price = el.querySelector('[class*="price"], .cost')?.textContent?.trim();

                                    if (title) {
                                        items.push({
                                            title: title,
                                            description: description || '',
                                            url: link || '',
                                            price: price || '',
                                            source: window.location.hostname
                                        });
                                    }
                                } catch (e) {}
                            });
                            break;  // Use the first selector that works
                        }
                    }

                    return items.slice(0, 100);  // Limit to 100 items
                }
            """)

            return {
                "url": url,
                "structured_data": {
                    "items": items_data,
                    "total_items": len(items_data),
                    "source": "listing_page"
                },
                "metadata": {
                    "extraction_method": "listing_page",
                    "items_found": len(items_data)
                }
            }

        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return self._extract_generic_content(page, url)

    def _extract_generic_content(self, page, url: str) -> dict:
        """
        Fallback generic content extraction
        """
        try:
            # Get basic page content
            title = page.title()
            content = page.content()

            # Try to extract some structured data
            headings = page.evaluate("""
                () => Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                    level: h.tagName.toLowerCase(),
                    text: h.textContent.trim()
                }))
            """)

            links = page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).slice(0, 20).map(a => ({
                    text: a.textContent.trim(),
                    url: a.href
                })).filter(link => link.text.length > 0)
            """)

            # Convert to markdown
            try:
                markdown = self.converter.handle(content)
            except:
                markdown = content

            return {
                "url": url,
                "raw_html_content": content[:10000],  # Limit content size
                "structured_data": {
                    "headings": headings,
                    "links": links
                },
                "metadata": {
                    "extraction_method": "generic",
                    "title": title,
                    "content_length": len(content)
                }
            }

        except Exception as e:
            logger.error(f"Error in generic content extraction: {e}")
            return {
                "url": url,
                "error": str(e),
                "structured_data": {},
                "metadata": {"extraction_method": "failed"}
            }
