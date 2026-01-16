from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import List, Optional, Literal, Dict, Any, Union

class SmartScrapeRequest(BaseModel):
    query: str = Field(..., description="User's objective, e.g., 'best deals for iphone17 PRO' or 'scrapes GPA'")
    urls: Optional[List[str]] = Field(default=None, description="Optional list of specific URLs to target")
    output_format: Literal["pdf", "csv", "json", "both"] = Field(default="json", description="Desired export format")
    use_local_llm: bool = Field(default=True, description="Use local Ollama LLM instead of cloud APIs")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Identify top 3 competitors to Tesla's Optimus robot with technical specs",
                    "urls": [],
                    "output_format": "json",
                    "use_local_llm": True
                }
            ]
        }
    }

# New specialized request schemas for different modes
class ChatRequest(BaseModel):
    message: str = Field(..., description="Natural language message that may contain URLs and research queries")
    output_format: Literal["pdf", "csv", "json", "both"] = Field(default="json", description="Desired export format")
    use_local_llm: bool = Field(default=True, description="Use local Ollama LLM instead of cloud APIs")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Research Tesla competitors and analyze these sites: https://example1.com, https://example2.com",
                    "output_format": "json",
                    "use_local_llm": True
                }
            ]
        }
    }

class SearchRequest(BaseModel):
    query: str = Field(..., description="Research query for web search")
    output_format: Literal["pdf", "csv", "json", "both"] = Field(default="json", description="Desired export format")
    use_local_llm: bool = Field(default=True, description="Use local Ollama LLM instead of cloud APIs")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What are the latest developments in quantum computing?",
                    "output_format": "json",
                    "use_local_llm": True
                }
            ]
        }
    }

class AnalyzeUrlsRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to analyze directly")
    query: Optional[str] = Field(default=None, description="Optional context query for the analysis")
    output_format: Literal["pdf", "csv", "json", "both"] = Field(default="json", description="Desired export format")
    use_local_llm: bool = Field(default=True, description="Use local Ollama LLM instead of cloud APIs")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "urls": ["https://example1.com", "https://example2.com"],
                    "query": "Compare these two websites",
                    "output_format": "json",
                    "use_local_llm": True
                }
            ]
        }
    }

class EntityData(BaseModel):
    name: str
    type: str
    attributes: Dict[str, Any] = {}

class LinkData(BaseModel):
    url: str
    text: str
    relevance: str = "medium"
    domain: Optional[str] = None

class KeyDataItem(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None

class KeyDataCategory(BaseModel):
    category: str
    items: List[KeyDataItem]


# NEW: Structured schema response
class StructuredSchemaData(BaseModel):
    """Auto-detected structured data with schema"""
    schema_type: str = Field(..., description="Detected data type (company, product, article, etc.)")
    schema_confidence: str = Field(..., description="Detection confidence (low, medium, high)")
    total_items: int
    data: List[Dict[str, Any]] = Field(..., description="Structured data following the detected schema")
    schema_fields: List[str] = Field(..., description="Available fields in this schema")


class ScrapeResponse(BaseModel):
    status: str
    summary_answer: str
    detailed_answer: Optional[str] = ""
    sources: List[str] = []
    
    # Enhanced structured data
    main_entities: List[EntityData] = []
    links_found: List[LinkData] = []
    key_data: List[KeyDataCategory] = []
    
    # Legacy fields for backward compatibility
    raw_data: List[dict] = []
    raw_search_results: str = ""
    
    download_links: dict
    metadata: Dict[str, Any] = {}
    
    llm_provider: str = "local"  # "local" or "cloud"
    confidence: str = "medium"
    
    # NEW: Smart structured data with auto-detected schema
    structured_data: Optional[StructuredSchemaData] = Field(
        default=None,
        description="Auto-detected structured data with appropriate schema (company, product, article, etc.)"
    )

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str = "Task started"


# ============================================================================
# WEB SEARCH API - 11-Step Workflow Schemas
# ============================================================================

class WebSearchRequest(BaseModel):
    """Request schema for the comprehensive web search API"""
    query: str = Field(..., description="User's research question, topic, or prompt")
    max_results: int = Field(default=15, ge=5, le=20, description="Number of search results to fetch (10-20)")
    use_local_llm: bool = Field(default=True, description="Use local Ollama LLM for AI processing")
    include_schema: bool = Field(default=True, description="Include optional structured schema assembly")
    output_format: Literal["json", "csv", "pdf", "both"] = Field(default="json", description="Export format for results")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What are the latest AI developments in 2025?",
                    "max_results": 15,
                    "use_local_llm": True,
                    "include_schema": True,
                    "output_format": "json"
                }
            ]
        }
    }


class SourceEntry(BaseModel):
    """Individual source entry in the research corpus"""
    url: str = Field(..., description="Source URL")
    title: str = Field(default="", description="Page title")
    domain: str = Field(default="", description="Domain name")
    extracted_content: str = Field(default="", description="Cleaned, parsed text content")
    raw_html_length: int = Field(default=0, description="Original HTML content length")
    quality_score: float = Field(default=0.0, description="Content quality score (0-100)")
    relevance_score: float = Field(default=0.0, description="Relevance to query (0-100)")
    is_top_source: bool = Field(default=False, description="Whether this is a top-ranked source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    scrape_status: str = Field(default="pending", description="Scraping status: success, failed, timeout")


class WebSearchAnswer(BaseModel):
    """The final generated answer with attribution"""
    answer: str = Field(..., description="Concise, high-quality answer to the query")
    explanation: str = Field(default="", description="Short explanation of how the answer was derived")
    confidence: str = Field(default="medium", description="Confidence level: low, medium, high")
    top_sources: List[Dict[str, str]] = Field(default_factory=list, description="Top sources used for the answer")


class WebSearchResponse(BaseModel):
    """Response schema for the comprehensive web search API"""
    status: str = Field(..., description="Response status: success, failed, processing")
    request_id: str = Field(..., description="Unique request identifier")
    query: str = Field(..., description="Original user query")
    
    # Step 8-9: Answer Generation with Source Attribution
    answer: WebSearchAnswer = Field(..., description="Generated answer with sources")
    
    # Step 6: Data Storage - Tabular format with all sources
    sources_corpus: List[SourceEntry] = Field(default_factory=list, description="Complete research corpus in tabular format")
    
    # Step 7: Quality Selection
    top_sources: List[SourceEntry] = Field(default_factory=list, description="Most reliable and relevant sources")
    
    # Step 10: Schema Assembly (Optional)
    structured_schema: Optional[Dict[str, Any]] = Field(default=None, description="Structured schema for reuse/export")
    
    # Step 11: Access & Transparency
    transparency: Dict[str, Any] = Field(default_factory=dict, description="Full traceability data")
    
    # Export links
    download_links: Dict[str, str] = Field(default_factory=dict, description="CSV/PDF download links")
    
    # Processing metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing statistics")


# ============================================================================
# TARGETED SCRAPING API - 9-Step Workflow Schemas
# ============================================================================

class TargetedScrapeRequest(BaseModel):
    """Request schema for the targeted scraping API"""
    urls: List[str] = Field(..., description="One or more website URLs (single or comma-separated list)")
    use_local_llm: bool = Field(default=True, description="Use local Ollama LLM for content normalization if needed")
    extract_tables: bool = Field(default=True, description="Extract tables from pages")
    extract_metadata: bool = Field(default=True, description="Extract page metadata (title, author, date)")
    output_format: Literal["json", "csv", "pdf", "both"] = Field(default="json", description="Export format")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "urls": ["https://example1.com", "https://example2.com"],
                    "use_local_llm": True,
                    "extract_tables": True,
                    "extract_metadata": True,
                    "output_format": "json"
                }
            ]
        }
    }


class TargetedScrapeResult(BaseModel):
    """Individual result for each scraped URL"""
    url: str = Field(..., description="Source website URL")
    status: Literal["success", "failed", "partial"] = Field(..., description="Scraping status")
    extracted_content: str = Field(default="", description="Cleaned main content from the page")
    structured_data: Dict[str, Any] = Field(default_factory=dict, description="LLM-formatted fields if applied")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    links: List[Dict[str, str]] = Field(default_factory=list, description="Links found on page")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Title, author, date, etc.")
    confidence: float = Field(default=0.0, description="Quality score of extraction (0-100)")
    llm_applied: bool = Field(default=False, description="Whether LLM was used to normalize content")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class TargetedScrapeResponse(BaseModel):
    """Response schema for the targeted scraping API"""
    status: str = Field(..., description="Overall status: success, partial, failed")
    request_id: str = Field(..., description="Unique request identifier")
    total_urls: int = Field(..., description="Total URLs processed")
    successful: int = Field(default=0, description="Number of successful scrapes")
    failed: int = Field(default=0, description="Number of failed scrapes")
    
    # Per-URL results
    results: List[TargetedScrapeResult] = Field(default_factory=list, description="Individual results for each URL")
    
    # Export links
    download_links: Dict[str, str] = Field(default_factory=dict, description="CSV/PDF download links")
    
    # Processing metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing statistics")


# ============================================================================
# CUSTOM WEB SCRAPE API - Advanced Prompt-Driven Extraction
# ============================================================================

class CustomScrapeRequest(BaseModel):
    """Request schema for the advanced custom web scrape API"""
    url: str = Field(..., description="Target URL to scrape")
    instruction: str = Field(..., description="Natural language instruction describing what to extract")
    use_stealth: bool = Field(default=True, description="Use stealth/browser-based scraping for protected sites")
    use_local_llm: bool = Field(default=True, description="Use local Ollama LLM for reasoning")
    max_retries: int = Field(default=3, ge=1, le=5, description="Maximum retry attempts for blocked requests")
    output_format: Literal["json", "csv", "pdf", "both"] = Field(default="json", description="Export format")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/stocks",
                    "instruction": "Extract the top 10 best stocks with their prices and growth percentages",
                    "use_stealth": True,
                    "use_local_llm": True,
                    "max_retries": 3,
                    "output_format": "json"
                }
            ]
        }
    }


class CustomScrapeResultItem(BaseModel):
    """Individual extracted item from custom scrape"""
    rank: Optional[int] = Field(default=None, description="Rank if applicable")
    name: str = Field(..., description="Entity name")
    value: Optional[str] = Field(default=None, description="Primary value or data point")
    reason: Optional[str] = Field(default=None, description="AI reasoning for this result")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional extracted attributes")
    source: str = Field(..., description="Source URL")
    confidence: float = Field(default=0.0, description="Extraction confidence (0-1)")


class CustomScrapeSource(BaseModel):
    """Source metadata for custom scrape"""
    url: str = Field(..., description="Source URL")
    type: str = Field(default="webpage", description="Source type: article, list, table, etc.")
    scrape_method: str = Field(default="unknown", description="Method used: lightweight, stealth, browser")
    bot_protection: bool = Field(default=False, description="Whether bot protection was detected")
    timestamp: str = Field(..., description="ISO-8601 timestamp of scrape")


class CustomScrapeResponse(BaseModel):
    """Response schema for the advanced custom web scrape API"""
    status: str = Field(..., description="Status: success, partial, failed")
    request_id: str = Field(..., description="Unique request identifier")
    query: str = Field(..., description="Original user instruction")
    url: str = Field(..., description="Target URL")
    
    # AI-generated answer to the instruction
    answer: str = Field(default="", description="AI-generated answer to the instruction")
    
    # Extracted results
    results: List[CustomScrapeResultItem] = Field(default_factory=list, description="Extracted entities/items")
    
    # Source tracking
    sources: List[CustomScrapeSource] = Field(default_factory=list, description="Source metadata and provenance")
    
    # Raw extracted content
    extracted_content: str = Field(default="", description="Raw extracted text content")
    
    # Export links
    download_links: Dict[str, str] = Field(default_factory=dict, description="CSV/PDF download links")
    
    # Processing metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing statistics and provenance")


# ============================================================================
# SOURCE INTELLIGENCE API - Source Evaluation & Credibility
# ============================================================================

class SourceIntelligenceRequest(BaseModel):
    """Request schema for evaluating source credibility and reliability"""
    urls: List[str] = Field(..., description="URLs to evaluate for credibility")
    check_bias: bool = Field(default=True, description="Check for potential bias indicators")
    check_credibility: bool = Field(default=True, description="Evaluate source credibility")
    check_freshness: bool = Field(default=True, description="Check content freshness/recency")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "urls": ["https://example.com/article", "https://news.site/report"],
                    "check_bias": True,
                    "check_credibility": True,
                    "check_freshness": True
                }
            ]
        }
    }


class SourceEvaluation(BaseModel):
    """Evaluation result for a single source"""
    url: str
    domain: str
    credibility_score: float = Field(default=0.0, description="0-100 credibility score")
    bias_indicator: str = Field(default="neutral", description="left, center, right, unknown")
    freshness: str = Field(default="unknown", description="fresh, recent, outdated, unknown")
    domain_authority: float = Field(default=0.0, description="Domain authority score")
    ssl_valid: bool = Field(default=False)
    content_type: str = Field(default="unknown")
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class SourceIntelligenceResponse(BaseModel):
    """Response schema for source intelligence API"""
    status: str
    request_id: str
    evaluations: List[SourceEvaluation] = Field(default_factory=list)
    overall_trust_score: float = Field(default=0.0)
    summary: str = Field(default="")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# FACT-CHECK API - Verification & Claim Analysis
# ============================================================================

class FactCheckRequest(BaseModel):
    """Request schema for fact-checking claims"""
    claim: str = Field(..., description="The claim or statement to verify")
    context: Optional[str] = Field(default=None, description="Additional context for the claim")
    source_url: Optional[str] = Field(default=None, description="Source URL where claim was found")
    deep_check: bool = Field(default=True, description="Perform deep web search for verification")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "claim": "Tesla sold 2 million cars in 2025",
                    "context": "From a news article about EV sales",
                    "source_url": "https://example.com/article",
                    "deep_check": True
                }
            ]
        }
    }


class FactCheckEvidence(BaseModel):
    """Evidence supporting or refuting a claim"""
    source_url: str
    source_name: str
    stance: str = Field(description="supports, refutes, neutral, unrelated")
    excerpt: str = Field(default="")
    credibility: float = Field(default=0.0)
    date_published: Optional[str] = None


class FactCheckResponse(BaseModel):
    """Response schema for fact-check API"""
    status: str
    request_id: str
    claim: str
    verdict: str = Field(description="true, false, partially_true, unverified, misleading")
    confidence: float = Field(default=0.0, description="0-100 confidence in verdict")
    explanation: str = Field(default="")
    evidence: List[FactCheckEvidence] = Field(default_factory=list)
    sources_checked: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# KNOWLEDGE BASE API - Knowledge Store & Retrieval
# ============================================================================

class KnowledgeBaseAddRequest(BaseModel):
    """Request to add knowledge to the store"""
    title: str = Field(..., description="Title of the knowledge entry")
    content: str = Field(..., description="Content to store")
    category: str = Field(default="general", description="Category for organization")
    tags: List[str] = Field(default_factory=list, description="Tags for searchability")
    source_url: Optional[str] = Field(default=None, description="Source URL if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Tesla Optimus Robot Specs",
                    "content": "The Optimus robot features...",
                    "category": "technology",
                    "tags": ["robotics", "tesla", "AI"],
                    "source_url": "https://tesla.com/optimus"
                }
            ]
        }
    }


class KnowledgeBaseSearchRequest(BaseModel):
    """Request to search the knowledge base"""
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(default=None, description="Filter by category")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    limit: int = Field(default=10, ge=1, le=50)


class KnowledgeEntry(BaseModel):
    """A single knowledge base entry"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    source_url: Optional[str]
    created_at: str
    relevance_score: float = Field(default=0.0)


class KnowledgeBaseResponse(BaseModel):
    """Response schema for knowledge base operations"""
    status: str
    request_id: str
    operation: str = Field(description="add, search, delete, list")
    entries: List[KnowledgeEntry] = Field(default_factory=list)
    total_count: int = Field(default=0)
    message: str = Field(default="")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# PLANNER API - Task Automation & Research Planning
# ============================================================================



class PlannerRequest(BaseModel):
    """Request to create a research plan"""
    objective: str = Field(..., description="The main research objective")
    constraints: Optional[Union[List[str], str]] = Field(default=None, description="Any constraints or requirements")
    max_steps: int = Field(default=10, ge=1, le=20, description="Maximum number of steps in plan")
    auto_execute: bool = Field(default=False, description="Automatically execute the plan")

    @field_validator('constraints')
    def convert_string_to_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "objective": "Research and compare top 5 AI coding assistants",
                    "constraints": ["Focus on 2025 releases", "Include pricing"],
                    "max_steps": 8,
                    "auto_execute": False
                }
            ]
        }
    }


class PlanStep(BaseModel):
    """A single step in the research plan"""
    step_number: int
    action: str = Field(description="Type: search, scrape, analyze, compare, summarize")
    description: str
    target: Optional[str] = Field(default=None, description="URL or query target")
    status: str = Field(default="pending", description="pending, running, completed, failed")
    output: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None


class PlannerResponse(BaseModel):
    """Response schema for planner API"""
    status: str
    request_id: str
    objective: str
    plan: List[PlanStep] = Field(default_factory=list)
    total_steps: int = Field(default=0)
    completed_steps: int = Field(default=0)
    estimated_time: str = Field(default="")
    execution_status: str = Field(default="planned", description="planned, executing, completed, failed")
    results: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MONITORING API - Change Alerts & Page Watching
# ============================================================================

class MonitoringAddRequest(BaseModel):
    """Request to add a URL for monitoring"""
    url: str = Field(..., description="URL to monitor for changes")
    check_interval: int = Field(default=3600, ge=60, description="Check interval in seconds")
    alert_on: Union[List[str], str] = Field(default=["content_change"], description="Alert triggers: content_change, price_change, new_items, keyword_appear")
    keywords: Optional[Union[List[str], str]] = Field(default=None, description="Keywords to watch for")
    selector: Optional[str] = Field(default=None, description="CSS selector to monitor specific element")

    @field_validator('alert_on', 'keywords')
    def convert_string_to_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/products",
                    "check_interval": 3600,
                    "alert_on": ["price_change", "new_items"],
                    "keywords": ["sale", "discount"],
                    "selector": ".product-list"
                }
            ]
        }
    }


class MonitoringListRequest(BaseModel):
    """Request to list monitored URLs"""
    status: Optional[str] = Field(default=None, description="Filter by status: active, paused, error")
    limit: int = Field(default=20, ge=1, le=100)


class MonitoredUrl(BaseModel):
    """A monitored URL entry"""
    id: str
    url: str
    check_interval: int
    alert_on: List[str]
    keywords: Optional[List[str]]
    selector: Optional[str]
    status: str = Field(default="active")
    last_checked: Optional[str] = None
    last_change: Optional[str] = None
    change_count: int = Field(default=0)
    created_at: str


class ChangeAlert(BaseModel):
    """A change alert notification"""
    id: str
    monitor_id: str
    url: str
    change_type: str
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    detected_at: str
    acknowledged: bool = Field(default=False)


class MonitoringResponse(BaseModel):
    """Response schema for monitoring API"""
    status: str
    request_id: str
    operation: str = Field(description="add, remove, list, alerts, check")
    monitors: List[MonitoredUrl] = Field(default_factory=list)
    alerts: List[ChangeAlert] = Field(default_factory=list)
    total_monitors: int = Field(default=0)
    active_alerts: int = Field(default=0)
    message: str = Field(default="")
    metadata: Dict[str, Any] = Field(default_factory=dict)




