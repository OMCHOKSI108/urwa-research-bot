import os
import json
import asyncio
from google import genai
from google.genai import types
from groq import Groq
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class LLMProcessor:
    def __init__(self):
        load_dotenv(override=True) # Force reload of env vars
        
        # Primary: Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=gemini_key)
        
        # Fallback: Groq
        groq_key = os.getenv("GROQ_API_KEY")
        logger.info(f"LLMProcessor Init - Groq Key configured: {bool(groq_key)}")
        
        self.groq_client = None
        if groq_key:
            self.groq_client = Groq(api_key=groq_key)

    async def _call_gemini(self, prompt: str, model: str = 'gemini-2.5-flash') -> dict:
        response = await asyncio.to_thread(
            self.gemini_client.models.generate_content,
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        return json.loads(response.text)

    async def _call_groq(self, prompt: str) -> dict:
        if not self.groq_client:
            raise ValueError("Groq API Key not configured")

        completion = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that outputs strictly valid JSON."},
                {"role": "user", "content": prompt + "\n\nRESPONSE MUST BE VALID JSON ONLY. NO MARKDOWN. NO CODE BLOCKS."} 
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        raw_content = completion.choices[0].message.content
        # Clean markdown code blocks if present
        if "```" in raw_content:
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
            
        return json.loads(raw_content)

    async def _call_groq_text(self, prompt: str) -> str:
        """Call Groq and return plain text (not JSON)."""
        if not self.groq_client:
            raise ValueError("Groq API Key not configured")

        completion = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful research analyst. Provide detailed, accurate answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return completion.choices[0].message.content

    async def _call_gemini_text(self, prompt: str, model: str = 'gemini-2.5-flash') -> str:
        """Call Gemini and return plain text."""
        response = await asyncio.to_thread(
            self.gemini_client.models.generate_content,
            model=model,
            contents=prompt
        )
        return response.text

    async def process(self, prompt: str) -> str:
        """Process a prompt and return plain text answer. Used by ResearchChat."""
        try:
            # Try Gemini first
            return await self._call_gemini_text(prompt)
        except Exception as e:
            logger.warning(f"Gemini process failed: {e}. Trying Groq...")
            
            # Fallback to Groq
            if self.groq_client:
                try:
                    return await self._call_groq_text(prompt)
                except Exception as groq_e:
                    logger.error(f"Groq process failed: {groq_e}")
            
            raise ValueError("All LLM providers failed")

    async def decide_action(self, query: str, markdown_content: str, current_url: str) -> dict:
        prompt = f"""
        You are a Deep Research Agent.
        User Goal: "{query}"
        Current Page URL: "{current_url}"
        
        Content Preview (First 15k chars):
        {markdown_content[:15000]}

        Analyze the content. Does it contain the *actual data* requested (e.g., specific prices, GPAs, exact numbers), 
        OR is it a navigation page (e.g., list of departments, list of product categories) containing LINKS to the data?

        Response Strategy:
        - If you see the Final Data: Set "action" to "extract".
        - If you see LINKS to the data: Set "action" to "crawl" and provide the top 3-5 most relevant full URLs.
        
        JSON Response Format:
        {{
            "action": "extract" | "crawl",
            "reasoning": "Why you chose this action",
            "links_to_crawl": ["https://...", "https://..."] (Only if action is crawl. Max 5. MUST be absolute URLs),
            "final_data": [] (Only if action is extract)
        }}
        """
        
        try:
            return await self._call_gemini(prompt)
        except Exception as e:
            logger.warning(f"Gemini Decision failed: {e}. Trying Groq fallback...")
            
            # Fallback to Groq
            if self.groq_client:
                try:
                    return await self._call_groq(prompt)
                except Exception as groq_e:
                    logger.error(f"Groq Decision failed: {groq_e}")
            
            return {"action": "extract", "final_data": []}

    async def synthesize(self, query: str, all_contents: list[str]) -> dict:
        # Limited context for speed and consistency
        combined_text = "\n\n---\n\n".join([c[:10000] for c in all_contents])
        
        prompt = f"""
        You are an expert Data Aggregator.
        User Query: "{query}"
        
        Scraped Data:
        {combined_text}
        
        Task:
        1. Extract all relevant data points.
        2. Format as valid JSON using the schema below.
        
        JSON Response Format:
        {{
            "summary": "Comprehensive text summary...",
            "structured_data": [
                {{ "category": "...", "item": "...", "value": "..." }}
            ]
        }}
        """
        
        try:
            return await self._call_gemini(prompt)
        except Exception as e:
            logger.warning(f"Gemini Synthesis failed: {e}. Trying Groq fallback...")
            
            if self.groq_client:
                try:
                    return await self._call_groq(prompt)
                except Exception as groq_e:
                    logger.error(f"Groq Synthesis failed: {groq_e}")
            else:
                 logger.error("Groq fallback skipped: No API Key configured.")
            
            # Return offline fallback if everything fails
            logger.error("All AI Models Failed. Engaging Offline Fallback.")
            return self._offline_fallback(all_contents)

    def _offline_fallback(self, contents: list[str]) -> dict:
        """
        Pure Python fallback when AI APIs are down.
        Extracts headers and creates a preview summary.
        """
        full_text = "\n".join(contents)
        
        # 1. Creation of a Manual Summary
        summary = "### ⚠️ AI Processing Unavailable - Showing Offline Analysis\n\n"
        summary += "**Raw Content Preview:**\n\n"
        clean_preview = " ".join(full_text.split())[:1500] 
        summary += f">{clean_preview}..."
        
        # 2. Offline 'Entity' Extraction using Regex
        structured_data = []
        import re
        
        # Extract headers (H1-H3) as 'Key Topics'
        headers = re.findall(r'^#{1,3}\s+(.+)$', full_text, re.MULTILINE)
        
        # Extract potential links or references
        links = re.findall(r'\[([^\]]+)\]\((http[^)]+)\)', full_text)
        
        for h in headers[:10]:
            structured_data.append({
                "category": "Key Topic",
                "item": h.strip(),
                "value": "Extracted from Page Structure"
            })
            
        for text, link in links[:5]:
             structured_data.append({
                "category": "Reference",
                "item": text[:30],
                "value": link
            })
            
        if not structured_data:
            structured_data.append({"category": "System", "item": "No Data", "value": "Could not parse structure"})

        return {
            "summary": summary,
            "structured_data": structured_data
        }
