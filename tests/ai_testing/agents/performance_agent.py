"""
Performance testing agent that specializes in evaluating system performance using AI-powered decision making.
"""

import os
import json
import time
import asyncio
import statistics
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from tests.ai_testing.agents.base_agent import BaseAgent
from tests.ai_testing.agents.api_agent import APIAgent
from tests.ai_testing.config import settings

class PerformanceAgent(BaseAgent):
    """Agent specialized in performance testing using AI-powered decision making."""
    
    def __init__(self, name: str = "PerformanceAgent", model_type: str = settings.AGENT_TYPE):
        super().__init__(name, model_type)
        self.api_agent = None
        self.performance_metrics = {
            "frontend": {},
            "backend": {},
            "system": {}
        }
        self.test_scenarios = []
        self.test_results = []
    
    async def setup(self):
        """Setup the performance agent and its dependencies."""
        await super().setup()
        if self.api_agent is None:
            self.api_agent = APIAgent(name=f"{self.name}-APIHelper", model_type=self.model_type)
            await self.api_agent.setup()
    
    async def close(self):
        """Close all resources."""
        if self.api_agent:
            await self.api_agent.close()
        await super().close()
    
    async def measure_api_response_time(self, method: str, endpoint: str, 
                                       data: Any = None, iterations: int = 5) -> Dict[str, Any]:
        """
        Measure API response time over multiple iterations.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            iterations: Number of iterations to run
            
        Returns:
            Dict with response time statistics
        """
        await self.setup()
        
        self.logger.info(f"Measuring response time for {method} {endpoint} over {iterations} iterations")
        
        response_times = []
        success_count = 0
        error_count = 0
        status_codes = {}
        
        for i in range(iterations):
            self.logger.info(f"Iteration {i+1}/{iterations}")
            
            try:
                if method.upper() in ["GET", "DELETE", "HEAD"]:
                    result = await self.api_agent.make_request(method, endpoint, params=data)
                else:
                    result = await self.api_agent.make_request(method, endpoint, data=data)
                
                response_times.append(result["duration_ms"])
                
                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1
                
                status_code = result.get("response", {}).get("status", 0)
                status_codes[status_code] = status_codes.get(status_code, 0) + 1
                
                # Add a small delay to avoid overloading the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error during iteration {i+1}: {str(e)}")
                error_count += 1
        
        # Calculate statistics
        metrics = {}
        
        if response_times:
            metrics = {
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "mean_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "p95_ms": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) >= 20 else None,
                "p99_ms": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) >= 100 else None,
                "std_dev_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        
        # Record the results
        result = {
            "method": method,
            "endpoint": endpoint,
            "iterations": iterations,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count / iterations) * 100 if iterations > 0 else 0,
            "status_codes": status_codes,
            "response_times": response_times,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in performance metrics
        endpoint_key = f"{method}:{endpoint}"
        self.performance_metrics["backend"][endpoint_key] = result
        
        return result
    
    async def measure_page_load_time(self, url: str, iterations: int = 3) -> Dict[str, Any]:
        """
        Measure page load time for a frontend URL.
        
        Args:
            url: URL to test
            iterations: Number of iterations to run
            
        Returns:
            Dict with page load metrics
        """
        await self.setup()
        
        self.logger.info(f"Measuring page load time for {url} over {iterations} iterations")
        
        load_times = []
        success_count = 0
        error_count = 0
        
        for i in range(iterations):
            self.logger.info(f"Iteration {i+1}/{iterations}")
            
            try:
                # Create a new page for each test
                page = await self.browser.new_page()
                
                # Measure page load time
                start_time = time.time()
                
                # Navigate to the URL and wait for network idle
                response = await page.goto(url, wait_until="networkidle")
                
                # Wait for the page to be fully loaded
                await page.wait_for_load_state("networkidle")
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                load_times.append(duration_ms)
                
                if response and response.ok:
                    success_count += 1
                else:
                    error_count += 1
                
                # Take a screenshot
                screenshot_path = os.path.join(settings.RESULTS_DIR, "screenshots", f"load_time_{i+1}_{int(time.time())}.png")
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                await page.screenshot(path=screenshot_path)
                
                # Close the page
                await page.close()
                
                # Add a small delay between iterations
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error during iteration {i+1}: {str(e)}")
                error_count += 1
        
        # Calculate statistics
        metrics = {}
        
        if load_times:
            metrics = {
                "min_ms": min(load_times),
                "max_ms": max(load_times),
                "mean_ms": statistics.mean(load_times),
                "median_ms": statistics.median(load_times),
                "p95_ms": sorted(load_times)[int(len(load_times) * 0.95)] if len(load_times) >= 20 else None,
                "std_dev_ms": statistics.stdev(load_times) if len(load_times) > 1 else 0
            }
        
        # Record the results
        url_key = url.replace(settings.FRONTEND_URL, "").strip("/") or "homepage"
        result = {
            "url": url,
            "url_key": url_key,
            "iterations": iterations,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count / iterations) * 100 if iterations > 0 else 0,
            "load_times": load_times,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in performance metrics
        self.performance_metrics["frontend"][url_key] = result
        
        return result
    
    async def analyze_performance_bottlenecks(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze performance metrics to identify bottlenecks using AI.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Dict with analysis results
        """
        await self.setup()
        
        # Prepare the metrics summary for the prompt
        frontend_metrics = metrics.get("frontend", {})
        backend_metrics = metrics.get("backend", {})
        
        frontend_summary = []
        for url_key, data in frontend_metrics.items():
            if "metrics" in data and data["metrics"]:
                frontend_summary.append({
                    "page": url_key,
                    "mean_load_time_ms": data["metrics"].get("mean_ms"),
                    "median_load_time_ms": data["metrics"].get("median_ms"),
                    "success_rate": data["success_rate"]
                })
        
        backend_summary = []
        for endpoint_key, data in backend_metrics.items():
            if "metrics" in data and data["metrics"]:
                backend_summary.append({
                    "endpoint": endpoint_key,
                    "mean_response_time_ms": data["metrics"].get("mean_ms"),
                    "median_response_time_ms": data["metrics"].get("median_ms"),
                    "success_rate": data["success_rate"]
                })
        
        # Create the prompt for the AI
        prompt = f"""
        Analyze these performance metrics for a web application and identify potential bottlenecks:
        
        Frontend page load times:
        ```
        {json.dumps(frontend_summary, indent=2)}
        ```
        
        Backend API response times:
        ```
        {json.dumps(backend_summary, indent=2)}
        ```
        
        Please provide a JSON response with:
        1. Identified bottlenecks (pages or endpoints that are slow)
        2. Potential causes for these bottlenecks
        3. Recommended actions to improve performance
        4. Performance benchmarks that should be targeted
        
        Return ONLY a JSON object with these sections and no additional text.
        """
        
        try:
            analysis = await self.think(prompt)
            
            # Extract JSON from response
            analysis = analysis.strip()
            first_brace = analysis.find('{')
            last_brace = analysis.rfind('}')
            if first_brace != -1 and last_brace != -1:
                json_str = analysis[first_brace:last_brace+1]
                analysis_json = json.loads(json_str)
            else:
                analysis_json = json.loads(analysis)
            
            return {
                "bottleneck_analysis": analysis_json,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance bottlenecks: {str(e)}")
            return {
                "error": f"Error analyzing performance bottlenecks: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_load_test(self, method: str, endpoint: str, 
                           data: Any = None, concurrent_users: int = 5, 
                           duration_seconds: int = 10) -> Dict[str, Any]:
        """
        Run a load test on an API endpoint simulating multiple concurrent users.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            concurrent_users: Number of concurrent users to simulate
            duration_seconds: Duration of the test in seconds
            
        Returns:
            Dict with load test results
        """
        await self.setup()
        
        self.logger.info(f"Running load test on {method} {endpoint} with {concurrent_users} concurrent users for {duration_seconds}s")
        
        # Create a list to store individual request results
        results = []
        
        # Create a function for a single user session
        async def user_session(session_id: int):
            session_start = time.time()
            session_end = session_start + duration_seconds
            request_count = 0
            success_count = 0
            error_count = 0
            response_times = []
            
            self.logger.info(f"User session {session_id} started")
            
            while time.time() < session_end:
                try:
                    if method.upper() in ["GET", "DELETE", "HEAD"]:
                        result = await self.api_agent.make_request(method, endpoint, params=data)
                    else:
                        result = await self.api_agent.make_request(method, endpoint, data=data)
                    
                    request_count += 1
                    response_times.append(result["duration_ms"])
                    
                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    # Add a small random delay to simulate real user behavior
                    await asyncio.sleep(0.1 + (0.3 * asyncio.get_event_loop().time() % 1))
                    
                except Exception as e:
                    self.logger.error(f"Error in user session {session_id}: {str(e)}")
                    error_count += 1
                    request_count += 1
            
            session_result = {
                "session_id": session_id,
                "duration_seconds": time.time() - session_start,
                "request_count": request_count,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": (success_count / request_count) * 100 if request_count > 0 else 0,
                "response_times": response_times,
                "avg_response_time": statistics.mean(response_times) if response_times else None
            }
            
            self.logger.info(f"User session {session_id} completed with {request_count} requests")
            return session_result
        
        # Create and run tasks for each simulated user
        tasks = [user_session(i) for i in range(concurrent_users)]
        session_results = await asyncio.gather(*tasks)
        
        # Aggregate results
        total_requests = sum(r["request_count"] for r in session_results)
        total_successes = sum(r["success_count"] for r in session_results)
        total_errors = sum(r["error_count"] for r in session_results)
        all_response_times = [t for r in session_results for t in r["response_times"]]
        
        # Calculate aggregated metrics
        metrics = {}
        
        if all_response_times:
            metrics = {
                "min_ms": min(all_response_times),
                "max_ms": max(all_response_times),
                "mean_ms": statistics.mean(all_response_times),
                "median_ms": statistics.median(all_response_times),
                "p95_ms": sorted(all_response_times)[int(len(all_response_times) * 0.95)] if len(all_response_times) >= 20 else None,
                "p99_ms": sorted(all_response_times)[int(len(all_response_times) * 0.99)] if len(all_response_times) >= 100 else None,
                "std_dev_ms": statistics.stdev(all_response_times) if len(all_response_times) > 1 else 0
            }
        
        # Calculate requests per second
        total_duration = duration_seconds * concurrent_users
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        
        # Record the final result
        result = {
            "method": method,
            "endpoint": endpoint,
            "concurrent_users": concurrent_users,
            "duration_seconds": duration_seconds,
            "total_requests": total_requests,
            "successful_requests": total_successes,
            "failed_requests": total_errors,
            "success_rate": (total_successes / total_requests) * 100 if total_requests > 0 else 0,
            "requests_per_second": requests_per_second,
            "response_time_metrics": metrics,
            "user_sessions": session_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to test results
        self.test_results.append({
            "type": "load_test",
            "target": f"{method} {endpoint}",
            "result": result
        })
        
        return result
    
    async def measure_system_resources(self, 
                                      frontend_url: str = None, 
                                      backend_endpoints: List[Dict] = None,
                                      duration_seconds: int = 30) -> Dict[str, Any]:
        """
        Measure system resource usage during application operation.
        Note: This method requires server access to properly measure CPU, memory etc.
        This implementation simulates such measurements for demonstration.
        
        Args:
            frontend_url: URL to load in browser during measurement
            backend_endpoints: List of endpoints to call during measurement
            duration_seconds: Duration of measurement
            
        Returns:
            Dict with resource usage metrics
        """
        await self.setup()
        
        self.logger.info(f"Measuring system resources for {duration_seconds}s")
        
        # Open the frontend page if URL provided
        if frontend_url:
            try:
                page = await self.browser.new_page()
                await page.goto(frontend_url, wait_until="networkidle")
                self.logger.info(f"Loaded frontend URL: {frontend_url}")
            except Exception as e:
                self.logger.error(f"Error loading frontend URL: {str(e)}")
        
        # Make periodic API calls if endpoints provided
        if backend_endpoints:
            for endpoint_info in backend_endpoints:
                method = endpoint_info.get("method", "GET")
                path = endpoint_info.get("path")
                data = endpoint_info.get("data")
                
                if path:
                    try:
                        if method.upper() in ["GET", "DELETE", "HEAD"]:
                            await self.api_agent.make_request(method, path, params=data)
                        else:
                            await self.api_agent.make_request(method, path, data=data)
                        self.logger.info(f"Called endpoint: {method} {path}")
                    except Exception as e:
                        self.logger.error(f"Error calling endpoint: {str(e)}")
        
        # In a real implementation, we would:
        # 1. Measure CPU usage
        # 2. Measure memory usage
        # 3. Measure network I/O
        # 4. Measure disk I/O
        
        # For demonstration, we'll simulate measurements
        
        # Simulate waiting for the specified duration
        await asyncio.sleep(duration_seconds)
        
        # Close the page if it was opened
        if frontend_url:
            try:
                await page.close()
            except:
                pass
        
        # Return simulated metrics
        metrics = {
            "note": "These are simulated metrics for demonstration",
            "cpu": {
                "usage_percent": 35.2,  # Simulated value
                "core_usage": [40.1, 32.5, 38.7, 29.5],  # Simulated values
            },
            "memory": {
                "total_mb": 4096,  # Simulated value
                "used_mb": 1843,   # Simulated value
                "usage_percent": 45.0,  # Simulated value
            },
            "network": {
                "rx_mb": 12.5,  # Simulated value
                "tx_mb": 3.2,   # Simulated value
                "connections": 24,  # Simulated value
            },
            "disk": {
                "read_mb": 8.3,  # Simulated value
                "write_mb": 2.1,  # Simulated value
                "iops": 45,  # Simulated value
            },
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration_seconds
        }
        
        # Store in performance metrics
        self.performance_metrics["system"]["resource_usage"] = metrics
        
        return metrics
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run a comprehensive performance test suite."""
        try:
            await self.setup()
            test_start_time = datetime.now()
            
            # 1. Test frontend page load times for main application pages
            frontend_pages = [
                settings.FRONTEND_URL,  # Homepage
                f"{settings.FRONTEND_URL}/jobs",
                f"{settings.FRONTEND_URL}/candidates",
                f"{settings.FRONTEND_URL}/matches"
            ]
            
            for page_url in frontend_pages:
                await self.measure_page_load_time(page_url, iterations=3)
            
            # 2. Test backend API endpoints
            api_endpoints = [
                {"method": "GET", "path": "/health"},
                {"method": "POST", "path": "/analyze/resume", "data": {"text": "Software Developer with 5 years of experience"}},
                {"method": "POST", "path": "/analyze/job", "data": {"text": "Looking for a Software Developer"}},
                {"method": "POST", "path": "/match", "data": {
                    "resume_data": {"skills": ["Python", "JavaScript"]},
                    "job_data": {"required_skills": ["Python"]}
                }}
            ]
            
            for endpoint in api_endpoints:
                await self.measure_api_response_time(
                    endpoint["method"], 
                    endpoint["path"], 
                    endpoint.get("data"), 
                    iterations=3
                )
            
            # 3. Run load test on key endpoints
            await self.run_load_test(
                "POST", 
                "/match", 
                data={
                    "resume_data": {"skills": ["Python", "JavaScript"]},
                    "job_data": {"required_skills": ["Python"]}
                },
                concurrent_users=3,
                duration_seconds=10
            )
            
            # 4. Measure system resources during normal operation
            await self.measure_system_resources(
                frontend_url=settings.FRONTEND_URL,
                backend_endpoints=[
                    {"method": "GET", "path": "/health"}
                ],
                duration_seconds=10
            )
            
            # 5. Analyze the performance metrics to identify bottlenecks
            bottleneck_analysis = await self.analyze_performance_bottlenecks(self.performance_metrics)
            
            # Generate a report
            test_duration = (datetime.now() - test_start_time).total_seconds()
            
            result = {
                "performance_metrics": self.performance_metrics,
                "bottleneck_analysis": bottleneck_analysis,
                "test_scenarios": self.test_scenarios,
                "test_results": self.test_results,
                "test_duration_seconds": test_duration,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            # Generate the report
            await self.generate_report(
                title="Performance Test Results",
                data=result
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during performance tests: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await self.close() 