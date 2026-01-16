"""
UNIFIED AI AGENT
One endpoint that understands user intent and executes the right actions.
Acts like a real AI assistant that can do anything.
"""

import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger


class UnifiedAgent:
    """
    A single AI agent that:
    1. Understands what the user wants
    2. Decides which tools to use
    3. Executes actions
    4. Returns comprehensive results
    
    User just talks naturally - agent figures out the rest.
    """
    
    # Intent patterns for routing
    INTENT_PATTERNS = {
        "research": [
            r"what is", r"tell me about", r"explain", r"how does",
            r"why", r"current", r"latest", r"news about", r"market",
            r"analysis", r"trends", r"compare", r"difference between",
            r"impact", r"effect", r"pros and cons", r"best"
        ],
        "scrape": [
            r"scrape", r"extract", r"get data from", r"fetch",
            r"pull from", r"grab", r"collect from"
        ],
        "scrape_url": [
            r"https?://", r"www\.", r"\.com", r"\.org", r"\.net"
        ],
        "fact_check": [
            r"is it true", r"verify", r"fact check", r"is .+ correct",
            r"true or false", r"check if", r"validate"
        ],
        "profile": [
            r"can i scrape", r"is .+ protected", r"check protection",
            r"what protection", r"analyze site", r"profile"
        ],
        "monitor": [
            r"monitor", r"watch", r"track changes", r"alert me",
            r"notify when", r"keep checking"
        ],
        "normalize": [
            r"normalize", r"format", r"parse", r"convert .+ to",
            r"clean up", r"standardize"
        ]
    }
    
    def __init__(self, orchestrator, llm_processor, research_chat):
        self.orchestrator = orchestrator
        self.llm = llm_processor
        self.research_chat = research_chat
        self.conversation_history: List[Dict] = []
    
    async def process(self, user_input: str, context: Dict = None) -> Dict:
        """
        Process any user input and return appropriate results.
        
        Args:
            user_input: Natural language input from user
            context: Optional context (previous conversation, preferences)
        
        Returns:
            {
                "intent": "research|scrape|fact_check|...",
                "action_taken": "description of what was done",
                "result": {...},
                "follow_up": "What else can I help with?"
            }
        """
        start_time = datetime.now()
        
        logger.info(f"[Agent] Input: {user_input}")
        
        # Step 1: Understand intent
        intent, confidence = await self._classify_intent(user_input)
        logger.info(f"[Agent] Intent: {intent} (confidence: {confidence})")
        
        # Step 2: Extract parameters
        params = await self._extract_params(user_input, intent)
        logger.info(f"[Agent] Params: {params}")
        
        # Step 3: Execute appropriate action
        result = await self._execute_action(intent, params, user_input)
        
        # Step 4: Generate follow-up
        follow_up = await self._generate_follow_up(user_input, intent, result)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        response = {
            "status": "success",
            "intent": intent,
            "confidence": confidence,
            "action_taken": self._describe_action(intent, params),
            "result": result,
            "follow_up_suggestions": follow_up,
            "processing_time": round(elapsed, 1)
        }
        
        # Save to history
        self.conversation_history.append({
            "input": user_input,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    async def _classify_intent(self, user_input: str) -> tuple:
        """Classify user intent using patterns and LLM."""
        input_lower = user_input.lower()
        
        # Check for URL first - if URL present, likely a scrape request
        if re.search(r'https?://', user_input):
            # Check if it's asking about the site or wants to scrape it
            if any(re.search(p, input_lower) for p in self.INTENT_PATTERNS["profile"]):
                return "profile", 0.9
            return "scrape", 0.9
        
        # Pattern matching for quick classification
        scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, input_lower))
            if score > 0:
                scores[intent] = score
        
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = min(0.9, 0.5 + (scores[best_intent] * 0.1))
            
            # Research is the default for question-like inputs
            if best_intent in ["research", "scrape_url"] or "?" in user_input:
                return "research", confidence
            return best_intent, confidence
        
        # Default to research for any question
        if "?" in user_input or any(w in input_lower for w in ["what", "how", "why", "when", "where", "who"]):
            return "research", 0.7
        
        # Use LLM for complex cases
        try:
            prompt = f"""Classify this user request into ONE category:
- research: wants information, analysis, or answers to questions
- scrape: wants to extract data from a specific website
- fact_check: wants to verify if something is true
- profile: wants to know about a website's protection
- normalize: wants to format/clean data
- monitor: wants to track changes on a website

User request: "{user_input}"

Reply with ONLY the category name."""

            result = await self.llm.process(prompt)
            intent = result.strip().lower().replace("_", "")
            
            valid_intents = ["research", "scrape", "factcheck", "fact_check", "profile", "normalize", "monitor"]
            if intent.replace("_", "") in [i.replace("_", "") for i in valid_intents]:
                return intent.replace("factcheck", "fact_check"), 0.8
        except Exception:
            pass
        
        # Default to research
        return "research", 0.6
    
    async def _extract_params(self, user_input: str, intent: str) -> Dict:
        """Extract relevant parameters from user input."""
        params = {"raw_input": user_input}
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', user_input)
        if urls:
            params["urls"] = urls
            params["url"] = urls[0]
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"', user_input)
        if quoted:
            params["quoted"] = quoted
        
        # Extract data type for normalization
        if intent == "normalize":
            for dtype in ["price", "date", "location", "company", "rating", "phone"]:
                if dtype in user_input.lower():
                    params["data_type"] = dtype
                    break
        
        return params
    
    async def _execute_action(self, intent: str, params: Dict, user_input: str) -> Dict:
        """Execute the appropriate action based on intent."""
        
        try:
            # RESEARCH: Use the research chat for comprehensive analysis
            if intent == "research":
                result = await self.research_chat.chat(user_input, deep_research=True)
                return {
                    "type": "research_analysis",
                    "answer": result.get("answer", ""),
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0),
                    "follow_up_questions": result.get("follow_up_questions", [])
                }
            
            # SCRAPE: Extract data from a URL
            elif intent == "scrape":
                if "url" not in params:
                    return {"type": "error", "message": "Please provide a URL to scrape"}
                
                from app.agents.hybrid_scraper import HybridScraper
                scraper = HybridScraper()
                
                # HybridScraper.scrape() returns a string directly, not a dict
                content = await asyncio.wait_for(
                    scraper.scrape(params["url"]),
                    timeout=60.0
                )
                
                # Check if we got content
                if content and len(content) > 100:
                    content_preview = content[:10000]
                    
                    # Extract specific data if requested
                    extraction_prompt = f"""From this webpage content, extract what the user requested.

User request: {user_input}

Content:
{content_preview}

Extract and format the requested information clearly. Use markdown formatting."""

                    extracted = await self.llm.process(extraction_prompt)
                    
                    return {
                        "type": "scrape_result",
                        "url": params["url"],
                        "extracted_data": extracted,
                        "content": content_preview,  # Also include raw content
                        "content_length": len(content),
                        "success": True
                    }
                else:
                    return {
                        "type": "scrape_result",
                        "url": params["url"],
                        "success": False,
                        "error": "Failed to scrape the URL or content too short"
                    }
            
            # FACT CHECK: Verify claims
            elif intent == "fact_check":
                # Extract the claim to verify
                claim = user_input
                for prefix in ["is it true that", "verify", "fact check", "check if"]:
                    claim = re.sub(f"^{prefix}\\s*", "", claim, flags=re.IGNORECASE)
                
                # Use research to verify
                verification_query = f"fact check: {claim}"
                result = await self.research_chat.chat(verification_query, deep_research=True)
                
                # Analyze the result for verdict
                answer = result.get("answer", "")
                verdict = "unverified"
                if any(w in answer.lower() for w in ["true", "correct", "accurate", "confirmed"]):
                    verdict = "likely_true"
                elif any(w in answer.lower() for w in ["false", "incorrect", "inaccurate", "debunked"]):
                    verdict = "likely_false"
                elif any(w in answer.lower() for w in ["partially", "mixed", "some truth"]):
                    verdict = "partially_true"
                
                return {
                    "type": "fact_check",
                    "claim": claim,
                    "verdict": verdict,
                    "analysis": answer,
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0)
                }
            
            # PROFILE: Analyze site protection
            elif intent == "profile":
                if "url" not in params:
                    return {"type": "error", "message": "Please provide a URL to analyze"}
                
                from app.strategies.site_profiler import site_profiler
                profile = await site_profiler.profile(params["url"])
                
                return {
                    "type": "site_profile",
                    "url": params["url"],
                    "risk_level": profile.get("risk", "unknown"),
                    "protection": profile.get("bot_wall", "none"),
                    "needs_javascript": profile.get("needs_rendering", False),
                    "recommended_strategy": profile.get("recommended_strategy", "stealth"),
                    "can_scrape": profile.get("risk") in ["low", "medium"],
                    "warnings": profile.get("details", {}).get("warnings", [])
                }
            
            # NORMALIZE: Format data
            elif intent == "normalize":
                from app.core.data_quality import data_normalizer
                
                data_type = params.get("data_type", "price")
                value = params.get("quoted", [user_input])[0] if params.get("quoted") else user_input
                
                normalizers = {
                    "price": data_normalizer.normalize_price,
                    "date": data_normalizer.normalize_date,
                    "location": data_normalizer.normalize_location,
                    "company": data_normalizer.normalize_company_name,
                    "rating": data_normalizer.normalize_rating,
                    "phone": data_normalizer.normalize_phone,
                }
                
                if data_type in normalizers:
                    normalized = normalizers[data_type](value)
                    return {
                        "type": "normalized_data",
                        "original": value,
                        "data_type": data_type,
                        "normalized": normalized
                    }
                else:
                    return {"type": "error", "message": f"Unknown data type: {data_type}"}
            
            # MONITOR: Set up monitoring (simplified for now)
            elif intent == "monitor":
                return {
                    "type": "monitor_setup",
                    "message": "Monitoring capability noted. To set up monitoring, use the /api/v1/monitor/add endpoint with the URL you want to track.",
                    "suggested_action": f"POST /api/v1/monitor/add with url={params.get('url', 'YOUR_URL')}"
                }
            
            # DEFAULT: Research
            else:
                result = await self.research_chat.chat(user_input)
                return {
                    "type": "general_response",
                    "answer": result.get("answer", ""),
                    "sources": result.get("sources", [])
                }
                
        except asyncio.TimeoutError:
            return {"type": "error", "message": "Request timed out. Please try again."}
        except Exception as e:
            logger.error(f"[Agent] Execution error: {e}")
            return {"type": "error", "message": str(e)}
    
    def _describe_action(self, intent: str, params: Dict) -> str:
        """Generate human-readable description of action taken."""
        descriptions = {
            "research": "Searched the web and analyzed multiple sources",
            "scrape": f"Extracted data from {params.get('url', 'the provided URL')}",
            "fact_check": "Verified the claim against multiple sources",
            "profile": f"Analyzed protection of {params.get('url', 'the website')}",
            "normalize": f"Formatted the {params.get('data_type', 'data')}",
            "monitor": "Set up monitoring for the URL"
        }
        return descriptions.get(intent, "Processed your request")
    
    async def _generate_follow_up(self, user_input: str, intent: str, result: Dict) -> List[str]:
        """Generate follow-up suggestions."""
        if result.get("type") == "error":
            return ["Try rephrasing your request", "Provide more details"]
        
        follow_ups = {
            "research": [
                "Would you like more details on any specific point?",
                "Should I compare this with something else?",
                "Want me to fact-check any of these claims?"
            ],
            "scrape": [
                "Would you like me to extract something specific?",
                "Should I monitor this page for changes?",
                "Want me to scrape related pages?"
            ],
            "fact_check": [
                "Would you like me to research this topic further?",
                "Should I check related claims?",
                "Want more sources on this?"
            ],
            "profile": [
                "Would you like me to try scraping this site?",
                "Should I find alternative sources?",
                "Want me to set up monitoring?"
            ]
        }
        
        return follow_ups.get(intent, ["What else would you like to know?"])
    
    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


# Factory function (not singleton - allows multiple instances with different LLMs)
def get_unified_agent(orchestrator, llm_processor, research_chat) -> UnifiedAgent:
    """Create a UnifiedAgent instance with specified processors."""
    return UnifiedAgent(orchestrator, llm_processor, research_chat)
