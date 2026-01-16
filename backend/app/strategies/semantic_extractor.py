"""
Strategy 6 & 7: Semantic Fallback Extraction + DOM Resilience
Multi-selector extraction with fallbacks for unknown site types.
"""

import re
from typing import Dict, List, Any, Optional
from loguru import logger


class SemanticExtractor:
    """
    Semantic fallback extractor that works on ANY website.
    
    Uses multiple strategies:
    - Multi-selector fallback (tries multiple selectors)
    - Text pattern detection
    - Generic list/table/card detection
    - Article body extraction
    """
    
    # Multi-selector fallbacks for common elements
    MULTI_SELECTORS = {
        "title": [
            "h1.title", "h1.headline", "h1.page-title", 
            ".title h1", "#title", "[data-title]",
            "article h1", ".article-title", ".post-title",
            "h1"  # Last resort
        ],
        "price": [
            ".price", "#price", "[data-price]",
            ".product-price", ".sale-price", ".current-price",
            "[itemprop='price']", ".price-value", ".cost",
            ".amount", ".pricing"
        ],
        "description": [
            ".description", "#description", "[data-description]",
            ".product-description", ".item-description",
            "[itemprop='description']", ".summary", ".excerpt",
            ".content p:first-of-type"
        ],
        "rating": [
            ".rating", "#rating", "[data-rating]",
            ".stars", ".review-rating", ".score",
            "[itemprop='ratingValue']", ".star-rating"
        ],
        "author": [
            ".author", "#author", "[data-author]",
            ".byline", ".writer", ".author-name",
            "[itemprop='author']", ".posted-by"
        ],
        "date": [
            ".date", "#date", "[data-date]",
            ".published", ".timestamp", ".post-date",
            "[itemprop='datePublished']", "time", ".article-date"
        ],
        "image": [
            ".main-image img", "#product-image img",
            "[data-main-image]", ".hero-image img",
            "article img:first-of-type", ".featured-image img",
            "[itemprop='image']"
        ],
        "list_items": [
            "ul.list > li", "ol > li", ".items > .item",
            ".list-item", ".card", ".result",
            "table tbody tr", ".row", ".entry"
        ]
    }
    
    # Text patterns for extraction
    TEXT_PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}',
        "price_usd": r'\$[\d,]+\.?\d*',
        "price_inr": r'₹[\d,]+\.?\d*',
        "price_eur": r'€[\d,]+\.?\d*',
        "date_iso": r'\d{4}-\d{2}-\d{2}',
        "date_us": r'\d{1,2}/\d{1,2}/\d{2,4}',
        "percentage": r'\d+\.?\d*\s*%',
        "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
    }
    
    @classmethod
    def extract_with_fallback(cls, html: str, field: str) -> Optional[str]:
        """
        Extract a field using multiple selectors with fallback.
        
        Args:
            html: Raw HTML content
            field: Field name to extract (e.g., "price", "title")
            
        Returns:
            Extracted value or None
        """
        selectors = cls.MULTI_SELECTORS.get(field, [])
        
        for selector in selectors:
            # Convert CSS selector to regex pattern (simplified)
            pattern = cls._selector_to_regex(selector)
            if pattern:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    value = cls._clean_text(match.group(1) if match.groups() else match.group(0))
                    if value and len(value) > 1:
                        logger.debug(f"[Semantic] Found {field} using selector: {selector}")
                        return value
        
        return None
    
    @classmethod
    def extract_all_patterns(cls, text: str) -> Dict[str, List[str]]:
        """
        Extract all recognizable patterns from text.
        
        Returns:
            Dict of pattern type -> list of matches
        """
        results = {}
        
        for pattern_name, pattern in cls.TEXT_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                # Deduplicate and limit
                unique_matches = list(dict.fromkeys(matches))[:20]
                results[pattern_name] = unique_matches
        
        return results
    
    @classmethod
    def extract_lists(cls, html: str) -> List[Dict[str, Any]]:
        """
        Extract list-like structures from HTML.
        
        Detects:
        - Unordered/ordered lists
        - Table rows
        - Card layouts
        - Repeated patterns
        """
        lists = []
        
        # Extract <ul> and <ol> lists
        list_pattern = r'<[ou]l[^>]*>([\s\S]*?)</[ou]l>'
        for match in re.findall(list_pattern, html, re.IGNORECASE):
            items = re.findall(r'<li[^>]*>([\s\S]*?)</li>', match, re.IGNORECASE)
            if items and len(items) >= 3:  # Only meaningful lists
                cleaned_items = [cls._clean_text(item) for item in items]
                lists.append({
                    "type": "list",
                    "items": cleaned_items[:50],  # Limit items
                    "count": len(items)
                })
        
        # Extract tables
        table_pattern = r'<table[^>]*>([\s\S]*?)</table>'
        for match in re.findall(table_pattern, html, re.IGNORECASE):
            rows = []
            row_pattern = r'<tr[^>]*>([\s\S]*?)</tr>'
            for row in re.findall(row_pattern, match, re.IGNORECASE):
                cells = re.findall(r'<t[dh][^>]*>([\s\S]*?)</t[dh]>', row, re.IGNORECASE)
                if cells:
                    rows.append([cls._clean_text(cell) for cell in cells])
            
            if rows and len(rows) >= 2:
                lists.append({
                    "type": "table",
                    "headers": rows[0] if len(rows) > 1 else [],
                    "rows": rows[1:50],  # Limit rows
                    "count": len(rows)
                })
        
        return lists
    
    @classmethod
    def extract_article_body(cls, html: str) -> str:
        """
        Extract main article content, filtering out navigation/ads.
        """
        # Try common article containers
        article_patterns = [
            r'<article[^>]*>([\s\S]*?)</article>',
            r'<div[^>]*class="[^"]*(?:article|content|post|entry)[^"]*"[^>]*>([\s\S]*?)</div>',
            r'<div[^>]*id="(?:content|main|article)[^"]*"[^>]*>([\s\S]*?)</div>',
            r'<main[^>]*>([\s\S]*?)</main>',
        ]
        
        for pattern in article_patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1)
                # Extract paragraphs
                paragraphs = re.findall(r'<p[^>]*>([\s\S]*?)</p>', content, re.IGNORECASE)
                if paragraphs:
                    cleaned = [cls._clean_text(p) for p in paragraphs if len(cls._clean_text(p)) > 50]
                    if cleaned:
                        return '\n\n'.join(cleaned[:20])  # Limit paragraphs
        
        return ""
    
    @classmethod
    def extract_cards(cls, html: str) -> List[Dict[str, Any]]:
        """
        Extract card-like repeated structures.
        """
        cards = []
        
        # Common card patterns
        card_patterns = [
            r'<div[^>]*class="[^"]*(?:card|item|product|result|listing)[^"]*"[^>]*>([\s\S]*?)</div>',
            r'<li[^>]*class="[^"]*(?:item|result|product)[^"]*"[^>]*>([\s\S]*?)</li>',
            r'<article[^>]*class="[^"]*(?:item|result|product)[^"]*"[^>]*>([\s\S]*?)</article>',
        ]
        
        for pattern in card_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if len(matches) >= 3:  # At least 3 cards to be meaningful
                for match in matches[:30]:  # Limit cards
                    card = cls._parse_card(match)
                    if card:
                        cards.append(card)
                
                if cards:
                    break  # Use first successful pattern
        
        return cards
    
    @classmethod
    def _parse_card(cls, html: str) -> Optional[Dict]:
        """Parse a single card element."""
        card = {}
        
        # Try to extract common card fields
        title_match = re.search(r'<h[1-4][^>]*>([^<]+)</h[1-4]>', html, re.IGNORECASE)
        if title_match:
            card["title"] = cls._clean_text(title_match.group(1))
        
        link_match = re.search(r'<a[^>]*href="([^"]+)"', html, re.IGNORECASE)
        if link_match:
            card["link"] = link_match.group(1)
        
        price_match = re.search(r'[\$₹€£][\d,]+\.?\d*', html)
        if price_match:
            card["price"] = price_match.group(0)
        
        img_match = re.search(r'<img[^>]*src="([^"]+)"', html, re.IGNORECASE)
        if img_match:
            card["image"] = img_match.group(1)
        
        # Get clean text as description
        text = cls._clean_text(html)
        if len(text) > 20:
            card["text"] = text[:200]
        
        return card if card else None
    
    @classmethod
    def _selector_to_regex(cls, selector: str) -> Optional[str]:
        """Convert a simple CSS selector to regex pattern."""
        if selector.startswith("#"):
            # ID selector
            return rf'<[^>]*id="{selector[1:]}"[^>]*>([^<]*)'
        elif selector.startswith("."):
            # Class selector
            class_name = selector[1:].replace(".", r"[^\"]*")
            return rf'<[^>]*class="[^"]*{class_name}[^"]*"[^>]*>([^<]*)'
        elif selector.startswith("["):
            # Attribute selector
            match = re.match(r'\[([^=]+)(?:=["\']?([^"\'\]]+)["\']?)?\]', selector)
            if match:
                attr, val = match.groups()
                if val:
                    return rf'<[^>]*{attr}="{val}"[^>]*>([^<]*)'
                return rf'<[^>]*{attr}="([^"]*)"'
        else:
            # Tag selector
            tag = selector.split()[0] if " " in selector else selector
            return rf'<{tag}[^>]*>([^<]*)</{tag}>'
        
        return None
    
    @classmethod
    def _clean_text(cls, html: str) -> str:
        """Clean HTML tags and normalize whitespace."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Decode entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @classmethod
    def universal_extract(cls, html: str, url: str = "") -> Dict[str, Any]:
        """
        Universal extraction that works on any website.
        
        Returns structured data with whatever can be extracted.
        """
        result = {
            "url": url,
            "fields": {},
            "patterns": {},
            "lists": [],
            "cards": [],
            "article": "",
            "extraction_methods": []
        }
        
        # Try field extraction with fallbacks
        for field in ["title", "price", "description", "rating", "author", "date"]:
            value = cls.extract_with_fallback(html, field)
            if value:
                result["fields"][field] = value
                result["extraction_methods"].append(f"field:{field}")
        
        # Extract text patterns
        text = cls._clean_text(html)
        result["patterns"] = cls.extract_all_patterns(text)
        if result["patterns"]:
            result["extraction_methods"].append("patterns")
        
        # Extract lists and tables
        result["lists"] = cls.extract_lists(html)
        if result["lists"]:
            result["extraction_methods"].append("lists")
        
        # Extract cards
        result["cards"] = cls.extract_cards(html)
        if result["cards"]:
            result["extraction_methods"].append("cards")
        
        # Extract article body
        result["article"] = cls.extract_article_body(html)
        if result["article"]:
            result["extraction_methods"].append("article")
        
        logger.info(f"[Semantic] Extracted using: {result['extraction_methods']}")
        
        return result


# Convenience function
def semantic_extract(html: str, url: str = "") -> Dict[str, Any]:
    """Quick semantic extraction."""
    return SemanticExtractor.universal_extract(html, url)
