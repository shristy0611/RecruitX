from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
from .base_agent import TestAgent
import asyncio
import aiofiles
import os
from pathlib import Path
import hashlib
import aiofiles.os

class MatchingAgent(TestAgent):
    """Agent specialized in testing matching capabilities"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_dir = Path("tests/backend/test_agents/cache")
        self.cache_ttl = 3600  # 1 hour cache TTL
        
    async def ensure_cache_dir(self):
        """Ensure cache directory exists"""
        if not await aiofiles.os.path.exists(self.cache_dir):
            await aiofiles.os.makedirs(self.cache_dir)
            
    def get_cache_key(self, data: str) -> str:
        """Generate cache key from input data"""
        return hashlib.sha256(data.encode()).hexdigest()
        
    async def get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result if available and not expired"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if await aiofiles.os.path.exists(cache_file):
                async with aiofiles.open(cache_file, 'r') as f:
                    cached = json.loads(await f.read())
                    if datetime.fromisoformat(cached['timestamp']) + timedelta(seconds=self.cache_ttl) > datetime.now():
                        return cached['result']
        except Exception:
            pass
        return None
        
    async def cache_result(self, cache_key: str, result: Dict):
        """Cache result with timestamp"""
        try:
            await self.ensure_cache_dir()
            cache_file = self.cache_dir / f"{cache_key}.json"
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'result': result
                }))
        except Exception:
            pass

    async def test_match(self, resume: str, job_desc: str) -> Dict[str, Any]:
        """Test matching between resume and job description with caching and retry logic"""
        cache_key = self.get_cache_key(f"{resume}:{job_desc}")
        
        # Try to get cached result first
        cached = await self.get_cached_result(cache_key)
        if cached:
            return {**cached, 'cached': True}
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Send matching request with properly formatted JSON data
                response = await self.client.post(
                    "/match",
                    json={
                        "resume_data": {"text": resume},
                        "job_data": {"text": job_desc}
                    }
                )
                
                # Analyze response
                analysis = await self.analyze_response(response)
                
                # Use Gemini to verify match quality
                prompt = f"""
                Analyze this match between resume and job description:
                Resume: {resume}
                Job Description: {job_desc}
                API Response: {response.text}
                
                Return a JSON with:
                - match_quality: number (0-100)
                - key_matches: list of matched skills/requirements
                - missing_requirements: list of unmet requirements
                - false_positives: list of incorrectly matched items
                - confidence_score: number (0-100)
                """
                
                verification = await self.think(prompt)
                result = {
                    "status_code": response.status_code,
                    "analysis": analysis,
                    "verification": json.loads(verification),
                    "cached": False
                }
                
                # Cache successful result
                await self.cache_result(cache_key, result)
                return result
                
            except Exception as e:
                if attempt == max_retries - 1:
                    return {
                        "status_code": getattr(e, 'status_code', 500),
                        "error": str(e),
                        "analysis": {
                            "is_success": False,
                            "issues": [f"Failed to process match: {str(e)}"],
                            "suggestions": ["Check server logs for details"]
                        },
                        "cached": False
                    }
                await asyncio.sleep(1 * (2 ** attempt))

    async def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases in matching"""
        test_cases = [
            {
                "name": "empty_inputs",
                "resume": "",
                "job_desc": ""
            },
            {
                "name": "long_inputs",
                "resume": "Python " * 1000,
                "job_desc": "Java " * 1000
            },
            {
                "name": "special_chars",
                "resume": "Python & Java (2+ years) - SQL; NoSQL",
                "job_desc": "Required: Python/Java & SQL Database {NoSQL preferred}"
            },
            {
                "name": "exact_match",
                "resume": "5 years Python experience",
                "job_desc": "5 years Python experience required"
            },
            {
                "name": "no_overlap",
                "resume": "Expert in Ruby and PHP",
                "job_desc": "Looking for Python and Java developer"
            }
        ]
        
        results = []
        for case in test_cases:
            result = await self.test_match(case["resume"], case["job_desc"])
            results.append({"case": case["name"], "result": result})
            
        return {"edge_case_tests": results}

    async def test_skill_variations(self) -> Dict[str, Any]:
        """Test matching with different skill variations"""
        skill_variations = [
            {
                "name": "different_versions",
                "resume": "Python 3.8, Java 11",
                "job_desc": "Python (any version), Java 8+"
            },
            {
                "name": "skill_levels",
                "resume": "Expert in Python, Intermediate Java",
                "job_desc": "Advanced Python, Basic Java knowledge"
            },
            {
                "name": "alternative_names",
                "resume": "JS, py, postgres",
                "job_desc": "JavaScript, Python, PostgreSQL"
            },
            {
                "name": "skill_combinations",
                "resume": "Full Stack: React/Node.js/MongoDB",
                "job_desc": "MERN Stack Developer needed"
            }
        ]
        
        results = []
        for case in skill_variations:
            result = await self.test_match(case["resume"], case["job_desc"])
            results.append({"case": case["name"], "result": result})
            
        return {"skill_variation_tests": results}

    async def run_tests(self) -> Dict[str, Any]:
        """Run all matching tests"""
        results = {
            "agent_type": "MatchingAgent",
            "timestamp": str(datetime.now()),
            "tests": {}
        }
        
        try:
            # Test basic matching
            basic_tests = [
                {
                    "resume": "Experienced Python developer with 5 years of experience in web development using Django and Flask. Strong SQL skills.",
                    "job_desc": "Looking for a Python developer with Django experience and database knowledge."
                },
                {
                    "resume": "Java developer with Spring Boot experience. Knowledge of microservices and Docker.",
                    "job_desc": "Senior Java developer needed. Must know Spring and containerization."
                }
            ]
            
            basic_results = []
            for test in basic_tests:
                result = await self.test_match(test["resume"], test["job_desc"])
                basic_results.append(result)
            results["tests"]["basic_matching"] = basic_results
            
            # Test edge cases
            results["tests"]["edge_cases"] = await self.test_edge_cases()
            
            # Test skill variations
            results["tests"]["skill_variations"] = await self.test_skill_variations()
            
            # Generate cognitive analysis of all results
            try:
                results["analysis"] = await self.think(f"""
                Analyze these matching test results and provide insights:
                {json.dumps(results, indent=2)}
                
                Focus on:
                1. Overall matching accuracy
                2. Edge case handling
                3. Skill variation handling
                4. False positive/negative rates
                5. Performance metrics
                6. Cache effectiveness
                7. API reliability
                
                Return a JSON with your analysis.
                """)
            except Exception as e:
                results["analysis_error"] = str(e)
            
        except Exception as e:
            results["error"] = str(e)
        
        return results 