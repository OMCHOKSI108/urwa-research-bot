"""
ADVANCED LLM Context Management
Handles large content with intelligent chunking and summarization
"""
from typing import List, Dict, Any
from loguru import logger
import re


class AdvancedContextManager:
    """
    Smart context management for LLMs:
    1. Intelligent chunking (semantic boundaries)
    2. Hierarchical summarization
    3. Key information preservation
    4. Adaptive compression
    """
    
    # Token limits for different models
    MODEL_LIMITS = {
        'ollama_phi3': 4096,
        'ollama_llama3': 8192,
        'gemini_flash': 32768,
        'groq_llama': 32768,
    }
    
    @staticmethod
    def prepare_content_for_llm(
        content: str, 
        query: str,
        model_type: str = 'ollama_phi3',
        max_chunks: int = 5
    ) -> List[Dict[str, Any]]:
        """
        ADVANCED: Prepare large content for LLM with intelligent chunking
        
        Strategy:
        1. Split at semantic boundaries (paragraphs, sentences)
        2. Preserve context at chunk boundaries
        3. Include query-relevant passages first
        4. Compress less relevant parts
        
        Returns: List of chunks with metadata
        """
        token_limit = AdvancedContextManager.MODEL_LIMITS.get(model_type, 4096)
        
        # SMART: Token estimation based on actual English text patterns
        # Average: 1 token ≈ 4 characters for English text
        # But code/JSON: 1 token ≈ 3 characters
        # Mixed content: use 3.5 as safe average
        estimated_tokens = len(content) / 3.5
        char_limit = int(token_limit * 3.5)  # Conservative estimate
        
        logger.info(f"Content: {len(content)} chars ≈ {int(estimated_tokens)} tokens (limit: {token_limit})")
        
        if len(content) <= char_limit:
            # Fits in one chunk
            return [{
                'content': content,
                'chunk_id': 0,
                'relevance': 1.0,
                'is_complete': True
            }]
        
        # ALGORITHM 1: Split at semantic boundaries
        chunks = AdvancedContextManager._semantic_split(content, char_limit)
        
        # ALGORITHM 2: Score chunks by relevance to query
        scored_chunks = AdvancedContextManager._score_by_relevance(chunks, query)
        
        # ALGORITHM 3: Select top chunks + add context
        selected = AdvancedContextManager._select_with_context(
            scored_chunks, 
            max_chunks,
            char_limit
        )
        
        logger.info(f"Split {len(content)} chars into {len(selected)} chunks (limit: {char_limit})")
        return selected
    
    @staticmethod
    def _semantic_split(content: str, chunk_size: int) -> List[str]:
        """
        ADVANCED: Split text at semantic boundaries
        
        Priority:
        1. Double newlines (paragraphs)
        2. Single newlines (sentences)
        3. Sentence endings (. ! ?)
        4. Word boundaries
        """
        chunks = []
        
        # STEP 1: Try splitting by paragraphs
        paragraphs = content.split('\n\n')
        
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            if para_size > chunk_size:
                # Para too large, split by sentences
                sentences = re.split(r'([.!?]+\s+)', para)
                
                sentence_chunk = ""
                for i in range(0, len(sentences), 2):
                    sent = sentences[i]
                    punct = sentences[i+1] if i+1 < len(sentences) else ""
                    full_sent = sent + punct
                    
                    if len(sentence_chunk) + len(full_sent) > chunk_size:
                        if sentence_chunk:
                            chunks.append(sentence_chunk)
                        sentence_chunk = full_sent
                    else:
                        sentence_chunk += full_sent
                
                if sentence_chunk:
                    current_chunk.append(sentence_chunk)
                    current_size += len(sentence_chunk)
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Add remaining
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    @staticmethod
    def _score_by_relevance(chunks: List[str], query: str) -> List[Dict]:
        """
        ADVANCED: Score chunks by relevance to query
        
        Uses multiple signals:
        - Keyword overlap
        - Query term frequency
        - Position in document (earlier = more relevant)
        """
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        scored = []
        for i, chunk in enumerate(chunks):
            chunk_lower = chunk.lower()
            chunk_words = set(re.findall(r'\w+', chunk_lower))
            
            # Keyword overlap
            overlap = len(query_terms & chunk_words)
            
            # Term frequency
            term_freq = sum(chunk_lower.count(term) for term in query_terms)
            
            # Position bonus (early chunks more relevant)
            position_score = 1.0 / (i + 1)
            
            # Length penalty (very short chunks less useful)
            length_score = min(len(chunk) / 1000, 1.0)
            
            # Combined score
            relevance = (
                overlap * 10 +
                term_freq * 5 +
                position_score * 3 +
                length_score * 2
            )
            
            scored.append({
                'content': chunk,
                'chunk_id': i,
                'relevance': relevance,
                'overlap': overlap,
                'term_freq': term_freq
            })
        
        # Sort by relevance
        scored.sort(key=lambda x: x['relevance'], reverse=True)
        
        return scored
    
    @staticmethod
    def _select_with_context(
        scored_chunks: List[Dict],
        max_chunks: int,
        char_limit: int
    ) -> List[Dict]:
        """
        ADVANCED: Select top chunks + add surrounding context
        
        Ensures chunks are contiguous when possible for better coherence
        """
        if len(scored_chunks) <= max_chunks:
            # Return all chunks
            for i, chunk in enumerate(scored_chunks):
                chunk['is_complete'] = True
            return scored_chunks
        
        # Select top chunks
        selected_ids = set([chunk['chunk_id'] for chunk in scored_chunks[:max_chunks]])
        
        # Add adjacent chunks if they fit
        total_size = sum(len(chunk['content']) for chunk in scored_chunks[:max_chunks])
        
        for chunk in scored_chunks[max_chunks:]:
            chunk_id = chunk['chunk_id']
            
            # Check if adjacent to selected
            if any(abs(chunk_id - sid) == 1 for sid in selected_ids):
                if total_size + len(chunk['content']) < char_limit:
                    selected_ids.add(chunk_id)
                    total_size += len(chunk['content'])
        
        # Build final selection
        selected = [chunk for chunk in scored_chunks if chunk['chunk_id'] in selected_ids]
        selected.sort(key=lambda x: x['chunk_id'])  # Sort by original order
        
        # Mark completeness
        all_ids = set(range(len(scored_chunks)))
        is_complete = selected_ids == all_ids
        
        for chunk in selected:
            chunk['is_complete'] = is_complete
        
        return selected
    
    @staticmethod
    def create_multi_pass_strategy(
        content: str,
        query: str,
        model_type: str = 'ollama_phi3'
    ) -> Dict[str, Any]:
        """
        ADVANCED: Multi-pass LLM strategy for very large content
        
        Pass 1: Extract key facts from each chunk
        Pass 2: Synthesize facts into final answer
        """
        chunks = AdvancedContextManager.prepare_content_for_llm(
            content, query, model_type, max_chunks=10
        )
        
        return {
            'strategy': 'multi_pass',
            'total_chunks': len(chunks),
            'pass1_prompts': [
                {
                    'chunk_id': chunk['chunk_id'],
                    'prompt': f"Extract key facts from this content related to: {query}\n\nContent:\n{chunk['content'][:3000]}"
                }
                for chunk in chunks
            ],
            'pass2_prompt': "Synthesize the following facts into a comprehensive answer:\n\n{facts}"
        }
    
    @staticmethod
    def compress_low_relevance_sections(content: str, query: str, target_size: int) -> str:
        """
        ADVANCED: Compress less relevant sections to fit token limit
        
        Keeps high-relevance passages intact, summarizes low-relevance
        """
        # Split into sentences
        sentences = re.split(r'([.!?]+\s+)', content)
        
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        # Score each sentence
        scored_sentences = []
        for i in range(0, len(sentences), 2):
            sent = sentences[i]
            punct = sentences[i+1] if i+1 < len(sentences) else ""
            full_sent = sent + punct
            
            sent_lower = sent.lower()
            overlap = sum(1 for term in query_terms if term in sent_lower)
            
            scored_sentences.append({
                'text': full_sent,
                'relevance': overlap,
                'index': i // 2
            })
        
        # Sort by relevance
        scored_sentences.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Keep high-relevance sentences + some context
        kept = []
        current_size = 0
        kept_indices = set()
        
        for sent in scored_sentences:
            if current_size + len(sent['text']) < target_size:
                kept.append(sent)
                kept_indices.add(sent['index'])
                current_size += len(sent['text'])
                
                # Add adjacent sentences for context
                for adj in [sent['index'] - 1, sent['index'] + 1]:
                    if adj >= 0 and adj < len(scored_sentences) and adj not in kept_indices:
                        adj_sent = next((s for s in scored_sentences if s['index'] == adj), None)
                        if adj_sent and current_size + len(adj_sent['text']) < target_size:
                            kept.append(adj_sent)
                            kept_indices.add(adj)
                            current_size += len(adj_sent['text'])
        
        # Sort by original order
        kept.sort(key=lambda x: x['index'])
        
        # Reconstruct text
        result = ''.join(s['text'] for s in kept)
        
        if len(result) < len(content):
            result += f"\n\n[...{len(content) - len(result)} characters omitted for brevity...]"
        
        return result
