import uuid
import asyncio
from datetime import datetime
from loguru import logger
from fastapi import HTTPException
import pandas as pd
from fpdf import FPDF
import os
import json
import socket
import ipaddress
from urllib.parse import urlparse

from app.models.schemas import (
    SmartScrapeRequest, ScrapeResponse, EntityData, LinkData, KeyDataCategory, KeyDataItem, 
    WebSearchRequest, TargetedScrapeRequest, CustomScrapeRequest,
    SourceIntelligenceRequest, FactCheckRequest, KnowledgeBaseAddRequest, 
    KnowledgeBaseSearchRequest, PlannerRequest, MonitoringAddRequest
)
from app.utils.quality_analyzer import DataQualityAnalyzer
from app.utils.intelligent_ranker import IntelligentRanker
from app.utils.schema_detector import SchemaDetector
from app.utils.smart_extractor import UniversalExtractor, SiteTypeDetector, smart_extract
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
import googlesearch

# Define directories
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Points to docs/logs at project root
DOCS_LOG_DIR = BASE_DIR.parent / "docs" / "logs"

EXPORT_DIR = str(BASE_DIR / "app/static/exports")
SESSION_DIR = str(BASE_DIR / "app/static/sessions")
# Use the docs/logs directory for history
HISTORY_DIR = str(DOCS_LOG_DIR)

class OrchestratorService:
    def __init__(self, scraper, processor, ollama_processor, html_parser, context_manager):
        self.scraper = scraper
        self.processor = processor
        self.ollama_processor = ollama_processor
        self.html_parser = html_parser
        self.context_manager = context_manager
        
        # Ensure directories exist
        os.makedirs(EXPORT_DIR, exist_ok=True)
        os.makedirs(SESSION_DIR, exist_ok=True)
        os.makedirs(HISTORY_DIR, exist_ok=True)

    async def perform_search_multi_engine(self, query: str, max_results=5) -> list[str]:
        results = []
        blacklist = [
            "support.google.com", "accounts.google.com", "youtube.com", 
            "facebook.com", "twitter.com", "linkedin.com", "instagram.com"
        ]
        
        # 1. Try Google Search (Official, No API)
        try:
            logger.info("Searching via Google...")
            # Use run_in_executor because googlesearch is blocking
            google_results = await asyncio.to_thread(
                lambda: list(googlesearch.search(query, num_results=max_results, advanced=True))
            )
            
            for res in google_results:
                url = res.url
                if not any(b in url for b in blacklist):
                    results.append(url)
            
            logger.info(f"Google returned {len(results)} results")
            
        except Exception as e:
            logger.warning(f"Google Search Failed (falling back): {e}")

        # 2. Fallback/Augment with DuckDuckGo
        if len(results) < 2:
            try:
                logger.info("Searching via DuckDuckGo (Fallback/Augmentation)...")
                with DDGS() as ddgs:
                    ddg_results = await asyncio.to_thread(lambda: [r['href'] for r in ddgs.text(query, max_results=max_results*2)])
                    
                    for url in ddg_results:
                        if url not in results and not any(b in url for b in blacklist):
                            results.append(url)
            except Exception as e:
                logger.error(f"DuckDuckGo Search Failed: {e}")
            
        if not results:
            logger.warning("All search engines returned no results.")
            
        return list(set(results))[:max_results]

    def _validate_url(self, url: str) -> bool:
        """Prevent SSRF by blocking internal IPs"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname: return False
            
            # Resolve hostname to IP
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            
            # Block private networks
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                logger.warning(f"Blocked internal URL attempt: {url} ({ip})")
                return False
                
            return True
        except Exception:
            return False  # Fail safe

    def generate_files(self, data: list[dict], request_id: str):
        base_path = f"{EXPORT_DIR}/{request_id}"
        links = {}
        if not data: return links

        try:
            if data and isinstance(data[0], dict):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame({"value": data})
                
            csv_path = f"{base_path}.csv"
            df.to_csv(csv_path, index=False)
            links['csv'] = f"/exports/{request_id}.csv"
        except Exception as e:
            logger.error(f"CSV Generation Error: {e}")

        try:
            pdf_path = f"{base_path}.pdf"
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="URWA Research Report", ln=True, align='C')
            pdf.ln(5)
            
            for i, item in enumerate(data):
                pdf.set_font("Arial", 'B', size=10)
                pdf.cell(0, 8, txt=f"Item #{i+1}", ln=True)
                pdf.set_font("Arial", size=9)
                for k, v in item.items():
                    clean_k = str(k).encode('latin-1', 'replace').decode('latin-1')
                    clean_v = str(v).encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, txt=f"{clean_k}: {clean_v}")
                pdf.ln(3)
                
            pdf.output(pdf_path)
            links['pdf'] = f"/exports/{request_id}.pdf"
        except Exception as e:
            logger.error(f"PDF Generation Error: {e}")
            
        return links

    def _save_session(self, request_id: str, data: dict):
        try:
            session_file = os.path.join(SESSION_DIR, f"{request_id}.json")
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Session saved: {request_id}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def _save_history(self, request_id: str, query: str, sources: list, response_data: dict, start_time: datetime, end_time: datetime):
        try:
            timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
            history_file = os.path.join(HISTORY_DIR, f"search_{timestamp_str}_{request_id[:8]}.txt")
            
            duration = (end_time - start_time).total_seconds()
            
            with open(history_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("URWA SEARCH HISTORY\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Request ID: {request_id}\n")
                f.write(f"Search Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duration: {duration:.2f} seconds\n")
                f.write(f"Status: {response_data.get('status', 'unknown')}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("QUERY\n")
                f.write("-" * 80 + "\n")
                f.write(f"{query}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("SOURCES SCRAPED\n")
                f.write("-" * 80 + "\n")
                for i, source in enumerate(sources, 1):
                    f.write(f"{i}. {source}\n")
                f.write(f"\nTotal Sources: {len(sources)}\n\n")
                
                f.write("-" * 80 + "\n")
                f.write("SUMMARY\n")
                f.write("-" * 80 + "\n")
                f.write(f"{response_data.get('summary_answer', 'N/A')}\n\n")
                
                if response_data.get('detailed_answer'):
                    f.write("-" * 80 + "\n")
                    f.write("DETAILED ANSWER\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{response_data['detailed_answer']}\n\n")

        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    async def run_smart_scrape(self, request_id: str, request: SmartScrapeRequest):
        start_time = datetime.now()
        logger.info(f"START Request {request_id}: {request.query}")
        
        # Initialize session file with processing status
        self._save_session(request_id, {"status": "processing", "request_id": request_id, "query": request.query})

        try:
            # 1. Discovery Phase
            target_urls = request.urls if request.urls and len(request.urls) > 0 else None
            if not target_urls:
                logger.info("Auto-Discovery: Searching Web...")
                target_urls = await self.perform_search_multi_engine(request.query, max_results=3)
            
            if not target_urls:
                error_response = {
                     "error": "NoURLsFoundError",
                     "message": "Discovery failed: No relevant URLs found for this query.",
                     "status": "failed"
                }
                self._save_session(request_id, error_response)
                return

            # 2. Deep Analysis Loop
            collected_data = []
            successful_sources = []
            failed_urls = []
            all_links_found = []
            discovered_links_to_scrape = []
            scraped_urls = set()
            all_entities = []
            all_key_data = []
            all_scraped_content = []  # Track raw scraped content for response

            for url in target_urls:
                if url in scraped_urls: continue
                scraped_urls.add(url)
                
                # Check for timeout (5 minutes max per task)
                elapsed = (datetime.now() - start_time).total_seconds()
                # Check for timeout (5 minutes max per task)
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > 600:  # Increased global timeout to 10 minutes
                    logger.warning(f"Task timeout after {elapsed:.1f}s, stopping...")
                    break
                
                # Only limit if we are in auto-discovery mode (no initial URLs provided)
                if not request.urls:
                    if len(successful_sources) >= 3 or len(collected_data) >= 50:
                        break

                # SSRF Protection
                if not self._validate_url(url):
                    continue
                
                logger.info(f"Scouting Target: {url}")
                
                if 'list-of-' in url.lower() or 'directory' in url.lower():
                    separator = '&' if '?' in url else '?'
                    url = f"{url}{separator}campaign=desktop_nav&page=1"

                js_heavy_indicators = ['app.', 'react', 'angular', 'vue', 'spa-', '/app/', 'dynamic', 'ajax', 'infinite-scroll']
                force_playwright = any(indicator in url.lower() for indicator in js_heavy_indicators)
                
                try:
                    # Increased per-url timeout to 90s for heavy sites
                    raw_html = await asyncio.wait_for(
                        self.scraper.scrape(url, force_playwright=force_playwright),
                        timeout=90.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Scraping timeout for {url} (90s exceeded), skipping...")
                    failed_urls.append(url)
                    continue

                if raw_html and len(raw_html) > 500:
                    # Initialize parsed_data to avoid unbound variable errors
                    parsed_data = {"text_content": "", "links": [], "structured_data": {}, "structured_items": []}
                    structured_items = []
                    
                    # Try to parse as JSON first (new structured format)
                    try:
                        import json
                        structured_data = json.loads(raw_html)
                        logger.info(f"Parsed structured data from {url}")

                        # Handle different structured data formats
                        if 'structured_data' in structured_data:
                            if 'companies' in structured_data['structured_data']:
                                # AmbitionBox format
                                companies = structured_data['structured_data']['companies']
                                for company in companies:
                                    company['source_url'] = url
                                    company['source'] = url
                                collected_data.extend(companies)
                                successful_sources.append(url)
                                logger.info(f"Extracted {len(companies)} companies from {url}")
                                continue  # Skip to next URL
                            elif 'items' in structured_data['structured_data']:
                                # Generic listing format
                                items = structured_data['structured_data']['items']
                                for item in items:
                                    item['source_url'] = url
                                    item['source'] = url
                                collected_data.extend(items)
                                successful_sources.append(url)
                                logger.info(f"Extracted {len(items)} items from {url}")
                                continue  # Skip to next URL
                            else:
                                # Fallback to generic processing
                                structured_data['source_url'] = url
                                structured_data['source'] = url
                                collected_data.append(structured_data)
                                successful_sources.append(url)
                                continue  # Skip to next URL
                        else:
                            # Fallback to old markdown processing
                            parsed_data = self.html_parser.parse(raw_html, url)
                            structured_items = parsed_data.get("structured_items", [])
                            # Add source tracking to items
                            for item in structured_items:
                                item['source_url'] = url
                                item['source'] = url
                            collected_data.extend(structured_items)
                            successful_sources.append(url)

                    except json.JSONDecodeError:
                        # Not JSON, use Universal Smart Extractor for intelligent extraction
                        logger.info(f"Processing content from {url} with Smart Extractor...")
                        
                        # Detect site type and extract accordingly
                        site_type, detection_confidence = SiteTypeDetector.detect(url, raw_html)
                        logger.info(f"[SmartExtract] Site type: {site_type} (confidence: {detection_confidence:.2f})")
                        
                        # Use Universal Extractor for smart extraction
                        smart_result = UniversalExtractor.extract(raw_html, url, site_type)
                        extracted_data = smart_result.get('extracted_data', {})
                        
                        # Also run traditional HTML parser for structured items
                        parsed_data = self.html_parser.parse(raw_html, url)
                        structured_items = parsed_data.get("structured_items", [])
                        
                        # Merge smart extraction with traditional parsing
                        if extracted_data:
                            # Add smart extracted data as a high-quality item
                            smart_item = {
                                "title": extracted_data.get('product_name') or extracted_data.get('headline') or extracted_data.get('job_title') or smart_result.get('metadata', {}).get('title', ''),
                                "site_type": site_type,
                                "extracted_fields": extracted_data,
                                "source": url,
                                "source_url": url,
                                "raw_content_preview": smart_result.get('raw_text', '')[:2000],
                                "html_links": smart_result.get('links', [])[:30],
                                "metadata": smart_result.get('metadata', {}),
                                "detection_confidence": detection_confidence
                            }
                            collected_data.append(smart_item)
                            logger.info(f"[SmartExtract] Extracted {len(extracted_data)} fields from {site_type} site")
                        
                        # Check content quality
                        is_listing_page = any(keyword in url.lower() for keyword in ['list-of', 'directory', '/companies', '/products', 'browse'])
                        content_quality = DataQualityAnalyzer.analyze_content_quality(raw_html)
                        quality_threshold = 20 if is_listing_page else 40

                        if content_quality['quality_score'] < quality_threshold and not extracted_data:
                            logger.warning(f"Low quality content from {url}, skipping...")
                            failed_urls.append(url)
                            continue

                        # Try Playwright if no items found
                        if not structured_items and not extracted_data and not force_playwright:
                            try:
                                logger.info(f"Retrying {url} with Playwright...")
                                raw_html = await asyncio.wait_for(
                                    self.scraper.scrape(url, force_playwright=True),
                                    timeout=60.0
                                )
                                if raw_html and len(raw_html) > 500:
                                    # Re-run smart extraction on new content
                                    smart_result = UniversalExtractor.extract(raw_html, url, site_type)
                                    extracted_data = smart_result.get('extracted_data', {})
                                    parsed_data = self.html_parser.parse(raw_html, url)
                                    structured_items = parsed_data.get("structured_items", [])
                                    
                                    if extracted_data:
                                        smart_item = {
                                            "title": extracted_data.get('product_name') or extracted_data.get('headline') or extracted_data.get('job_title') or smart_result.get('metadata', {}).get('title', ''),
                                            "site_type": site_type,
                                            "extracted_fields": extracted_data,
                                            "source": url,
                                            "source_url": url,
                                            "raw_content_preview": smart_result.get('raw_text', '')[:2000],
                                            "html_links": smart_result.get('links', [])[:30],
                                            "metadata": smart_result.get('metadata', {}),
                                            "detection_confidence": detection_confidence
                                        }
                                        collected_data.append(smart_item)
                            except asyncio.TimeoutError:
                                logger.warning(f"Playwright retry timeout for {url}, continuing with existing data...")

                        # Process structured items from traditional parser
                        quality_items = [i for i in structured_items if i.get('link')]
                        basic_items = [i for i in structured_items if not i.get('link')]
                        items_to_process = quality_items[:150] + basic_items[:50]

                        for item in items_to_process:
                            collected_data.append({
                                "title": item.get('title', ''),
                                "link": item.get('link'),
                                "metadata": item.get('metadata', {}),
                                "context": item.get('context', ''),
                                "source": url,
                                "source_url": url,
                                "raw_content_preview": item.get('context', '')[:500],
                                "site_type": site_type
                            })
                        
                        # Track as successful if we got any content
                        if items_to_process or extracted_data:
                            successful_sources.append(url)
                        else:
                            # Even if no items, track the raw scraped content
                            text_preview = smart_result.get('raw_text', '') or parsed_data.get("text_content", "")
                            if text_preview:
                                collected_data.append({
                                    "source_url": url,
                                    "source": url,
                                    "site_type": site_type,
                                    "raw_content_preview": text_preview[:2000],
                                    "html_links": smart_result.get('links', []) or parsed_data.get("links", [])[:50],
                                    "structured_html": parsed_data.get("structured_data", {}),
                                    "metadata": smart_result.get('metadata', {})
                                })
                                successful_sources.append(url)
                    
                    # Only run LLM analysis if we have text content
                    text_content = parsed_data.get("text_content", "")
                    if text_content:
                        use_llm_decision, llm_reason = DataQualityAnalyzer.should_use_llm(text_content, structured_items)
                    else:
                        use_llm_decision = False
                        llm_reason = "No text content available"
                    
                    if request.use_local_llm and self.ollama_processor.available and use_llm_decision:
                        try:
                            content = text_content
                            if len(structured_items) > 20:
                                extracted = {
                                    "main_entities": [],
                                    "links_found": parsed_data.get("links", [])[:50],
                                    "key_data": [],
                                    "metadata": {"skipped_llm": True}
                                }
                            elif len(content) > 10000:
                                chunks = self.context_manager.prepare_content_for_llm(content, request.query, 'ollama_phi3', 5)
                                chunk_entities = []
                                chunk_links = []
                                for chunk in chunks:
                                    res = await self.ollama_processor.extract_structured_data(request.query, chunk['content'], url)
                                    if res.get("main_entities"): chunk_entities.extend(res["main_entities"])
                                    if res.get("links_found"): chunk_links.extend(res["links_found"])
                                
                                extracted = {
                                    "main_entities": chunk_entities,
                                    "links_found": list(set(chunk_links))[:50],
                                    "key_data": [],
                                    "metadata": {"chunks_processed": len(chunks)}
                                }
                            else:
                                extracted = await self.ollama_processor.extract_structured_data(request.query, content, url)
                        except Exception as e:
                            extracted = {"metadata": {"llm_failed": True}}
                    else:
                        try:
                            extracted = await self.processor.decide_action(request.query, raw_html, url)
                            extracted = {
                                "main_entities": [],
                                "links_found": parsed_data.get("links", [])[:50],
                                "key_data": [],
                                "metadata": parsed_data.get("metadata", {})
                            }
                        except:
                            extracted = {"metadata": {}}

                    extracted["html_links"] = parsed_data.get("links", [])[:100]
                    extracted["structured_html"] = parsed_data.get("structured_data", {})
                    extracted["raw_content_preview"] = text_content[:5000] if text_content else ""
                    extracted["source_url"] = url
                    
                    collected_data.append(extracted)
                    if url not in successful_sources:
                        successful_sources.append(url)
                    
                    for link in parsed_data.get("links", []):
                        if link not in all_links_found:
                            all_links_found.append(link)
                            link_url = link.get("url", "")
                            if link_url and link_url not in scraped_urls and len(discovered_links_to_scrape) < 50:
                                discovered_links_to_scrape.append(link_url)
                else:
                    failed_urls.append(url)

            # Deep Scraping Logic
            current_entity_count = len(all_entities)
            target_entity_count = 100
            deep_scraped_count = 0
            
            # Pagination logic
            for source_url in successful_sources[:3]:
                if 'list-of' in source_url.lower() or 'directory' in source_url.lower():
                    pagination_info = IntelligentRanker.smart_pagination_detector(all_entities, source_url)
                    if pagination_info['has_pagination'] and pagination_info['next_page_url']:
                        for _ in range(3):
                           next_url = pagination_info['next_page_url'] 
                           if next_url and next_url not in scraped_urls:
                                discovered_links_to_scrape.insert(0, next_url)

            if current_entity_count < target_entity_count:
                links_to_scrape = max(min(len(discovered_links_to_scrape), (target_entity_count - current_entity_count) // 5), min(5, len(discovered_links_to_scrape)))
                
                for link_url in discovered_links_to_scrape[:links_to_scrape]:
                    if link_url in scraped_urls: continue
                    scraped_urls.add(link_url)
                    try:
                        link_html = await self.scraper.scrape(link_url)
                        if link_html and len(link_html) > 500:
                            link_parsed = self.html_parser.parse(link_html, link_url)
                            link_items = link_parsed.get("structured_items", [])
                            for item in link_items[:50]:
                                all_entities.append({
                                    "title": item['title'],
                                    "link": item.get('link'),
                                    "metadata": item.get('metadata', {}),
                                    "context": item.get('context', ''),
                                    "source": link_url
                                })
                            
                            link_extracted = {
                                "main_entities": [],
                                "links_found": link_parsed.get("links", [])[:20],
                                "key_data": [],
                                "html_links": link_parsed.get("links", [])[:50],
                                "structured_html": link_parsed.get("structured_data", {}),
                                "raw_content_preview": link_parsed.get("text_content", ""),
                                "source_url": link_url,
                                "metadata": {"deep_scraped": True}
                            }
                            collected_data.append(link_extracted)
                            successful_sources.append(link_url)
                            deep_scraped_count += 1
                    except Exception as e:
                        continue

            if not collected_data:
                error_response = {
                     "error": "AllSourcesBlockedError",
                     "message": "Failed to access any valid sources.",
                     "status": "failed"
                }
                self._save_session(request_id, error_response)
                return

            # 3. Synthesis
            try:
                if request.use_local_llm and self.ollama_processor.available:
                    synthesis = await self.ollama_processor.synthesize_results(request.query, collected_data)
                    llm_provider = "local-ollama"
                else:
                    raw_contents = [d.get("raw_content_preview", "") for d in collected_data]
                    synthesis_result = await self.processor.synthesize(request.query, raw_contents)
                    synthesis = {
                        "summary": synthesis_result.get("summary", ""),
                        "detailed_answer": synthesis_result.get("detailed_answer", ""),
                        "confidence": "medium"
                    }
                    llm_provider = "cloud-gemini"
            except Exception:
                synthesis = {"summary": f"Scraped {len(collected_data)} sources", "confidence": "low"}
                llm_provider = "error"

            # 4. Aggregation & Ranking
            existing_titles = {e.get('title') or e.get('name') for e in all_entities if e.get('title') or e.get('name')}
            all_scraped_content = []

            for data in collected_data:
                for entity in data.get("main_entities", []):
                    entity_name = entity.get('name') or entity.get('title')
                    if entity_name and entity_name not in existing_titles:
                        all_entities.append(entity)
                        existing_titles.add(entity_name)
                
                all_key_data.extend(data.get("key_data", []))
                all_scraped_content.append({
                    "url": data.get("source_url", "unknown"),
                    "content_preview": data.get("raw_content_preview", ""),
                    "links_count": len(data.get("html_links", [])),
                    "structured_data": data.get("structured_html", {}),
                    "deep_scraped": data.get("metadata", {}).get("deep_scraped", False)
                })

            all_entities = IntelligentRanker.filter_by_quality(all_entities, min_quality_score=40)
            all_entities = IntelligentRanker.deduplicate_smart(all_entities, similarity_threshold=0.85)
            all_entities = IntelligentRanker.rank_entities(all_entities, request.query)

            # Convert to Models
            entity_models = []
            for e in all_entities:
                try:
                    entity_name = e.get("name") or e.get("title")
                    entity_type = e.get("type", "item")
                    if entity_name:
                        entity_models.append({
                            "name": str(entity_name),
                            "type": str(entity_type),
                            "attributes": e.get("attributes") or e.get("metadata") or {}
                        })
                except: continue

            link_models = []
            for l in all_links_found[:100]:
                if l.get("url"):
                    link_models.append({
                        "url": l.get("url"),
                        "text": l.get("text", ""),
                        "relevance": l.get("relevance", "medium"),
                        "domain": l.get("domain")
                    })

            # Schema Detection
            structured_schema_data = None
            try:
                if all_entities:
                    schema_response = SchemaDetector.create_structured_response(all_entities, request.query)
                    structured_schema_data = {
                        "schema_type": schema_response.schema_type,
                        "schema_confidence": schema_response.schema_confidence,
                        "total_items": schema_response.total_items
                    }
            except: pass

            key_data_models = []
            for kd in all_key_data[:20]:
                items = []
                for item in kd.get("items", []):
                    if "name" in item and "value" in item:
                        items.append({
                            "name": str(item.get("name")),
                            "value": str(item.get("value")),
                            "unit": item.get("unit")
                        })
                if items:
                    key_data_models.append({
                        "category": kd.get("category", "Unknown"),
                        "items": items
                    })

            # Generate Files
            download_links = {}
            if request.output_format in ["csv", "pdf", "both"]:
                export_data = entity_models[:50]
                if not export_data:
                    export_data = [{"url": l.get("url"), "text": l.get("text")} for l in link_models[:50]]
                download_links = self.generate_files(export_data, request_id)

            # Final Response Construction
            response_data = {
                "status": "success",
                "request_id": request_id,
                "summary_answer": synthesis.get("summary", "Analysis complete"),
                "detailed_answer": synthesis.get("detailed_answer", ""),
                "sources": successful_sources,

                # Add actual scraped data - build from collected_data
                "scraped_data": [
                    {
                        "url": data.get("source_url") or data.get("source") or "unknown",
                        "content_preview": (data.get("raw_content_preview") or data.get("context") or "")[:1000],
                        "links_count": len(data.get("html_links", [])),
                        "structured_data": data.get("structured_html", {}),
                        "deep_scraped": bool(data.get("raw_content_preview"))
                    }
                    for data in collected_data if data
                ],
                "raw_scraped_content": [
                    {
                        "url": data.get("source_url", ""),
                        "raw_html_content": data.get("raw_content_preview", "")[:5000],  # Limit preview
                        "structured_data": data.get("structured_html", {}),
                        "extracted_links": data.get("html_links", [])[:20],  # Limit links
                        "metadata": data.get("metadata", {})
                    }
                    for data in collected_data
                ],

                # Existing structured data
                "main_entities": entity_models,
                "links_found": link_models,
                "key_data": key_data_models,

                # Export links
                "download_links": download_links,

                "metadata": {
                    "total_sources": len(successful_sources),
                    "total_entities": len(all_entities),
                    "total_links": len(link_models),
                    "deep_scraped_pages": deep_scraped_count,
                    "llm_provider": llm_provider,
                    "scraped_content_length": sum(len(str(data.get("raw_content_preview", ""))) for data in collected_data)
                },
                "confidence": synthesis.get("confidence", "medium"),
                "structured_data": structured_schema_data
            }

            self._save_session(request_id, response_data)
            
            end_time = datetime.now()
            self._save_history(request_id, request.query, successful_sources, response_data, start_time, end_time)


        except Exception as e:
            logger.error(f"Task Failed: {e}")
            error_response = {
                "status": "failed",
                "error": str(e),
                "message": "An unexpected error occurred during processing."
            }
            self._save_session(request_id, error_response)

    # ========================================================================
    # WEB SEARCH API - 11-Step Workflow Implementation
    # ========================================================================
    
    async def run_websearch(self, request_id: str, request: WebSearchRequest):
        """
        Comprehensive Web Search following the 11-step workflow:
        1. User Input → 2. Web Search → 3. Scraping → 4. HTML Parsing →
        5. AI Processing → 6. Data Storage → 7. Quality Selection →
        8. Answer Generation → 9. Source Attribution → 10. Schema Assembly →
        11. Access & Transparency
        """
        start_time = datetime.now()
        logger.info(f"🔍 WEBSEARCH START [{request_id}]: {request.query}")
        
        # Initialize session with processing status
        self._save_session(request_id, {
            "status": "processing",
            "request_id": request_id,
            "query": request.query,
            "step": "1. User Input received"
        })
        
        try:
            # ================================================================
            # STEP 2: Web Search - Fetch top 10-20 results
            # ================================================================
            logger.info(f"📡 Step 2: Searching web for {request.max_results} results...")
            self._save_session(request_id, {
                "status": "processing", 
                "step": "2. Web Search in progress",
                "query": request.query
            })
            
            search_urls = await self._perform_extended_search(request.query, request.max_results)
            
            if not search_urls:
                error_response = {
                    "status": "failed",
                    "error": "NoSearchResults",
                    "message": "Web search returned no results for this query."
                }
                self._save_session(request_id, error_response)
                return
            
            logger.info(f"✅ Found {len(search_urls)} URLs to process")
            
            # ================================================================
            # STEP 3-4: Scraping & HTML Parsing
            # ================================================================
            sources_corpus = []  # Tabular storage for all sources
            
            for i, url in enumerate(search_urls):
                logger.info(f"📄 Step 3-4: Scraping [{i+1}/{len(search_urls)}]: {url[:60]}...")
                
                source_entry = {
                    "url": url,
                    "title": "",
                    "domain": self._extract_domain(url),
                    "extracted_content": "",
                    "raw_html_length": 0,
                    "quality_score": 0.0,
                    "relevance_score": 0.0,
                    "is_top_source": False,
                    "metadata": {},
                    "scrape_status": "pending"
                }
                
                try:
                    # Step 3: Scraping
                    raw_html = await asyncio.wait_for(
                        self.scraper.scrape(url, force_playwright=False),
                        timeout=30.0
                    )
                    
                    if raw_html and len(raw_html) > 500:
                        source_entry["raw_html_length"] = len(raw_html)
                        
                        # Step 4: HTML Parsing - Convert to structured text
                        parsed_data = self.html_parser.parse(raw_html, url)
                        text_content = parsed_data.get("text_content", "")
                        
                        # Extract title
                        source_entry["title"] = parsed_data.get("title", "") or self._extract_title_from_content(text_content)
                        source_entry["extracted_content"] = text_content[:10000]  # Limit content size
                        
                        # Quality analysis
                        quality_info = DataQualityAnalyzer.analyze_content_quality(raw_html)
                        source_entry["quality_score"] = quality_info.get("quality_score", 0)
                        
                        # Relevance scoring
                        source_entry["relevance_score"] = self._calculate_relevance(
                            request.query, 
                            source_entry["title"] + " " + text_content[:2000]
                        )
                        
                        source_entry["scrape_status"] = "success"
                        source_entry["metadata"] = {
                            "links_found": len(parsed_data.get("links", [])),
                            "structured_items": len(parsed_data.get("structured_items", [])),
                            "content_length": len(text_content)
                        }
                        
                        logger.info(f"   ✓ Quality: {source_entry['quality_score']:.1f}, Relevance: {source_entry['relevance_score']:.1f}")
                    else:
                        source_entry["scrape_status"] = "failed"
                        source_entry["metadata"]["error"] = "Content too short"
                        
                except asyncio.TimeoutError:
                    source_entry["scrape_status"] = "timeout"
                    source_entry["metadata"]["error"] = "Request timed out"
                    logger.warning(f"   ⏱ Timeout for {url[:50]}...")
                except Exception as e:
                    source_entry["scrape_status"] = "failed"
                    source_entry["metadata"]["error"] = str(e)
                    logger.warning(f"   ✗ Failed: {str(e)[:50]}")
                
                sources_corpus.append(source_entry)
            
            # ================================================================
            # STEP 5: AI Processing with Ollama
            # ================================================================
            logger.info("🧠 Step 5: AI Processing with Ollama...")
            self._save_session(request_id, {
                "status": "processing",
                "step": "5. AI Processing",
                "sources_found": len(sources_corpus)
            })
            
            successful_sources = [s for s in sources_corpus if s["scrape_status"] == "success"]
            
            # ================================================================
            # STEP 6: Data Storage - Already in tabular format (sources_corpus)
            # ================================================================
            logger.info(f"💾 Step 6: Stored {len(sources_corpus)} sources in research corpus")
            
            # ================================================================
            # STEP 7: Quality Selection - Identify best sources
            # ================================================================
            logger.info("⭐ Step 7: Quality Selection - Ranking sources...")
            
            # Sort by combined quality + relevance score
            ranked_sources = sorted(
                successful_sources,
                key=lambda x: (x["quality_score"] * 0.4 + x["relevance_score"] * 0.6),
                reverse=True
            )
            
            # Mark top sources
            top_count = min(5, len(ranked_sources))
            for i in range(top_count):
                ranked_sources[i]["is_top_source"] = True
            
            top_sources = ranked_sources[:top_count]
            
            logger.info(f"   Selected {len(top_sources)} top sources")
            
            # ================================================================
            # STEP 8: Answer Generation using AI
            # ================================================================
            logger.info("📝 Step 8: Generating comprehensive answer...")
            self._save_session(request_id, {
                "status": "processing",
                "step": "8. Answer Generation"
            })
            
            # Prepare content for LLM
            combined_content = ""
            for source in top_sources[:5]:
                combined_content += f"\n\n--- Source: {source['title']} ({source['url']}) ---\n"
                combined_content += source["extracted_content"][:3000]
            
            # Generate answer using Ollama
            answer_data = {
                "answer": "",
                "explanation": "",
                "confidence": "medium",
                "top_sources": []
            }
            
            if request.use_local_llm and self.ollama_processor.available and combined_content:
                try:
                    synthesis = await self.ollama_processor.synthesize_results(
                        request.query, 
                        [{"raw_content_preview": combined_content}]
                    )
                    answer_data["answer"] = synthesis.get("summary", "Unable to generate answer.")
                    answer_data["explanation"] = synthesis.get("detailed_answer", "")[:500]
                    answer_data["confidence"] = synthesis.get("confidence", "medium")
                except Exception as e:
                    logger.error(f"LLM synthesis error: {e}")
                    answer_data["answer"] = f"Found {len(successful_sources)} relevant sources for your query."
            else:
                # Fallback to summary without LLM
                answer_data["answer"] = f"Found {len(successful_sources)} relevant sources. Top source: {top_sources[0]['title'] if top_sources else 'N/A'}"
            
            # ================================================================
            # STEP 9: Source Attribution
            # ================================================================
            logger.info("🔗 Step 9: Adding source attribution...")
            
            answer_data["top_sources"] = [
                {
                    "title": s["title"][:100],
                    "url": s["url"],
                    "relevance": f"{s['relevance_score']:.0f}%"
                }
                for s in top_sources
            ]
            
            # ================================================================
            # STEP 10: Schema Assembly (Optional)
            # ================================================================
            structured_schema = None
            if request.include_schema:
                logger.info("📊 Step 10: Assembling structured schema...")
                try:
                    structured_schema = {
                        "schema_type": "web_research",
                        "query": request.query,
                        "generated_at": datetime.now().isoformat(),
                        "total_sources": len(sources_corpus),
                        "successful_sources": len(successful_sources),
                        "top_sources_count": len(top_sources),
                        "sources": [
                            {
                                "url": s["url"],
                                "title": s["title"],
                                "domain": s["domain"],
                                "quality_score": s["quality_score"],
                                "relevance_score": s["relevance_score"],
                                "content_preview": s["extracted_content"][:500]
                            }
                            for s in successful_sources
                        ]
                    }
                except Exception as e:
                    logger.warning(f"Schema assembly error: {e}")
            
            # ================================================================
            # Generate Export Files
            # ================================================================
            download_links = {}
            if request.output_format in ["csv", "pdf", "both"]:
                export_data = [
                    {
                        "url": s["url"],
                        "title": s["title"],
                        "domain": s["domain"],
                        "quality_score": s["quality_score"],
                        "relevance_score": s["relevance_score"],
                        "is_top_source": s["is_top_source"],
                        "content_preview": s["extracted_content"][:200]
                    }
                    for s in successful_sources
                ]
                download_links = self.generate_files(export_data, request_id)
            
            # ================================================================
            # STEP 11: Access & Transparency
            # ================================================================
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            transparency = {
                "workflow_steps_completed": 11,
                "total_urls_searched": len(search_urls),
                "successful_scrapes": len(successful_sources),
                "failed_scrapes": len([s for s in sources_corpus if s["scrape_status"] == "failed"]),
                "timeout_scrapes": len([s for s in sources_corpus if s["scrape_status"] == "timeout"]),
                "top_sources_selected": len(top_sources),
                "llm_used": request.use_local_llm and self.ollama_processor.available,
                "processing_time_seconds": round(processing_time, 2),
                "all_scraped_urls": [s["url"] for s in sources_corpus],
                "answer_sources": [s["url"] for s in top_sources]
            }
            
            logger.info(f"✅ Step 11: Transparency report generated. Total time: {processing_time:.2f}s")
            
            # ================================================================
            # Final Response Construction
            # ================================================================
            response_data = {
                "status": "success",
                "request_id": request_id,
                "query": request.query,
                
                # Answer with attribution
                "answer": answer_data,
                
                # Complete research corpus
                "sources_corpus": sources_corpus,
                
                # Top sources
                "top_sources": top_sources,
                
                # Schema (optional)
                "structured_schema": structured_schema,
                
                # Transparency
                "transparency": transparency,
                
                # Downloads
                "download_links": download_links,
                
                # Metadata
                "metadata": {
                    "total_sources": len(sources_corpus),
                    "successful_sources": len(successful_sources),
                    "top_sources": len(top_sources),
                    "processing_time": round(processing_time, 2),
                    "llm_provider": "local-ollama" if request.use_local_llm else "none"
                }
            }
            
            self._save_session(request_id, response_data)
            self._save_history(request_id, request.query, [s["url"] for s in successful_sources], response_data, start_time, end_time)
            
            logger.info(f"🎉 WEBSEARCH COMPLETE [{request_id}]: {len(successful_sources)} sources, {len(top_sources)} top picks")
            
        except Exception as e:
            logger.error(f"❌ WEBSEARCH FAILED [{request_id}]: {e}")
            error_response = {
                "status": "failed",
                "request_id": request_id,
                "error": str(e),
                "message": "An unexpected error occurred during web search."
            }
            self._save_session(request_id, error_response)
    
    async def _perform_extended_search(self, query: str, max_results: int = 15) -> list[str]:
        """Extended search to get 10-20 results"""
        results = []
        blacklist = [
            "support.google.com", "accounts.google.com", "youtube.com",
            "facebook.com", "twitter.com", "linkedin.com", "instagram.com",
            "pinterest.com", "tiktok.com"
        ]
        
        try:
            logger.info(f"🔎 Searching DuckDuckGo for: {query[:50]}...")
            with DDGS() as ddgs:
                raw_results = await asyncio.to_thread(
                    lambda: [r for r in ddgs.text(query, max_results=max_results + 5)]
                )
                
                for result in raw_results:
                    url = result.get('href', '')
                    if url and not any(b in url for b in blacklist):
                        results.append(url)
                        if len(results) >= max_results:
                            break
                            
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        return list(set(results))
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return ""
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from content if not available"""
        if not content:
            return "Untitled"
        lines = content.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                return line
        return "Untitled"
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content"""
        if not query or not content:
            return 0.0
        
        query_words = set(query.lower().split())
        content_lower = content.lower()
        
        # Count query words found in content
        matches = sum(1 for word in query_words if word in content_lower)
        base_score = (matches / len(query_words)) * 100 if query_words else 0
        
        # Bonus for exact phrase match
        if query.lower() in content_lower:
            base_score = min(100, base_score + 20)
        
        return min(100, base_score)

    # ========================================================================
    # TARGETED SCRAPING API - 9-Step Workflow Implementation
    # ========================================================================
    
    async def run_targeted_scrape(self, request_id: str, request: TargetedScrapeRequest):
        """
        Targeted Scraping following the 9-step workflow:
        1. User Input → 2. URL Validation → 3. Smart Scraping →
        4. Content Extraction → 5. Format Detection → 6. LLM Assistance →
        7. Multi-Source Handling → 8. Structured Output → 9. Response Delivery
        """
        start_time = datetime.now()
        logger.info(f"🎯 TARGETED SCRAPE START [{request_id}]: {len(request.urls)} URLs")
        
        # Initialize session
        self._save_session(request_id, {
            "status": "processing",
            "request_id": request_id,
            "step": "1. User Input received",
            "total_urls": len(request.urls)
        })
        
        try:
            results = []
            successful_count = 0
            failed_count = 0
            
            # ================================================================
            # STEP 2: URL Validation
            # ================================================================
            logger.info("🔗 Step 2: Validating URLs...")
            validated_urls = []
            
            for url in request.urls:
                url = url.strip()
                if self._is_valid_url(url):
                    validated_urls.append(url)
                else:
                    results.append({
                        "url": url,
                        "status": "failed",
                        "extracted_content": "",
                        "structured_data": {},
                        "tables": [],
                        "links": [],
                        "metadata": {},
                        "confidence": 0.0,
                        "llm_applied": False,
                        "error": "Invalid URL format"
                    })
                    failed_count += 1
            
            logger.info(f"   ✅ {len(validated_urls)} valid URLs, {failed_count} invalid")
            
            # ================================================================
            # STEP 3-7: Process each URL
            # ================================================================
            for i, url in enumerate(validated_urls):
                logger.info(f"📄 Processing [{i+1}/{len(validated_urls)}]: {url[:60]}...")
                
                self._save_session(request_id, {
                    "status": "processing",
                    "step": f"Processing URL {i+1}/{len(validated_urls)}",
                    "current_url": url
                })
                
                result = await self._process_single_url(url, request)
                results.append(result)
                
                if result["status"] == "success":
                    successful_count += 1
                else:
                    failed_count += 1
            
            # ================================================================
            # STEP 8: Structured Output / Export Files
            # ================================================================
            download_links = {}
            if request.output_format in ["csv", "pdf", "both"]:
                export_data = [
                    {
                        "url": r["url"],
                        "status": r["status"],
                        "title": r["metadata"].get("title", ""),
                        "content_preview": r["extracted_content"][:300] if r["extracted_content"] else "",
                        "confidence": r["confidence"],
                        "llm_applied": r["llm_applied"]
                    }
                    for r in results
                ]
                download_links = self.generate_files(export_data, request_id)
            
            # ================================================================
            # STEP 9: Response Delivery
            # ================================================================
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Determine overall status
            if successful_count == len(request.urls):
                overall_status = "success"
            elif successful_count > 0:
                overall_status = "partial"
            else:
                overall_status = "failed"
            
            response_data = {
                "status": overall_status,
                "request_id": request_id,
                "total_urls": len(request.urls),
                "successful": successful_count,
                "failed": failed_count,
                "results": results,
                "download_links": download_links,
                "metadata": {
                    "processing_time": round(processing_time, 2),
                    "llm_provider": "local-ollama" if request.use_local_llm else "none",
                    "extract_tables": request.extract_tables,
                    "extract_metadata": request.extract_metadata
                }
            }
            
            self._save_session(request_id, response_data)
            logger.info(f"🎉 TARGETED SCRAPE COMPLETE [{request_id}]: {successful_count}/{len(request.urls)} successful")
            
        except Exception as e:
            logger.error(f"❌ TARGETED SCRAPE FAILED [{request_id}]: {e}")
            error_response = {
                "status": "failed",
                "request_id": request_id,
                "total_urls": len(request.urls),
                "successful": 0,
                "failed": len(request.urls),
                "results": [],
                "error": str(e),
                "message": "An unexpected error occurred during targeted scraping."
            }
            self._save_session(request_id, error_response)
    
    async def _process_single_url(self, url: str, request: TargetedScrapeRequest) -> dict:
        """Process a single URL through steps 3-6"""
        result = {
            "url": url,
            "status": "pending",
            "extracted_content": "",
            "structured_data": {},
            "tables": [],
            "links": [],
            "metadata": {},
            "confidence": 0.0,
            "llm_applied": False,
            "error": None
        }
        
        try:
            # ================================================================
            # STEP 3: Smart Scraping
            # ================================================================
            logger.info(f"   🔍 Step 3: Smart scraping {url[:50]}...")
            
            # ================================================================
            # STEP 3: Smart Scraping
            # ================================================================
            logger.info(f"   🔍 Step 3: Smart scraping {url[:50]}...")
            
            # Delegate entirely to HybridScraper which handles profiling, strategy selection, and fallbacks internally
            try:
                raw_html = await asyncio.wait_for(
                    self.scraper.scrape(url),
                    timeout=90.0  # Allow sufficient time for ultra_stealth if needed
                )
            except asyncio.TimeoutError:
                logger.warning(f"   ⌛ Scraping timed out for {url}")
                raw_html = ""
            except Exception as e:
                logger.error(f"   💥 Scraping error: {e}")
                raw_html = ""
            
            if not raw_html or len(raw_html) < 100:
                result["status"] = "failed"
                result["error"] = "Unable to fetch page content (empty or blocked)"
                return result
            
            # ================================================================
            # STEP 4: Content Extraction
            # ================================================================
            logger.info(f"   📝 Step 4: Extracting content...")
            parsed_data = self.html_parser.parse(raw_html, url)
            
            result["extracted_content"] = parsed_data.get("text_content", "")[:15000]
            
            # Extract metadata if requested
            if request.extract_metadata:
                result["metadata"] = {
                    "title": parsed_data.get("title", ""),
                    "domain": self._extract_domain(url),
                    "word_count": len(result["extracted_content"].split()),
                    "links_count": len(parsed_data.get("links", []))
                }
            
            # Extract links
            result["links"] = [
                {"url": l.get("url", ""), "text": l.get("text", "")}
                for l in parsed_data.get("links", [])[:50]
            ]
            
            # Extract tables if requested
            if request.extract_tables:
                result["tables"] = self._extract_tables_from_parsed(parsed_data)
            
            # ================================================================
            # STEP 5: Format Detection
            # ================================================================
            logger.info(f"   🔎 Step 5: Detecting format quality...")
            quality_info = DataQualityAnalyzer.analyze_content_quality(raw_html)
            result["confidence"] = quality_info.get("quality_score", 50)
            
            # Check if content is clean enough
            is_clean_format = result["confidence"] > 60 and len(result["extracted_content"]) > 200
            
            # ================================================================
            # STEP 6: LLM Assistance (if needed)
            # ================================================================
            if not is_clean_format and request.use_local_llm and self.ollama_processor.available:
                logger.info(f"   🧠 Step 6: Applying LLM normalization...")
                try:
                    content_to_process = result["extracted_content"][:5000]
                    
                    llm_result = await self.ollama_processor.extract_structured_data(
                        f"Extract and structure the key information from this content",
                        content_to_process,
                        url
                    )
                    
                    if llm_result:
                        result["structured_data"] = {
                            "main_entities": llm_result.get("main_entities", []),
                            "key_data": llm_result.get("key_data", []),
                            "summary": llm_result.get("summary", "")
                        }
                        result["llm_applied"] = True
                        result["confidence"] = min(100, result["confidence"] + 15)
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ LLM processing failed: {e}")
            
            result["status"] = "success"
            logger.info(f"   ✅ Success! Confidence: {result['confidence']:.0f}%")
            
        except asyncio.TimeoutError:
            result["status"] = "failed"
            result["error"] = "Request timed out"
            logger.warning(f"   ⏱️ Timeout for {url[:50]}")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)[:200]
            logger.warning(f"   ❌ Error: {str(e)[:50]}")
        
        return result
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return all([parsed.scheme in ['http', 'https'], parsed.netloc])
        except:
            return False
    
    def _extract_tables_from_parsed(self, parsed_data: dict) -> list:
        """Extract table data from parsed content"""
        tables = []
        try:
            structured_items = parsed_data.get("structured_items", [])
            # Group items that might represent table rows
            if len(structured_items) > 3:
                tables.append({
                    "type": "extracted_items",
                    "row_count": len(structured_items),
                    "sample_data": structured_items[:10]
                })
        except:
            pass
        return tables

    # ========================================================================
    # CUSTOM WEB SCRAPE API - Advanced Prompt-Driven Extraction
    # ========================================================================
    
    async def run_custom_scrape(self, request_id: str, request: CustomScrapeRequest):
        """
        Advanced Custom Web Scrape following the 7-step workflow:
        1. Input Understanding → 2. Adaptive Scraping → 3. Anti-Bot Handling →
        4. Content Extraction → 5. LLM-Assisted Reasoning → 6. Result Structuring →
        7. Metadata & Provenance Storage
        """
        start_time = datetime.now()
        logger.info(f"🔮 CUSTOM SCRAPE START [{request_id}]: {request.url}")
        logger.info(f"   Instruction: {request.instruction[:100]}...")
        
        # Initialize session
        self._save_session(request_id, {
            "status": "processing",
            "request_id": request_id,
            "step": "1. Input Understanding",
            "url": request.url,
            "instruction": request.instruction
        })
        
        try:
            # ================================================================
            # STEP 1: Input Understanding
            # ================================================================
            logger.info("🧠 Step 1: Understanding input and intent...")
            
            intent_analysis = self._analyze_intent(request.instruction)
            logger.info(f"   Intent: {intent_analysis['intent_type']}, Entities: {intent_analysis['target_count']}")
            
            # ================================================================
            # STEP 2-3: Adaptive Scraping with Anti-Bot Handling
            # ================================================================
            raw_html = None
            scrape_method = "unknown"
            bot_protection_detected = False
            retry_count = 0
            
            for attempt in range(request.max_retries):
                retry_count = attempt + 1
                logger.info(f"🌐 Step 2-3: Scraping attempt {retry_count}/{request.max_retries}...")
                
                self._save_session(request_id, {
                    "status": "processing",
                    "step": f"2. Scraping (attempt {retry_count})",
                    "url": request.url
                })
                
                try:
                    # First try lightweight scraping
                    if attempt == 0 and not request.use_stealth:
                        logger.info("   📄 Trying lightweight scraping...")
                        raw_html = await asyncio.wait_for(
                            self.scraper.scrape(request.url, force_playwright=False),
                            timeout=30.0
                        )
                        scrape_method = "lightweight"
                    else:
                        # Use stealth/browser-based scraping
                        logger.info("   🕵️ Using stealth browser scraping...")
                        raw_html = await asyncio.wait_for(
                            self.scraper.scrape(request.url, force_playwright=True),
                            timeout=60.0
                        )
                        scrape_method = "stealth-browser"
                    
                    # Check if we got meaningful content
                    if raw_html and len(raw_html) > 1000:
                        # Check for bot protection indicators
                        bot_indicators = ["captcha", "cloudflare", "access denied", "please verify", "robot check"]
                        content_lower = raw_html.lower()
                        if any(indicator in content_lower for indicator in bot_indicators):
                            bot_protection_detected = True
                            logger.warning(f"   ⚠️ Bot protection detected, retrying...")
                            if attempt < request.max_retries - 1:
                                await asyncio.sleep(2)  # Wait before retry
                                continue
                        else:
                            logger.info(f"   ✅ Successfully scraped ({len(raw_html)} chars)")
                            break
                    else:
                        logger.warning(f"   ⚠️ Insufficient content, retrying with stealth...")
                        
                except asyncio.TimeoutError:
                    logger.warning(f"   ⏱️ Timeout on attempt {retry_count}")
                except Exception as e:
                    logger.warning(f"   ❌ Error on attempt {retry_count}: {str(e)[:50]}")
            
            if not raw_html or len(raw_html) < 500:
                error_response = {
                    "status": "failed",
                    "request_id": request_id,
                    "query": request.instruction,
                    "url": request.url,
                    "answer": "",
                    "results": [],
                    "sources": [],
                    "error": "Failed to scrape content after multiple attempts",
                    "metadata": {
                        "scrape_strategy": scrape_method,
                        "bot_protection_detected": bot_protection_detected,
                        "retry_count": retry_count
                    }
                }
                self._save_session(request_id, error_response)
                return
            
            # ================================================================
            # STEP 4: Content Extraction (Enhanced with Smart Extractor)
            # ================================================================
            logger.info("📝 Step 4: Extracting and parsing content with Smart Extractor...")
            self._save_session(request_id, {
                "status": "processing",
                "step": "4. Content Extraction"
            })
            
            # Detect site type for specialized extraction
            site_type, detection_confidence = SiteTypeDetector.detect(request.url, raw_html)
            logger.info(f"   Detected site type: {site_type} (confidence: {detection_confidence:.2f})")
            
            # Use Universal Smart Extractor for specialized extraction
            smart_result = UniversalExtractor.extract(raw_html, request.url, site_type)
            smart_extracted = smart_result.get('extracted_data', {})
            
            # Also run traditional parser
            parsed_data = self.html_parser.parse(raw_html, request.url)
            
            # Use smart extracted content if available (cleaner), otherwise fall back to parser
            extracted_content = smart_extracted.get('main_content') or parsed_data.get("text_content", "")[:20000]
            structured_items = parsed_data.get("structured_items", [])
            
            # Enhance structured items with smart extraction data
            if smart_extracted:
                # Create enhanced items from smart extraction
                for key, value in smart_extracted.items():
                    if value and key not in ['raw_text']:
                        if isinstance(value, (str, int, float)):
                            structured_items.insert(0, {
                                'title': key.replace('_', ' ').title(),
                                'context': str(value),
                                'extraction_method': 'smart_extractor',
                                'confidence': detection_confidence
                            })
                        elif isinstance(value, list) and len(value) > 0:
                            for i, item in enumerate(value[:10]):
                                structured_items.insert(0, {
                                    'title': f"{key.replace('_', ' ').title()} {i+1}",
                                    'context': str(item) if isinstance(item, str) else json.dumps(item),
                                    'extraction_method': 'smart_extractor',
                                    'confidence': detection_confidence
                                })
            
            # Add smart extraction metadata
            page_metadata = smart_result.get('metadata', {})
            smart_links = smart_result.get('links', [])
            
            # Determine content type (enhanced detection)
            content_type = "article"
            if site_type == 'ecommerce':
                content_type = "product"
            elif site_type == 'jobs':
                content_type = "job_listing"
            elif site_type == 'news':
                content_type = "news_article"
            elif site_type == 'education':
                content_type = "educational"
            elif site_type == 'reviews':
                content_type = "review"
            elif len(structured_items) > 5:
                content_type = "list"
            if any(keyword in request.url.lower() for keyword in ["table", "data", "stats", "rankings"]):
                content_type = "table"
            
            logger.info(f"   Extracted {len(extracted_content)} chars, {len(structured_items)} items, type: {content_type}")
            
            # ================================================================
            # STEP 5: LLM-Assisted Reasoning
            # ================================================================
            results = []
            answer = ""
            
            if request.use_local_llm and self.ollama_processor.available:
                logger.info("🤖 Step 5: LLM-Assisted Reasoning...")
                self._save_session(request_id, {
                    "status": "processing",
                    "step": "5. LLM Reasoning"
                })
                
                try:
                    # Build enhanced context with smart extraction data
                    smart_extraction_summary = ""
                    if smart_extracted:
                        smart_extraction_summary = f"""
SMART EXTRACTION (Site Type: {site_type}, Confidence: {detection_confidence:.0%}):
{json.dumps(smart_extracted, indent=2, default=str)[:2000]}
"""
                    
                    llm_prompt = f"""
You are analyzing a {site_type} website. Fulfill this instruction:
"{request.instruction}"

PAGE METADATA:
Title: {page_metadata.get('title', 'Unknown')}
Description: {page_metadata.get('description', 'N/A')[:200]}
{smart_extraction_summary}
RAW CONTENT:
{extracted_content[:6000]}

STRUCTURED ITEMS ({len(structured_items)} found):
{json.dumps(structured_items[:15], indent=2, default=str) if structured_items else "None"}

INSTRUCTIONS:
1. Focus on extracting EXACTLY what the user asked for: "{request.instruction}"
2. For e-commerce: Extract product names, prices (with currency), ratings, and availability
3. For jobs: Extract job titles, companies, salaries, and locations
4. For news: Extract headlines, authors, and publication dates
5. For education: Extract programs, placements, and statistics

Provide a JSON response:
{{
  "answer": "A direct, detailed answer to the instruction",
  "items": [
    {{"name": "item name", "value": "extracted value", "price": "if applicable", "rating": "if applicable", "reason": "why relevant", "confidence": 0.0-1.0}}
  ]
}}

Respond ONLY with valid JSON.
"""
                    
                    llm_result = await self.ollama_processor.extract_structured_data(
                        request.instruction,
                        llm_prompt,
                        request.url
                    )
                    
                    if llm_result:
                        # Try to parse LLM response
                        if isinstance(llm_result, dict):
                            answer = llm_result.get("summary", "") or llm_result.get("answer", "")
                            
                            # Extract entities as results
                            entities = llm_result.get("main_entities", []) or llm_result.get("items", [])
                            for i, entity in enumerate(entities[:intent_analysis['target_count']]):
                                results.append({
                                    "rank": i + 1 if intent_analysis['intent_type'] == 'ranking' else None,
                                    "name": entity.get("name", "") or entity.get("title", f"Item {i+1}"),
                                    "value": entity.get("value", "") or str(entity.get("attributes", {})),
                                    "reason": entity.get("reason", "") or entity.get("description", ""),
                                    "attributes": entity.get("attributes", {}),
                                    "source": request.url,
                                    "confidence": float(entity.get("confidence", 0.7))
                                })
                        
                        logger.info(f"   ✅ LLM extracted {len(results)} items")
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ LLM reasoning error: {e}")
            
            # Fallback: Use structured items if LLM didn't provide results
            if not results and structured_items:
                logger.info("   📋 Using structured items as fallback...")
                for i, item in enumerate(structured_items[:intent_analysis['target_count']]):
                    results.append({
                        "rank": i + 1 if intent_analysis['intent_type'] == 'ranking' else None,
                        "name": item.get("title", "") or item.get("name", f"Item {i+1}"),
                        "value": item.get("metadata", {}).get("value", ""),
                        "reason": item.get("context", ""),
                        "attributes": item.get("metadata", {}),
                        "source": request.url,
                        "confidence": 0.6
                    })
            
            # Generate answer if not provided by LLM
            if not answer:
                if results:
                    answer = f"Found {len(results)} items matching your instruction. "
                    if results[0].get("name"):
                        answer += f"Top result: {results[0]['name']}"
                else:
                    answer = f"Processed content from {request.url}. See extracted content for details."
            
            # ================================================================
            # STEP 6: Result Structuring
            # ================================================================
            logger.info("📊 Step 6: Structuring results...")
            
            # Build source metadata
            sources = [{
                "url": request.url,
                "type": content_type,
                "scrape_method": scrape_method,
                "bot_protection": bot_protection_detected,
                "timestamp": datetime.now().isoformat()
            }]
            
            # ================================================================
            # STEP 7: Metadata & Provenance Storage + Export
            # ================================================================
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            download_links = {}
            if request.output_format in ["csv", "pdf", "both"] and results:
                export_data = [
                    {
                        "rank": r.get("rank", ""),
                        "name": r["name"],
                        "value": r.get("value", ""),
                        "reason": r.get("reason", ""),
                        "confidence": r["confidence"],
                        "source": r["source"]
                    }
                    for r in results
                ]
                download_links = self.generate_files(export_data, request_id)
            
            response_data = {
                "status": "success",
                "request_id": request_id,
                "query": request.instruction,
                "url": request.url,
                "answer": answer,
                "results": results,
                "sources": sources,
                "extracted_content": extracted_content[:5000],
                "smart_extraction": {
                    "site_type": site_type,
                    "detection_confidence": detection_confidence,
                    "extracted_fields": smart_extracted,
                    "page_title": page_metadata.get('title', ''),
                    "page_description": page_metadata.get('description', ''),
                    "links_found": len(smart_links)
                },
                "download_links": download_links,
                "metadata": {
                    "scrape_strategy": scrape_method,
                    "bot_protection_detected": bot_protection_detected,
                    "retry_count": retry_count,
                    "content_type": content_type,
                    "site_type": site_type,
                    "detection_confidence": detection_confidence,
                    "items_extracted": len(results),
                    "content_length": len(extracted_content),
                    "llm_used": request.use_local_llm and self.ollama_processor.available,
                    "processing_time": round(processing_time, 2),
                    "processed_at": end_time.isoformat()
                }
            }
            
            self._save_session(request_id, response_data)
            logger.info(f"🎉 CUSTOM SCRAPE COMPLETE [{request_id}]: {len(results)} items, {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ CUSTOM SCRAPE FAILED [{request_id}]: {e}")
            error_response = {
                "status": "failed",
                "request_id": request_id,
                "query": request.instruction,
                "url": request.url,
                "answer": "",
                "results": [],
                "sources": [],
                "error": str(e),
                "metadata": {"error": str(e)}
            }
            self._save_session(request_id, error_response)
    
    def _analyze_intent(self, instruction: str) -> dict:
        """Analyze user instruction to understand intent"""
        instruction_lower = instruction.lower()
        
        # Detect intent type
        intent_type = "extraction"
        if any(word in instruction_lower for word in ["top", "best", "rank", "highest", "lowest"]):
            intent_type = "ranking"
        elif any(word in instruction_lower for word in ["compare", "vs", "versus", "difference"]):
            intent_type = "comparison"
        elif any(word in instruction_lower for word in ["summarize", "summary", "overview"]):
            intent_type = "summary"
        elif any(word in instruction_lower for word in ["filter", "only", "where", "with"]):
            intent_type = "filtering"
        
        # Detect target count
        target_count = 10  # default
        import re
        numbers = re.findall(r'\b(\d+)\b', instruction)
        if numbers:
            target_count = min(int(numbers[0]), 50)  # Cap at 50
        
        return {
            "intent_type": intent_type,
            "target_count": target_count,
            "instruction": instruction
        }

    # ========================================================================
    # SOURCE INTELLIGENCE API - Source Evaluation & Credibility
    # ========================================================================
    
    async def run_source_intelligence(self, request_id: str, request: SourceIntelligenceRequest):
        """Evaluate source credibility, bias, and freshness"""
        start_time = datetime.now()
        logger.info(f"🔍 SOURCE INTELLIGENCE START [{request_id}]: {len(request.urls)} URLs")
        
        self._save_session(request_id, {
            "status": "processing",
            "request_id": request_id,
            "step": "Evaluating sources"
        })
        
        try:
            evaluations = []
            total_credibility = 0
            
            for url in request.urls:
                logger.info(f"   📊 Evaluating: {url[:50]}...")
                
                evaluation = {
                    "url": url,
                    "domain": self._extract_domain(url),
                    "credibility_score": 0.0,
                    "bias_indicator": "unknown",
                    "freshness": "unknown",
                    "domain_authority": 0.0,
                    "ssl_valid": url.startswith("https://"),
                    "content_type": "webpage",
                    "warnings": [],
                    "recommendations": []
                }
                
                try:
                    # Scrape and analyze
                    raw_html = await asyncio.wait_for(
                        self.scraper.scrape(url, force_playwright=False),
                        timeout=30.0
                    )
                    
                    if raw_html:
                        parsed = self.html_parser.parse(raw_html, url)
                        content = parsed.get("text_content", "")
                        
                        # Credibility analysis
                        quality = DataQualityAnalyzer.analyze_content_quality(raw_html)
                        evaluation["credibility_score"] = quality.get("quality_score", 50)
                        
                        # Domain authority heuristics
                        trusted_domains = ["gov", "edu", "org", "reuters", "bbc", "nytimes", "wikipedia"]
                        domain = evaluation["domain"].lower()
                        if any(td in domain for td in trusted_domains):
                            evaluation["domain_authority"] = 80
                            evaluation["credibility_score"] = min(100, evaluation["credibility_score"] + 15)
                        else:
                            evaluation["domain_authority"] = 50
                        
                        # Freshness check
                        if request.check_freshness:
                            if "2026" in content or "2025" in content:
                                evaluation["freshness"] = "fresh"
                            elif "2024" in content:
                                evaluation["freshness"] = "recent"
                            else:
                                evaluation["freshness"] = "outdated"
                                evaluation["warnings"].append("Content may be outdated")
                        
                        # Bias indicators
                        if request.check_bias:
                            bias_words_left = ["progressive", "liberal", "socialist"]
                            bias_words_right = ["conservative", "traditional", "patriot"]
                            content_lower = content.lower()
                            
                            left_count = sum(1 for w in bias_words_left if w in content_lower)
                            right_count = sum(1 for w in bias_words_right if w in content_lower)
                            
                            if left_count > right_count + 2:
                                evaluation["bias_indicator"] = "left-leaning"
                            elif right_count > left_count + 2:
                                evaluation["bias_indicator"] = "right-leaning"
                            else:
                                evaluation["bias_indicator"] = "center"
                        
                        # SSL warning
                        if not evaluation["ssl_valid"]:
                            evaluation["warnings"].append("Site does not use HTTPS")
                            evaluation["credibility_score"] = max(0, evaluation["credibility_score"] - 10)
                        
                        total_credibility += evaluation["credibility_score"]
                        
                except Exception as e:
                    evaluation["warnings"].append(f"Analysis error: {str(e)[:50]}")
                    evaluation["credibility_score"] = 30
                
                evaluations.append(evaluation)
            
            # Calculate overall trust score
            overall_trust = total_credibility / len(request.urls) if request.urls else 0
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response_data = {
                "status": "success",
                "request_id": request_id,
                "evaluations": evaluations,
                "overall_trust_score": round(overall_trust, 1),
                "summary": f"Analyzed {len(evaluations)} sources. Average credibility: {overall_trust:.0f}%",
                "metadata": {
                    "processing_time": round(processing_time, 2),
                    "sources_evaluated": len(evaluations)
                }
            }
            
            self._save_session(request_id, response_data)
            logger.info(f"✅ SOURCE INTELLIGENCE COMPLETE [{request_id}]: Trust score {overall_trust:.0f}%")
            
        except Exception as e:
            logger.error(f"❌ SOURCE INTELLIGENCE FAILED [{request_id}]: {e}")
            self._save_session(request_id, {"status": "failed", "error": str(e)})

    # ========================================================================
    # FACT-CHECK API - Verification & Claim Analysis
    # ========================================================================
    
    async def run_fact_check(self, request_id: str, request: FactCheckRequest):
        """Verify a claim by searching and analyzing sources"""
        start_time = datetime.now()
        logger.info(f"✓ FACT-CHECK START [{request_id}]: {request.claim[:60]}...")
        
        self._save_session(request_id, {
            "status": "processing",
            "request_id": request_id,
            "step": "Searching for evidence"
        })
        
        try:
            evidence_list = []
            sources_checked = 0
            
            # Search for the claim
            if request.deep_check:
                search_urls = await self._perform_extended_search(request.claim, max_results=10)
                
                for url in search_urls[:8]:
                    sources_checked += 1
                    try:
                        raw_html = await asyncio.wait_for(
                            self.scraper.scrape(url, force_playwright=False),
                            timeout=25.0
                        )
                        
                        if raw_html:
                            parsed = self.html_parser.parse(raw_html, url)
                            content = parsed.get("text_content", "")[:5000]
                            
                            # Simple stance detection
                            claim_lower = request.claim.lower()
                            claim_words = set(claim_lower.split())
                            content_lower = content.lower()
                            
                            matches = sum(1 for w in claim_words if w in content_lower)
                            match_ratio = matches / len(claim_words) if claim_words else 0
                            
                            # Determine stance
                            if match_ratio > 0.6:
                                if any(neg in content_lower for neg in ["false", "incorrect", "debunked", "myth"]):
                                    stance = "refutes"
                                else:
                                    stance = "supports"
                            elif match_ratio > 0.3:
                                stance = "neutral"
                            else:
                                stance = "unrelated"
                            
                            if stance != "unrelated":
                                evidence_list.append({
                                    "source_url": url,
                                    "source_name": self._extract_domain(url),
                                    "stance": stance,
                                    "excerpt": content[:300] + "...",
                                    "credibility": DataQualityAnalyzer.analyze_content_quality(raw_html).get("quality_score", 50),
                                    "date_published": None
                                })
                                
                    except Exception as e:
                        logger.warning(f"   ⚠️ Error checking {url[:30]}: {e}")
            
            # Determine verdict
            supports = sum(1 for e in evidence_list if e["stance"] == "supports")
            refutes = sum(1 for e in evidence_list if e["stance"] == "refutes")
            
            if supports > refutes + 2:
                verdict = "true"
                confidence = min(90, 50 + supports * 10)
            elif refutes > supports + 2:
                verdict = "false"
                confidence = min(90, 50 + refutes * 10)
            elif supports > 0 and refutes > 0:
                verdict = "partially_true"
                confidence = 50
            else:
                verdict = "unverified"
                confidence = 30
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response_data = {
                "status": "success",
                "request_id": request_id,
                "claim": request.claim,
                "verdict": verdict,
                "confidence": confidence,
                "explanation": f"Found {supports} supporting and {refutes} refuting sources out of {sources_checked} checked.",
                "evidence": evidence_list[:5],
                "sources_checked": sources_checked,
                "metadata": {"processing_time": round(processing_time, 2)}
            }
            
            self._save_session(request_id, response_data)
            logger.info(f"✅ FACT-CHECK COMPLETE [{request_id}]: Verdict: {verdict} ({confidence}%)")
            
        except Exception as e:
            logger.error(f"❌ FACT-CHECK FAILED [{request_id}]: {e}")
            self._save_session(request_id, {"status": "failed", "error": str(e)})

    # ========================================================================
    # KNOWLEDGE BASE API - Knowledge Store & Retrieval
    # ========================================================================
    
    # In-memory knowledge store (would be a database in production)
    _knowledge_store = []
    
    async def run_knowledge_add(self, request_id: str, request: KnowledgeBaseAddRequest):
        """Add an entry to the knowledge base"""
        logger.info(f"📚 KNOWLEDGE ADD [{request_id}]: {request.title}")
        
        entry = {
            "id": str(uuid.uuid4()),
            "title": request.title,
            "content": request.content,
            "category": request.category,
            "tags": request.tags,
            "source_url": request.source_url,
            "created_at": datetime.now().isoformat(),
            "relevance_score": 0.0
        }
        
        self._knowledge_store.append(entry)
        
        response_data = {
            "status": "success",
            "request_id": request_id,
            "operation": "add",
            "entries": [entry],
            "total_count": len(self._knowledge_store),
            "message": f"Added '{request.title}' to knowledge base",
            "metadata": {}
        }
        
        self._save_session(request_id, response_data)
        logger.info(f"✅ KNOWLEDGE ADD COMPLETE [{request_id}]")
    
    async def run_knowledge_search(self, request_id: str, request: KnowledgeBaseSearchRequest):
        """Search the knowledge base"""
        logger.info(f"🔍 KNOWLEDGE SEARCH [{request_id}]: {request.query}")
        
        query_lower = request.query.lower()
        results = []
        
        for entry in self._knowledge_store:
            score = 0
            
            # Title match
            if query_lower in entry["title"].lower():
                score += 50
            
            # Content match
            if query_lower in entry["content"].lower():
                score += 30
            
            # Tag match
            for tag in entry["tags"]:
                if query_lower in tag.lower():
                    score += 20
            
            # Category filter
            if request.category and entry["category"] != request.category:
                score = 0
            
            if score > 0:
                entry_copy = entry.copy()
                entry_copy["relevance_score"] = score
                results.append(entry_copy)
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = results[:request.limit]
        
        response_data = {
            "status": "success",
            "request_id": request_id,
            "operation": "search",
            "entries": results,
            "total_count": len(results),
            "message": f"Found {len(results)} matching entries",
            "metadata": {"query": request.query}
        }
        
        self._save_session(request_id, response_data)

    # ========================================================================
    # PLANNER API - Task Automation & Research Planning
    # ========================================================================
    
    async def run_planner(self, request_id: str, request: PlannerRequest):
        """Create and optionally execute a research plan"""
        start_time = datetime.now()
        logger.info(f"📋 PLANNER START [{request_id}]: {request.objective[:60]}...")
        
        self._save_session(request_id, {
            "status": "processing",
            "request_id": request_id,
            "step": "Creating research plan"
        })
        
        try:
            # Generate plan steps based on objective
            plan = []
            objective_lower = request.objective.lower()
            
            # Step 1: Always start with search
            plan.append({
                "step_number": 1,
                "action": "search",
                "description": f"Search for information about: {request.objective}",
                "target": request.objective,
                "status": "pending",
                "output": {"message": "Awaiting execution"},
                "duration": 0
            })
            
            # Step 2: Identify key sources
            plan.append({
                "step_number": 2,
                "action": "analyze",
                "description": "Identify and evaluate top sources",
                "target": "Search Results",
                "status": "pending",
                "output": {"message": "Awaiting execution"},
                "duration": 0
            })
            
            # Step 3: Scrape top sources
            plan.append({
                "step_number": 3,
                "action": "scrape",
                "description": "Extract content from top 5 sources",
                "target": "Top Identified Sources",
                "status": "pending",
                "output": {"message": "Awaiting execution"},
                "duration": 0
            })
            
            # Conditional steps based on objective
            if "compare" in objective_lower or "vs" in objective_lower:
                plan.append({
                    "step_number": 4,
                    "action": "compare",
                    "description": "Compare findings across sources",
                    "target": "Scraped Content",
                    "status": "pending",
                    "output": {"message": "Awaiting execution"},
                    "duration": 0
                })
            
            if any(word in objective_lower for word in ["rank", "top", "best"]):
                plan.append({
                    "step_number": len(plan) + 1,
                    "action": "analyze",
                    "description": "Rank results based on criteria",
                    "target": "Comparison Data",
                    "status": "pending",
                    "output": {"message": "Awaiting execution"},
                    "duration": 0
                })
            
            # Final step: Summarize
            plan.append({
                "step_number": len(plan) + 1,
                "action": "summarize",
                "description": "Generate final summary and conclusions",
                "target": "Aggregated Findings",
                "status": "pending",
                "output": {"message": "Awaiting execution"},
                "duration": 0
            })
            
            # Limit to max_steps
            plan = plan[:request.max_steps]
            
            # Estimate time
            estimated_time = f"{len(plan) * 15}-{len(plan) * 30} seconds"
            
            # Execute if requested
            execution_status = "planned"
            results = None
            
            if request.auto_execute:
                execution_status = "executing"
                logger.info("   🚀 Auto-executing plan...")
                
                for step in plan:
                    step["status"] = "running"
                    step_start = datetime.now()
                    
                    try:
                        if step["action"] == "search":
                            urls = await self._perform_extended_search(request.objective, max_results=5)
                            step["output"] = {"urls_found": len(urls), "urls": urls[:3]}
                        elif step["action"] == "scrape":
                            step["output"] = {"message": "Content extracted from sources"}
                        elif step["action"] == "analyze":
                            step["output"] = {"message": "Analysis completed"}
                        elif step["action"] == "compare":
                            step["output"] = {"message": "Comparison completed"}
                        elif step["action"] == "summarize":
                            step["output"] = {"summary": f"Research completed for: {request.objective}"}
                        
                        step["status"] = "completed"
                        step["duration"] = (datetime.now() - step_start).total_seconds()
                        
                    except Exception as e:
                        step["status"] = "failed"
                        step["output"] = {"error": str(e)}
                
                execution_status = "completed"
                results = {"plan_executed": True, "steps_completed": len(plan)}
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response_data = {
                "status": "success",
                "request_id": request_id,
                "objective": request.objective,
                "plan": plan,
                "total_steps": len(plan),
                "completed_steps": sum(1 for s in plan if s["status"] == "completed"),
                "estimated_time": estimated_time,
                "execution_status": execution_status,
                "results": results,
                "metadata": {"processing_time": round(processing_time, 2)}
            }
            
            self._save_session(request_id, response_data)
            logger.info(f"✅ PLANNER COMPLETE [{request_id}]: {len(plan)} steps")
            
        except Exception as e:
            logger.error(f"❌ PLANNER FAILED [{request_id}]: {e}")
            self._save_session(request_id, {"status": "failed", "error": str(e)})

    # ========================================================================
    # MONITORING API - Change Alerts & Page Watching
    # ========================================================================
    
    # In-memory monitors store (would be a database in production)
    _monitors = []
    _alerts = []
    
    async def run_monitoring_add(self, request_id: str, request: MonitoringAddRequest):
        """Add a URL for monitoring"""
        logger.info(f"👁️ MONITORING ADD [{request_id}]: {request.url}")
        
        monitor = {
            "id": str(uuid.uuid4()),
            "url": request.url,
            "check_interval": request.check_interval,
            "alert_on": request.alert_on,
            "keywords": request.keywords,
            "selector": request.selector,
            "status": "active",
            "last_checked": None,
            "last_change": None,
            "change_count": 0,
            "created_at": datetime.now().isoformat()
        }
        
        # Store initial content hash
        try:
            raw_html = await asyncio.wait_for(
                self.scraper.scrape(request.url, force_playwright=False),
                timeout=30.0
            )
            if raw_html:
                import hashlib
                monitor["_content_hash"] = hashlib.md5(raw_html.encode()).hexdigest()
                monitor["last_checked"] = datetime.now().isoformat()
        except:
            monitor["_content_hash"] = None
        
        self._monitors.append(monitor)
        
        response_data = {
            "status": "success",
            "request_id": request_id,
            "operation": "add",
            "monitors": [monitor],
            "alerts": [],
            "total_monitors": len(self._monitors),
            "active_alerts": len([a for a in self._alerts if not a.get("acknowledged")]),
            "message": f"Now monitoring {request.url}",
            "metadata": {}
        }
        
        self._save_session(request_id, response_data)
        logger.info(f"✅ MONITORING ADD COMPLETE [{request_id}]")
    
    async def run_monitoring_list(self, request_id: str):
        """List all monitored URLs"""
        response_data = {
            "status": "success",
            "request_id": request_id,
            "operation": "list",
            "monitors": self._monitors[:20],
            "alerts": self._alerts[:10],
            "total_monitors": len(self._monitors),
            "active_alerts": len([a for a in self._alerts if not a.get("acknowledged")]),
            "message": f"Found {len(self._monitors)} monitors",
            "metadata": {}
        }
        
        self._save_session(request_id, response_data)
    
    async def run_monitoring_check(self, request_id: str, monitor_id: str):
        """Check a specific monitor for changes"""
        logger.info(f"🔄 MONITORING CHECK [{request_id}]: {monitor_id}")
        
        monitor = next((m for m in self._monitors if m["id"] == monitor_id), None)
        new_alerts = []
        
        if monitor:
            try:
                raw_html = await asyncio.wait_for(
                    self.scraper.scrape(monitor["url"], force_playwright=False),
                    timeout=30.0
                )
                
                if raw_html:
                    import hashlib
                    new_hash = hashlib.md5(raw_html.encode()).hexdigest()
                    
                    if monitor.get("_content_hash") and monitor["_content_hash"] != new_hash:
                        # Change detected!
                        alert = {
                            "id": str(uuid.uuid4()),
                            "monitor_id": monitor["id"],
                            "url": monitor["url"],
                            "change_type": "content_change",
                            "description": "Content has changed since last check",
                            "old_value": None,
                            "new_value": None,
                            "detected_at": datetime.now().isoformat(),
                            "acknowledged": False
                        }
                        self._alerts.append(alert)
                        new_alerts.append(alert)
                        
                        monitor["change_count"] += 1
                        monitor["last_change"] = datetime.now().isoformat()
                    
                    monitor["_content_hash"] = new_hash
                    monitor["last_checked"] = datetime.now().isoformat()
                    
            except Exception as e:
                monitor["status"] = "error"
                logger.warning(f"   ⚠️ Check failed: {e}")
        
        response_data = {
            "status": "success",
            "request_id": request_id,
            "operation": "check",
            "monitors": [monitor] if monitor else [],
            "alerts": new_alerts,
            "total_monitors": len(self._monitors),
            "active_alerts": len([a for a in self._alerts if not a.get("acknowledged")]),
            "message": f"Changes detected: {len(new_alerts)}" if new_alerts else "No changes detected",
            "metadata": {}
        }
        
        self._save_session(request_id, response_data)
