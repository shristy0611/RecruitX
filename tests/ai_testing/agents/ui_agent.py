"""
UI testing agent that specializes in testing frontend components using AI-powered decision making.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from tests.ai_testing.agents.base_agent import BaseAgent
from tests.ai_testing.config import settings
from tests.ai_testing.tools.selector_tools import find_best_selector

class UIAgent(BaseAgent):
    """Agent specialized in UI testing using AI-powered decision making."""
    
    def __init__(self, name: str = "UIAgent", model_type: str = settings.AGENT_TYPE):
        super().__init__(name, model_type)
        self.components_tested = []
        self.interaction_history = []
        self.page_states = []
        self.accessibility_issues = []
        
    async def setup(self):
        """Setup the UI agent by initializing the browser."""
        await super().setup()
        await self.setup_browser()
        self.logger.info(f"UI Agent setup complete")
        
    async def analyze_component(self, component_name: str, selector: str = None) -> Dict[str, Any]:
        """Analyze a UI component using AI."""
        if not self.page:
            await self.setup_browser()
        
        # If no selector is provided, try to find the best one
        if not selector:
            from tests.ai_testing.tools.selector_tools import find_best_selector
            selector = await find_best_selector(self.page, component_name)
            
        self.logger.info(f"Analyzing component: {component_name} with selector: {selector}")
        
        # First check if the component exists
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if not element:
                self.logger.warning(f"Component not found: {component_name} with selector: {selector}")
                return {
                    "component_name": component_name,
                    "exists": False,
                    "error": "Component not found"
                }
            
            # Get component properties
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            # Get HTML and text content
            html_content = await self.page.evaluate(f"document.querySelector('{selector}').outerHTML")
            text_content = await element.text_content() or ""
            
            # Take a screenshot of the component
            screenshot_path = ""
            try:
                screenshot_path = await self.take_screenshot(f"component_{component_name}")
            except Exception as e:
                self.logger.error(f"Error taking component screenshot: {str(e)}")
            
            # Gather information about the component
            component_info = {
                "component_name": component_name,
                "selector": selector,
                "exists": True,
                "visible": is_visible,
                "enabled": is_enabled,
                "text_content": text_content.strip(),
                "html_length": len(html_content),
                "screenshot": screenshot_path,
                "timestamp": datetime.now().isoformat()
            }
            
            # AI analysis of the component
            ai_prompt = f"""
            Analyze this UI component and provide insights:
            
            Component: {component_name}
            HTML: {html_content[:5000] if len(html_content) > 5000 else html_content}
            
            Provide a JSON response with the following structure:
            {{
                "purpose": "What you think this component does based on its structure and content",
                "ui_issues": [List of potential UI issues such as poor contrast, unclear purpose, etc.],
                "accessibility_issues": [List of potential accessibility concerns],
                "suggestions": [Suggestions for improvement]
            }}
            
            Return ONLY the JSON with no additional text.
            """
            
            ai_analysis = await self.think(ai_prompt)
            
            try:
                # Extract JSON from the response (handle cases where the LLM adds explanatory text)
                ai_analysis = ai_analysis.strip()
                first_brace = ai_analysis.find('{')
                last_brace = ai_analysis.rfind('}')
                if first_brace != -1 and last_brace != -1:
                    json_str = ai_analysis[first_brace:last_brace+1]
                    analysis_json = json.loads(json_str)
                else:
                    analysis_json = json.loads(ai_analysis)
                
                component_info["ai_analysis"] = analysis_json
                
                # Add any accessibility issues to the list
                if "accessibility_issues" in analysis_json and analysis_json["accessibility_issues"]:
                    for issue in analysis_json["accessibility_issues"]:
                        self.accessibility_issues.append({
                            "component": component_name,
                            "issue": issue,
                            "url": self.page.url,
                            "timestamp": datetime.now().isoformat()
                        })
                
            except json.JSONDecodeError:
                self.logger.error("Failed to parse AI analysis as JSON")
                component_info["ai_analysis_error"] = "Failed to parse AI response as JSON"
                component_info["ai_analysis_raw"] = ai_analysis
            
            # Store this component test
            self.components_tested.append(component_info)
            return component_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing component {component_name}: {str(e)}")
            return {
                "component_name": component_name,
                "exists": False,
                "error": str(e)
            }
    
    async def interact_with_component(self, selector: str, action: str, value: str = None) -> Dict[str, Any]:
        """Interact with a UI component."""
        if not self.page:
            await self.setup_browser()
        
        self.logger.info(f"Interacting with component: {selector} with action: {action}")
        
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if not element:
                self.logger.warning(f"Component not found: {selector}")
                return {
                    "success": False,
                    "error": "Component not found"
                }
            
            if action == "click":
                await element.click()
            elif action == "type":
                await element.fill(value)
            elif action == "hover":
                await element.hover()
            elif action == "check":
                await element.check()
            elif action == "uncheck":
                await element.uncheck()
            elif action == "select":
                await element.select_option(value=value)
            else:
                self.logger.warning(f"Unsupported action: {action}")
                return {
                    "success": False,
                    "error": f"Unsupported action: {action}"
                }
            
            self.interaction_history.append({
                "selector": selector,
                "action": action,
                "value": value,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "action": action,
                "selector": selector,
                "value": value
            }
        except Exception as e:
            self.logger.error(f"Error interacting with component: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_workflow(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a workflow of multiple steps."""
        if not self.page:
            await self.setup_browser()
        
        self.logger.info(f"Executing workflow with {len(steps)} steps")
        
        results = []
        success_count = 0
        
        for i, step in enumerate(steps):
            self.logger.info(f"Executing step {i+1}/{len(steps)}: {step['action']}")
            
            try:
                if step["action"] == "navigate":
                    await self.page.goto(step["url"])
                    results.append({
                        "step": i+1,
                        "action": "navigate",
                        "url": step["url"],
                        "success": True
                    })
                    success_count += 1
                elif step["action"] == "wait_for_selector":
                    element = await self.page.wait_for_selector(step["selector"], timeout=10000)
                    results.append({
                        "step": i+1,
                        "action": "wait_for_selector",
                        "selector": step["selector"],
                        "success": element is not None
                    })
                    if element:
                        success_count += 1
                elif step["action"] == "wait_for_navigation":
                    await self.page.wait_for_navigation(timeout=10000)
                    results.append({
                        "step": i+1,
                        "action": "wait_for_navigation",
                        "success": True
                    })
                    success_count += 1
                elif step["action"] == "upload":
                    await self.page.set_input_files(step["selector"], step["file_path"])
                    results.append({
                        "step": i+1,
                        "action": "upload",
                        "selector": step["selector"],
                        "file_path": step["file_path"],
                        "success": True
                    })
                    success_count += 1
                else:
                    # For other actions, use interact_with_component
                    result = await self.interact_with_component(
                        step["selector"], 
                        step["action"],
                        step.get("text") or step.get("value")
                    )
                    results.append({
                        "step": i+1,
                        **result
                    })
                    if result["success"]:
                        success_count += 1
                
                # Take a screenshot after each step if recording is enabled
                if settings.VIDEO_RECORDING:
                    screenshot_path = settings.RESULTS_DIR / "screenshots" / f"workflow_step_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await self.page.screenshot(path=str(screenshot_path))
                
            except Exception as e:
                self.logger.error(f"Error executing step {i+1}: {str(e)}")
                results.append({
                    "step": i+1,
                    "action": step["action"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "total_steps": len(steps),
            "successful_steps": success_count,
            "success_rate": success_count / len(steps) if steps else 0,
            "results": results
        }
    
    async def perform_accessibility_test(self) -> Dict[str, Any]:
        """Perform an accessibility test on the current page."""
        if not self.page:
            await self.setup_browser()
        
        self.logger.info("Performing accessibility test")
        
        try:
            # Inject axe-core for accessibility testing
            await self.page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js")
            
            # Run the accessibility audit
            results = await self.page.evaluate('''() => {
                return new Promise(resolve => {
                    axe.run((err, results) => {
                        if (err) throw err;
                        resolve(results);
                    });
                });
            }''')
            
            # Extract the violations
            violations = results.get("violations", [])
            
            # Format the results
            accessibility_results = {
                "url": self.page.url,
                "timestamp": datetime.now().isoformat(),
                "total_issues": len(violations),
                "violations": violations,
                "passes": len(results.get("passes", [])),
                "screenshot": await self.take_screenshot("accessibility_test")
            }
            
            # Add to the list of accessibility issues
            for violation in violations:
                for node in violation.get("nodes", []):
                    self.accessibility_issues.append({
                        "component": node.get("html", "Unknown"),
                        "issue": violation.get("description", "Unknown issue"),
                        "impact": violation.get("impact", "Unknown"),
                        "url": self.page.url,
                        "timestamp": datetime.now().isoformat()
                    })
            
            self.logger.info(f"Accessibility test completed. Found {len(violations)} issues")
            return accessibility_results
            
        except Exception as e:
            self.logger.error(f"Error performing accessibility test: {str(e)}")
            return {
                "url": self.page.url,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def test_component_workflow(self, component_name: str, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Test a complete workflow involving multiple interactions with a component.
        
        Args:
            component_name: Name of the component to test
            workflow_steps: List of steps to execute
                [
                    {"action": "click", "selector": ".button", "description": "Click submit button"},
                    {"action": "type", "selector": "input[name=email]", "value": "test@example.com", "description": "Enter email"}
                ]
        
        Returns:
            Dict with workflow test results
        """
        if not self.page:
            await self.setup_browser()
        
        self.logger.info(f"Testing workflow for component: {component_name} with {len(workflow_steps)} steps")
        
        workflow_result = {
            "component_name": component_name,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "success": True
        }
        
        for i, step in enumerate(workflow_steps):
            step_number = i + 1
            action = step.get("action")
            selector = step.get("selector")
            value = step.get("value")
            description = step.get("description", f"Step {step_number}: {action}")
            
            self.logger.info(f"Executing workflow step {step_number}/{len(workflow_steps)}: {description}")
            
            step_result = {
                "step_number": step_number,
                "action": action,
                "selector": selector,
                "value": value,
                "description": description,
                "start_time": datetime.now().isoformat()
            }
            
            try:
                # Execute the step based on action type
                if action == "navigate":
                    url = value
                    if url.startswith("/"):
                        # Relative URL
                        base_url = settings.FRONTEND_URL
                        url = f"{base_url}{url}"
                    success = await self.navigate(url)
                    step_result["success"] = success
                    if not success:
                        step_result["error"] = "Navigation failed"
                        workflow_result["success"] = False
                
                elif action in ["click", "type", "hover", "check", "uncheck", "select"]:
                    interaction_result = await self.interact_with_component(
                        selector=selector,
                        action=action,
                        value=value
                    )
                    step_result["success"] = interaction_result["success"]
                    if not interaction_result["success"]:
                        step_result["error"] = interaction_result.get("error", "Interaction failed")
                        workflow_result["success"] = False
                
                elif action == "wait":
                    # Wait for a specific amount of time or for an element
                    if selector:
                        # Wait for element
                        try:
                            await self.page.wait_for_selector(selector, timeout=int(value or 10000))
                            step_result["success"] = True
                        except Exception as e:
                            step_result["success"] = False
                            step_result["error"] = f"Wait for selector failed: {str(e)}"
                            workflow_result["success"] = False
                    else:
                        # Wait for time
                        time_ms = int(value or 1000)
                        await asyncio.sleep(time_ms / 1000)
                        step_result["success"] = True
                
                elif action == "assert":
                    # Assert that an element exists or has specific content
                    assertion_type = step.get("assertion_type", "exists")
                    
                    if assertion_type == "exists":
                        try:
                            element = await self.page.wait_for_selector(selector, timeout=5000)
                            step_result["success"] = element is not None
                            if not element:
                                step_result["error"] = f"Element does not exist: {selector}"
                                workflow_result["success"] = False
                        except Exception as e:
                            step_result["success"] = False
                            step_result["error"] = f"Assertion failed: {str(e)}"
                            workflow_result["success"] = False
                    
                    elif assertion_type == "text":
                        try:
                            element = await self.page.wait_for_selector(selector, timeout=5000)
                            if not element:
                                step_result["success"] = False
                                step_result["error"] = f"Element does not exist: {selector}"
                                workflow_result["success"] = False
                            else:
                                text = await element.text_content()
                                expected_text = value or ""
                                if expected_text in text:
                                    step_result["success"] = True
                                else:
                                    step_result["success"] = False
                                    step_result["error"] = f"Text mismatch. Expected: '{expected_text}', Actual: '{text}'"
                                    workflow_result["success"] = False
                        except Exception as e:
                            step_result["success"] = False
                            step_result["error"] = f"Assertion failed: {str(e)}"
                            workflow_result["success"] = False
                
                else:
                    step_result["success"] = False
                    step_result["error"] = f"Unknown action type: {action}"
                    workflow_result["success"] = False
                
                # Take a screenshot after each step
                screenshot_path = await self.take_screenshot(f"workflow_{component_name}_step_{step_number}")
                step_result["screenshot"] = screenshot_path
                
            except Exception as e:
                step_result["success"] = False
                step_result["error"] = f"Step execution error: {str(e)}"
                workflow_result["success"] = False
                
                # Take an error screenshot
                if settings.SCREENSHOT_ON_FAILURE:
                    screenshot_path = await self.take_screenshot(f"error_workflow_{component_name}_step_{step_number}")
                    step_result["error_screenshot"] = screenshot_path
            
            # Record step completion
            step_result["end_time"] = datetime.now().isoformat()
            workflow_result["steps"].append(step_result)
            
            # If a step failed and we shouldn't continue on failure, break the loop
            if not step_result["success"] and not step.get("continue_on_failure", False):
                self.logger.warning(f"Workflow step {step_number} failed, stopping workflow execution")
                break
        
        # Finalize workflow result
        workflow_result["end_time"] = datetime.now().isoformat()
        workflow_result["success_rate"] = sum(1 for step in workflow_result["steps"] if step["success"]) / len(workflow_result["steps"])
        
        self.logger.info(f"Workflow test completed with success rate: {workflow_result['success_rate']:.2%}")
        return workflow_result
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run UI component tests using AI-driven testing."""
        try:
            # Start with the homepage
            await self.navigate(settings.FRONTEND_URL)
            
            # Observe the initial state
            observation = await self.observe("Initial page load")
            
            # Use AI to identify important components to test
            prompt = f"""
            Based on the current page at {self.page.url}, identify key UI components that should be tested.
            The page title is: {observation.get('title', 'Unknown')}
            
            Please provide a JSON response with a list of components to test, including:
            1. Component name
            2. CSS selector to find the component
            3. Type of component (button, input, form, etc.)
            4. Priority (high, medium, low)
            5. Suggested tests (click, type, etc.)
            
            The response should look like:
            {{
                "components": [
                    {{
                        "name": "Login Button",
                        "selector": ".login-btn",
                        "type": "button",
                        "priority": "high",
                        "tests": [
                            {{"action": "click", "expected": "Should navigate to login page"}}
                        ]
                    }},
                    // More components...
                ]
            }}
            
            Return ONLY the JSON with no additional text.
            """
            
            components_to_test = []
            try:
                response = await self.think(prompt)
                
                # Extract JSON from the response
                response = response.strip()
                first_brace = response.find('{')
                last_brace = response.rfind('}')
                if first_brace != -1 and last_brace != -1:
                    json_str = response[first_brace:last_brace+1]
                    components_json = json.loads(json_str)
                else:
                    components_json = json.loads(response)
                
                components_to_test = components_json.get("components", [])
                self.logger.info(f"AI identified {len(components_to_test)} components to test")
                
            except Exception as e:
                self.logger.error(f"Error parsing AI response for components: {str(e)}")
                # Fallback to basic components
                components_to_test = [
                    {
                        "name": "Dashboard",
                        "selector": ".dashboard-container",
                        "type": "container",
                        "priority": "high",
                        "tests": [{"action": "observe", "expected": "Should contain main content"}]
                    }
                ]
            
            # Test each component based on priority
            results = []
            for component in sorted(components_to_test, key=lambda c: {"high": 0, "medium": 1, "low": 2}.get(c.get("priority", "low"), 3)):
                
                component_name = component.get("name", "Unknown")
                selector = component.get("selector", "")
                
                # First, analyze the component
                analysis = await self.analyze_component(component_name, selector)
                
                # If component exists, run the tests
                if analysis.get("exists", False):
                    # Process each test for this component
                    for test in component.get("tests", []):
                        action = test.get("action", "observe")
                        
                        if action == "observe":
                            # Already done during analysis
                            pass
                        elif action in ["click", "type", "hover", "check", "uncheck", "select"]:
                            # Run interaction test
                            value = test.get("value", "")
                            interaction_result = await self.interact_with_component(
                                selector=selector,
                                action=action,
                                value=value
                            )
                            results.append(interaction_result)
                
                # Add accessibility test if this is a high priority component
                if component.get("priority") == "high":
                    await self.perform_accessibility_test()
            
            # Finally, generate report
            return await self.generate_report()
                
        except Exception as e:
            self.logger.error(f"Error during UI tests: {str(e)}")
            return {
                "error": str(e),
                "components_tested": len(self.components_tested),
                "interactions": len(self.interaction_history),
                "accessibility_issues": len(self.accessibility_issues)
            }
        finally:
            await self.close()

    async def take_screenshot(self, name: str) -> str:
        """Take a screenshot of the current page state."""
        if not self.page:
            await self.setup_browser()
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = settings.RESULTS_DIR / "screenshots" / filename
        
        await self.page.screenshot(path=str(filepath))
        self.logger.info(f"Screenshot saved to {filepath}")
        
        return str(filepath) 