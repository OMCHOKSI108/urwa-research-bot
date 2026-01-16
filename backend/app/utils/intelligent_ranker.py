"""
Intelligent Result Ranker
Ranks and filters results by relevance to query
POWER: Returns best results first, not just random order
"""
from typing import List, Dict
from loguru import logger
import re
from collections import Counter


class IntelligentRanker:
    """
    Ranks scraped entities by relevance to query
    Uses multiple signals for smart ranking
    """
    
    @staticmethod
    def rank_entities(entities: List[Dict], query: str) -> List[Dict]:
        """
        SMART ranking using multi-signal scoring
        
        Signals:
        1. Query term overlap in title
        2. Query term frequency in context
        3. Entity completeness (has link, metadata)
        4. Title quality (length, capitalization)
        5. Context relevance
        """
        if not entities or not query:
            return entities
        
        # Extract query terms
        query_terms = set(re.findall(r'\w+', query.lower()))
        # Remove stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
            'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were'
        }
        query_terms = query_terms - stop_words
        
        scored_entities = []
        
        for entity in entities:
            score = 0
            signals = {}
            
            title = str(entity.get('title', '')).lower()
            context = str(entity.get('context', '')).lower()
            
            # SIGNAL 1: Query term overlap in title (most important)
            title_words = set(re.findall(r'\w+', title))
            title_overlap = len(query_terms & title_words)
            score += title_overlap * 20  # High weight
            signals['title_overlap'] = title_overlap
            
            # SIGNAL 2: Query term frequency in context
            context_freq = sum(context.count(term) for term in query_terms)
            score += min(context_freq * 5, 30)  # Cap at 30 points
            signals['context_freq'] = context_freq
            
            # SIGNAL 3: Entity completeness
            completeness = 0
            if entity.get('link'):
                completeness += 1
            if entity.get('metadata') and len(entity['metadata']) > 0:
                completeness += 1
            if entity.get('context') and len(entity['context']) > 50:
                completeness += 1
            
            score += completeness * 10
            signals['completeness'] = completeness
            
            # SIGNAL 4: Title quality
            title_length = len(entity.get('title', ''))
            if 20 <= title_length <= 150:  # Good length
                score += 5
                signals['title_quality'] = 5
            elif title_length < 10:  # Too short
                score -= 5
                signals['title_quality'] = -5
            
            # SIGNAL 5: Position bias (earlier in source = more relevant)
            # Assume entities are in document order
            position_score = max(0, 10 - (entities.index(entity) // 10))
            score += position_score
            signals['position'] = position_score
            
            # SIGNAL 6: Link quality
            link = entity.get('link', '')
            if link:
                # Prefer detail pages over list pages
                if any(keyword in link.lower() for keyword in ['detail', 'view', 'profile', 'show']):
                    score += 8
                    signals['link_quality'] = 8
                # Penalize navigation links
                elif any(keyword in link.lower() for keyword in ['login', 'search', 'category', 'tag']):
                    score -= 5
                    signals['link_quality'] = -5
            
            # SIGNAL 7: Metadata richness
            metadata = entity.get('metadata', {})
            metadata_count = len(metadata)
            score += min(metadata_count * 2, 10)  # Cap at 10 points
            signals['metadata_richness'] = metadata_count
            
            scored_entities.append({
                'entity': entity,
                'score': score,
                'signals': signals
            })
        
        # Sort by score descending
        scored_entities.sort(key=lambda x: x['score'], reverse=True)
        
        # Log top scores for debugging
        if scored_entities:
            top_scores = [f"{s['score']:.0f}" for s in scored_entities[:5]]
            logger.info(f"Top 5 scores: {', '.join(top_scores)}")
        
        # Return ranked entities
        return [item['entity'] for item in scored_entities]
    
    @staticmethod
    def deduplicate_smart(entities: List[Dict], similarity_threshold: float = 0.8) -> List[Dict]:
        """
        SMART deduplication using fuzzy matching
        More powerful than exact title matching
        """
        if not entities:
            return []
        
        unique_entities = []
        seen_signatures = []
        
        for entity in entities:
            title = str(entity.get('title', '')).lower().strip()
            
            if not title or len(title) < 3:
                continue
            
            # Create signature (normalized title)
            # Remove special chars, extra spaces
            signature = re.sub(r'[^\w\s]', '', title)
            signature = re.sub(r'\s+', ' ', signature).strip()
            
            # Check similarity with existing signatures
            is_duplicate = False
            for existing_sig in seen_signatures:
                similarity = IntelligentRanker._calculate_similarity(signature, existing_sig)
                
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_entities.append(entity)
                seen_signatures.append(signature)
        
        logger.info(f"Deduplication: {len(entities)} -> {len(unique_entities)} unique items")
        return unique_entities
    
    @staticmethod
    def _calculate_similarity(str1: str, str2: str) -> float:
        """
        Calculate Jaccard similarity between two strings
        Fast and effective for fuzzy matching
        """
        if not str1 or not str2:
            return 0.0
        
        # Use word-level Jaccard similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def filter_by_quality(entities: List[Dict], min_quality_score: int = 40) -> List[Dict]:
        """
        Filter entities by minimum quality threshold
        POWER: Remove noise before processing
        """
        from app.utils.quality_analyzer import DataQualityAnalyzer
        
        filtered = []
        
        for entity in entities:
            # Quick quality check
            title = entity.get('title', '')
            
            # Basic checks
            if not title or len(title) < 3:
                continue
            
            # Check for garbage patterns
            if re.search(r'[^\x00-\x7F]{10,}', title):  # Too much non-ASCII
                continue
            
            # Check for spam keywords
            spam_keywords = ['click here', 'subscribe now', 'buy now', 'ad', 'advertisement']
            if any(keyword in title.lower() for keyword in spam_keywords):
                continue
            
            filtered.append(entity)
        
        removed = len(entities) - len(filtered)
        if removed > 0:
            logger.info(f"Quality filter: Removed {removed} low-quality entities")
        
        return filtered
    
    @staticmethod
    def smart_pagination_detector(entities: List[Dict], url: str) -> Dict[str, any]:
        """
        POWER: Detect if current page has pagination
        Returns next page URL if available
        """
        # Look for pagination indicators in URLs
        pagination_patterns = [
            r'page=(\d+)',
            r'p=(\d+)',
            r'/page/(\d+)',
            r'offset=(\d+)',
            r'start=(\d+)'
        ]
        
        current_page = 1
        for pattern in pagination_patterns:
            match = re.search(pattern, url)
            if match:
                current_page = int(match.group(1))
                break
        
        # Look for "next page" links in entities
        next_page_url = None
        for entity in entities:
            link = entity.get('link', '')
            title = str(entity.get('title', '')).lower()
            
            if any(keyword in title for keyword in ['next', 'next page', '→', 'more']):
                next_page_url = link
                break
        
        # If no explicit next link, construct one
        if not next_page_url and current_page:
            for pattern in pagination_patterns:
                if re.search(pattern, url):
                    next_page_url = re.sub(
                        pattern,
                        lambda m: f"{m.group(0).split('=')[0] if '=' in m.group(0) else '/page/'}={current_page + 1}",
                        url
                    )
                    break
        
        return {
            'has_pagination': bool(next_page_url),
            'current_page': current_page,
            'next_page_url': next_page_url,
            'estimated_total_pages': None  # Could be enhanced with ML
        }
