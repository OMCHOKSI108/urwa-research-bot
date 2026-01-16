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
        # Branch to Deep Dive Pipeline if requested
        if deep_research:
            return await self._run_deep_research_pipeline(query)

        # Standard Research Mode (Fast)
        search_queries = await self._generate_search_queries(query)
        # ... (rest of standard logic remains, but we can reuse the existing methods if we want. 
        # actually, to avoid code duplication and huge diffs, let's just replace the body of chat to branch)
        
        start_time = datetime.now()
        logger.info(f"[ResearchChat] Query: {query}")
        
        # Step 1: Analyze query to determine search strategy
        search_queries = await self._generate_search_queries(query)
        logger.info(f"[ResearchChat] Search queries: {search_queries}")
        
        # Step 2: Search the web
        all_results = []
        for sq in search_queries[:2]:
            try:
                results = await self._search_web(sq)
                all_results.extend(results)
            except Exception:
                pass
        
        unique_results = self._deduplicate_results(all_results)
        
        # Step 3: Scrape top sources
        scraped_content = []
        for result in unique_results[:5]:
            try:
                content = await self._scrape_source(result["url"])
                if content:
                    scraped_content.append({"url": result["url"], "title": result.get("title", ""), "content": content})
            except Exception:
                pass
        
        # Step 4: Synthesize
        if scraped_content:
            answer = await self._synthesize_answer(query, scraped_content)
        else:
            answer = await self._synthesize_from_snippets(query, unique_results[:5])
            
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            "answer": answer,
            "sources": [{"url": s["url"], "title": s["title"]} for s in scraped_content] or unique_results[:5],
            "confidence": 0.7 if scraped_content else 0.4,
            "research_time": elapsed,
            "query": query
        }

    def _deduplicate_results(self, results):
        seen = set()
        unique = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                unique.append(r)
        return unique

    async def _run_deep_research_pipeline(self, query: str) -> Dict:
        """
        Execute a massively scaled 'Deep Dive' research workflow.
        Method: Map-Reduce (Scrape many -> Extract Notes -> Synthesize)
        """
        start_time = datetime.now()
        logger.info(f"[DeepResearch] STARTING MASSIVE RESEARCH: {query}")
        
        # 1. EXPANSION PHASE: Generate 12+ queries across different angles
        # We manually construct specific angles to ensure breadth
        angles = [
            f"{query} scientific research paper 2024 2025",
            f"{query} statistical data and figures",
            f"{query} literature review abstract",
            f"{query} controversy and debate",
            f"{query} market analysis report 2025",
            f"{query} clinical trials and experimental results",
            f"{query} technical whitepaper",
            f"{query} expert commentary and interviews",
            f"latest developments in {query}",
            f"history and evolution of {query}"
        ]
        logger.info(f"[DeepResearch] generated {len(angles)} search angles")

        # 2. DISCOVERY PHASE: Massive parallel search
        all_results = []
        
        # Run searches in parallel batches
        batch_size = 5
        for i in range(0, len(angles), batch_size):
            batch = angles[i:i+batch_size]
            tasks = [self._search_web(q) for q in batch]
            batch_results = await asyncio.gather(*tasks)
            for res in batch_results:
                all_results.extend(res)
        
        # Deduplicate and prioritize
        unique_results = self._deduplicate_results(all_results)
        logger.info(f"[DeepResearch] Found {len(unique_results)} unique potential sources")
        
        # Filter to top 25 most promising URLs (mix of academic, news, general)
        # In a real system, we'd use an LLM ranker here, but for now we take the top results from varied queries
        targets = unique_results[:25] 
        
        # 3. CONSUMPTION PHASE: Scrape & Map (Extract Notes)
        research_notes = []
        scraped_sources = []
        
        sem = asyncio.Semaphore(5) # Concurrency limit
        
        async def process_url(target):
            async with sem:
                try:
                    logger.debug(f"[DeepResearch] Scraping: {target['url']}")
                    content = await self._scrape_source(target["url"])
                    
                    if not content or len(content) < 500:
                        return None
                        
                    # MAP STEP: Immediate Extraction (Save tokens)
                    # Instead of saving 50k chars, we extract 2k chars of "Gold"
                    notes = await self._extract_insights_from_source(query, content, target)
                    return {
                        "url": target["url"],
                        "title": target.get("title", ""),
                        "notes": notes,
                        "raw_snippet": content[:500] # Keep a bit of raw
                    }
                except Exception as e:
                    logger.warning(f"Failed to process {target['url']}: {e}")
                    return None

        # Execute scrape & map
        tasks = [process_url(t) for t in targets]
        results = await asyncio.gather(*tasks)
        
        # Filter valid notes
        for r in results:
            if r:
                research_notes.append(r)
                scraped_sources.append({"url": r["url"], "title": r["title"]})
        
        logger.info(f"[DeepResearch] Successfully analyzed {len(research_notes)} deep sources")
        
        # 4. SYNTHESIS PHASE: Reduce (Compile Report)
        
        # Construct the "Researcher's Notebook" context
        notebook_context = ""
        for i, note in enumerate(research_notes, 1):
            notebook_context += f"""
--- SOURCE {i} ---
URL: {note['url']}
TITLE: {note['title']}
KEY INSIGHTS:
{note['notes']}
------------------
"""
        
        # Final Synthesis Prompt
        final_answer = await self._synthesize_deep_report(query, notebook_context, len(research_notes))
        
        # 5. ARTIFACT GENERATION
        file_path = self._save_research_file(query, final_answer, scraped_sources)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            "answer": final_answer, # The abstract/summary goes to CLI
            "sources": [{"url": s["url"], "title": s["title"]} for s in scraped_sources],
            "confidence": 0.95,
            "research_time": round(elapsed, 1),
            "sources_scraped": len(scraped_sources),
            "query": query,
            "file_path": file_path
        }

    async def _extract_insights_from_source(self, query: str, content: str, meta: Dict) -> str:
        """Map Step: Extract key relevant/hard facts from a single source."""
        prompt = f"""Analyze this text for a research report on: "{query}".
        
Extract the following (if present):
- Hard statistics and data points.
- Specific dates, names, and entities.
- "Literature Review" style summaries of findings.
- Descriptions of any Tables or Figures mentioned.
- Contrasting viewpoints.

TEXT TO ANALYZE:
{content[:15000]} 

Return ONLY the extracted notes as bullet points. Be extremely dense and factual. No fluff."""
        
        try:
            # fast model for extraction if possible, but using main llm for now
            return await self.llm.process(prompt)
        except:
            return content[:2000] # Fallback to raw truncation

    async def _synthesize_deep_report(self, query: str, notebook_context: str, source_count: int) -> str:
        prompt = f"""You are a Principal Investigator conducting a systematic review.
        
Topic: {query}
Scope: Analysis of {source_count} separate sources including literature and data.

RESEARCH NOTES (Aggregated Findings):
{notebook_context}

TASK:
Write a comprehensive "State of the Art" Research Report. 
You must synthesize the disparate notes into a cohesive narrative.

STRUCTURE:
1. **ABSTRACT** (200 words): High-level summary of the entire landscape.
2. **LITERATURE REVIEW**: What do the sources say? Group them by themes.
3. **DATA & FIGURES**: Present a text-based representation of key data found (tables/stats).
4. **CRITICAL ANALYSIS**: Where are the gaps? What is the consensus?
5. **CONCLUSION**

Tone: Academic, Rigorous, Objective.
Citations: Use [Source X] to reference findings.

Generate the full report now."""
        return await self.llm.process(prompt)

    def _save_research_file(self, query, content, sources):
        try:
            import os
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = re.sub(r'[^a-zA-Z0-9]', '_', query)[:30]
            filename = f"DEEP_RESEARCH_{safe_query}_{timestamp}.txt"
            
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            EXPORT_DIR = os.path.join(BASE_DIR, "app", "static", "exports")
            os.makedirs(EXPORT_DIR, exist_ok=True)
            
            full_path = os.path.join(EXPORT_DIR, filename)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.write("\n\nREFERENCES:\n")
                for s in sources:
                    f.write(f"- {s['url']} ({s['title']})\n")
            
            return full_path
        except:
            return None
        
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
        

        prompt = f"""You are a Principal Researcher conducting a Deep Dive analysis. Your goal is to synthesize a months' worth of research into a comprehensive report.

USER TOPIC: {query}

SOURCES PROVIDED:
{context}

REPORT STRUCTURE (Strictly Follow):

1. **ABSTRACT** (Max 200 words)
   - concise summary of the most critical findings.
   - The "Bottom Line Up Front".

2. **COMPREHENSIVE ANALYSIS**
   - **Current State of Knowledge**: What do we know for sure? citations required [1].
   - **Key Findings & Statistics**: Hard data, percentages, clinical trial results (if medical), or market data (if financial).
   - **Debates & Conflicts**: Where do sources disagree? 

3. **DETAILED BREAKDOWN**
   - Break down the logic step-by-step.
   - If medical: Symptoms, Diagnosis, Treatments, New Research.
   - If technical: Architecture, Performance, Pros/Cons.

4. **FUTURE OUTLOOK**
   - What is coming next? (Clinical trials in pipe, upcoming tech releases).

5. **CONCLUSION**
   - Final verdict based on evidence.

FORMATTING RULES:
- CITATIONS ARE MANDATORY: Use [1], [2] next to every fact.
- Be objective and exhaustive.
- If sources are thin, admit it. Do not hallucinate.

Generate the full report now."""

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
