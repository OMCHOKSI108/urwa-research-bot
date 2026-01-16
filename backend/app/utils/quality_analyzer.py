"""
SMART Data Quality Analyzer
Evaluates scraped content quality and recommends actions
"""
from typing import Dict, List, Tuple
from loguru import logger
import re
from collections import Counter


class DataQualityAnalyzer:
    """
    Analyzes data quality and provides intelligent recommendations
    POWER: Prevents wasting resources on low-quality data
    """
    
    @staticmethod
    def analyze_content_quality(content: str) -> Dict[str, any]:
        """
        SMART quality analysis with multiple signals
        
        Returns quality score (0-100) and metrics
        """
        if not content or len(content) < 100:
            return {
                "quality_score": 0,
                "recommendation": "reject",
                "reason": "insufficient_content"
            }
        
        metrics = {}
        score = 100  # Start with perfect score
        
        # 1. Length check (penalize too short or suspiciously long)
        length = len(content)
        metrics["length"] = length
        
        if length < 500:
            score -= 30
            metrics["length_penalty"] = -30
        elif length > 500000:  # Suspiciously large
            score -= 20
            metrics["length_penalty"] = -20
        
        # 2. Word count and average word length
        words = content.split()
        word_count = len(words)
        metrics["word_count"] = word_count
        
        if word_count < 50:
            score -= 25
            metrics["word_count_penalty"] = -25
        
        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0
        metrics["avg_word_length"] = round(avg_word_length, 2)
        
        # Abnormal word lengths indicate garbage/base64/compressed data
        if avg_word_length < 2 or avg_word_length > 20:
            score -= 40
            metrics["word_length_penalty"] = -40
        
        # 3. Sentence structure
        sentences = re.split(r'[.!?]+', content)
        sentence_count = len([s for s in sentences if len(s.strip()) > 10])
        metrics["sentence_count"] = sentence_count
        
        if sentence_count < 5:
            score -= 15
            metrics["sentence_penalty"] = -15
        
        # 4. Repeated character detection (noise/garbage)
        max_repeat = max(
            (len(list(g)) for k, g in __import__('itertools').groupby(content)),
            default=0
        )
        metrics["max_char_repeat"] = max_repeat
        
        if max_repeat > 20:
            score -= 30
            metrics["repeat_penalty"] = -30
        
        # 5. Special character ratio
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / length
        metrics["special_char_ratio"] = round(special_ratio, 3)
        
        if special_ratio > 0.3:  # Too many special chars
            score -= 20
            metrics["special_char_penalty"] = -20
        
        # 6. Number vs text ratio
        digit_ratio = sum(1 for c in content if c.isdigit()) / length
        metrics["digit_ratio"] = round(digit_ratio, 3)
        
        if digit_ratio > 0.5:  # Mostly numbers
            score -= 15
            metrics["digit_penalty"] = -15
        
        # 7. Capitalization ratio (all caps = shouting/garbage)
        if word_count > 0:
            caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
            caps_ratio = caps_words / word_count
            metrics["caps_ratio"] = round(caps_ratio, 3)
            
            if caps_ratio > 0.3:
                score -= 15
                metrics["caps_penalty"] = -15
        
        # 8. Link density (too many links = spam)
        link_count = content.lower().count('http')
        link_density = link_count / word_count if word_count > 0 else 0
        metrics["link_density"] = round(link_density, 3)
        
        if link_density > 0.1:  # More than 1 link per 10 words
            score -= 10
            metrics["link_density_penalty"] = -10
        
        # 9. Common spam/error indicators
        spam_indicators = [
            'cloudflare', 'enable javascript', 'cookie consent',
            'access denied', '403', '404', 'error', 'captcha',
            'please verify', 'not found'
        ]
        content_lower = content.lower()
        spam_found = [ind for ind in spam_indicators if ind in content_lower]
        
        if spam_found:
            score -= 25
            metrics["spam_found"] = spam_found
        
        # 10. Vocabulary richness (unique words / total words)
        if word_count > 50:
            unique_words = len(set(w.lower() for w in words))
            vocab_richness = unique_words / word_count
            metrics["vocab_richness"] = round(vocab_richness, 3)
            
            if vocab_richness < 0.3:  # Too repetitive
                score -= 10
                metrics["vocab_penalty"] = -10
        
        # Normalize score to 0-100
        score = max(0, min(100, score))
        metrics["quality_score"] = score
        
        # Recommendation
        if score >= 70:
            recommendation = "accept"
            reason = "high_quality"
        elif score >= 40:
            recommendation = "accept_with_caution"
            reason = "medium_quality"
        else:
            recommendation = "reject"
            reason = "low_quality"
        
        return {
            "quality_score": score,
            "recommendation": recommendation,
            "reason": reason,
            "metrics": metrics
        }
    
    @staticmethod
    def analyze_entity_quality(entities: List[Dict]) -> Dict[str, any]:
        """
        SMART: Analyze quality of extracted entities
        """
        if not entities:
            return {
                "quality_score": 0,
                "recommendation": "reject",
                "reason": "no_entities"
            }
        
        metrics = {}
        score = 100
        
        # 1. Entity count
        entity_count = len(entities)
        metrics["entity_count"] = entity_count
        
        if entity_count < 3:
            score -= 30
            metrics["count_penalty"] = -30
        elif entity_count > 1000:  # Suspiciously many
            score -= 20
            metrics["count_penalty"] = -20
        
        # 2. Completeness (entities with all fields)
        complete_entities = sum(
            1 for e in entities 
            if e.get('title') and e.get('link') and e.get('context')
        )
        completeness_ratio = complete_entities / entity_count
        metrics["completeness_ratio"] = round(completeness_ratio, 3)
        
        if completeness_ratio < 0.5:
            score -= 25
            metrics["completeness_penalty"] = -25
        
        # 3. Title quality (check for meaningful titles)
        titles = [e.get('title', '') for e in entities if e.get('title')]
        
        if titles:
            avg_title_length = sum(len(t) for t in titles) / len(titles)
            metrics["avg_title_length"] = round(avg_title_length, 2)
            
            if avg_title_length < 10:  # Too short
                score -= 20
                metrics["title_length_penalty"] = -20
            elif avg_title_length > 200:  # Too long
                score -= 15
                metrics["title_length_penalty"] = -15
            
            # Check for duplicate titles
            unique_titles = len(set(titles))
            duplicate_ratio = 1 - (unique_titles / len(titles))
            metrics["duplicate_ratio"] = round(duplicate_ratio, 3)
            
            if duplicate_ratio > 0.3:  # More than 30% duplicates
                score -= 20
                metrics["duplicate_penalty"] = -20
        
        # 4. Metadata richness
        entities_with_metadata = sum(
            1 for e in entities 
            if e.get('metadata') and len(e['metadata']) > 0
        )
        metadata_ratio = entities_with_metadata / entity_count
        metrics["metadata_ratio"] = round(metadata_ratio, 3)
        
        # Bonus for rich metadata
        if metadata_ratio > 0.7:
            score += 10
            metrics["metadata_bonus"] = 10
        elif metadata_ratio < 0.2:
            score -= 15
            metrics["metadata_penalty"] = -15
        
        # 5. Link validity
        entities_with_links = sum(
            1 for e in entities 
            if e.get('link') and e['link'].startswith('http')
        )
        link_ratio = entities_with_links / entity_count
        metrics["link_ratio"] = round(link_ratio, 3)
        
        if link_ratio < 0.3:
            score -= 20
            metrics["link_penalty"] = -20
        
        # Normalize
        score = max(0, min(100, score))
        metrics["quality_score"] = score
        
        # Recommendation
        if score >= 70:
            recommendation = "accept"
            reason = "high_quality"
        elif score >= 40:
            recommendation = "accept_with_caution"
            reason = "medium_quality"
        else:
            recommendation = "reject"
            reason = "low_quality"
        
        return {
            "quality_score": score,
            "recommendation": recommendation,
            "reason": reason,
            "metrics": metrics
        }
    
    @staticmethod
    def should_use_llm(content: str, entities: List[Dict]) -> Tuple[bool, str]:
        """
        POWER: Intelligent decision on whether to use LLM
        Saves tokens and time by skipping LLM when not needed
        """
        # 1. If entities already good quality, skip LLM
        entity_analysis = DataQualityAnalyzer.analyze_entity_quality(entities)
        
        if entity_analysis["quality_score"] >= 80 and len(entities) >= 20:
            return False, "sufficient_quality_entities"
        
        # 2. If content is low quality, LLM won't help
        content_analysis = DataQualityAnalyzer.analyze_content_quality(content)
        
        if content_analysis["quality_score"] < 40:
            return False, "low_quality_content"
        
        # 3. If content is structured enough (tables, lists), skip LLM
        table_count = content.count('<table')
        list_count = content.count('<ul') + content.count('<ol')
        
        if table_count > 5 or list_count > 10:
            return False, "sufficient_structure"
        
        # 4. Use LLM for complex unstructured content
        if len(entities) < 10 and content_analysis["quality_score"] >= 60:
            return True, "complex_content_needs_llm"
        
        # 5. Use LLM for medium quality with few entities
        if entity_analysis["quality_score"] < 60 and len(entities) < 20:
            return True, "entities_need_enrichment"
        
        # Default: skip LLM to save resources
        return False, "default_skip"
