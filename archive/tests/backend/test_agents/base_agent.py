from abc import ABC, abstractmethod
import asyncio
import json
from typing import Any, Dict, List
import httpx
from fastapi import UploadFile
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
from google.api_core import retry
from itertools import cycle

# Load environment variables
load_dotenv()

class TestAgent(ABC):
    """Base class for all test agents"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
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
        
        # Initialize with flash 2.0 lite model
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
    
    async def analyze_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Analyze API response using Gemini"""
        prompt = f"""
        Analyze this API response and provide insights:
        Status Code: {response.status_code}
        Response Body: {response.text}
        
        Return a JSON with:
        - is_success: boolean
        - issues: list of potential issues
        - suggestions: list of improvements
        """
        try:
            analysis = await self.think(prompt)
            return json.loads(analysis)
        except json.JSONDecodeError:
            return {
                "is_success": False,
                "issues": ["Failed to parse Gemini API response"],
                "suggestions": ["Check Gemini API status and retry"]
            }
    
    @abstractmethod
    async def run_tests(self) -> Dict[str, Any]:
        """Run agent's test suite"""
        pass
    
    async def report_results(self, results: Dict[str, Any]) -> str:
        """Generate a detailed test report"""
        prompt = f"""
        Generate a detailed test report from these results:
        {json.dumps(results, indent=2)}
        
        Include:
        1. Overall test status
        2. Key findings
        3. Recommendations
        4. Next steps
        """
        try:
            return await self.think(prompt)
        except Exception as e:
            return f"Error generating report: {str(e)}"
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose() 