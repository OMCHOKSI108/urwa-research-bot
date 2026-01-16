"""
Advanced HTML Parser with link extraction and structured data parsing
"""
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin, urlparse
from typing import Dict, List
from collections import Counter, defaultdict
from loguru import logger
import re

class EnhancedHTMLParser:
    """Parse HTML and extract structured data including links"""
    
    @staticmethod
    def parse(html_content: str, base_url: str) -> Dict:
        """
        Parse HTML and extract comprehensive structured data
        
        Returns:
            {
                "text_content": "clean text",
                "links": [...],
                "structured_data": {...},
                "metadata": {...}
            }
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Extract links
            links = EnhancedHTMLParser._extract_links(soup, base_url)
            
            # Extract structured data
            structured_data = EnhancedHTMLParser._extract_structured_data(soup)
            
            # Extract metadata
            metadata = EnhancedHTMLParser._extract_metadata(soup)
            
            # Get clean text
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Extract ALL structured items (UNIVERSAL - not company-specific)
            structured_items = EnhancedHTMLParser._extract_structured_items(soup, base_url)
            
            return {
                "text_content": text_content,
                "links": links,
                "structured_data": structured_data,
                "metadata": metadata,
                "structured_items": structured_items  # GENERIC items extraction
            }
            
        except Exception as e:
            logger.error(f"HTML parsing error: {e}")
            return {
                "text_content": "",
                "links": [],
                "structured_data": {},
                "metadata": {}
            }
    
    @staticmethod
    def _extract_links(soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract all links with context and relevance scoring"""
        links = []
        seen_urls = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Skip duplicates, anchors, and non-http links
            if absolute_url in seen_urls or absolute_url.startswith(('#', 'javascript:', 'mailto:')):
                continue
            
            # Skip common non-content links
            if any(skip in absolute_url.lower() for skip in ['login', 'signin', 'register', 'cart', 'checkout']):
                continue
            
            seen_urls.add(absolute_url)
            
            # Get link text and surrounding context
            link_text = a_tag.get_text(strip=True)
            
            # Get parent context for relevance
            parent_text = ""
            if a_tag.parent:
                parent_text = a_tag.parent.get_text(strip=True)[:200]
            
            # Calculate relevance score
            relevance = "low"
            if link_text and len(link_text) > 10:
                relevance = "medium"
            if a_tag.get('title') or (link_text and len(link_text) > 20):
                relevance = "high"
            
            links.append({
                "url": absolute_url,
                "text": link_text[:200] if link_text else "No text",
                "title": a_tag.get('title', ''),
                "context": parent_text,
                "domain": urlparse(absolute_url).netloc,
                "relevance": relevance
            })
        
        return links
    
    @staticmethod
    def _extract_structured_data(soup: BeautifulSoup) -> Dict:
        """Extract structured data from common HTML patterns"""
        structured = {
            "headings": [],
            "lists": [],
            "tables": [],
            "articles": []
        }
        
        # Extract headings hierarchy
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                structured["headings"].append({
                    "level": level,
                    "text": heading.get_text(strip=True)
                })
        
        # Extract lists
        for ul in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
            if items:
                structured["lists"].append({
                    "type": ul.name,
                    "items": items[:20]  # Limit to 20 items
                })
        
        # Extract tables
        for table in soup.find_all('table'):
            table_data = EnhancedHTMLParser._parse_table(table)
            if table_data:
                structured["tables"].append(table_data)
        
        # Extract article-like content
        for article in soup.find_all(['article', 'main', 'div'], class_=re.compile(r'(article|post|content|entry)', re.I)):
            text = article.get_text(strip=True)
            if len(text) > 200:  # Substantial content
                structured["articles"].append({
                    "text": text[:1000],  # First 1000 chars
                    "tag": article.name,
                    "class": ' '.join(article.get('class', []))
                })
        
        return structured
    
    @staticmethod
    def _parse_table(table) -> Dict:
        """Parse HTML table into structured format"""
        try:
            rows = []
            headers = []
            
            # Try to find headers
            thead = table.find('thead')
            if thead:
                header_cells = thead.find_all(['th', 'td'])
                headers = [cell.get_text(strip=True) for cell in header_cells]
            
            # Get data rows
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr')[:50]:  # Limit to 50 rows
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    rows.append(row_data)
            
            if not headers and rows:
                # First row might be headers
                headers = rows[0]
                rows = rows[1:]
            
            return {
                "headers": headers,
                "rows": rows,
                "row_count": len(rows)
            }
        except Exception as e:
            logger.error(f"Table parsing error: {e}")
            return {}
    
    @staticmethod
    def _extract_metadata(soup: BeautifulSoup) -> Dict:
        """Extract page metadata"""
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            metadata['canonical_url'] = canonical.get('href')
        
        return metadata
    
    @staticmethod
    def _extract_by_dom_similarity(soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """
        ADVANCED ALGORITHM: DOM Tree Similarity Detection
        
        Strategy:
        1. Build structural signatures for all elements
        2. Find elements with identical/similar signatures (repeating patterns)
        3. Extract data from these repeated structures
        
        This finds data cards, product listings, article grids, etc. AUTOMATICALLY
        """
        items = []
        seen_content = set()
        
        # STEP 1: Build DOM signatures (tag + class structure)
        signature_map = defaultdict(list)
        
        for element in soup.find_all(True):  # All tags
            if not isinstance(element, Tag):
                continue
            
            # Skip inline/text elements
            if element.name in ['span', 'a', 'i', 'b', 'strong', 'em', 'small']:
                continue
            
            # Build structural signature
            signature = EnhancedHTMLParser._get_dom_signature(element)
            if signature:
                signature_map[signature].append(element)
        
        # STEP 2: Find repeating patterns (appearing 3+ times = data structure)
        logger.info(f"Found {len(signature_map)} unique DOM patterns")
        
        for signature, elements in signature_map.items():
            if len(elements) < 3:  # Must repeat at least 3 times
                continue
            
            logger.info(f"Pattern '{signature[:50]}...' appears {len(elements)} times")
            
            # STEP 3: Extract data from each instance
            for element in elements[:200]:  # Limit per pattern
                item = EnhancedHTMLParser._extract_item_from_element(element, base_url)
                
                if item and item['title']:
                    # Intelligent deduplication using content hash
                    content_hash = hash(item['title'][:100])
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        items.append(item)
        
        logger.info(f"Extracted {len(items)} unique items using DOM similarity")
        return items
    
    @staticmethod
    def _get_dom_signature(element: Tag) -> str:
        """
        Create structural signature for DOM element.
        Elements with same signature likely contain similar data.
        
        Signature format: tag.class1.class2>child_tag>child_tag
        """
        try:
            # Element's own structure
            classes = element.get('class', [])
            sig_parts = [element.name]
            
            # Add class names (sorted for consistency)
            if classes:
                sig_parts.extend(sorted(classes)[:3])  # Max 3 classes
            
            # Add child structure (2 levels deep)
            children = [child.name for child in element.children if isinstance(child, Tag)]
            if children:
                child_counts = Counter(children)
                # Add most common children
                for child_tag, count in child_counts.most_common(3):
                    sig_parts.append(f">{child_tag}")
            
            return '.'.join(sig_parts)
        except:
            return ""
    
    @staticmethod
    def _extract_item_from_element(element: Tag, base_url: str) -> Dict:
        """
        Extract structured data from a single DOM element.
        Uses heuristics to find title, link, metadata.
        """
        try:
            # Find title (prioritize headings, then links, then spans)
            title = None
            title_tag = None
            
            for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                title_tag = element.find(tag_name)
                if title_tag:
                    break
            
            if not title_tag:
                # Try finding prominent link or span
                title_tag = element.find('a', href=True) or element.find('strong') or element.find('span')
            
            if title_tag:
                title = title_tag.get_text(strip=True)
                title = re.sub(r'\s+', ' ', title)
            
            if not title or len(title) < 3:
                return None
            
            # Skip navigation items
            if title.lower() in ['home', 'login', 'signup', 'menu', 'search', 'next', 'previous', 'close']:
                return None
            
            # Find associated link
            link = None
            link_tag = element.find('a', href=True)
            if link_tag:
                link = urljoin(base_url, link_tag['href'])
            
            # Extract all text for context
            context = element.get_text(separator=' ', strip=True)
            context = re.sub(r'\s+', ' ', context)[:500]
            
            # Extract metadata (numbers, ratings, etc.)
            metadata = {}
            for tag in element.find_all(['span', 'div', 'p']):
                text = tag.get_text(strip=True)
                # Find numbers
                numbers = re.findall(r'[\d,]+\.?\d*', text)
                if numbers:
                    class_name = ' '.join(tag.get('class', []))[:30]
                    if class_name:
                        metadata[class_name] = numbers[0]
            
            return {
                'title': title,
                'link': link,
                'context': context,
                'metadata': metadata,
                'source': 'dom_similarity'
            }
        except:
            return None
    
    @staticmethod
    def _extract_structured_items(soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """
        UNIVERSAL extraction of structured items from HTML.
        Works for ANY type of data (companies, products, articles, jobs, etc.)
        
        Detects repeating patterns automatically.
        """
        items = []
        seen_texts = set()
        
        # Use DOM similarity algorithm for intelligent extraction
        try:
            dom_items = EnhancedHTMLParser._extract_by_dom_similarity(soup, base_url)
            items.extend(dom_items)
            for item in dom_items:
                if item.get('title'):
                    seen_texts.add(item['title'][:100])
        except Exception as e:
            logger.warning(f"DOM similarity extraction failed: {e}")
        
        # Pattern 1: Find repeating container patterns
        for tag_name in ['div', 'article', 'li', 'section']:
            containers = soup.find_all(tag_name, class_=True)
            
            for container in containers:
                try:
                    # Find title (any heading or prominent text)
                    title_tag = None
                    for h_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        title_tag = container.find(h_tag)
                        if title_tag:
                            break
                    
                    if not title_tag:
                        title_tag = container.find('a', href=True) or container.find('strong')
                    
                    if not title_tag:
                        continue
                    
                    title_text = title_tag.get_text(strip=True)
                    title_text = re.sub(r'\s+', ' ', title_text)
                    
                    # Skip duplicates and navigation items
                    if title_text in seen_texts or len(title_text) < 3:
                        continue
                    if title_text.lower() in ['home', 'login', 'signup', 'menu', 'search']:
                        continue
                    
                    seen_texts.add(title_text)
                    
                    # Extract associated link
                    link_tag = container.find('a', href=True)
                    link_url = urljoin(base_url, link_tag['href']) if link_tag else None
                    
                    # Extract ALL metadata (ratings, prices, dates, descriptions, etc)
                    metadata = {}
                    
                    # Look for numeric values (ratings, prices, counts, etc)
                    for span in container.find_all(['span', 'div', 'p'], class_=True):
                        text = span.get_text(strip=True)
                        # Extract numbers (ratings, prices, etc)
                        numeric_match = re.search(r'([\d,]+\.?\d*)', text)
                        if numeric_match:
                            class_name = ' '.join(span.get('class', []))
                            metadata[f'numeric_{class_name[:30]}'] = numeric_match.group(1)
                    
                    # Extract full text content for context
                    full_text = container.get_text(separator=' ', strip=True)[:500]
                    
                    items.append({
                        'title': title_text,
                        'link': link_url,
                        'metadata': metadata,
                        'context': full_text,
                        'container_type': tag_name
                    })
                    
                except Exception as e:
                    logger.debug(f"Error extracting item: {e}")
                    continue
        
        # Pattern 2: Extract from tables (universal format)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                if cells and len(cells) >= 1:
                    first_cell_text = cells[0].get_text(strip=True)
                    
                    if first_cell_text and len(first_cell_text) > 2 and first_cell_text not in seen_texts:
                        seen_texts.add(first_cell_text)
                        
                        # Get link if exists
                        link = None
                        link_tag = cells[0].find('a', href=True)
                        if link_tag:
                            link = urljoin(base_url, link_tag['href'])
                        
                        # Extract all cell data
                        cell_data = [cell.get_text(strip=True) for cell in cells]
                        
                        items.append({
                            'title': first_cell_text,
                            'link': link,
                            'metadata': {'table_data': cell_data},
                            'context': ' | '.join(cell_data),
                            'container_type': 'table_row'
                        })
        
        logger.info(f"Extracted {len(items)} structured items (universal)")
        return items
