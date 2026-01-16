"""
Smart schema detector - uses LLM to identify data type and structure accordingly
"""
from typing import Dict, List, Any, Tuple
from loguru import logger
import json
import re
from app.models.data_schemas import DataSchemaType, SCHEMA_MAP, StructuredDataResponse


class SchemaDetector:
    """Detects data type and applies appropriate schema"""
    
    @staticmethod
    def detect_schema_type(query: str, sample_items: List[Dict]) -> Tuple[DataSchemaType, str]:
        """
        SMART schema detection - analyzes actual data patterns, not just keywords.
        Returns (schema_type, confidence)
        """
        if not sample_items:
            return DataSchemaType.GENERIC, "low"
        
        # SMART: Analyze actual data patterns from multiple items
        field_patterns = {}
        value_patterns = {}
        
        # Sample up to 10 items for pattern detection
        for item in sample_items[:10]:
            if not isinstance(item, dict):
                continue
            
            for key, value in item.items():
                key_lower = str(key).lower()
                value_str = str(value).lower() if value else ""
                
                # Track field frequency
                field_patterns[key_lower] = field_patterns.get(key_lower, 0) + 1
                
                # Detect value patterns
                if value_str:
                    # Numeric patterns (prices, ratings, counts)
                    if any(char in value_str for char in ['$', '€', '¥', '₹']):
                        value_patterns['has_currency'] = value_patterns.get('has_currency', 0) + 1
                    # Rating patterns
                    if any(word in value_str for word in ['star', 'rating', '/5', 'out of']):
                        value_patterns['has_rating'] = value_patterns.get('has_rating', 0) + 1
                    # Location patterns
                    if any(word in value_str for word in ['city', 'street', 'address', ',']):
                        value_patterns['has_location'] = value_patterns.get('has_location', 0) + 1
        
        # Calculate scores for each schema type based on field presence
        schema_scores = {
            DataSchemaType.COMPANY: 0,
            DataSchemaType.PRODUCT: 0,
            DataSchemaType.ARTICLE: 0,
            DataSchemaType.JOB: 0,
            DataSchemaType.PERSON: 0,
            DataSchemaType.RECIPE: 0,
            DataSchemaType.EVENT: 0,
            DataSchemaType.REVIEW: 0,
            DataSchemaType.PLACE: 0,
        }
        
        # Score based on field patterns
        for field, count in field_patterns.items():
            # Company indicators
            if any(keyword in field for keyword in ['company', 'industry', 'founded', 'revenue', 'employee']):
                schema_scores[DataSchemaType.COMPANY] += count * 3
            # Product indicators  
            if any(keyword in field for keyword in ['price', 'brand', 'product', 'sku', 'stock', 'cart']):
                schema_scores[DataSchemaType.PRODUCT] += count * 3
            # Article indicators
            if any(keyword in field for keyword in ['author', 'publish', 'article', 'content', 'tag', 'category']):
                schema_scores[DataSchemaType.ARTICLE] += count * 3
            # Job indicators
            if any(keyword in field for keyword in ['salary', 'job', 'position', 'experience', 'apply', 'employer']):
                schema_scores[DataSchemaType.JOB] += count * 3
            # Person indicators
            if any(keyword in field for keyword in ['email', 'phone', 'linkedin', 'bio', 'profile']):
                schema_scores[DataSchemaType.PERSON] += count * 3
            # Recipe indicators
            if any(keyword in field for keyword in ['ingredient', 'cook', 'prep', 'cuisine', 'serving']):
                schema_scores[DataSchemaType.RECIPE] += count * 3
            # Event indicators
            if any(keyword in field for keyword in ['event', 'date', 'venue', 'organizer', 'ticket']):
                schema_scores[DataSchemaType.EVENT] += count * 3
            # Review indicators
            if any(keyword in field for keyword in ['review', 'rating', 'verified', 'helpful', 'pros', 'cons']):
                schema_scores[DataSchemaType.REVIEW] += count * 3
            # Place indicators
            if any(keyword in field for keyword in ['address', 'city', 'state', 'postal', 'latitude', 'longitude']):
                schema_scores[DataSchemaType.PLACE] += count * 3
            
            # Universal fields add smaller scores
            if any(keyword in field for keyword in ['rating', 'review']):
                schema_scores[DataSchemaType.COMPANY] += count
                schema_scores[DataSchemaType.PRODUCT] += count
                schema_scores[DataSchemaType.PLACE] += count
        
        # Boost scores with value patterns
        if value_patterns.get('has_currency', 0) > 0:
            schema_scores[DataSchemaType.PRODUCT] += value_patterns['has_currency'] * 2
            schema_scores[DataSchemaType.JOB] += value_patterns['has_currency']
        if value_patterns.get('has_rating', 0) > 0:
            schema_scores[DataSchemaType.COMPANY] += value_patterns['has_rating']
            schema_scores[DataSchemaType.PRODUCT] += value_patterns['has_rating']
            schema_scores[DataSchemaType.REVIEW] += value_patterns['has_rating'] * 2
        if value_patterns.get('has_location', 0) > 0:
            schema_scores[DataSchemaType.COMPANY] += value_patterns['has_location']
            schema_scores[DataSchemaType.JOB] += value_patterns['has_location']
            schema_scores[DataSchemaType.PLACE] += value_patterns['has_location'] * 3
        
        # Find highest scoring schema
        best_schema = max(schema_scores.items(), key=lambda x: x[1])
        
        if best_schema[1] > 5:
            confidence = "high"
        elif best_schema[1] > 2:
            confidence = "medium"
        else:
            confidence = "low"
            return DataSchemaType.GENERIC, confidence
        
        logger.info(f"Schema scores: {dict(sorted(schema_scores.items(), key=lambda x: x[1], reverse=True)[:3])}")
        return best_schema[0], confidence
    
    @staticmethod
    def map_to_schema(items: List[Dict], schema_type: DataSchemaType) -> List[Dict]:
        """
        Map raw items to the detected schema structure.
        Intelligently matches fields even if names don't match exactly.
        """
        schema_class = SCHEMA_MAP[schema_type]
        schema_fields = schema_class.model_fields.keys()
        
        structured_items = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            structured_item = {}
            
            # Smart field mapping based on schema type
            if schema_type == DataSchemaType.COMPANY:
                structured_item = SchemaDetector._map_company(item)
            elif schema_type == DataSchemaType.PRODUCT:
                structured_item = SchemaDetector._map_product(item)
            elif schema_type == DataSchemaType.ARTICLE:
                structured_item = SchemaDetector._map_article(item)
            elif schema_type == DataSchemaType.JOB:
                structured_item = SchemaDetector._map_job(item)
            elif schema_type == DataSchemaType.PERSON:
                structured_item = SchemaDetector._map_person(item)
            else:
                # Generic mapping
                structured_item = {
                    'title': item.get('title') or item.get('name') or item.get('text', 'Untitled'),
                    'description': item.get('context') or item.get('description'),
                    'url': item.get('link') or item.get('url'),
                    'metadata': item.get('metadata', {})
                }
            
            if structured_item:
                structured_items.append(structured_item)
        
        return structured_items
    
    @staticmethod
    def _map_company(item: Dict) -> Dict:
        """Map to company schema"""
        # Extract rating from metadata or context
        rating = None
        reviews_count = None
        
        metadata = item.get('metadata', {})
        for key, value in metadata.items():
            if 'rating' in key.lower():
                rating = value
            elif 'review' in key.lower() or 'count' in key.lower():
                reviews_count = value
        
        # Parse context for industry/location
        context = item.get('context', '')
        industry = None
        location = None
        
        # Look for " | " pattern (common separator)
        if ' | ' in context:
            parts = context.split(' | ')
            if len(parts) >= 2:
                industry = parts[0].strip()
                location = parts[1].strip()
        
        return {
            'name': item.get('title') or item.get('name', 'Unknown'),
            'rating': rating,
            'reviews_count': reviews_count,
            'industry': industry,
            'location': location,
            'url': item.get('link') or item.get('url'),
            'description': context[:200] if context else None
        }
    
    @staticmethod
    def _map_product(item: Dict) -> Dict:
        """Map to product schema"""
        metadata = item.get('metadata', {})
        price = None
        rating = None
        
        for key, value in metadata.items():
            if any(word in key.lower() for word in ['price', 'cost', 'amount']):
                price = value
            elif 'rating' in key.lower():
                rating = value
        
        return {
            'name': item.get('title') or item.get('name', 'Unknown'),
            'price': price,
            'rating': rating,
            'url': item.get('link') or item.get('url'),
            'description': item.get('context', '')[:200] if item.get('context') else None
        }
    
    @staticmethod
    def _map_article(item: Dict) -> Dict:
        """Map to article schema"""
        return {
            'title': item.get('title') or item.get('name', 'Untitled'),
            'url': item.get('link') or item.get('url'),
            'summary': item.get('context', '')[:300] if item.get('context') else None,
            'source': item.get('source')
        }
    
    @staticmethod
    def _map_job(item: Dict) -> Dict:
        """Map to job schema"""
        context = item.get('context', '')
        
        # Try to extract company and location from context
        company = None
        location = None
        if ' - ' in context:
            parts = context.split(' - ')
            if len(parts) >= 2:
                company = parts[0].strip()
                location = parts[1].strip()
        
        return {
            'title': item.get('title') or item.get('name', 'Unknown'),
            'company': company or 'Unknown',
            'location': location,
            'url': item.get('link') or item.get('url'),
            'description': context[:300] if context else None
        }
    
    @staticmethod
    def _map_person(item: Dict) -> Dict:
        """Map to person schema"""
        return {
            'name': item.get('title') or item.get('name', 'Unknown'),
            'title': item.get('metadata', {}).get('title'),
            'url': item.get('link') or item.get('url'),
            'bio': item.get('context', '')[:200] if item.get('context') else None
        }
    
    @staticmethod
    def create_structured_response(
        items: List[Dict], 
        query: str
    ) -> StructuredDataResponse:
        """
        Create structured response with auto-detected schema.
        This is the main entry point.
        """
        # Detect schema type
        schema_type, confidence = SchemaDetector.detect_schema_type(query, items)
        
        logger.info(f"Detected schema: {schema_type.value} (confidence: {confidence})")
        
        # Map items to schema
        structured_data = SchemaDetector.map_to_schema(items, schema_type)
        
        # Get schema fields
        schema_class = SCHEMA_MAP[schema_type]
        schema_fields = list(schema_class.model_fields.keys())
        
        return StructuredDataResponse(
            schema_type=schema_type,
            schema_confidence=confidence,
            total_items=len(structured_data),
            data=structured_data,
            schema_fields=schema_fields
        )
