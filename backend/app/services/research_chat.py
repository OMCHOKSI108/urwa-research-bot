"""
PERPLEXITY-STYLE AI RESEARCH CHAT
Real-time web research with AI analysis and citations.
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger


class ResearchChat:
    """
    Perplexity-style AI chat that:
    1. Understands user query
    2. Searches the web for current info
    3. Scrapes relevant sources
    4. Synthesizes comprehensive answer with citations
    """
    
    def __init__(self, orchestrator, llm_processor):
        self.orchestrator = orchestrator
        self.llm = llm_processor
        self.conversation_history: List[Dict] = []
    
    async def chat(self, query: str, deep_research: bool = False) -> Dict:
        """
        Process a research query and return comprehensive answer.
        
        Args:
            query: User's question
            deep_research: If True, scrapes more sources (slower but more comprehensive)
        
        Returns:
            {
                "answer": "Comprehensive answer...",
                "sources": [{url, title, snippet}],
                "follow_up_questions": [],
                "confidence": 0.85,
                "research_time": 5.2
            }
        """
        start_time = datetime.now()
        
        logger.info(f"[ResearchChat] Query: {query}")
        
        # Step 1: Analyze query to determine search strategy
        search_queries = await self._generate_search_queries(query)
        logger.info(f"[ResearchChat] Search queries: {search_queries}")
        
        # Step 2: Search the web with expanded queries
        all_results = []
        max_queries = 4 if deep_research else 2  # More queries for deep research
        for sq in search_queries[:max_queries]:
            try:
                results = await self._search_web(sq)
                all_results.extend(results)
                logger.debug(f"[ResearchChat] Query '{sq[:50]}...' returned {len(results)} results")
            except Exception as e:
                logger.warning(f"[ResearchChat] Search failed for '{sq}': {e}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r.get("url") not in seen_urls:
                seen_urls.add(r.get("url"))
                unique_results.append(r)
        
        logger.info(f"[ResearchChat] Found {len(unique_results)} unique sources")
        
        # Step 3: Scrape top sources (more for deep research)
        max_sources = 8 if deep_research else 5
        scraped_content = []
        
        # Also try to get news results for current data
        if deep_research:
            news_results = await self._search_news(query)
            for nr in news_results[:3]:
                if nr.get("url") not in seen_urls:
                    unique_results.insert(0, nr)  # Prioritize news
        
        for result in unique_results[:max_sources]:
            try:
                content = await self._scrape_source(result["url"])
                if content and len(content) > 200:
                    scraped_content.append({
                        "url": result["url"],
                        "title": result.get("title", ""),
                        "content": content[:10000]  # More content for analysis
                    })
            except Exception as e:
                logger.debug(f"[ResearchChat] Scrape failed: {e}")
        
        logger.info(f"[ResearchChat] Scraped {len(scraped_content)} sources")
        
        # Step 4: Synthesize answer with LLM
        if scraped_content:
            answer = await self._synthesize_answer(query, scraped_content)
        else:
            # Fallback to search snippets if scraping failed
            answer = await self._synthesize_from_snippets(query, unique_results[:5])
        
        # Step 5: Generate follow-up questions
        follow_ups = await self._generate_follow_ups(query, answer)
        
        # Calculate timing
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Build response
        response = {
            "answer": answer,
            "sources": [
                {
                    "url": s["url"],
                    "title": s.get("title", ""),
                    "snippet": s.get("content", "")[:200] + "..."
                }
                for s in scraped_content
            ] if scraped_content else [
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", "")
                }
                for r in unique_results[:5]
            ],
            "follow_up_questions": follow_ups,
            "confidence": self._calculate_confidence(scraped_content, answer),
            "research_time": round(elapsed, 1),
            "sources_scraped": len(scraped_content),
            "query": query
        }
        
        # Save to history
        self.conversation_history.append({
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    async def _generate_search_queries(self, query: str) -> List[str]:
        """Generate optimized search queries from user question."""
        try:
            prompt = f"""You are a search query optimizer for a web research tool. Given this user question, generate 4-5 specific search queries that would find NEWS and FACTUAL information.

User Question: {query}

IMPORTANT RULES:
- Generate SPECIFIC, descriptive queries (not single words)
- Add context words like "news", "2026", "latest", "report", "analysis"
- Avoid queries that would match dictionary definitions
- Focus on finding news articles, research papers, and authoritative sources

Generate queries covering:
1. News query: "[topic] news 2026" or "[topic] latest news"
2. Data query: "[topic] statistics data 2026"
3. Analysis query: "[topic] analysis report"
4. Specific query: Most specific phrasing of the question
5. Alternative: Different angle on the topic

Return ONLY the search queries, one per line. No numbering, no explanations."""
            
            result = await self.llm.process(prompt)
            queries = [q.strip() for q in result.strip().split('\n') if q.strip() and len(q.strip()) > 10]
            
            # Always include a news-focused version of original query
            news_query = f"{query} latest news 2026"
            if news_query not in queries:
                queries.insert(0, news_query)
            
            # Return up to 5 diverse queries
            return queries[:5]
        except Exception as e:
            logger.debug(f"[ResearchChat] Query expansion failed: {e}")
            # Fallback: return news-focused query
            return [f"{query} latest news 2026", query]
    
    # Sites to exclude from search results (dictionaries, translations, etc.)
    EXCLUDED_DOMAINS = [
        'dictionary.cambridge.org', 'merriam-webster.com', 'dictionary.com',
        'thesaurus.com', 'translate.google.com', 'wordreference.com',
        'linguee.com', 'dict.cc', 'bab.la', 'reverso.net', 'leo.org',
        'collinsdictionary.com', 'oxford', 'wiktionary.org'
    ]
    
    async def _search_web(self, query: str) -> List[Dict]:
        """Search the web using DuckDuckGo with filtering."""
        try:
            # Use the new package name
            from ddgs import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=15))  # Get more, filter later
                
                filtered_results = []
                for r in results:
                    url = r.get("href", "")
                    # Skip dictionary and translation sites
                    if any(excluded in url.lower() for excluded in self.EXCLUDED_DOMAINS):
                        logger.debug(f"[ResearchChat] Filtered out: {url}")
                        continue
                    filtered_results.append({
                        "url": url,
                        "title": r.get("title", ""),
                        "snippet": r.get("body", "")
                    })
                
                return filtered_results[:10]  # Return top 10 relevant
        except Exception as e:
            logger.error(f"[ResearchChat] Search error: {e}")
            return []
    
    async def _search_news(self, query: str) -> List[Dict]:
        """Search for recent news articles."""
        try:
            from ddgs import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=5))
                return [
                    {
                        "url": r.get("url", ""),
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "date": r.get("date", ""),
                        "source": r.get("source", "")
                    }
                    for r in results
                ]
        except Exception as e:
            logger.debug(f"[ResearchChat] News search error: {e}")
            return []
    
    async def _scrape_source(self, url: str) -> Optional[str]:
        """Scrape content from a URL."""
        try:
            # Use scraper from orchestrator to reuse resources
            if hasattr(self.orchestrator, 'scraper'):
                scraper = self.orchestrator.scraper
            else:
                from app.agents.hybrid_scraper import HybridScraper
                scraper = HybridScraper()
            
            # Increase timeout for protected sites (60s)
            content = await asyncio.wait_for(
                scraper.scrape(url),
                timeout=60.0
            )
            
            # HybridScraper returns a string directly, not a dict
            if content and len(content) > 100:
                return content
            return None
        except asyncio.TimeoutError:
            logger.warning(f"[ResearchChat] Timeout scraping {url}")
            return None
        except Exception as e:
            logger.warning(f"[ResearchChat] Scrape error for {url}: {e}")
            return None
    
    async def _synthesize_answer(self, query: str, sources: List[Dict]) -> str:
        """Synthesize comprehensive answer from scraped content."""
        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(f"""
SOURCE {i}: {source['title']}
URL: {source['url']}
CONTENT:
{source['content'][:4000]}
""")
        
        context = "\n---\n".join(context_parts)
        
        prompt = f"""You are a senior research analyst providing a comprehensive briefing. Based on the following sources, provide an in-depth, professional analysis that a real analyst would give.

USER QUESTION: {query}

SOURCES:
{context}

ANALYSIS REQUIREMENTS:
1. **Executive Summary** - Start with 2-3 key findings
2. **Current Status & Data**
   - Include specific numbers, prices, percentages
   - Quote actual statistics from the sources
   - Mention dates/timeframes for the data
3. **Trend Analysis**
   - What direction is the trend moving?
   - Compare to historical data if available
   - Identify patterns (bullish/bearish, growing/declining)
4. **Key Factors & Drivers**
   - What factors are influencing the situation?
   - Expert opinions and market sentiment
   - Regulatory or policy impacts
5. **Regional/Sector Impact**
   - How different regions/sectors are affected
   - Specific impacts mentioned in sources
6. **Risk Assessment**
   - Potential risks and concerns
   - Volatility indicators
   - Warning signs to watch
7. **Outlook & Predictions**
   - Short-term outlook (days/weeks)
   - Medium-term projections (months)
   - Expert predictions if available
8. **Actionable Insights**
   - What should someone watching this space know?
   - Key levels/thresholds to monitor
   - Recommended actions or considerations

FORMAT RULES:
- Use ACTUAL numbers and data from sources (don't make up numbers)
- Cite sources using [1], [2], etc.
- Use bullet points for clarity
- Include specific dates when data was reported
- If data is missing, say "data not available in sources"
- Be specific, not vague

PROFESSIONAL ANALYSIS:"""

        try:
            answer = await self.llm.process(prompt)
            return answer.strip()
        except Exception as e:
            logger.error(f"[ResearchChat] LLM error: {e}")
            return "I apologize, but I encountered an error synthesizing the research. Please try again."
    
    async def _synthesize_from_snippets(self, query: str, results: List[Dict]) -> str:
        """Fallback: synthesize from search snippets when scraping fails."""
        snippets = "\n\n".join([
            f"- {r.get('title', '')}: {r.get('snippet', '')}"
            for r in results
        ])
        
        prompt = f"""Based on these search results, provide a helpful answer to the user's question.

USER QUESTION: {query}

SEARCH RESULTS:
{snippets}

Note: These are search snippets, so some information may be incomplete. Provide the best answer possible based on available information, and indicate where more detailed research might be needed.

ANSWER:"""

        try:
            answer = await self.llm.process(prompt)
            return answer.strip()
        except Exception:
            return "I couldn't find enough information to answer your question. Please try rephrasing or asking a more specific question."
    
    async def _generate_follow_ups(self, query: str, answer: str) -> List[str]:
        """Generate follow-up questions based on the answer."""
        try:
            prompt = f"""Based on this Q&A, suggest 3 follow-up questions the user might want to ask.

Question: {query}
Answer: {answer[:1000]}

Return ONLY the 3 follow-up questions, one per line. No numbering or bullet points."""

            result = await self.llm.process(prompt)
            questions = [q.strip() for q in result.strip().split('\n') if q.strip()]
            return questions[:3]
        except Exception:
            return []
    
    def _calculate_confidence(self, sources: List[Dict], answer: str) -> float:
        """Calculate confidence score for the answer."""
        score = 0.5  # Base score
        
        # More sources = higher confidence
        if len(sources) >= 3:
            score += 0.2
        elif len(sources) >= 1:
            score += 0.1
        
        # Longer answer with substance
        if len(answer) > 1000:
            score += 0.15
        elif len(answer) > 500:
            score += 0.1
        
        # Contains numbers/data (likely factual)
        if re.search(r'\d+', answer):
            score += 0.1
        
        # Contains citations
        if re.search(r'\[\d+\]', answer):
            score += 0.05
        
        return min(0.95, round(score, 2))
    
    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


# Factory function (not singleton - allows multiple instances with different LLMs)
def get_research_chat(orchestrator, llm_processor) -> ResearchChat:
    """Create a ResearchChat instance with specified processor."""
    return ResearchChat(orchestrator, llm_processor)
