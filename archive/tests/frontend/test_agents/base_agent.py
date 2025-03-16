from abc import ABC, abstractmethod
import asyncio
import json
from typing import Any, Dict, List
import httpx
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
from google.api_core import retry
from itertools import cycle
from pathlib import Path
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

class FrontendTestAgent(ABC):
    """Base class for all frontend test agents"""
    
    def __init__(self, base_url: str = "http://localhost:5173"):
        self.base_url = base_url
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.http_client = httpx.AsyncClient(base_url=self.api_url)
        self.api_keys = self._load_api_keys()
        self.key_iterator = cycle(self.api_keys)
        self.gemini_model = self._init_gemini()
        self.retry_delay = 1  # Initial delay in seconds
        self.max_retries = 3
        self.request_count = 0
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds
        
    def _load_api_keys(self) -> List[str]:
        """Load all available Gemini API keys"""
        keys = []
        for i in range(1, 11):  # Check for 10 possible API keys
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                keys.append(key)
        if not keys:
            raise ValueError("No Gemini API keys found in environment variables")
        return keys
    
    def _init_gemini(self):
        """Initialize Gemini model for agent's cognitive abilities"""
        api_key = next(self.key_iterator)
        genai.configure(api_key=api_key)
        
        # Initialize with Gemini 1.5 flash model
        model = genai.GenerativeModel('gemini-1.5-flash-002',
                                    generation_config={
                                        'temperature': 0.1,
                                        'top_p': 0.8,
                                        'top_k': 40,
                                        'max_output_tokens': 2048,
                                    })
        return model
    
    async def _rotate_api_key(self):
        """Rotate to next API key when rate limit is hit"""
        api_key = next(self.key_iterator)
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash-002',
                                                generation_config={
                                                    'temperature': 0.1,
                                                    'top_p': 0.8,
                                                    'top_k': 40,
                                                    'max_output_tokens': 2048,
                                                })
        
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
        self.request_count += 1
    
    @retry.Retry(
        initial=1.0,
        maximum=60.0,
        multiplier=2.0,
        predicate=retry.if_exception_type(Exception)
    )
    async def think(self, prompt: str, retries: int = 0) -> str:
        """Agent's cognitive function using Gemini with retry logic"""
        try:
            await self._rate_limit()
            
            response = await asyncio.to_thread(
                lambda: self.gemini_model.generate_content(
                    prompt,
                    safety_settings=[
                        {
                            "category": "HARM_CATEGORY_DANGEROUS",
                            "threshold": "BLOCK_NONE"
                        }
                    ]
                ).text
            )
            
            # Clean up markdown-formatted JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            return response.strip()
            
        except Exception as e:
            if "429" in str(e):
                if retries < len(self.api_keys):
                    await self._rotate_api_key()
                    await asyncio.sleep(self.retry_delay * (2 ** retries))
                    return await self.think(prompt, retries + 1)
                else:
                    raise ValueError("All API keys exhausted")
            raise
    
    async def analyze_ui(self, page_html: str, screenshot_path: str = None) -> Dict[str, Any]:
        """Analyze UI using Gemini"""
        prompt = f"""
        Analyze this webpage UI and provide insights:
        HTML: {page_html[:10000]}  # Limiting to 10000 chars to avoid token limits
        
        Return a JSON with:
        - is_rendered_properly: boolean
        - ui_issues: list of potential UI issues
        - accessibility_issues: list of potential accessibility issues
        - suggestions: list of UI improvements
        """
        
        try:
            analysis = await self.think(prompt)
            return json.loads(analysis)
        except json.JSONDecodeError:
            return {
                "is_rendered_properly": False,
                "ui_issues": ["Failed to parse Gemini API response"],
                "accessibility_issues": ["Unknown"],
                "suggestions": ["Check Gemini API status and retry"]
            }
    
    async def analyze_network_requests(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network requests using Gemini"""
        prompt = f"""
        Analyze these network requests and provide insights:
        Requests: {json.dumps(requests, indent=2)}
        
        Return a JSON with:
        - performance_issues: list of potential performance issues
        - security_issues: list of potential security concerns
        - suggestions: list of improvements
        """
        
        try:
            analysis = await self.think(prompt)
            return json.loads(analysis)
        except json.JSONDecodeError:
            return {
                "performance_issues": ["Failed to parse Gemini API response"],
                "security_issues": ["Unknown"],
                "suggestions": ["Check Gemini API status and retry"]
            }
    
    @abstractmethod
    async def run_tests(self) -> Dict[str, Any]:
        """Run agent's test suite"""
        pass
    
    async def report_results(self, results: Dict[str, Any]) -> str:
        """Generate a detailed test report"""
        prompt = f"""
        Generate a detailed frontend test report from these results:
        {json.dumps(results, indent=2)}
        
        Include:
        1. Overall UI status
        2. Component functionality assessment
        3. Performance metrics
        4. User experience evaluation
        5. Accessibility assessment
        6. Key findings
        7. Recommendations
        8. Next steps
        """
        try:
            return await self.think(prompt)
        except Exception as e:
            return f"Error generating report: {str(e)}"
    
    async def close(self):
        """Cleanup resources"""
        await self.http_client.aclose() 