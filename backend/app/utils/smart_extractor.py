"""
Universal Smart Extraction Engine
Handles intelligent extraction from any website type with specialized patterns
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from loguru import logger


class SiteTypeDetector:
    """Detect the type of website based on URL and content patterns"""
    
    SITE_PATTERNS = {
        'ecommerce': {
            'domains': ['amazon', 'ebay', 'walmart', 'flipkart', 'alibaba', 'shopify', 'etsy', 'bestbuy', 'target', 'aliexpress'],
            'url_patterns': ['/product', '/item', '/dp/', '/p/', 'buy', 'shop', 'cart', '/pd/', 'goods'],
            'content_patterns': ['add to cart', 'buy now', 'price', 'in stock', 'out of stock', 'free shipping', 'reviews', 'ratings']
        },
        'news': {
            'domains': ['cnn', 'bbc', 'nytimes', 'reuters', 'theguardian', 'washingtonpost', 'news', 'times', 'post', 'herald', 'tribune'],
            'url_patterns': ['/news/', '/article/', '/story/', '/politics/', '/world/', '/business/', '/tech/'],
            'content_patterns': ['breaking news', 'published', 'updated', 'reporter', 'journalist', 'opinion', 'editorial']
        },
        'social': {
            'domains': ['twitter', 'facebook', 'linkedin', 'instagram', 'reddit', 'tiktok', 'youtube', 'pinterest', 'x.com'],
            'url_patterns': ['/post/', '/status/', '/user/', '/profile/', '/watch', '/reel/', '/video/'],
            'content_patterns': ['followers', 'following', 'likes', 'shares', 'comments', 'subscribe', 'retweet']
        },
        'jobs': {
            'domains': ['linkedin', 'indeed', 'glassdoor', 'monster', 'naukri', 'ziprecruiter', 'dice', 'careerbuilder', 'lever', 'greenhouse'],
            'url_patterns': ['/jobs/', '/job/', '/careers/', '/vacancy/', '/opening/', '/position/', '/apply/'],
            'content_patterns': ['apply now', 'job description', 'requirements', 'salary', 'experience', 'qualifications', 'full-time', 'part-time']
        },
        'education': {
            'domains': ['coursera', 'udemy', 'edx', 'khan', 'university', 'college', 'edu', 'school', 'academy', 'institute'],
            'url_patterns': ['/course/', '/program/', '/degree/', '/certificate/', '/class/', '/learn/', '/placement'],
            'content_patterns': ['enroll', 'curriculum', 'syllabus', 'instructor', 'certificate', 'credits', 'semester', 'placements']
        },
        'reviews': {
            'domains': ['yelp', 'tripadvisor', 'trustpilot', 'g2', 'capterra', 'producthunt', 'ambitionbox'],
            'url_patterns': ['/review/', '/reviews/', '/rating/', '/compare/', '/vs/'],
            'content_patterns': ['stars', 'rating', 'review', 'recommend', 'pros', 'cons', 'verified purchase']
        },
        'directory': {
            'domains': ['yellowpages', 'whitepages', 'zomato', 'justdial', 'craigslist', 'olx'],
            'url_patterns': ['/listing/', '/directory/', '/list/', '/business/', '/local/', '/companies/'],
            'content_patterns': ['address', 'phone', 'contact', 'hours', 'location', 'map', 'nearby']
        },
        'documentation': {
            'domains': ['docs', 'readme', 'gitbook', 'notion', 'confluence', 'wiki', 'github.io'],
            'url_patterns': ['/docs/', '/documentation/', '/api/', '/reference/', '/guide/', '/tutorial/'],
            'content_patterns': ['installation', 'getting started', 'api reference', 'example', 'usage', 'parameters']
        },
        'forum': {
            'domains': ['stackoverflow', 'stackexchange', 'quora', 'reddit', 'discourse', 'phpbb', 'vbulletin'],
            'url_patterns': ['/questions/', '/answer/', '/thread/', '/topic/', '/discussion/', '/forum/'],
            'content_patterns': ['answered', 'votes', 'accepted', 'asked', 'answer', 'reply', 'upvote', 'downvote']
        },
        'wiki': {
            'domains': ['wikipedia', 'wiktionary', 'wikibooks', 'wikinews', 'wikiquote', 'wikisource', 'wikiversity', 'wikivoyage', 'fandom', 'wikia'],
            'url_patterns': ['/wiki/', '/index.php?title='],
            'content_patterns': ['edit', 'history', 'talk', 'read', 'main page', 'contents', 'current events', 'random article']
        }
    }
    
    @classmethod
    def detect(cls, url: str, content: str = "") -> Tuple[str, float]:
        """
        Detect site type with confidence score
        Returns: (site_type, confidence)
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        content_lower = content.lower()[:5000]  # Check first 5000 chars
        
        scores = {}
        
        for site_type, patterns in cls.SITE_PATTERNS.items():
            score = 0
            
            # Domain matching (high weight)
            for d in patterns['domains']:
                if d in domain:
                    score += 40
                    break
            
            # URL pattern matching (medium weight)
            for p in patterns['url_patterns']:
                if p in path:
                    score += 20
                    break
            
            # Content pattern matching (low weight but cumulative)
            content_matches = sum(1 for p in patterns['content_patterns'] if p in content_lower)
            score += min(content_matches * 5, 30)  # Cap at 30
            
            scores[site_type] = score
        
        if not scores:
            return 'generic', 0.0
        
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type] / 100.0, 1.0)
        
        if confidence < 0.2:
            return 'generic', confidence
        
        return best_type, confidence


class UniversalExtractor:
    """Universal content extractor with site-specific patterns"""
    
    # E-commerce extraction patterns
    ECOMMERCE_PATTERNS = {
        'price': [
            r'\$[\d,]+\.?\d*',
            r'₹[\d,]+\.?\d*',
            r'€[\d,]+\.?\d*',
            r'£[\d,]+\.?\d*',
            r'Price:\s*[\$₹€£]?[\d,]+\.?\d*',
            r'MRP:\s*[\$₹€£]?[\d,]+\.?\d*',
            r'[\d,]+\.\d{2}\s*(?:USD|INR|EUR|GBP)',
        ],
        'rating': [
            r'(\d+\.?\d*)\s*(?:out of|/)\s*5',
            r'(\d+\.?\d*)\s*stars?',
            r'Rating:\s*(\d+\.?\d*)',
            r'★+\s*(\d+\.?\d*)',
        ],
        'reviews_count': [
            r'(\d+[,\d]*)\s*(?:reviews?|ratings?)',
            r'(\d+[,\d]*)\s*customer reviews?',
            r'Based on\s*(\d+[,\d]*)\s*reviews?',
        ],
        'product_name': [
            r'<h1[^>]*>(.+?)</h1>',
            r'data-product-name="([^"]+)"',
            r'"name":\s*"([^"]+)"',
            r'itemprop="name"[^>]*>([^<]+)',
        ],
        'availability': [
            r'(in stock|out of stock|available|unavailable|sold out)',
            r'(?:only\s+)?(\d+)\s*left\s*in\s*stock',
        ]
    }
    
    # Wiki extraction patterns
    WIKI_PATTERNS = {
        'headings': [
            r'<h1[^>]*id="firstHeading"[^>]*>(.+?)</h1>',
            r'<span class="mw-page-title-main">(.+?)</span>',
            r'<h1[^>]*>(.+?)</h1>',
        ],
        'categories': [
            r'<div id="mw-normal-catlinks"[^>]*>([\s\S]*?)</div>',
            r'Category:([^"<\n]+)',
        ],
        'infobox': [
            r'<table class="infobox[^"]*"[^>]*>([\s\S]*?)</table>',
        ]
    }

    # News extraction patterns
    NEWS_PATTERNS = {
        'headline': [
            r'<h1[^>]*class="[^"]*headline[^"]*"[^>]*>(.+?)</h1>',
            r'<h1[^>]*>(.+?)</h1>',
            r'"headline":\s*"([^"]+)"',
        ],
        'author': [
            r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'author["\s:]+([^"<\n]+)',
            r'data-author="([^"]+)"',
            r'"author"[^}]*"name":\s*"([^"]+)"',
        ],
        'published_date': [
            r'published[:\s]+(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}\s+\w+\s+\d{4})',
            r'"datePublished":\s*"([^"]+)"',
        ],
        'content': [
            r'<article[^>]*>([\s\S]*?)</article>',
            r'<div[^>]*class="[^"]*article-body[^"]*"[^>]*>([\s\S]*?)</div>',
        ]
    }
    
    # Jobs extraction patterns
    JOBS_PATTERNS = {
        'job_title': [
            r'<h1[^>]*class="[^"]*job-title[^"]*"[^>]*>(.+?)</h1>',
            r'"title":\s*"([^"]+)"',
            r'<h1[^>]*>(.+?)</h1>',
        ],
        'company': [
            r'company[:\s"]+([^"<\n]+)',
            r'data-company="([^"]+)"',
            r'"hiringOrganization"[^}]*"name":\s*"([^"]+)"',
        ],
        'location': [
            r'location[:\s"]+([^"<\n]+)',
            r'(?:remote|on-site|hybrid)',
            r'"jobLocation"[^}]*"name":\s*"([^"]+)"',
        ],
        'salary': [
            r'salary[:\s"]+([^"<\n]+)',
            r'\$[\d,]+\s*-\s*\$[\d,]+',
            r'₹[\d,]+\s*-\s*₹[\d,]+',
            r'(\d+[,\d]*)\s*(?:LPA|per year|annually)',
        ],
        'experience': [
            r'(\d+)\s*(?:-\s*\d+)?\s*years?\s*(?:of\s+)?experience',
            r'experience[:\s"]+(\d+)',
        ]
    }
    
    # Education/Placement patterns
    EDUCATION_PATTERNS = {
        'institution': [
            r'university|college|institute|school|academy',
            r'"name":\s*"([^"]*(?:university|college|institute)[^"]*)"',
        ],
        'program': [
            r'(?:B\.?Tech|M\.?Tech|MBA|BBA|B\.?Sc|M\.?Sc|Ph\.?D|Bachelor|Master)',
            r'course[:\s"]+([^"<\n]+)',
        ],
        'placement_stats': [
            r'highest\s*(?:package|salary)[:\s]*[\$₹€£]?([\d,]+(?:\.\d+)?)\s*(?:LPA|lakhs?|crores?)?',
            r'average\s*(?:package|salary)[:\s]*[\$₹€£]?([\d,]+(?:\.\d+)?)\s*(?:LPA|lakhs?|crores?)?',
            r'(\d+)\s*%?\s*(?:placement|placed)',
            r'(\d+)\s*companies\s*(?:visited|recruited)',
        ],
        'recruiters': [
            r'(?:top\s+)?recruiters?[:\s]+([^<\n]+)',
            r'companies?\s*(?:like|include|visiting)[:\s]+([^<\n]+)',
        ]
    }
    
    # Review patterns
    REVIEW_PATTERNS = {
        'overall_rating': [
            r'(\d+\.?\d*)\s*(?:out of|/)\s*5',
            r'overall\s*(?:rating)?[:\s]*(\d+\.?\d*)',
        ],
        'pros': [
            r'pros?[:\s]+([^<\n]+)',
            r'advantages?[:\s]+([^<\n]+)',
            r'good\s*(?:things?)?[:\s]+([^<\n]+)',
        ],
        'cons': [
            r'cons?[:\s]+([^<\n]+)',
            r'disadvantages?[:\s]+([^<\n]+)',
            r'bad\s*(?:things?)?[:\s]+([^<\n]+)',
        ],
        'reviewer': [
            r'reviewed?\s*by[:\s]+([^<\n]+)',
            r'(?:verified\s+)?(?:buyer|customer|user)[:\s]+([^<\n]+)',
        ]
    }
    
    @classmethod
    def extract(cls, content: str, url: str, site_type: str = None) -> Dict[str, Any]:
        """
        Extract structured data based on site type
        """
        if not site_type:
            site_type, confidence = SiteTypeDetector.detect(url, content)
        
        logger.info(f"[Extractor] Site type: {site_type} for {url[:50]}...")
        
        result = {
            'site_type': site_type,
            'url': url,
            'extracted_data': {},
            'raw_text': '',
            'links': [],
            'metadata': {}
        }
        
        # Extract based on site type
        if site_type == 'ecommerce':
            result['extracted_data'] = cls._extract_ecommerce(content)
        elif site_type == 'news':
            result['extracted_data'] = cls._extract_news(content)
        elif site_type == 'jobs':
            result['extracted_data'] = cls._extract_jobs(content)
        elif site_type == 'education':
            result['extracted_data'] = cls._extract_education(content)
        elif site_type == 'reviews':
            result['extracted_data'] = cls._extract_reviews(content)
        elif site_type == 'wiki':
            result['extracted_data'] = cls._extract_wiki(content)
        else:
            result['extracted_data'] = cls._extract_generic(content)
        
        # Always extract common elements
        result['raw_text'] = cls._clean_text(content)[:10000]
        result['links'] = cls._extract_links(content, url)
        result['metadata'] = cls._extract_metadata(content)
        
        return result
    
    @classmethod
    def _extract_patterns(cls, content: str, patterns: Dict[str, List[str]]) -> Dict[str, Any]:
        """Extract data using regex patterns"""
        results = {}
        for field, regexes in patterns.items():
            for regex in regexes:
                try:
                    matches = re.findall(regex, content, re.IGNORECASE)
                    if matches:
                        # Get unique matches
                        if isinstance(matches[0], tuple):
                            matches = [m[0] if m[0] else m[-1] for m in matches]
                        unique_matches = list(dict.fromkeys(matches))
                        results[field] = unique_matches[0] if len(unique_matches) == 1 else unique_matches
                        break
                except Exception:
                    continue
        return results
    
    @classmethod
    def _extract_ecommerce(cls, content: str) -> Dict[str, Any]:
        """Extract e-commerce specific data"""
        data = cls._extract_patterns(content, cls.ECOMMERCE_PATTERNS)
        
        # Try to find product details in JSON-LD
        json_ld = cls._extract_json_ld(content, 'Product')
        if json_ld:
            data.update({
                'product_name': json_ld.get('name', data.get('product_name')),
                'price': json_ld.get('offers', {}).get('price', data.get('price')),
                'currency': json_ld.get('offers', {}).get('priceCurrency', 'USD'),
                'brand': json_ld.get('brand', {}).get('name', ''),
                'description': json_ld.get('description', ''),
                'image': json_ld.get('image', ''),
                'sku': json_ld.get('sku', ''),
            })
        
        return data
    
    @classmethod
    def _extract_news(cls, content: str) -> Dict[str, Any]:
        """Extract news article data"""
        data = cls._extract_patterns(content, cls.NEWS_PATTERNS)
        
        # Try JSON-LD for NewsArticle
        json_ld = cls._extract_json_ld(content, 'NewsArticle')
        if not json_ld:
            json_ld = cls._extract_json_ld(content, 'Article')
        
        if json_ld:
            data.update({
                'headline': json_ld.get('headline', data.get('headline')),
                'author': json_ld.get('author', {}).get('name', data.get('author')),
                'published_date': json_ld.get('datePublished', data.get('published_date')),
                'publisher': json_ld.get('publisher', {}).get('name', ''),
                'description': json_ld.get('description', ''),
            })
        
        return data
    
    @classmethod
    def _extract_jobs(cls, content: str) -> Dict[str, Any]:
        """Extract job listing data"""
        data = cls._extract_patterns(content, cls.JOBS_PATTERNS)
        
        # Try JSON-LD for JobPosting
        json_ld = cls._extract_json_ld(content, 'JobPosting')
        if json_ld:
            data.update({
                'job_title': json_ld.get('title', data.get('job_title')),
                'company': json_ld.get('hiringOrganization', {}).get('name', data.get('company')),
                'location': json_ld.get('jobLocation', {}).get('address', {}).get('addressLocality', data.get('location')),
                'description': json_ld.get('description', ''),
                'employment_type': json_ld.get('employmentType', ''),
                'posted_date': json_ld.get('datePosted', ''),
            })
        
        return data
    
    @classmethod
    def _extract_education(cls, content: str) -> Dict[str, Any]:
        """Extract education/placement data"""
        data = cls._extract_patterns(content, cls.EDUCATION_PATTERNS)
        
        # Extract tables for placement data
        tables = cls._extract_tables(content)
        if tables:
            data['placement_tables'] = tables[:3]  # Keep first 3 tables
        
        return data
    
    @classmethod
    def _extract_reviews(cls, content: str) -> Dict[str, Any]:
        """Extract review data"""
        data = cls._extract_patterns(content, cls.REVIEW_PATTERNS)
        
        # Try JSON-LD for Review
        json_ld = cls._extract_json_ld(content, 'Review')
        if json_ld:
            data.update({
                'rating': json_ld.get('reviewRating', {}).get('ratingValue', data.get('overall_rating')),
                'reviewer': json_ld.get('author', {}).get('name', data.get('reviewer')),
                'review_text': json_ld.get('reviewBody', ''),
            })
        
        return data
    
    @classmethod
    def _extract_wiki(cls, content: str) -> Dict[str, Any]:
        """Extract wiki content"""
        data = cls._extract_patterns(content, cls.WIKI_PATTERNS)
        
        # Isolate main content if possible to avoid sidebar/nav links
        main_content_match = re.search(r'<div[^>]*id="mw-content-text"[^>]*>([\s\S]*?)<!--\s*NewPP', content, re.IGNORECASE)
        if not main_content_match:
             main_content_match = re.search(r'<main[^>]*>([\s\S]*?)</main>', content, re.IGNORECASE)
        
        main_text = ""
        if main_content_match:
            # Use only the main content for text extraction
            main_text_html = main_content_match.group(1)
            main_text = cls._clean_text(main_text_html)
            # Update content in data to be the focused main text
            data['main_content'] = main_text[:15000] # Capture a good chunk of actual text
        
        return data

    @classmethod
    def _extract_generic(cls, content: str) -> Dict[str, Any]:
        """Generic extraction for unknown site types"""
        # Combine all patterns for best effort
        all_data = {}
        
        for patterns in [cls.ECOMMERCE_PATTERNS, cls.NEWS_PATTERNS, cls.JOBS_PATTERNS]:
            extracted = cls._extract_patterns(content, patterns)
            for key, value in extracted.items():
                if key not in all_data and value:
                    all_data[key] = value
        
        return all_data
    
    @classmethod
    def _extract_json_ld(cls, content: str, schema_type: str) -> Optional[Dict]:
        """Extract JSON-LD structured data"""
        import json
        
        pattern = r'<script[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        for match in matches:
            try:
                data = json.loads(match)
                
                # Handle array of schemas
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == schema_type:
                            return item
                elif data.get('@type') == schema_type:
                    return data
                elif '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == schema_type:
                            return item
            except:
                continue
        
        return None
    
    @classmethod
    def _extract_tables(cls, content: str) -> List[Dict]:
        """Extract table data"""
        tables = []
        table_pattern = r'<table[^>]*>([\s\S]*?)</table>'
        
        for match in re.findall(table_pattern, content, re.IGNORECASE)[:5]:
            rows = []
            row_pattern = r'<tr[^>]*>([\s\S]*?)</tr>'
            
            for row in re.findall(row_pattern, match, re.IGNORECASE):
                cells = []
                cell_pattern = r'<t[dh][^>]*>([\s\S]*?)</t[dh]>'
                for cell in re.findall(cell_pattern, row, re.IGNORECASE):
                    clean_cell = re.sub(r'<[^>]+>', '', cell).strip()
                    if clean_cell:
                        cells.append(clean_cell)
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({'rows': rows, 'row_count': len(rows)})
        
        return tables
    
    @classmethod
    def _extract_links(cls, content: str, base_url: str) -> List[Dict]:
        """Extract all links with context"""
        from urllib.parse import urljoin
        
        links = []
        pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>'
        
        for match in re.findall(pattern, content, re.IGNORECASE)[:100]:
            href, text = match
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            full_url = urljoin(base_url, href)
            clean_text = text.strip()
            
            if clean_text and len(clean_text) > 2:
                links.append({
                    'url': full_url,
                    'text': clean_text[:100],
                    'domain': urlparse(full_url).netloc
                })
        
        return links
    
    @classmethod
    def _extract_metadata(cls, content: str) -> Dict[str, str]:
        """Extract page metadata"""
        metadata = {}
        
        # Title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Meta tags
        meta_patterns = {
            'description': r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
            'keywords': r'<meta[^>]*name="keywords"[^>]*content="([^"]+)"',
            'og_title': r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
            'og_description': r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"',
            'og_image': r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
        }
        
        for key, pattern in meta_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()
        
        return metadata
    
    @classmethod
    def _clean_text(cls, content: str) -> str:
        """Clean HTML to plain text"""
        # Remove script and style
        content = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<!--[\s\S]*?-->', '', content)
        
        # Remove tags
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Clean whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n', content)
        
        return content.strip()


# Convenience function for quick extraction
def smart_extract(url: str, content: str) -> Dict[str, Any]:
    """Quick extraction with auto-detected site type"""
    site_type, confidence = SiteTypeDetector.detect(url, content)
    result = UniversalExtractor.extract(content, url, site_type)
    result['detection_confidence'] = confidence
    return result
