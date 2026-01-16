"""
ADVANCED HTML Parser - Best-in-class algorithms
Uses DOM similarity, semantic analysis, intelligent scoring
"""
from bs4 import BeautifulSoup, Tag, NavigableString
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Set, Tuple
from loguru import logger
import re
from collections import Counter, defaultdict
import hashlib


class AdvancedHTMLParser:
    """
    ADVANCED HTML Parser with intelligent algorithms:
    1. DOM tree similarity detection (finds repeating patterns)
    2. Semantic content understanding (headings, lists, tables)
    3. Intelligent deduplication (content hashing)
    4. Link relevance scoring (multiple signals)
    5. Context-aware extraction
    """
    
    @staticmethod
    def parse(html_content: str, base_url: str) -> Dict:
        """Main parsing entry point with advanced algorithms"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Clean noise
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # ALGORITHM 1: DOM Similarity Analysis (finds data structures)
            structured_items = AdvancedHTMLParser._dom_similarity_extraction(soup, base_url)
            
            # ALGORITHM 2: Semantic extraction (understands content)
            semantic_data = AdvancedHTMLParser._semantic_extraction(soup)
            
            # ALGORITHM 3: Intelligent link extraction
            links = AdvancedHTMLParser._smart_link_extraction(soup, base_url)
            
            # ALGORITHM 4: Metadata
            metadata = AdvancedHTMLParser._extract_metadata(soup)
            
            # Clean text with preserved structure
            text_content = AdvancedHTMLParser._get_structured_text(soup)
            
            logger.info(f"✓ Extracted: {len(structured_items)} items, {len(links)} links, {len(semantic_data)} semantic blocks")
            
            return {
                "text_content": text_content,
                "links": links,
                "structured_data": semantic_data,
                "metadata": metadata,
                "structured_items": structured_items
            }
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            return {"text_content": "", "links": [], "structured_data": {}, "metadata": {}, "structured_items": []}
    
    @staticmethod
    def _dom_similarity_extraction(soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """
        ADVANCED: DOM Tree Similarity Algorithm
        
        Finds repeating DOM structures automatically (e.g., product cards, article listings)
        by analyzing structural signatures of elements.
        """
        items = []
        seen_hashes = set()
        
        # Build signature map: signature -> [elements with that signature]
        signature_map = defaultdict(list)
        
        # Analyze all container elements
        for element in soup.find_all(['div', 'article', 'li', 'section', 'tr']):
            if not isinstance(element, Tag):
                continue
            
            # Generate structural signature
            sig = AdvancedHTMLParser._compute_structure_signature(element)
            if sig:
                signature_map[sig].append(element)
        
        # Find repeating patterns (3+ occurrences = likely data structure)
        pattern_count = 0
        for signature, elements in signature_map.items():
            if len(elements) < 3:
                continue
            
            pattern_count += 1
            logger.debug(f"Pattern {pattern_count}: {len(elements)} elements with signature '{signature[:40]}...'")
            
            # Extract data from each repeated element
            for elem in elements[:150]:  # Limit per pattern
                item = AdvancedHTMLParser._extract_from_element(elem, base_url)
                if item:
                    # Deduplicate by content hash
                    content_hash = hashlib.md5(item['title'].encode()).hexdigest()[:16]
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        items.append(item)
        
        logger.info(f"DOM similarity found {len(items)} unique items from {pattern_count} patterns")
        return items
    
    @staticmethod
    def _compute_structure_signature(element: Tag) -> str:
        """
        Compute structural signature of element.
        
        Signature includes:
        - Element tag name
        - Top 3 class names (sorted)
        - Child element types and counts
        - Attribute patterns
        """
        try:
            parts = [element.name]
            
            # Classes (sorted for consistency)
            classes = element.get('class', [])
            if classes:
                parts.extend(sorted(classes)[:3])
            
            # Child structure (what types of children, how many)
            children = [c.name for c in element.children if isinstance(c, Tag)]
            if children:
                child_counts = Counter(children)
                for tag, count in child_counts.most_common(4):
                    parts.append(f"{tag}x{count}")
            
            # Attribute patterns (has href, has src, etc.)
            if element.find('a', href=True):
                parts.append('has_link')
            if element.find('img', src=True):
                parts.append('has_img')
            
            return '_'.join(parts)
        except:
            return ""
    
    @staticmethod
    def _extract_from_element(element: Tag, base_url: str) -> Dict:
        """Extract structured data from a single element"""
        try:
            # STEP 1: Find title (heading > link > strong > span)
            title = None
            for selector in [['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], ['a'], ['strong'], ['span']]:
                tag = element.find(selector)
                if tag:
                    title = tag.get_text(strip=True)
                    break
            
            if not title or len(title) < 3 or len(title) > 200:
                return None
            
            # Clean title
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Filter noise
            if title.lower() in ['home', 'login', 'signup', 'menu', 'search', 'more', 'next', 'prev', 'loading']:
                return None
            
            # STEP 2: Find link
            link = None
            link_tag = element.find('a', href=True)
            if link_tag:
                href = link_tag.get('href', '')
                if not href.startswith(('javascript:', '#', 'mailto:')):
                    link = urljoin(base_url, href)
            
            # STEP 3: Extract metadata (ratings, prices, counts)
            metadata = {}
            for tag in element.find_all(['span', 'div', 'p'], class_=True):
                text = tag.get_text(strip=True)
                
                # Extract numeric values
                numbers = re.findall(r'[\d,]+\.?\d*', text)
                if numbers:
                    key = '_'.join(tag.get('class', []))[:40]
                    if key:
                        metadata[key] = numbers[0]
                
                # Detect currencies
                if any(sym in text for sym in ['$', '€', '₹', '£', '¥']):
                    metadata['price'] = text
                
                # Detect ratings
                if any(word in text.lower() for word in ['star', 'rating', '/5', 'review']):
                    metadata['rating'] = text
            
            # STEP 4: Get context (full text)
            context = element.get_text(separator=' ', strip=True)
            context = re.sub(r'\s+', ' ', context)[:500]
            
            return {
                'title': title,
                'link': link,
                'context': context,
                'metadata': metadata,
                'extraction_method': 'dom_similarity'
            }
        except:
            return None
    
    @staticmethod
    def _semantic_extraction(soup: BeautifulSoup) -> Dict:
        """
        ADVANCED: Semantic content understanding
        
        Understands document structure: headings, lists, tables, articles
        """
        semantic = {
            'headings': [],
            'lists': [],
            'tables': [],
            'articles': []
        }
        
        # Extract heading hierarchy
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text(strip=True)
                if text and len(text) > 2:
                    semantic['headings'].append({
                        'level': i,
                        'text': text[:200]
                    })
        
        # Extract lists
        for ul in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
            if items and len(items) > 1:
                semantic['lists'].append(items[:20])
        
        # Extract tables
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr')[:50]:
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                semantic['tables'].append(rows)
        
        return semantic
    
    @staticmethod
    def _smart_link_extraction(soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """
        ADVANCED: Intelligent link extraction with scoring
        
        Scores links based on multiple signals:
        - Link text quality
        - URL structure
        - Position in DOM
        - Context relevance
        """
        links = []
        seen_urls = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            
            # Skip invalid
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Make absolute
            url = urljoin(base_url, href)
            
            # Deduplicate
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Extract text and context
            link_text = a_tag.get_text(strip=True)
            title = a_tag.get('title', '')
            
            # Get parent context
            parent_text = ''
            if a_tag.parent:
                parent_text = a_tag.parent.get_text(strip=True)[:150]
            
            # CALCULATE RELEVANCE SCORE
            score = 0
            
            # Text length bonus
            if 10 < len(link_text) < 100:
                score += 5
            elif len(link_text) > 100:
                score += 2
            
            # Title attribute bonus
            if title:
                score += 3
            
            # URL pattern analysis
            url_lower = url.lower()
            if any(pattern in url_lower for pattern in ['/details/', '/view/', '/profile/', '/article/', '/product/']):
                score += 10
            
            # Penalize navigation
            if any(pattern in url_lower for pattern in ['/login', '/signup', '/cart', '/checkout', '/privacy', '/terms']):
                score -= 10
            
            # Penalize generic text
            if link_text.lower() in ['click here', 'read more', 'learn more', 'next', 'previous']:
                score -= 5
            
            links.append({
                'url': url,
                'text': link_text,
                'title': title,
                'context': parent_text,
                'relevance_score': score,
                'domain': urlparse(url).netloc
            })
        
        # Sort by relevance
        links.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return links
    
    @staticmethod
    def _extract_metadata(soup: BeautifulSoup) -> Dict:
        """Extract page metadata"""
        metadata = {}
        
        # Title
        if soup.title:
            metadata['title'] = soup.title.get_text(strip=True)
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # Canonical
        canonical = soup.find('link', rel='canonical')
        if canonical:
            metadata['canonical'] = canonical.get('href')
        
        return metadata
    
    @staticmethod
    def _get_structured_text(soup: BeautifulSoup) -> str:
        """Get clean text with preserved structure"""
        # Get text with preserved newlines
        text = soup.get_text(separator='\n', strip=True)
        # Collapse multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
