"""
BROWSER PROFILE MANAGEMENT
Maintains real browser sessions with authentic fingerprints and cookies.

This is the key to bypassing advanced protection - appearing as a real returning user.
"""

import asyncio
import random
import json
import os
import hashlib
import shutil
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger


class BrowserProfile:
    """
    A persistent browser profile with:
    - Real cookies
    - Browser storage
    - Consistent fingerprint
    - Session history
    """
    
    PROFILES_DIR = "app/static/browser_profiles"
    
    def __init__(self, profile_name: str = None):
        self.name = profile_name or self._generate_name()
        self.path = os.path.join(self.PROFILES_DIR, self.name)
        self.fingerprint = None
        self.created_at = None
        self.last_used = None
        self.sites_visited = []
        self.cookies = {}
        
        os.makedirs(self.PROFILES_DIR, exist_ok=True)
    
    def _generate_name(self) -> str:
        """Generate unique profile name."""
        return f"profile_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
    
    def create(self, fingerprint: Dict = None):
        """Create new browser profile."""
        os.makedirs(self.path, exist_ok=True)
        
        self.created_at = datetime.now().isoformat()
        self.fingerprint = fingerprint or self._generate_fingerprint()
        
        self._save_metadata()
        logger.info(f"[Profile] Created: {self.name}")
    
    def _generate_fingerprint(self) -> Dict:
        """Generate consistent fingerprint for this profile."""
        # Screen resolution
        screens = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (2560, 1440)]
        screen = random.choice(screens)
        
        # WebGL
        webgl_vendors = [
            ("Intel Inc.", "Intel Iris OpenGL Engine"),
            ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce GTX 1080)"),
            ("Google Inc. (Intel)", "ANGLE (Intel UHD Graphics 630)"),
        ]
        webgl = random.choice(webgl_vendors)
        
        return {
            "screen_width": screen[0],
            "screen_height": screen[1],
            "color_depth": 24,
            "pixel_ratio": random.choice([1, 1.25, 2]),
            "timezone": random.choice([
                "America/New_York", "America/Los_Angeles", "Europe/London",
                "Europe/Paris", "Asia/Tokyo"
            ]),
            "language": random.choice(["en-US", "en-GB", "en"]),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "hardware_concurrency": random.choice([4, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16]),
            "webgl_vendor": webgl[0],
            "webgl_renderer": webgl[1],
            "user_agent": self._generate_user_agent(),
            "canvas_hash": hashlib.md5(str(random.random()).encode()).hexdigest()[:16],
            "audio_hash": hashlib.md5(str(random.random()).encode()).hexdigest()[:12],
        }
    
    def _generate_user_agent(self) -> str:
        """Generate consistent user agent."""
        chrome_version = random.choice(["120", "121", "122", "123"])
        
        if random.random() > 0.5:
            # Windows
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
        else:
            # Mac
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
    
    def _save_metadata(self):
        """Save profile metadata."""
        metadata = {
            "name": self.name,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "fingerprint": self.fingerprint,
            "sites_visited": self.sites_visited[-100:],  # Keep last 100
        }
        
        with open(os.path.join(self.path, "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load(self) -> bool:
        """Load existing profile."""
        metadata_path = os.path.join(self.path, "metadata.json")
        
        if not os.path.exists(metadata_path):
            return False
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            
            self.created_at = data.get("created_at")
            self.last_used = data.get("last_used")
            self.fingerprint = data.get("fingerprint")
            self.sites_visited = data.get("sites_visited", [])
            
            return True
        except Exception as e:
            logger.error(f"[Profile] Load failed: {e}")
            return False
    
    async def save_browser_state(self, context):
        """Save browser context state (cookies, localStorage)."""
        try:
            # Save cookies
            cookies = await context.cookies()
            
            cookies_path = os.path.join(self.path, "cookies.json")
            with open(cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            # Save storage state
            state = await context.storage_state()
            state_path = os.path.join(self.path, "storage.json")
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.last_used = datetime.now().isoformat()
            self._save_metadata()
            
            logger.info(f"[Profile] Saved {len(cookies)} cookies for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"[Profile] Save state failed: {e}")
            return False
    
    async def load_browser_state(self, context) -> bool:
        """Load saved state into browser context."""
        try:
            # Load cookies
            cookies_path = os.path.join(self.path, "cookies.json")
            if os.path.exists(cookies_path):
                with open(cookies_path, 'r') as f:
                    cookies = json.load(f)
                
                if cookies:
                    await context.add_cookies(cookies)
                    logger.info(f"[Profile] Loaded {len(cookies)} cookies")
            
            return True
            
        except Exception as e:
            logger.error(f"[Profile] Load state failed: {e}")
            return False
    
    def record_visit(self, domain: str):
        """Record a visited site."""
        self.sites_visited.append({
            "domain": domain,
            "timestamp": datetime.now().isoformat()
        })
        self._save_metadata()
    
    def get_stealth_script(self) -> str:
        """Generate stealth JavaScript using this profile's fingerprint."""
        fp = self.fingerprint
        
        return f"""
        (() => {{
            // Webdriver
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined
            }});
            
            // Platform
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fp["platform"]}'
            }});
            
            // Languages
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['{fp["language"]}', 'en']
            }});
            
            // Hardware
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fp["hardware_concurrency"]}
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fp["device_memory"]}
            }});
            
            // Screen
            Object.defineProperty(screen, 'width', {{
                get: () => {fp["screen_width"]}
            }});
            
            Object.defineProperty(screen, 'height', {{
                get: () => {fp["screen_height"]}
            }});
            
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {fp["color_depth"]}
            }});
            
            // WebGL
            const getParameterProto = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(param) {{
                if (param === 37445) return '{fp["webgl_vendor"]}';
                if (param === 37446) return '{fp["webgl_renderer"]}';
                return getParameterProto.call(this, param);
            }};
            
            // Chrome object
            window.chrome = {{
                runtime: {{}},
                loadTimes: () => ({{}}),
                csi: () => ({{}})
            }};
            
            // Plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = [
                        {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' }},
                        {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' }},
                        {{ name: 'Native Client', filename: 'internal-nacl-plugin' }}
                    ];
                    plugins.refresh = () => {{}};
                    return plugins;
                }}
            }});
            
            console.log('[Profile] Fingerprint applied: {self.name}');
        }})();
        """
    
    def delete(self):
        """Delete this profile."""
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
            logger.info(f"[Profile] Deleted: {self.name}")


class ProfileManager:
    """
    Manages multiple browser profiles for different scraping needs.
    """
    
    PROFILES_DIR = "app/static/browser_profiles"
    
    def __init__(self):
        os.makedirs(self.PROFILES_DIR, exist_ok=True)
        self.profiles: Dict[str, BrowserProfile] = {}
        self._load_all_profiles()
    
    def _load_all_profiles(self):
        """Load all existing profiles."""
        if not os.path.exists(self.PROFILES_DIR):
            return
        
        for name in os.listdir(self.PROFILES_DIR):
            profile_path = os.path.join(self.PROFILES_DIR, name)
            if os.path.isdir(profile_path):
                profile = BrowserProfile(name)
                if profile.load():
                    self.profiles[name] = profile
        
        logger.info(f"[ProfileManager] Loaded {len(self.profiles)} profiles")
    
    def create_profile(self, name: str = None) -> BrowserProfile:
        """Create a new profile."""
        profile = BrowserProfile(name)
        profile.create()
        self.profiles[profile.name] = profile
        return profile
    
    def get_profile(self, name: str) -> Optional[BrowserProfile]:
        """Get profile by name."""
        return self.profiles.get(name)
    
    def get_random_profile(self) -> Optional[BrowserProfile]:
        """Get a random profile."""
        if not self.profiles:
            return self.create_profile()
        return random.choice(list(self.profiles.values()))
    
    def get_best_profile_for_domain(self, domain: str) -> Optional[BrowserProfile]:
        """
        Get the best profile for a specific domain.
        Prefers profiles that have successfully visited the domain before.
        """
        # Find profiles that have visited this domain
        domain_profiles = []
        
        for profile in self.profiles.values():
            for visit in profile.sites_visited:
                if domain in visit.get("domain", ""):
                    domain_profiles.append(profile)
                    break
        
        if domain_profiles:
            # Return most recently used
            return max(domain_profiles, key=lambda p: p.last_used or "")
        
        # No domain-specific profile, return random or create new
        return self.get_random_profile()
    
    def list_profiles(self) -> List[Dict]:
        """List all profiles with metadata."""
        return [
            {
                "name": p.name,
                "created_at": p.created_at,
                "last_used": p.last_used,
                "sites_count": len(p.sites_visited)
            }
            for p in self.profiles.values()
        ]
    
    def cleanup_old_profiles(self, max_age_days: int = 30):
        """Remove profiles older than max_age_days that haven't been used."""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        for name, profile in list(self.profiles.items()):
            if profile.last_used:
                last_used = datetime.fromisoformat(profile.last_used)
                if last_used < cutoff:
                    profile.delete()
                    del self.profiles[name]


# Singleton instance
profile_manager = ProfileManager()
