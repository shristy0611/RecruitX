import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Locator
from .base_agent import FrontendTestAgent

class UIComponentAgent(FrontendTestAgent):
    """Agent specialized in testing UI components and their rendering"""
    
    COMPONENTS_TO_TEST = [
        {"name": "Dashboard", "route": "/", "selectors": [".dashboard-container"]},
        {"name": "FileUpload", "route": "/", "selectors": [".file-upload"]},
        {"name": "Navbar", "route": "/", "selectors": [".navbar"]},
        {"name": "Footer", "route": "/", "selectors": [".footer"]},
        {"name": "ResumeAnalysis", "route": "/resume-analysis", "selectors": [".resume-analysis-container"]},
        {"name": "JobAnalysis", "route": "/job-analysis", "selectors": [".job-analysis-container"]},
        {"name": "Matching", "route": "/matching", "selectors": [".matching-container"]},
        {"name": "ApiStatus", "route": "/api-status", "selectors": [".api-status-container"]},
        {"name": "SkillList", "route": "/", "selectors": [".skill-list"]},
        {"name": "NotFound", "route": "/nonexistent-page", "selectors": [".not-found-container"]}
    ]
    
    def __init__(self, base_url: str = "http://localhost:5173"):
        super().__init__(base_url)
        self.screenshots_dir = Path("tests/frontend/test_results/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def setup_browser(self):
        """Initialize browser for UI testing"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=Path("tests/frontend/test_results/videos")
        )
        
    async def take_screenshot(self, page: Page, name: str) -> str:
        """Take screenshot of current page"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = str(self.screenshots_dir / f"{name}_{timestamp}.png")
        await page.screenshot(path=file_path, full_page=True)
        return file_path
        
    async def test_component_rendering(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Test if a component renders correctly"""
        page = await self.context.new_page()
        result = {
            "component": component["name"],
            "route": component["route"],
            "timestamp": str(datetime.now()),
            "status": "untested",
            "visible": False,
            "screenshot": None,
            "network_requests": [],
            "ui_analysis": {},
            "errors": []
        }
        
        try:
            # Navigate to the page with a shorter timeout
            await page.goto(f"{self.base_url}{component['route']}", timeout=10000)
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Collect network requests
            for request in page.request.all():
                if request.response():
                    result["network_requests"].append({
                        "url": request.url,
                        "method": request.method,
                        "status": request.response().status,
                        "content_type": request.response().headers.get("content-type", "")
                    })
            
            # Check component visibility
            all_visible = True
            for selector in component["selectors"]:
                try:
                    element = page.locator(selector)
                    is_visible = await element.is_visible(timeout=5000)
                    if not is_visible:
                        all_visible = False
                        result["errors"].append(f"Selector '{selector}' not visible")
                except Exception as e:
                    all_visible = False
                    result["errors"].append(f"Error finding selector '{selector}': {str(e)}")
            
            result["visible"] = all_visible
            
            # Take screenshot
            result["screenshot"] = await self.take_screenshot(page, component["name"])
            
            # Analyze UI
            page_html = await page.content()
            result["ui_analysis"] = await self.analyze_ui(page_html, result["screenshot"])
            
            # Set final status
            if all_visible and not result["errors"]:
                result["status"] = "passed"
            else:
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
        finally:
            await page.close()
            
        return result
        
    async def test_component_interactions(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Test interactive elements of a component"""
        page = await self.context.new_page()
        result = {
            "component": component["name"],
            "route": component["route"],
            "timestamp": str(datetime.now()),
            "status": "untested",
            "interactions": [],
            "errors": []
        }
        
        # Define interaction tests for specific components
        interaction_tests = {
            "FileUpload": [
                {"action": "click", "selector": "input[type=file]", "description": "Click file input"}
            ],
            "Navbar": [
                {"action": "click", "selector": "a[href='/']", "description": "Click home link"},
                {"action": "click", "selector": "a[href='/resume-analysis']", "description": "Click resume analysis link"},
                {"action": "click", "selector": "a[href='/job-analysis']", "description": "Click job analysis link"},
                {"action": "click", "selector": "a[href='/matching']", "description": "Click matching link"}
            ]
        }
        
        try:
            # Navigate to the page with a shorter timeout
            await page.goto(f"{self.base_url}{component['route']}", timeout=10000)
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Skip if no interactions defined
            if component["name"] not in interaction_tests:
                result["status"] = "skipped"
                result["interactions"].append({"description": "No interactions defined for this component"})
                return result
                
            # Perform interactions
            tests = interaction_tests[component["name"]]
            for test in tests:
                interaction_result = {
                    "description": test["description"],
                    "success": False,
                    "error": None
                }
                
                try:
                    selector = test["selector"]
                    element = page.locator(selector)
                    
                    # Wait for element to be visible with shorter timeout
                    await element.wait_for(state="visible", timeout=5000)
                    
                    if test["action"] == "click":
                        await element.click(timeout=5000)
                        interaction_result["success"] = True
                    elif test["action"] == "type":
                        await element.type(test.get("text", "Test input"), timeout=5000)
                        interaction_result["success"] = True
                    # Add more actions as needed
                    
                except Exception as e:
                    interaction_result["error"] = str(e)
                    result["errors"].append(f"Error in {test['description']}: {str(e)}")
                    
                result["interactions"].append(interaction_result)
                
            # Set final status
            if not result["errors"]:
                result["status"] = "passed"
            else:
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
        finally:
            await page.close()
            
        return result
    
    async def test_api_interactions(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Test component API interactions"""
        page = await self.context.new_page()
        result = {
            "component": component["name"],
            "route": component["route"],
            "timestamp": str(datetime.now()),
            "status": "untested",
            "api_calls": [],
            "errors": []
        }
        
        # Define components that interact with the API
        api_components = ["ResumeAnalysis", "JobAnalysis", "Matching", "ApiStatus"]
        
        try:
            if component["name"] not in api_components:
                result["status"] = "skipped"
                return result
                
            # Navigate to the page with a shorter timeout
            await page.goto(f"{self.base_url}{component['route']}", timeout=10000)
            
            # Listen for API calls
            page.on("request", lambda request: result["api_calls"].append({
                "url": request.url,
                "method": request.method,
                "timestamp": str(datetime.now())
            }) if self.api_url in request.url else None)
            
            # Wait for network idle with shorter timeout
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Let the page sit for a bit to catch any delayed API calls
            await asyncio.sleep(1)
            
            # For Matching component, simulate file upload
            if component["name"] == "ResumeAnalysis":
                # Simplified simulation - in a real test we'd upload actual files
                try:
                    file_button = page.locator("input[type=file]")
                    await file_button.set_input_files("tests/fixtures/sample_resume.pdf", timeout=5000)
                    submit_button = page.locator("button[type=submit]")
                    await submit_button.click(timeout=5000)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(1)  # Wait for potential async operations
                except Exception as e:
                    result["errors"].append(f"Error simulating file upload: {str(e)}")
            
            # Set final status
            if len(result["api_calls"]) > 0 and not result["errors"]:
                result["status"] = "passed"
            elif len(result["api_calls"]) == 0:
                result["status"] = "failed"
                result["errors"].append("No API calls detected")
            else:
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
        finally:
            await page.close()
            
        return result
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run all UI component tests"""
        results = {
            "agent_type": "UIComponentAgent",
            "timestamp": str(datetime.now()),
            "components_tested": 0,
            "components_passed": 0,
            "components_failed": 0,
            "tests": []
        }
        
        try:
            await self.setup_browser()
            
            for component in self.COMPONENTS_TO_TEST:
                component_results = {
                    "component": component["name"],
                    "timestamp": str(datetime.now()),
                    "rendering_test": await self.test_component_rendering(component),
                    "interaction_test": await self.test_component_interactions(component),
                    "api_test": await self.test_api_interactions(component)
                }
                
                # Determine overall status
                if (component_results["rendering_test"]["status"] in ["passed", "skipped"] and
                    component_results["interaction_test"]["status"] in ["passed", "skipped"] and
                    component_results["api_test"]["status"] in ["passed", "skipped"]):
                    component_results["status"] = "passed"
                    results["components_passed"] += 1
                else:
                    component_results["status"] = "failed"
                    results["components_failed"] += 1
                    
                results["tests"].append(component_results)
                results["components_tested"] += 1
                
            # Generate network analysis
            all_requests = []
            for test in results["tests"]:
                if "network_requests" in test["rendering_test"]:
                    all_requests.extend(test["rendering_test"]["network_requests"])
            
            if all_requests:
                results["network_analysis"] = await self.analyze_network_requests(all_requests[:100])  # Limit to 100 requests
                
        except Exception as e:
            results["error"] = str(e)
        finally:
            # Close browser
            await self.context.close()
            await self.browser.close()
            await self.playwright.stop()
            
        return results 