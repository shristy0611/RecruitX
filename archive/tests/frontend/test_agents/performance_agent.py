import asyncio
import json
import os
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from playwright.async_api import async_playwright, Page
from .base_agent import FrontendTestAgent

class PerformanceAgent(FrontendTestAgent):
    """Agent specialized in testing frontend performance"""
    
    ROUTES_TO_TEST = [
        {"name": "Home", "route": "/"}
    ]
    
    def __init__(self, base_url: str = "http://localhost:5173"):
        super().__init__(base_url)
        self.traces_dir = Path("tests/frontend/test_results/traces")
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        self.iterations = 1  # Reduced number of measurements to take for each test
    
    async def setup_browser(self):
        """Initialize browser for performance testing"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_har_path=Path("tests/frontend/test_results/har/browsing.har")
        )
    
    async def measure_page_load(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """Measure page load performance for a route"""
        result = {
            "route": route["name"],
            "path": route["route"],
            "timestamp": str(datetime.now()),
            "load_times": [],
            "dom_content_loaded_times": [],
            "first_paint_times": [],
            "largest_contentful_paint_times": [],
            "cumulative_layout_shift": [],
            "network_requests": [],
            "resource_sizes": {},
            "errors": []
        }
        
        for i in range(self.iterations):
            page = await self.context.new_page()
            
            try:
                # Start tracing
                await page.context.tracing.start(screenshots=True, snapshots=True)
                
                # Create client for performance metrics
                perf_metrics = {}
                await page.evaluate("""
                window.performanceData = {
                    lcpTime: 0,
                    clsValue: 0
                };
                
                // LCP Observer
                new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    window.performanceData.lcpTime = lastEntry.startTime;
                }).observe({type: 'largest-contentful-paint', buffered: true});
                
                // CLS Observer
                let clsValue = 0;
                new PerformanceObserver((entryList) => {
                    for (const entry of entryList.getEntries()) {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                            window.performanceData.clsValue = clsValue;
                        }
                    }
                }).observe({type: 'layout-shift', buffered: true});
                """)
                
                # Collect performance metrics
                start_time = time.time()
                response = await page.goto(f"{self.base_url}{route['route']}", 
                                        wait_until="networkidle",
                                        timeout=10000)
                
                # Measure load time
                load_time = time.time() - start_time
                result["load_times"].append(load_time)
                
                # Get Navigation Timing metrics
                perf_timing = await page.evaluate("""
                    const navigation = performance.getEntriesByType('navigation')[0];
                    const paint = performance.getEntriesByType('paint');
                    const firstPaint = paint.find(entry => entry.name === 'first-paint');
                    
                    return {
                        navigationStart: navigation.startTime,
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.startTime,
                        firstPaint: firstPaint ? firstPaint.startTime : 0,
                        lcp: window.performanceData.lcpTime,
                        cls: window.performanceData.clsValue
                    };
                """)
                
                result["dom_content_loaded_times"].append(perf_timing["domContentLoaded"])
                result["first_paint_times"].append(perf_timing["firstPaint"])
                result["largest_contentful_paint_times"].append(perf_timing["lcp"])
                result["cumulative_layout_shift"].append(perf_timing["cls"])
                
                # Collect resource information
                resources = await page.evaluate("""
                    const resources = performance.getEntriesByType('resource');
                    return resources.map(resource => ({
                        name: resource.name,
                        type: resource.initiatorType,
                        size: resource.transferSize,
                        duration: resource.duration
                    }));
                """)
                
                # Aggregate resource sizes by type
                for resource in resources:
                    resource_type = resource.get("type", "other")
                    if resource_type not in result["resource_sizes"]:
                        result["resource_sizes"][resource_type] = []
                    result["resource_sizes"][resource_type].append(resource.get("size", 0))
                
                # Collect network requests
                if i == 0:  # Only capture network requests on first iteration to reduce data
                    for request in page.request.all():
                        if request.response():
                            result["network_requests"].append({
                                "url": request.url,
                                "method": request.method,
                                "status": request.response().status,
                                "content_type": request.response().headers.get("content-type", ""),
                                "size": request.response().headers.get("content-length", "0")
                            })
                
                # Stop tracing
                trace_path = self.traces_dir / f"{route['name']}_trace_{i}.zip"
                await page.context.tracing.stop(path=trace_path)
                
            except Exception as e:
                result["errors"].append(f"Iteration {i+1}: {str(e)}")
            finally:
                await page.close()
        
        # Calculate averages and median values
        if result["load_times"]:
            result["avg_load_time"] = statistics.mean(result["load_times"])
            result["median_load_time"] = statistics.median(result["load_times"])
        
        if result["dom_content_loaded_times"]:
            result["avg_dom_content_loaded"] = statistics.mean(result["dom_content_loaded_times"])
            result["median_dom_content_loaded"] = statistics.median(result["dom_content_loaded_times"])
        
        if result["first_paint_times"]:
            result["avg_first_paint"] = statistics.mean(result["first_paint_times"])
            result["median_first_paint"] = statistics.median(result["first_paint_times"])
        
        if result["largest_contentful_paint_times"]:
            result["avg_lcp"] = statistics.mean(result["largest_contentful_paint_times"])
            result["median_lcp"] = statistics.median(result["largest_contentful_paint_times"])
        
        if result["cumulative_layout_shift"]:
            result["avg_cls"] = statistics.mean(result["cumulative_layout_shift"])
        
        # Aggregate resource sizes
        for resource_type, sizes in result["resource_sizes"].items():
            result["resource_sizes"][resource_type] = {
                "total": sum(sizes),
                "avg": statistics.mean(sizes) if sizes else 0,
                "count": len(sizes)
            }
        
        return result
    
    async def test_responsiveness(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """Test UI responsiveness through interaction measurements"""
        page = await self.context.new_page()
        result = {
            "route": route["name"],
            "path": route["route"],
            "timestamp": str(datetime.now()),
            "interactions": [],
            "errors": []
        }
        
        # Define common interactive elements to test
        interactions = [
            {"selector": "button", "description": "Button click", "action": "click"},
            {"selector": "a", "description": "Link click", "action": "click"}
        ]
        
        try:
            # Navigate to the page
            await page.goto(f"{self.base_url}{route['route']}", wait_until="networkidle", timeout=10000)
            
            # Find interactions that are available on this page
            available_interactions = []
            for interaction in interactions:
                count = await page.locator(interaction["selector"]).count()
                if count > 0:
                    available_interactions.append(interaction)
            
            # Measure interaction responsiveness
            for interaction in available_interactions:
                element = page.locator(interaction["selector"]).first
                
                try:
                    # Measure time to respond to interaction
                    start_time = time.time() * 1000  # Convert to ms
                    
                    if interaction["action"] == "click":
                        await element.click(timeout=5000)
                    
                    # Wait for any reactions to complete (animations, etc.)
                    await page.wait_for_timeout(100)
                    
                    # Get the time it took
                    response_time = (time.time() * 1000) - start_time
                    
                    result["interactions"].append({
                        "description": interaction["description"],
                        "response_time_ms": response_time,
                        "action": interaction["action"]
                    })
                    
                except Exception as e:
                    result["errors"].append(f"Error in {interaction['description']}: {str(e)}")
        
        except Exception as e:
            result["errors"].append(str(e))
        finally:
            await page.close()
        
        return result
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        results = {
            "agent_type": "PerformanceAgent",
            "timestamp": str(datetime.now()),
            "routes_tested": 0,
            "page_load_results": [],
            "responsiveness_results": [],
            "summary": {},
            "errors": []
        }
        
        try:
            await self.setup_browser()
            
            # Test each route
            for route in self.ROUTES_TO_TEST:
                # Measure page load performance
                load_result = await self.measure_page_load(route)
                results["page_load_results"].append(load_result)
                
                # Test responsiveness
                resp_result = await self.test_responsiveness(route)
                results["responsiveness_results"].append(resp_result)
                
                results["routes_tested"] += 1
            
            # Generate summary statistics
            avg_load_times = [r.get("avg_load_time", 0) for r in results["page_load_results"] if "avg_load_time" in r]
            avg_lcp_times = [r.get("avg_lcp", 0) for r in results["page_load_results"] if "avg_lcp" in r]
            avg_cls_values = [r.get("avg_cls", 0) for r in results["page_load_results"] if "avg_cls" in r]
            
            if avg_load_times:
                results["summary"]["avg_load_time_all_routes"] = statistics.mean(avg_load_times)
                results["summary"]["slowest_route"] = max(
                    [(r.get("route", "unknown"), r.get("avg_load_time", 0)) 
                     for r in results["page_load_results"] if "avg_load_time" in r],
                    key=lambda x: x[1]
                )
                results["summary"]["fastest_route"] = min(
                    [(r.get("route", "unknown"), r.get("avg_load_time", 0)) 
                     for r in results["page_load_results"] if "avg_load_time" in r],
                    key=lambda x: x[1]
                )
                
            if avg_lcp_times:
                results["summary"]["avg_lcp_all_routes"] = statistics.mean(avg_lcp_times)
                
            if avg_cls_values:
                results["summary"]["avg_cls_all_routes"] = statistics.mean(avg_cls_values)
                
            # Analyze performance against good practice thresholds
            good_lcp_threshold = 2500  # 2.5 seconds
            good_cls_threshold = 0.1
            
            if avg_lcp_times:
                results["summary"]["routes_with_good_lcp"] = sum(1 for t in avg_lcp_times if t < good_lcp_threshold)
                results["summary"]["routes_with_poor_lcp"] = sum(1 for t in avg_lcp_times if t >= good_lcp_threshold)
                
            if avg_cls_values:
                results["summary"]["routes_with_good_cls"] = sum(1 for c in avg_cls_values if c < good_cls_threshold)
                results["summary"]["routes_with_poor_cls"] = sum(1 for c in avg_cls_values if c >= good_cls_threshold)
                
            # Add insights from Gemini
            load_data_for_analysis = []
            for r in results["page_load_results"]:
                if "avg_load_time" in r and "avg_lcp" in r and "avg_cls" in r:
                    load_data_for_analysis.append({
                        "route": r["route"],
                        "avg_load_time": r["avg_load_time"],
                        "avg_lcp": r["avg_lcp"],
                        "avg_cls": r["avg_cls"],
                        "resource_sizes": r["resource_sizes"]
                    })
            
            if load_data_for_analysis:
                prompt = f"""
                Analyze this frontend performance data and provide insights:
                {json.dumps(load_data_for_analysis, indent=2)}
                
                Return a JSON with:
                - performance_summary: brief assessment of overall performance
                - critical_issues: list of most pressing performance issues
                - optimization_suggestions: list of specific optimization recommendations
                - priority_routes: routes that need immediate attention
                """
                try:
                    results["summary"]["ai_analysis"] = json.loads(await self.think(prompt))
                except:
                    results["errors"].append("Failed to generate AI analysis of performance data")
            
        except Exception as e:
            results["errors"].append(str(e))
        finally:
            # Clean up
            await self.context.close()
            await self.browser.close()
            await self.playwright.stop()
            
        return results 