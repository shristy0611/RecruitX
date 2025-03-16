"""
API testing agent that specializes in testing backend API endpoints using AI-powered decision making.
"""

import os
import json
import asyncio
import aiohttp
import hashlib
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from tests.ai_testing.agents.base_agent import BaseAgent
from tests.ai_testing.config import settings

class APIAgent(BaseAgent):
    """Agent specialized in API testing using AI-powered decision making."""
    
    def __init__(self, name: str = "APIAgent", model_type: str = settings.AGENT_TYPE):
        super().__init__(name, model_type)
        self.api_endpoints_tested = []
        self.request_history = []
        self.response_history = []
        self.response_times = {}
        self.session = None
    
    async def setup_session(self):
        """Initialize the HTTP client session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=settings.TIMEOUT / 1000)  # Convert from ms to seconds
            self.session = aiohttp.ClientSession(timeout=timeout)
            self.logger.info("HTTP session initialized")
    
    async def setup(self):
        """Setup the API agent by initializing the HTTP session."""
        await super().setup()
        await self.setup_session()
        self.logger.info(f"API Agent setup complete")
    
    async def close(self):
        """Close all resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("HTTP session closed")
        await super().close()
    
    async def make_request(self, method: str, endpoint: str, data: Any = None, 
                          params: Dict[str, Any] = None, headers: Dict[str, str] = None,
                          auth: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (will be appended to the base URL)
            data: Request body data
            params: Query parameters
            headers: HTTP headers
            auth: Authentication dictionary with username and password
            
        Returns:
            Dictionary with request results
        """
        await self.setup_session()
        
        # Prepare the URL
        if endpoint.startswith('http'):
            url = endpoint
        else:
            # Remove leading slash if present
            if endpoint.startswith('/'):
                endpoint = endpoint[1:]
            url = f"{settings.BACKEND_URL}/{endpoint}"
        
        # Prepare headers
        if headers is None:
            headers = {}
        
        # Set default Content-Type if not provided
        if 'Content-Type' not in headers and data is not None:
            headers['Content-Type'] = 'application/json'
        
        # Convert data to JSON string if it's a dict
        json_data = None
        if data is not None and headers.get('Content-Type') == 'application/json':
            if isinstance(data, (dict, list)):
                json_data = data
                data = None
        
        self.logger.info(f"Making {method} request to {url}")
        
        # Record request details
        request_id = hashlib.md5(f"{method}:{url}:{datetime.now().isoformat()}".encode()).hexdigest()
        request_details = {
            "id": request_id,
            "method": method,
            "url": url,
            "params": params,
            "headers": {k: v for k, v in headers.items() if k.lower() != 'authorization'},  # Don't log auth tokens
            "data": json_data if json_data else data,
            "timestamp": datetime.now().isoformat()
        }
        self.request_history.append(request_details)
        
        # Make the request
        start_time = datetime.now()
        try:
            if method.upper() == 'GET':
                response = await self.session.get(url, params=params, headers=headers, auth=aiohttp.BasicAuth(*auth) if auth else None)
            elif method.upper() == 'POST':
                response = await self.session.post(url, params=params, headers=headers, json=json_data, data=data, auth=aiohttp.BasicAuth(*auth) if auth else None)
            elif method.upper() == 'PUT':
                response = await self.session.put(url, params=params, headers=headers, json=json_data, data=data, auth=aiohttp.BasicAuth(*auth) if auth else None)
            elif method.upper() == 'DELETE':
                response = await self.session.delete(url, params=params, headers=headers, auth=aiohttp.BasicAuth(*auth) if auth else None)
            elif method.upper() == 'PATCH':
                response = await self.session.patch(url, params=params, headers=headers, json=json_data, data=data, auth=aiohttp.BasicAuth(*auth) if auth else None)
            elif method.upper() == 'HEAD':
                response = await self.session.head(url, params=params, headers=headers, auth=aiohttp.BasicAuth(*auth) if auth else None)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Get response data
            if method.upper() != 'HEAD':
                try:
                    response_text = await response.text()
                    try:
                        response_data = await response.json()
                    except:
                        response_data = response_text
                except:
                    response_text = "Failed to get response text"
                    response_data = None
            else:
                response_text = ""
                response_data = None
            
            # Record response details
            response_details = {
                "request_id": request_id,
                "status": response.status,
                "headers": dict(response.headers),
                "data": response_data,
                "text": response_text[:1000] if len(response_text) > 1000 else response_text,
                "duration_ms": duration_ms,
                "timestamp": end_time.isoformat()
            }
            self.response_history.append(response_details)
            
            # Update response time metrics
            endpoint_key = f"{method.upper()}:{endpoint}"
            if endpoint_key not in self.response_times:
                self.response_times[endpoint_key] = []
            self.response_times[endpoint_key].append(duration_ms)
            
            self.logger.info(f"Request completed with status {response.status} in {duration_ms:.2f}ms")
            
            return {
                "request": request_details,
                "response": response_details,
                "success": 200 <= response.status < 300,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            error_details = {
                "request_id": request_id,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": end_time.isoformat()
            }
            self.response_history.append(error_details)
            
            self.logger.error(f"Request failed: {str(e)}")
            
            return {
                "request": request_details,
                "error": str(e),
                "success": False,
                "duration_ms": duration_ms
            }
    
    async def discover_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Attempt to discover available API endpoints by checking common paths.
        
        Returns:
            List of discovered endpoints
        """
        common_endpoints = [
            # Health and status endpoints
            {"method": "GET", "path": "/health"},
            {"method": "GET", "path": "/status"},
            {"method": "GET", "path": "/api/health"},
            
            # Documentation endpoints
            {"method": "GET", "path": "/docs"},
            {"method": "GET", "path": "/redoc"},
            {"method": "GET", "path": "/swagger"},
            {"method": "GET", "path": "/openapi.json"},
            
            # API version endpoints
            {"method": "GET", "path": "/version"},
            {"method": "GET", "path": "/api/version"},
            
            # RecruitX specific endpoints
            {"method": "POST", "path": "/analyze/resume"},
            {"method": "POST", "path": "/analyze/job"},
            {"method": "POST", "path": "/match"}
        ]
        
        discovered_endpoints = []
        
        for endpoint in common_endpoints:
            method = endpoint["method"]
            path = endpoint["path"]
            
            try:
                result = await self.make_request(method, path)
                
                if result["success"] or result.get("response", {}).get("status") in [401, 403]:
                    # If successful or auth required, endpoint exists
                    discovered_endpoints.append({
                        "method": method,
                        "path": path,
                        "status": result.get("response", {}).get("status", 0),
                        "requires_auth": result.get("response", {}).get("status") in [401, 403],
                        "response_time_ms": result["duration_ms"]
                    })
                    self.logger.info(f"Discovered endpoint: {method} {path}")
            except Exception as e:
                self.logger.warning(f"Error checking endpoint {method} {path}: {str(e)}")
        
        return discovered_endpoints
    
    async def analyze_api_schema(self) -> Dict[str, Any]:
        """
        Analyze the API schema by looking for OpenAPI documentation.
        
        Returns:
            Dict with API schema information
        """
        schema_endpoints = [
            "/openapi.json",
            "/api/openapi.json",
            "/docs/openapi.json",
            "/swagger/v1/swagger.json"
        ]
        
        for endpoint in schema_endpoints:
            try:
                result = await self.make_request("GET", endpoint)
                
                if result["success"] and isinstance(result.get("response", {}).get("data"), dict):
                    schema = result["response"]["data"]
                    self.logger.info(f"Found API schema at {endpoint}")
                    
                    # Extract endpoints from schema
                    paths = schema.get("paths", {})
                    api_endpoints = []
                    
                    for path, methods in paths.items():
                        for method, details in methods.items():
                            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                                api_endpoints.append({
                                    "method": method.upper(),
                                    "path": path,
                                    "summary": details.get("summary", ""),
                                    "description": details.get("description", ""),
                                    "parameters": details.get("parameters", []),
                                    "request_body": details.get("requestBody", {}),
                                    "responses": details.get("responses", {})
                                })
                    
                    return {
                        "title": schema.get("info", {}).get("title", "Unknown API"),
                        "version": schema.get("info", {}).get("version", "Unknown"),
                        "description": schema.get("info", {}).get("description", ""),
                        "endpoints": api_endpoints,
                        "schema_source": endpoint
                    }
            except Exception as e:
                self.logger.warning(f"Error fetching schema from {endpoint}: {str(e)}")
        
        self.logger.warning("No API schema found")
        return {"error": "No API schema found"}
    
    async def test_api_endpoint(self, method: str, endpoint: str, 
                               test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Test a specific API endpoint with AI-driven test data generation.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            test_data: Optional test data to use
            
        Returns:
            Dict with test results
        """
        self.logger.info(f"Testing API endpoint: {method} {endpoint}")
        
        # Generate test data if not provided
        if test_data is None:
            prompt = f"""
            Generate test data for API endpoint: {method} {endpoint}
            
            I need a JSON object with test data for this endpoint. Consider typical parameters and data types.
            If this is likely a POST, PUT, or PATCH endpoint, generate a reasonable request body.
            If this is likely a GET endpoint, generate query parameters.
            
            Return ONLY a JSON object containing the test data with no additional text.
            """
            
            try:
                response = await self.think(prompt)
                
                # Extract JSON from response
                response = response.strip()
                first_brace = response.find('{')
                last_brace = response.rfind('}')
                if first_brace != -1 and last_brace != -1:
                    json_str = response[first_brace:last_brace+1]
                    test_data = json.loads(json_str)
                else:
                    test_data = json.loads(response)
                
                self.logger.info(f"Generated test data: {json.dumps(test_data)[:100]}...")
            except Exception as e:
                self.logger.error(f"Error generating test data: {str(e)}")
                test_data = {}
        
        # Make the request
        if method.upper() in ["GET", "DELETE", "HEAD"]:
            result = await self.make_request(method, endpoint, params=test_data)
        else:
            result = await self.make_request(method, endpoint, data=test_data)
        
        # Record the endpoint test
        endpoint_test = {
            "method": method,
            "endpoint": endpoint,
            "test_data": test_data,
            "success": result["success"],
            "status_code": result.get("response", {}).get("status", 0),
            "response_time_ms": result["duration_ms"],
            "timestamp": datetime.now().isoformat()
        }
        
        if not result["success"]:
            endpoint_test["error"] = result.get("error") or f"Status code {endpoint_test['status_code']}"
        
        self.api_endpoints_tested.append(endpoint_test)
        
        # If successful, analyze the response with AI
        if result["success"]:
            response_data = result.get("response", {}).get("data")
            
            if response_data:
                prompt = f"""
                Analyze this API response from {method} {endpoint}:
                
                ```
                {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else response_data}
                ```
                
                Provide a JSON response with:
                1. A brief description of what this endpoint seems to do
                2. The key fields in the response and their purpose
                3. Any potential issues or anomalies in the response
                4. Suggestions for additional tests on this endpoint
                
                Return ONLY a JSON object with no additional text.
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
                    
                    endpoint_test["ai_analysis"] = analysis_json
                except Exception as e:
                    self.logger.error(f"Error analyzing response: {str(e)}")
                    endpoint_test["ai_analysis_error"] = str(e)
        
        return endpoint_test
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run API tests using AI-driven testing."""
        try:
            # Verify that the API is reachable
            health_result = await self.make_request("GET", "/health")
            
            if not health_result["success"]:
                self.logger.error(f"API is not reachable: {health_result.get('error', 'Unknown error')}")
                return {
                    "error": f"API is not reachable: {health_result.get('error', 'Unknown error')}",
                    "endpoints_tested": 0,
                    "success": False
                }
            
            # Try to discover API endpoints
            self.logger.info("Discovering API endpoints")
            discovered_endpoints = await self.discover_api_endpoints()
            
            # Try to analyze API schema
            self.logger.info("Analyzing API schema")
            schema_analysis = await self.analyze_api_schema()
            
            # Test each discovered endpoint
            for endpoint_info in discovered_endpoints:
                method = endpoint_info["method"]
                path = endpoint_info["path"]
                
                if not endpoint_info.get("requires_auth", False):
                    await self.test_api_endpoint(method, path)
            
            # Test the main RecruitX endpoints with specific test data
            
            # Test /analyze/resume with dummy data
            resume_test_data = {
                "text": "Software Developer with 5 years of experience in Python and JavaScript."
            }
            await self.test_api_endpoint("POST", "/analyze/resume", resume_test_data)
            
            # Test /analyze/job with dummy data
            job_test_data = {
                "text": "Looking for a Software Developer with experience in Python and React."
            }
            await self.test_api_endpoint("POST", "/analyze/job", job_test_data)
            
            # Test /match with dummy data
            match_test_data = {
                "resume_data": {
                    "skills": ["Python", "JavaScript", "Django", "React"],
                    "experience": ["Software Developer - 5 years"],
                    "education": ["Bachelor's in Computer Science"]
                },
                "job_data": {
                    "required_skills": ["Python", "Django", "AWS"],
                    "responsibilities": ["Develop web applications"],
                    "qualifications": ["Bachelor's degree in CS"]
                }
            }
            await self.test_api_endpoint("POST", "/match", match_test_data)
            
            # Generate a report
            return await self.generate_report()
            
        except Exception as e:
            self.logger.error(f"Error during API tests: {str(e)}")
            return {
                "error": str(e),
                "endpoints_tested": len(self.api_endpoints_tested),
                "success": False
            }
        finally:
            await self.close() 