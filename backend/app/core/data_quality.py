"""
DATA QUALITY INFRASTRUCTURE
Normalization + Versioned Extractors for production-grade outputs.
"""

import re
import hashlib
from typing import Dict, Optional, List, Any, Union
from datetime import datetime, date
from dataclasses import dataclass, field
from loguru import logger
import json


# ============================================================================
# DATA NORMALIZATION STRATEGY
# ============================================================================

class DataNormalizer:
    """
    Normalize extracted data to consistent formats.
    Production systems are judged by data quality, not scraping speed.
    """
    
    # Currency symbols to names
    CURRENCY_MAP = {
        "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR",
        "A$": "AUD", "C$": "CAD", "CHF": "CHF", "HK$": "HKD"
    }
    
    @classmethod
    def normalize_price(cls, price_str: str) -> Dict:
        """
        Normalize price strings to structured format.
        
        Input: "$1,234.56", "€ 99.99", "1,000 USD"
        Output: {"amount": 1234.56, "currency": "USD", "raw": "$1,234.56"}
        """
        if not price_str:
            return {"amount": None, "currency": None, "raw": None}
        
        raw = price_str.strip()
        
        # Detect currency
        currency = "USD"  # Default
        for symbol, code in cls.CURRENCY_MAP.items():
            if symbol in raw:
                currency = code
                break
        
        # Also check currency codes
        for code in ["USD", "EUR", "GBP", "JPY", "INR", "AUD", "CAD"]:
            if code in raw.upper():
                currency = code
                break
        
        # Extract numeric value
        numbers = re.findall(r'[\d,]+\.?\d*', raw)
        if numbers:
            # Take the largest number (likely the price, not quantity)
            num_str = max(numbers, key=len)
            amount = float(num_str.replace(',', ''))
        else:
            amount = None
        
        return {
            "amount": amount,
            "currency": currency,
            "raw": raw
        }
    
    @classmethod
    def normalize_date(cls, date_str: str) -> Dict:
        """
        Normalize date strings to ISO format.
        
        Input: "Jan 15, 2024", "15/01/2024", "2024-01-15"
        Output: {"iso": "2024-01-15", "timestamp": 1705276800, "raw": "Jan 15, 2024"}
        """
        if not date_str:
            return {"iso": None, "timestamp": None, "raw": None}
        
        raw = date_str.strip()
        
        # Common date patterns
        patterns = [
            # ISO format
            (r'(\d{4})-(\d{2})-(\d{2})', lambda m: f"{m[1]}-{m[2]}-{m[3]}"),
            # US format: MM/DD/YYYY
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: f"{m[3]}-{m[1].zfill(2)}-{m[2].zfill(2)}"),
            # EU format: DD/MM/YYYY  
            (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', lambda m: f"{m[3]}-{m[2].zfill(2)}-{m[1].zfill(2)}"),
            # Month name: Jan 15, 2024
            (r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', cls._parse_month_name),
            # Day Month Year: 15 Jan 2024
            (r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', lambda m: cls._parse_month_name((m[2], m[1], m[3]))),
        ]
        
        iso_date = None
        for pattern, converter in patterns:
            match = re.search(pattern, raw)
            if match:
                try:
                    iso_date = converter(match.groups() if hasattr(match, 'groups') else match)
                    break
                except:
                    continue
        
        # Calculate timestamp
        timestamp = None
        if iso_date:
            try:
                dt = datetime.strptime(iso_date, "%Y-%m-%d")
                timestamp = int(dt.timestamp())
            except:
                pass
        
        return {
            "iso": iso_date,
            "timestamp": timestamp,
            "raw": raw
        }
    
    @classmethod
    def _parse_month_name(cls, groups) -> str:
        """Parse date with month name."""
        months = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        month_str = groups[0].lower()[:3]
        day = groups[1].zfill(2)
        year = groups[2]
        
        month = months.get(month_str, '01')
        return f"{year}-{month}-{day}"
    
    @classmethod
    def normalize_location(cls, location_str: str) -> Dict:
        """
        Normalize location strings.
        
        Input: "New York, NY, USA", "London, UK", "Remote"
        Output: {"city": "New York", "state": "NY", "country": "USA", "remote": false}
        """
        if not location_str:
            return {"city": None, "state": None, "country": None, "remote": False, "raw": None}
        
        raw = location_str.strip()
        lower = raw.lower()
        
        # Check for remote
        remote = any(word in lower for word in ['remote', 'work from home', 'wfh', 'anywhere'])
        
        # Split by comma
        parts = [p.strip() for p in raw.split(',')]
        
        city = None
        state = None
        country = None
        
        if len(parts) >= 3:
            city, state, country = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            city, country = parts[0], parts[1]
            # Check if second part is US state
            if len(parts[1].strip()) == 2:
                state = parts[1].strip()
                country = "USA"
        elif len(parts) == 1 and not remote:
            city = parts[0]
        
        return {
            "city": city,
            "state": state,
            "country": country,
            "remote": remote,
            "raw": raw
        }
    
    @classmethod
    def normalize_company_name(cls, name: str) -> Dict:
        """
        Normalize company names.
        
        Input: "Google LLC", "APPLE INC.", "amazon.com"
        Output: {"name": "Google", "legal_suffix": "LLC", "raw": "Google LLC"}
        """
        if not name:
            return {"name": None, "legal_suffix": None, "raw": None}
        
        raw = name.strip()
        
        # Remove common suffixes
        suffixes = ['LLC', 'Inc.', 'Inc', 'Corp.', 'Corp', 'Ltd.', 'Ltd', 
                    'Limited', 'Co.', 'Co', 'Corporation', 'GmbH', 'S.A.', 'PLC']
        
        clean_name = raw
        legal_suffix = None
        
        for suffix in suffixes:
            pattern = rf'\s*,?\s*{re.escape(suffix)}\.?\s*$'
            if re.search(pattern, clean_name, re.IGNORECASE):
                legal_suffix = suffix.replace('.', '')
                clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE).strip()
                break
        
        # Remove .com, .org etc from name
        clean_name = re.sub(r'\.(com|org|net|io|co)$', '', clean_name, flags=re.IGNORECASE)
        
        # Title case
        clean_name = clean_name.title()
        
        return {
            "name": clean_name,
            "legal_suffix": legal_suffix,
            "raw": raw
        }
    
    @classmethod
    def normalize_phone(cls, phone_str: str) -> Dict:
        """Normalize phone numbers."""
        if not phone_str:
            return {"e164": None, "raw": None}
        
        raw = phone_str.strip()
        
        # Extract digits only
        digits = re.sub(r'\D', '', raw)
        
        # Detect country code
        if digits.startswith('1') and len(digits) == 11:
            e164 = f"+{digits}"
        elif len(digits) == 10:
            e164 = f"+1{digits}"  # Assume US
        else:
            e164 = f"+{digits}"
        
        return {
            "e164": e164 if len(digits) >= 10 else None,
            "raw": raw
        }
    
    @classmethod
    def normalize_rating(cls, rating_str: str) -> Dict:
        """
        Normalize rating strings.
        
        Input: "4.5 out of 5", "4.5/5", "4.5 stars"
        Output: {"value": 4.5, "max": 5, "percent": 90, "raw": "4.5 out of 5"}
        """
        if not rating_str:
            return {"value": None, "max": None, "percent": None, "raw": None}
        
        raw = rating_str.strip()
        
        # Extract numbers
        numbers = re.findall(r'[\d.]+', raw)
        
        if not numbers:
            return {"value": None, "max": None, "percent": None, "raw": raw}
        
        value = float(numbers[0])
        max_val = float(numbers[1]) if len(numbers) > 1 else 5.0  # Default max is 5
        
        # Normalize percentage ratings
        if max_val == 100:
            percent = value
            value = value / 20  # Convert to 5-star
            max_val = 5
        else:
            percent = (value / max_val) * 100
        
        return {
            "value": round(value, 1),
            "max": max_val,
            "percent": round(percent, 0),
            "raw": raw
        }


# ============================================================================
# VERSIONED EXTRACTORS STRATEGY
# ============================================================================

@dataclass
class ExtractorVersion:
    """Version info for an extractor."""
    version: str
    created_at: str
    changelog: str
    selectors: Dict[str, List[str]]
    hash: str = ""
    
    def __post_init__(self):
        # Generate hash from selectors
        selector_str = json.dumps(self.selectors, sort_keys=True)
        self.hash = hashlib.md5(selector_str.encode()).hexdigest()[:8]


class VersionedExtractor:
    """
    Extractor with version control.
    When sites change, you can rollback without breaking everything.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.versions: Dict[str, ExtractorVersion] = {}
        self.current_version: str = "1.0.0"
        self.active_version: Optional[ExtractorVersion] = None
    
    def add_version(self, version: str, selectors: Dict[str, List[str]], 
                   changelog: str = "") -> ExtractorVersion:
        """Add a new version of selectors."""
        v = ExtractorVersion(
            version=version,
            created_at=datetime.now().isoformat(),
            changelog=changelog,
            selectors=selectors
        )
        
        self.versions[version] = v
        self.current_version = version
        self.active_version = v
        
        logger.info(f"[Extractor] {self.name} v{version} registered (hash: {v.hash})")
        return v
    
    def rollback(self, version: str) -> bool:
        """Rollback to a previous version."""
        if version not in self.versions:
            logger.error(f"[Extractor] Version {version} not found")
            return False
        
        self.current_version = version
        self.active_version = self.versions[version]
        logger.info(f"[Extractor] {self.name} rolled back to v{version}")
        return True
    
    def get_selectors(self, field: str) -> List[str]:
        """Get selectors for a field from current version."""
        if not self.active_version:
            return []
        return self.active_version.selectors.get(field, [])
    
    def get_version_history(self) -> List[Dict]:
        """Get version history."""
        return [
            {
                "version": v.version,
                "created_at": v.created_at,
                "changelog": v.changelog,
                "hash": v.hash,
                "is_active": v.version == self.current_version
            }
            for v in self.versions.values()
        ]


class ExtractorRegistry:
    """
    Registry of all versioned extractors.
    """
    
    def __init__(self):
        self.extractors: Dict[str, VersionedExtractor] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default extractors."""
        
        # Amazon product extractor
        amazon = VersionedExtractor("amazon_product")
        amazon.add_version("1.0.0", {
            "title": ["#productTitle", "h1#title span"],
            "price": [".a-price-whole", "#priceblock_ourprice", "#priceblock_dealprice"],
            "rating": ["i.a-icon-star span", "#acrPopover span"],
            "reviews_count": ["#acrCustomerReviewText", "#averageCustomerReviews_feature_div"],
            "description": ["#productDescription p", "#feature-bullets li"],
            "image": ["#landingImage", "#imgBlkFront"]
        }, changelog="Initial Amazon product selectors")
        self.extractors["amazon_product"] = amazon
        
        # LinkedIn profile extractor
        linkedin = VersionedExtractor("linkedin_profile")
        linkedin.add_version("1.0.0", {
            "name": ["h1.text-heading-xlarge", ".pv-top-card--list li:first-child"],
            "headline": [".text-body-medium", ".pv-top-card--headline"],
            "location": [".text-body-small:last-child", ".pv-top-card--location"],
            "connections": [".pv-top-card--connections", "span.t-bold"],
            "about": ["#about ~ .display-flex p", ".pv-about-section p"]
        }, changelog="Initial LinkedIn profile selectors")
        self.extractors["linkedin_profile"] = linkedin
        
        # Job listing extractor
        job = VersionedExtractor("job_listing")
        job.add_version("1.0.0", {
            "title": [".jobTitle", "h1.job-title", "h2.title", "[data-testid='jobTitle']"],
            "company": [".companyName", ".company-name", "[data-testid='company-name']"],
            "location": [".companyLocation", ".location", "[data-testid='location']"],
            "salary": [".salary-snippet", ".salary", "[data-testid='salary']"],
            "description": [".job-description", "#jobDescriptionText", ".description"]
        }, changelog="Initial job listing selectors")
        self.extractors["job_listing"] = job
        
        # E-commerce product extractor
        ecommerce = VersionedExtractor("ecommerce_product")
        ecommerce.add_version("1.0.0", {
            "title": ["h1", ".product-title", "[data-testid='product-title']", ".pdp-title"],
            "price": [".price", "[data-testid='price']", ".product-price", ".current-price"],
            "original_price": [".was-price", ".original-price", "s", ".strike"],
            "rating": [".rating", ".stars", "[data-rating]", ".review-rating"],
            "image": [".product-image img", ".gallery img:first-child", "[data-testid='image']"],
            "availability": [".availability", ".stock-status", "[data-availability]"]
        }, changelog="Generic e-commerce product selectors")
        self.extractors["ecommerce_product"] = ecommerce
    
    def get_extractor(self, name: str) -> Optional[VersionedExtractor]:
        return self.extractors.get(name)
    
    def register_extractor(self, name: str, selectors: Dict[str, List[str]], 
                          changelog: str = "") -> VersionedExtractor:
        """Register a new extractor or update existing."""
        if name in self.extractors:
            extractor = self.extractors[name]
            # Auto-increment version
            parts = extractor.current_version.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = '.'.join(parts)
            extractor.add_version(new_version, selectors, changelog)
        else:
            extractor = VersionedExtractor(name)
            extractor.add_version("1.0.0", selectors, changelog)
            self.extractors[name] = extractor
        
        return extractor
    
    def list_extractors(self) -> List[Dict]:
        """List all extractors with current versions."""
        return [
            {
                "name": name,
                "current_version": e.current_version,
                "hash": e.active_version.hash if e.active_version else None,
                "fields": list(e.active_version.selectors.keys()) if e.active_version else []
            }
            for name, e in self.extractors.items()
        ]


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

data_normalizer = DataNormalizer()
extractor_registry = ExtractorRegistry()
