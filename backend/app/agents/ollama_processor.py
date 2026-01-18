"""
Local LLM Processor using Ollama
Supports phi3:mini and llama3.2-vision for offline processing
"""
import json
import asyncio
import subprocess
import time
from typing import Dict, List, Optional
from loguru import logger
import requests

class OllamaProcessor:
    """Process content using local Ollama models"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "phi3:mini"):
        self.base_url = base_url
        self.model = model
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [m["name"] for m in models]
                logger.info(f"Ollama available. Models: {available_models}")
                
                # Check if our model is available
                if any(self.model in m for m in available_models):
                    return True
                else:
                    logger.warning(f"Model {self.model} not found. Available: {available_models}")
                    return False
            return False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            # Try to start Ollama
            self._start_ollama()
            time.sleep(5)  # Wait for Ollama to start
            # Check again
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    available_models = [m["name"] for m in models]
                    if any(self.model in m for m in available_models):
                        logger.info(f"Ollama started successfully. Models: {available_models}")
                        return True
            except:
                pass
            logger.error("Failed to start Ollama")
            return False
    
    def _start_ollama(self):
        """Start Ollama server in background"""
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("Started Ollama serve")
        except Exception as e:
            logger.error(f"Failed to start Ollama: {e}")
    
    async def _generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Increased timeout for complex queries
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama request failed: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return ""
    
    async def process(self, prompt: str) -> str:
        """
        Process a prompt and return plain text response.
        This method matches LLMProcessor interface for compatibility with ResearchChat.
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                # NO format: json - we want plain text for synthesis
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 4096  # Allow longer responses
                }
            }
            
            logger.info(f"[Ollama] Processing prompt ({len(prompt)} chars)")
            
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=180  # Longer timeout for synthesis
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "")
                logger.info(f"[Ollama] Generated response ({len(text)} chars)")
                return text
            else:
                logger.error(f"[Ollama] Request failed: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"[Ollama] Process error: {e}")
            return ""
    
    async def extract_structured_data(self, query: str, content: str, url: str) -> Dict:
        """
        Extract structured data from content based on query
        Returns: {
            "main_entities": [...],
            "links_found": [...],
            "key_data": [...],
            "summary": "..."
        }
        """
        # SMART: Multi-factor content quality check
        try:
            sample = content[:1000]
            
            # 1. Language detection
            non_ascii_ratio = sum(1 for c in sample if ord(c) > 127) / len(sample) if sample else 0
            
            # 2. Noise detection (repeated chars, garbage)
            repeated_chars = max(len(list(g)) for k, g in __import__('itertools').groupby(sample)) if sample else 0
            
            # 3. Meaningful content ratio
            words = len([w for w in sample.split() if len(w) > 2])
            meaningful_ratio = words / len(sample.split()) if sample.split() else 0
            
            if non_ascii_ratio > 0.3:
                logger.warning(f"Non-English content ({non_ascii_ratio:.1%} non-ASCII), skipping Ollama")
                raise ValueError("Non-English content")
            
            if repeated_chars > 20:
                logger.warning(f"Noise detected (repeated chars: {repeated_chars}), skipping Ollama")
                raise ValueError("Low quality content")
            
            if meaningful_ratio < 0.5:
                logger.warning(f"Low meaningful content ({meaningful_ratio:.1%}), skipping Ollama")
                raise ValueError("Low quality content")
                
        except Exception as e:
            if any(keyword in str(e) for keyword in ['Non-English', 'quality']):
                raise
        
        system_prompt = """You are a highly capable data extraction agent.
        Your task is to extract structured information from the provided text completely and accurately.
        Output MUST be pure, valid JSON. No markdown, no explanations, no comments.
        Refuse to answer if the content is completely irrelevant, return empty JSON structures."""
        
        # PRO USE: Adaptive Context Management
        # If content is massive, we assume caller chunked it, but we still protect the context window.
        # phi3 standard context is 4k tokens (~16k chars). Safe limit 12k chars.
        # If content > 12k chars, we perform smart middle-out compression or truncation.
        
        effective_content = content
        if len(content) > 12000:
            logger.info(f"[Ollama] Content too large ({len(content)}), performing smart truncation for context window.")
            effective_content = content[:6000] + "\n...[middle section omitted]...\n" + content[-6000:]
            
        prompt = f"""
        ### GOAL
        Extract specific data based on this query: "{query}"

        ### SOURCE TEXT
        {effective_content}

        ### INSTRUCTIONS
        1. Identify MAIN ENTITIES (companies, products, people) related to the query.
        2. Extract KEY SPECS/DATA (prices, dates, values) with units.
        3. Ignore navigation menus, footers, and ads.
        4. If a value is not found, do not invent it.

        ### OUTPUT FORMAT (JSON ONLY)
        {{
            "main_entities": [
                {{"name": "Exact Name", "type": "Company/Product/etc", "attributes": {{"key": "value"}}}},
            ],
            "key_data": [
                {{"category": "Specifications", "items": [{{"name": "Battery", "value": "5000mAh", "unit": "mAh"}}]}}
            ]
        }}
        """
        
        response = await self._generate(prompt, system_prompt)
        
        try:
            # Clean response
            response = response.strip()
            logger.debug(f"[Ollama] Raw output len={len(response)}: {response[:200]}...")
            
            # Check for garbage/corrupted output
            if any(char in response for char in ['', '\x00', '\ufffd']) or len(response) < 10:
                logger.warning("Corrupted Ollama response detected")
                raise ValueError("Corrupted response")
            
            # 1. Markdown code block extraction
            if "```" in response:
                import re
                code_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
                if code_match:
                    response = code_match.group(1)
            
            # 2. Outer brace extraction (if markdown failed or missing)
            if not response.startswith("{"):
                import re
                brace_match = re.search(r'\{[\s\S]*\}', response)
                if brace_match:
                    response = brace_match.group(0)

            # 3. Strip JS comments (common local LLM artifact)
            import re
            response = re.sub(r'//.*$', '', response, flags=re.MULTILINE)
            
            # 4. Try to fix incomplete JSON by adding closing braces
            response = response.strip()
            if response and not response.endswith("}"):
                # Count braces and add missing ones
                open_braces = response.count("{")
                close_braces = response.count("}")
                if open_braces > close_braces:
                    response += "]" * (response.count("[") - response.count("]"))
                    response += "}" * (open_braces - close_braces)
            
            # Remove any invalid control characters
            response = ''.join(char for char in response if ord(char) >= 32 or char in '\n\r\t')
            
            data = json.loads(response)
            
            # Validate and clean entity data
            if "main_entities" in data:
                cleaned_entities = []
                for entity in data["main_entities"]:
                    if isinstance(entity, dict) and "name" in entity and "type" in entity:
                        # Ensure name and type are valid strings
                        name = str(entity.get("name", "")).strip()
                        entity_type = str(entity.get("type", "")).strip()
                        
                        if name and entity_type and len(name) < 500:  # Sanity check
                            cleaned_entities.append({
                                "name": name,
                                "type": entity_type,
                                "attributes": entity.get("attributes", {})
                            })
                data["main_entities"] = cleaned_entities
            
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama JSON response: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            return {
                "main_entities": [],
                "links_found": [],
                "key_data": [],
                "metadata": {"error": "JSON parsing failed", "partial_response": True}
            }
        except Exception as e:
            logger.warning(f"Ollama extraction error: {e}")
            return {
                "main_entities": [],
                "links_found": [],
                "key_data": [],
                "metadata": {"error": str(e), "fallback_required": True}
            }
    
    async def synthesize_results(self, query: str, extracted_data_list: List[Dict]) -> Dict:
        """
        Synthesize multiple extracted data sources into a final answer
        """
        system_prompt = """Synthesize research findings. Output valid JSON only."""
        
        # Combine all data
        all_entities = []
        all_key_data = []
        
        for data in extracted_data_list:
            all_entities.extend(data.get("main_entities", []))
            all_key_data.extend(data.get("key_data", []))
        
        # Simplified prompt
        prompt = f"""
Query: "{query}"

Found {len(all_entities)} entities and {len(all_key_data)} data points from {len(extracted_data_list)} sources.

Sample entities: {json.dumps(all_entities[:5], indent=2)}

Create answer as JSON:
{{
    "summary": "2-3 sentence direct answer",
    "detailed_answer": "detailed explanation",
    "confidence": "high"
}}

JSON only:
"""
        
        response = await self._generate(prompt, system_prompt)
        
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            data = json.loads(response)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse synthesis JSON: {e}")
            return {
                "summary": f"Processed {len(all_entities)} entities from {len(extracted_data_list)} sources",
                "detailed_answer": "Data collection complete",
                "top_results": [],
                "related_links": [],
                "confidence": "medium"
            }

    async def process(self, prompt: str) -> str:
        """Compatibility method for UnifiedAgent intent classification"""
        return await self._generate(prompt)

    async def synthesize(self, query: str, all_contents: list[str]) -> dict:
        """Compatibility method for ResearchChat synthesis"""
        # Convert list of strings to list of dicts for internal method
        extracted_data_list = []
        for content in all_contents:
            # Quick extraction to feed into synthesis
            try:
                extracted = await self.extract_structured_data(query, content, "")
                extracted_data_list.append(extracted)
            except:
                continue
                
        # Use existing logic
        result = await self.synthesize_results(query, extracted_data_list)
        
        # Map result keys to match LLMProcessor output expected by ResearchChat
        # LLMProcessor returns: {"summary": "...", "structured_data": [...]}
        # Ollama returns: {"summary": "...", "detailed_answer": "...", "confidence": "..."}
        
        # Smart answer extraction (handles model deviations)
        answer_text = result.get("detailed_answer") or result.get("answer") or result.get("summary") or str(result)
        
        mapped_result = {
            "summary": result.get("summary", ""),
            "answer": answer_text,
            "structured_data": result.get("top_results", [])
        }
        
        # Merge dictionary to keep original fields too
        mapped_result.update(result)
        return mapped_result
