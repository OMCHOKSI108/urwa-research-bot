"""
ADVANCED PROTECTED SITE BYPASS
Implements techniques that go beyond standard scraping.

Features:
- CAPTCHA solving integration (2Captcha)
- Browser session persistence with real profiles
- Cloudflare UAM bypass
- Cookie harvesting from real browsers
- Visual extraction with OCR
- Human-in-the-loop queue
"""

import asyncio
import aiohttp
import random
import time
import json
import os
import base64
import hashlib
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from loguru import logger


class CaptchaSolver:
    """
    CAPTCHA solving integration.
    Supports 2Captcha, Anti-Captcha, CapMonster.
    """
    
    def __init__(self, api_key: str = None, service: str = "2captcha"):
        self.api_key = api_key or os.getenv("CAPTCHA_API_KEY")
        self.service = service
        self.solved_count = 0
        self.failed_count = 0
        
        # Service endpoints
        self.endpoints = {
            "2captcha": {
                "submit": "http://2captcha.com/in.php",
                "result": "http://2captcha.com/res.php"
            },
            "anticaptcha": {
                "submit": "https://api.anti-captcha.com/createTask",
                "result": "https://api.anti-captcha.com/getTaskResult"
            }
        }
    
    async def solve_recaptcha(self, site_key: str, page_url: str, 
                              invisible: bool = False) -> Optional[str]:
        """
        Solve reCAPTCHA v2/v3.
        
        Args:
            site_key: The reCAPTCHA site key from the page
            page_url: URL of the page with CAPTCHA
            invisible: Whether it's invisible reCAPTCHA
            
        Returns:
            CAPTCHA solution token or None
        """
        if not self.api_key:
            logger.warning("[CAPTCHA] No API key configured")
            return None
        
        try:
            if self.service == "2captcha":
                return await self._solve_2captcha_recaptcha(site_key, page_url, invisible)
            else:
                return await self._solve_anticaptcha_recaptcha(site_key, page_url, invisible)
        except Exception as e:
            logger.error(f"[CAPTCHA] Solve failed: {e}")
            self.failed_count += 1
            return None
    
    async def _solve_2captcha_recaptcha(self, site_key: str, page_url: str,
                                         invisible: bool) -> Optional[str]:
        """2Captcha reCAPTCHA solving."""
        async with aiohttp.ClientSession() as session:
            # Submit task
            params = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "invisible": 1 if invisible else 0,
                "json": 1
            }
            
            async with session.get(self.endpoints["2captcha"]["submit"], params=params) as resp:
                result = await resp.json()
                
            if result.get("status") != 1:
                logger.error(f"[2Captcha] Submit failed: {result}")
                return None
            
            task_id = result["request"]
            logger.info(f"[2Captcha] Task submitted: {task_id}")
            
            # Poll for result (max 120 seconds)
            for _ in range(24):
                await asyncio.sleep(5)
                
                async with session.get(
                    self.endpoints["2captcha"]["result"],
                    params={"key": self.api_key, "action": "get", "id": task_id, "json": 1}
                ) as resp:
                    result = await resp.json()
                
                if result.get("status") == 1:
                    self.solved_count += 1
                    logger.info(f"[2Captcha] Solved! (total: {self.solved_count})")
                    return result["request"]
                elif result.get("request") != "CAPCHA_NOT_READY":
                    logger.error(f"[2Captcha] Error: {result}")
                    return None
            
            logger.error("[2Captcha] Timeout waiting for solution")
            return None
    
    async def _solve_anticaptcha_recaptcha(self, site_key: str, page_url: str,
                                            invisible: bool) -> Optional[str]:
        """Anti-Captcha reCAPTCHA solving."""
        async with aiohttp.ClientSession() as session:
            # Create task
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "RecaptchaV2TaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": site_key,
                    "isInvisible": invisible
                }
            }
            
            async with session.post(
                self.endpoints["anticaptcha"]["submit"],
                json=payload
            ) as resp:
                result = await resp.json()
            
            if result.get("errorId") != 0:
                logger.error(f"[AntiCaptcha] Submit failed: {result}")
                return None
            
            task_id = result["taskId"]
            
            # Poll for result
            for _ in range(24):
                await asyncio.sleep(5)
                
                async with session.post(
                    self.endpoints["anticaptcha"]["result"],
                    json={"clientKey": self.api_key, "taskId": task_id}
                ) as resp:
                    result = await resp.json()
                
                if result.get("status") == "ready":
                    self.solved_count += 1
                    return result["solution"]["gRecaptchaResponse"]
            
            return None
    
    async def solve_image_captcha(self, image_base64: str) -> Optional[str]:
        """Solve image-based CAPTCHA."""
        if not self.api_key:
            return None
        
        async with aiohttp.ClientSession() as session:
            params = {
                "key": self.api_key,
                "method": "base64",
                "body": image_base64,
                "json": 1
            }
            
            async with session.post(self.endpoints["2captcha"]["submit"], data=params) as resp:
                result = await resp.json()
            
            if result.get("status") != 1:
                return None
            
            task_id = result["request"]
            
            for _ in range(12):
                await asyncio.sleep(5)
                
                async with session.get(
                    self.endpoints["2captcha"]["result"],
                    params={"key": self.api_key, "action": "get", "id": task_id, "json": 1}
                ) as resp:
                    result = await resp.json()
                
                if result.get("status") == 1:
                    self.solved_count += 1
                    return result["request"]
            
            return None
    
    def get_stats(self) -> Dict:
        return {
            "solved": self.solved_count,
            "failed": self.failed_count,
            "service": self.service,
            "configured": bool(self.api_key)
        }


class CloudflareBypass:
    """
    Cloudflare UAM (Under Attack Mode) bypass techniques.
    """
    
    # Known Cloudflare challenge indicators
    CF_INDICATORS = [
        "cf-browser-verification",
        "cf_chl_opt",
        "Checking your browser",
        "Just a moment",
        "__cf_bm",
        "cf-ray"
    ]
    
    @classmethod
    async def detect_cloudflare(cls, page) -> Dict:
        """Detect Cloudflare protection type."""
        try:
            content = await page.content()
            title = await page.title()
            cookies = await page.context.cookies()
            
            result = {
                "detected": False,
                "type": None,
                "challenge_token": None
            }
            
            content_lower = content.lower()
            
            # Check for JS challenge
            if "checking your browser" in content_lower or "just a moment" in content_lower:
                result["detected"] = True
                result["type"] = "js_challenge"
            
            # Check for managed challenge (CAPTCHA)
            if "cf-chl-widget" in content or "turnstile" in content_lower:
                result["detected"] = True
                result["type"] = "managed_challenge"
            
            # Check for block page
            if "access denied" in content_lower and "cloudflare" in content_lower:
                result["detected"] = True
                result["type"] = "block"
            
            # Check cookies for clearance
            for cookie in cookies:
                if cookie.get("name") == "cf_clearance":
                    result["clearance_cookie"] = cookie
                    break
            
            return result
            
        except Exception as e:
            logger.debug(f"[CF] Detection error: {e}")
            return {"detected": False}
    
    @classmethod
    async def wait_for_challenge(cls, page, timeout: int = 30) -> bool:
        """
        Wait for Cloudflare JS challenge to complete.
        Some challenges auto-solve after waiting.
        """
        start = time.time()
        
        while time.time() - start < timeout:
            cf_status = await cls.detect_cloudflare(page)
            
            if not cf_status["detected"]:
                # Challenge passed!
                logger.info("[CF] Challenge completed!")
                return True
            
            if cf_status["type"] == "managed_challenge":
                # CAPTCHA required - can't auto-solve
                logger.warning("[CF] CAPTCHA challenge - requires solving")
                return False
            
            if cf_status["type"] == "block":
                logger.warning("[CF] Blocked by Cloudflare")
                return False
            
            # JS challenge - wait for it to complete
            await asyncio.sleep(2)
        
        logger.warning("[CF] Challenge timeout")
        return False
    
    @classmethod
    async def extract_turnstile_token(cls, page, captcha_solver: CaptchaSolver = None) -> Optional[str]:
        """
        Extract and solve Cloudflare Turnstile.
        """
        try:
            # Find turnstile iframe
            turnstile_frame = await page.query_selector("iframe[src*='challenges.cloudflare.com']")
            
            if not turnstile_frame:
                return None
            
            # Extract site key
            src = await turnstile_frame.get_attribute("src")
            if "sitekey=" in src:
                site_key = src.split("sitekey=")[1].split("&")[0]
                
                if captcha_solver:
                    # Use CAPTCHA service
                    return await captcha_solver.solve_recaptcha(
                        site_key=site_key,
                        page_url=page.url,
                        invisible=True
                    )
            
            return None
            
        except Exception as e:
            logger.debug(f"[CF] Turnstile extraction error: {e}")
            return None


class ProxyIntelligence:
    """
    Smart proxy management and rotation.
    Scores proxies based on success, latency, and bans.
    """
    
    def __init__(self):
        self.proxies: List[Dict] = []
        self.proxy_scores: Dict[str, Dict] = {}
        self.banned_proxies: set = set()
    
    def add_proxy(self, proxy: str, proxy_type: str = "http"):
        """Add a proxy to the pool."""
        proxy_id = hashlib.md5(proxy.encode()).hexdigest()[:8]
        
        self.proxies.append({
            "id": proxy_id,
            "url": proxy,
            "type": proxy_type
        })
        
        self.proxy_scores[proxy_id] = {
            "success": 0,
            "failure": 0,
            "latency_avg": 0,
            "last_used": None,
            "banned_on": []
        }
    
    def add_proxies_from_list(self, proxy_list: List[str]):
        """Add multiple proxies."""
        for proxy in proxy_list:
            self.add_proxy(proxy)
    
    def get_best_proxy(self, domain: str = None) -> Optional[Dict]:
        """
        Get the best performing proxy for a domain.
        Considers success rate, latency, and domain-specific bans.
        """
        if not self.proxies:
            return None
        
        # Filter out globally banned and domain-banned proxies
        available = []
        for proxy in self.proxies:
            pid = proxy["id"]
            
            if pid in self.banned_proxies:
                continue
            
            score = self.proxy_scores[pid]
            
            if domain and domain in score.get("banned_on", []):
                continue
            
            available.append(proxy)
        
        if not available:
            logger.warning("[Proxy] No available proxies!")
            return None
        
        # Score and sort
        def calculate_score(proxy):
            s = self.proxy_scores[proxy["id"]]
            total = s["success"] + s["failure"]
            if total == 0:
                return 0.5  # Untested proxy
            
            success_rate = s["success"] / total
            latency_penalty = min(s["latency_avg"] / 5000, 0.5)  # Penalize slow proxies
            
            return success_rate - latency_penalty
        
        # Sort by score, pick best with some randomization
        available.sort(key=calculate_score, reverse=True)
        
        # Pick from top 3 randomly for distribution
        top_count = min(3, len(available))
        return random.choice(available[:top_count])
    
    def record_result(self, proxy_id: str, success: bool, latency: float = 0, 
                      domain: str = None, banned: bool = False):
        """Record proxy usage result."""
        if proxy_id not in self.proxy_scores:
            return
        
        score = self.proxy_scores[proxy_id]
        
        if success:
            score["success"] += 1
        else:
            score["failure"] += 1
        
        # Update latency average
        if latency > 0:
            old_avg = score["latency_avg"]
            total = score["success"] + score["failure"]
            score["latency_avg"] = (old_avg * (total - 1) + latency) / total
        
        score["last_used"] = datetime.now().isoformat()
        
        if banned and domain:
            score["banned_on"].append(domain)
            logger.warning(f"[Proxy] {proxy_id} banned on {domain}")
    
    def get_stats(self) -> Dict:
        return {
            "total_proxies": len(self.proxies),
            "banned_count": len(self.banned_proxies),
            "scores": {
                pid: {
                    "success_rate": s["success"] / max(1, s["success"] + s["failure"]),
                    "latency": s["latency_avg"],
                    "banned_domains": len(s.get("banned_on", []))
                }
                for pid, s in list(self.proxy_scores.items())[:10]
            }
        }


class HumanInTheLoop:
    """
    Queue system for human intervention when automation fails.
    Routes CAPTCHAs, logins, and blocks to a manual queue.
    """
    
    QUEUE_FILE = "app/static/human_queue.json"
    
    def __init__(self):
        self.queue: List[Dict] = []
        self.completed: Dict[str, Dict] = {}
        self._load_queue()
    
    def _load_queue(self):
        try:
            if os.path.exists(self.QUEUE_FILE):
                with open(self.QUEUE_FILE, 'r') as f:
                    data = json.load(f)
                    self.queue = data.get("queue", [])
                    self.completed = data.get("completed", {})
        except Exception as e:
            logger.warning(f"[HumanQueue] Load failed: {e}")
    
    def _save_queue(self):
        try:
            os.makedirs(os.path.dirname(self.QUEUE_FILE), exist_ok=True)
            with open(self.QUEUE_FILE, 'w') as f:
                json.dump({
                    "queue": self.queue,
                    "completed": self.completed
                }, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"[HumanQueue] Save failed: {e}")
    
    def add_task(self, task_type: str, url: str, 
                 screenshot_base64: str = None,
                 additional_data: Dict = None) -> str:
        """
        Add a task requiring human intervention.
        
        Args:
            task_type: captcha, login, verification, block
            url: URL that needs intervention
            screenshot_base64: Screenshot of the page
            additional_data: Extra context
            
        Returns:
            Task ID
        """
        task_id = hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:12]
        
        task = {
            "id": task_id,
            "type": task_type,
            "url": url,
            "screenshot": screenshot_base64,
            "data": additional_data or {},
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        self.queue.append(task)
        self._save_queue()
        
        logger.info(f"[HumanQueue] Added {task_type} task: {task_id}")
        return task_id
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks."""
        return [t for t in self.queue if t["status"] == "pending"]
    
    def complete_task(self, task_id: str, result: Dict) -> bool:
        """
        Complete a human task.
        
        Args:
            task_id: The task to complete
            result: The solution (cookies, token, etc.)
        """
        for task in self.queue:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                task["result"] = result
                
                self.completed[task_id] = task
                self.queue.remove(task)
                self._save_queue()
                
                logger.info(f"[HumanQueue] Completed task: {task_id}")
                return True
        
        return False
    
    async def wait_for_completion(self, task_id: str, timeout: int = 3600) -> Optional[Dict]:
        """
        Wait for a human to complete a task.
        
        Args:
            task_id: Task to wait for
            timeout: Max wait time in seconds
            
        Returns:
            Task result or None on timeout
        """
        start = time.time()
        
        while time.time() - start < timeout:
            if task_id in self.completed:
                return self.completed[task_id].get("result")
            
            # Reload queue in case external update
            self._load_queue()
            
            await asyncio.sleep(5)
        
        logger.warning(f"[HumanQueue] Task {task_id} timed out")
        return None
    
    def cleanup_expired(self):
        """Remove expired tasks."""
        now = datetime.now()
        self.queue = [
            t for t in self.queue 
            if datetime.fromisoformat(t["expires_at"]) > now
        ]
        self._save_queue()


class VisualExtractor:
    """
    Extract data from screenshots using OCR.
    For when DOM is obfuscated or data is rendered as images.
    """
    
    def __init__(self):
        self.ocr_available = False
        try:
            import pytesseract
            self.ocr = pytesseract
            self.ocr_available = True
            logger.info("[Visual] OCR available")
        except ImportError:
            logger.warning("[Visual] pytesseract not available - OCR disabled")
    
    async def extract_from_screenshot(self, page, 
                                      regions: List[Dict] = None) -> Dict:
        """
        Extract text from page screenshot.
        
        Args:
            page: Playwright page
            regions: Optional list of regions to extract
                     [{"x": 0, "y": 0, "width": 100, "height": 50}]
        """
        if not self.ocr_available:
            return {"error": "OCR not available", "text": ""}
        
        try:
            from PIL import Image
            import io
            
            # Take screenshot
            screenshot = await page.screenshot(type="png")
            img = Image.open(io.BytesIO(screenshot))
            
            results = {
                "full_text": "",
                "regions": []
            }
            
            if regions:
                # Extract from specific regions
                for region in regions:
                    cropped = img.crop((
                        region["x"],
                        region["y"],
                        region["x"] + region["width"],
                        region["y"] + region["height"]
                    ))
                    text = self.ocr.image_to_string(cropped)
                    results["regions"].append({
                        "region": region,
                        "text": text.strip()
                    })
            else:
                # Extract from full page
                results["full_text"] = self.ocr.image_to_string(img)
            
            return results
            
        except Exception as e:
            logger.error(f"[Visual] Extraction error: {e}")
            return {"error": str(e)}
    
    async def find_text_location(self, page, target_text: str) -> Optional[Dict]:
        """
        Find the location of specific text in screenshot.
        Useful for clicking on text that's not in DOM.
        """
        if not self.ocr_available:
            return None
        
        try:
            from PIL import Image
            import io
            
            screenshot = await page.screenshot(type="png")
            img = Image.open(io.BytesIO(screenshot))
            
            # Get OCR data with boxes
            data = self.ocr.image_to_data(img, output_type=self.ocr.Output.DICT)
            
            for i, text in enumerate(data["text"]):
                if target_text.lower() in text.lower():
                    return {
                        "x": data["left"][i] + data["width"][i] // 2,
                        "y": data["top"][i] + data["height"][i] // 2,
                        "width": data["width"][i],
                        "height": data["height"][i],
                        "confidence": data["conf"][i]
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"[Visual] Find text error: {e}")
            return None


# Singleton instances
captcha_solver = CaptchaSolver()
cloudflare_bypass = CloudflareBypass()
proxy_intelligence = ProxyIntelligence()
human_queue = HumanInTheLoop()
visual_extractor = VisualExtractor()
