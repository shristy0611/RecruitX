"""
Enhanced UI Agent with debugging capabilities.

This module provides a UI testing agent that incorporates advanced debugging features
for better visibility into agent behavior and decision-making.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import asdict

from playwright.async_api import Page, Browser, async_playwright

from tests.ai_testing.tools.debugging_tools import (
    TraceEvent,
    AgentDebugger,
    debugger as global_debugger
)

logger = logging.getLogger(__name__)

class EnhancedUIAgent:
    """UI testing agent with advanced debugging capabilities."""
    
    def __init__(
        self,
        name: str,
        model_type: str = "gemini",
        record_mode: bool = False,
        auto_instrument: bool = True
    ):
        self.name = name
        self.model_type = model_type
        self.record_mode = record_mode
        self.auto_instrument = auto_instrument
        
        # Initialize debugging components
        self._debugger = global_debugger
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def setup(self):
        """Set up the agent with browser and debugging."""
        try:
            # Start debugging session
            await self._debugger.start_debugging_session(self.name)
            logger.info(f"Started debugging session for agent {self.name}")
            
            # Record setup event
            await self._record_event(
                event_type="setup",
                action="initialize",
                context={
                    "model_type": self.model_type,
                    "record_mode": self.record_mode,
                    "auto_instrument": self.auto_instrument
                }
            )
            
            # Set up browser
            await self.setup_browser()
            logger.info("Browser setup complete")
            
        except Exception as e:
            error_msg = f"Error during agent setup: {str(e)}"
            logger.error(error_msg)
            await self._record_event(
                event_type="setup",
                action="initialize",
                context={},
                error=error_msg
            )
            raise
            
    async def setup_browser(self):
        """Set up the browser for UI testing."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            
            # Enable automatic tracing if requested
            if self.auto_instrument:
                await self._setup_auto_instrumentation()
                
        except Exception as e:
            error_msg = f"Error setting up browser: {str(e)}"
            logger.error(error_msg)
            await self._record_event(
                event_type="browser",
                action="setup",
                context={},
                error=error_msg
            )
            raise
            
    async def _setup_auto_instrumentation(self):
        """Set up automatic instrumentation of page events."""
        if not self.page:
            return
            
        # Monitor page events
        self.page.on("console", lambda msg: self._handle_console_message(msg))
        self.page.on("pageerror", lambda err: self._handle_page_error(err))
        self.page.on("request", lambda req: self._handle_request(req))
        self.page.on("response", lambda res: self._handle_response(res))
        
        logger.info("Automatic instrumentation set up")
        
    async def navigate(self, url: str):
        """Navigate to a URL with debugging."""
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            await self._record_event(
                event_type="navigation",
                action="start",
                context={"url": url}
            )
            
            await self.page.goto(url)
            
            await self._record_event(
                event_type="navigation",
                action="complete",
                context={"url": url}
            )
            
        except Exception as e:
            error_msg = f"Error navigating to {url}: {str(e)}"
            logger.error(error_msg)
            await self._record_event(
                event_type="navigation",
                action="error",
                context={"url": url},
                error=error_msg
            )
            raise
            
    async def smart_interaction(
        self,
        component_name: str,
        action: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Perform a smart interaction with a UI component."""
        try:
            await self._record_event(
                event_type="interaction",
                action=f"start_{action}",
                context={
                    "component": component_name,
                    "action": action,
                    "params": kwargs
                }
            )
            
            # Analyze the component first
            analysis = await self.analyze_component(component_name)
            
            if not analysis.get("exists", False):
                raise ValueError(f"Component '{component_name}' not found")
                
            # Perform the interaction
            result = await self.interact_with_component(
                component_name,
                action,
                analysis,
                **kwargs
            )
            
            await self._record_event(
                event_type="interaction",
                action=f"complete_{action}",
                context={
                    "component": component_name,
                    "action": action,
                    "params": kwargs
                },
                result=result
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error during {action} on {component_name}: {str(e)}"
            logger.error(error_msg)
            await self._record_event(
                event_type="interaction",
                action=f"error_{action}",
                context={
                    "component": component_name,
                    "action": action,
                    "params": kwargs
                },
                error=error_msg
            )
            raise
            
    async def analyze_component(self, component_name: str) -> Dict[str, Any]:
        """Analyze a UI component with debugging."""
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            # First try to find the component
            selector = await self._find_component(component_name)
            
            if not selector:
                return {"exists": False}
                
            # Get component properties
            element = await self.page.query_selector(selector)
            if not element:
                return {"exists": False}
                
            # Analyze the element
            properties = await element.evaluate("""element => {
                const rect = element.getBoundingClientRect();
                return {
                    tag: element.tagName.toLowerCase(),
                    id: element.id,
                    classes: Array.from(element.classList),
                    text: element.textContent,
                    visible: rect.width > 0 && rect.height > 0,
                    enabled: !element.disabled,
                    attributes: Object.fromEntries(
                        Array.from(element.attributes)
                            .map(attr => [attr.name, attr.value])
                    ),
                    position: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }
                };
            }""")
            
            analysis = {
                "exists": True,
                "selector": selector,
                **properties
            }
            
            await self._record_event(
                event_type="analysis",
                action="component",
                context={"component": component_name},
                result=analysis
            )
            
            return analysis
            
        except Exception as e:
            error_msg = f"Error analyzing component {component_name}: {str(e)}"
            logger.error(error_msg)
            await self._record_event(
                event_type="analysis",
                action="component",
                context={"component": component_name},
                error=error_msg
            )
            raise
            
    async def interact_with_component(
        self,
        component_name: str,
        action: str,
        analysis: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Interact with a UI component."""
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            selector = analysis["selector"]
            element = await self.page.query_selector(selector)
            
            if not element:
                raise ValueError(f"Component '{component_name}' not found")
                
            result = {}
            
            # Perform the requested action
            if action == "click":
                await element.click()
                result["clicked"] = True
                
            elif action == "type":
                text = kwargs.get("text", "")
                await element.type(text)
                result["typed"] = text
                
            elif action == "select":
                value = kwargs.get("value", "")
                await element.select_option(value=value)
                result["selected"] = value
                
            elif action == "hover":
                await element.hover()
                result["hovered"] = True
                
            elif action == "screenshot":
                path = kwargs.get("path", f"component_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                await element.screenshot(path=path)
                result["screenshot"] = path
                
            else:
                raise ValueError(f"Unsupported action: {action}")
                
            result["success"] = True
            return result
            
        except Exception as e:
            error_msg = f"Error interacting with {component_name}: {str(e)}"
            logger.error(error_msg)
            raise
            
    async def perform_accessibility_test(self) -> Dict[str, Any]:
        """Perform accessibility testing on the current page."""
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            # Inject and run axe-core
            await self.page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js")
            
            results = await self.page.evaluate("""() => {
                return new Promise(resolve => {
                    axe.run(document, {
                        runOnly: {
                            type: 'tag',
                            values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
                        }
                    }).then(results => resolve(results));
                });
            }""")
            
            await self._record_event(
                event_type="accessibility",
                action="test",
                context={},
                result=results
            )
            
            return results
            
        except Exception as e:
            error_msg = f"Error during accessibility testing: {str(e)}"
            logger.error(error_msg)
            await self._record_event(
                event_type="accessibility",
                action="test",
                context={},
                error=error_msg
            )
            raise
            
    async def take_screenshot(self, name: str = "screenshot") -> str:
        """Take a screenshot of the current page state."""
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{name}_{timestamp}.png"
            
            await self.page.screenshot(path=path)
            
            await self._record_event(
                event_type="screenshot",
                action="capture",
                context={"name": name},
                result={"path": path}
            )
            
            return path
            
        except Exception as e:
            error_msg = f"Error taking screenshot: {str(e)}"
            logger.error(error_msg)
            await self._record_event(
                event_type="screenshot",
                action="capture",
                context={"name": name},
                error=error_msg
            )
            raise
            
    async def generate_timeline_report(self) -> str:
        """Generate a timeline report of all component changes."""
        try:
            timeline = await self._debugger.visualizer.create_timeline_view(
                self._debugger.tracer.traces
            )
            return timeline
        except Exception as e:
            logger.error(f"Error generating timeline report: {str(e)}")
            raise
            
    async def generate_debug_report(self) -> Dict[str, Any]:
        """Generate a comprehensive debug report."""
        try:
            return await self._debugger.generate_debug_report()
        except Exception as e:
            logger.error(f"Error generating debug report: {str(e)}")
            raise
            
    async def close(self):
        """Clean up resources."""
        try:
            if self.browser:
                await self.browser.close()
                
            await self._record_event(
                event_type="cleanup",
                action="close",
                context={}
            )
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            
    async def _record_event(
        self,
        event_type: str,
        action: str,
        context: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Record a trace event."""
        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            agent_id=self.name,
            action=action,
            context=context,
            result=result,
            error=error
        )
        await self._debugger.record_event(event)
        
    async def _find_component(self, component_name: str) -> Optional[str]:
        """Find the best selector for a component."""
        # This would use the selector_tools module
        from tests.ai_testing.tools.selector_tools import find_best_selector
        return await find_best_selector(self.page, component_name)
        
    def _handle_console_message(self, message):
        """Handle console messages from the page."""
        logger.info(f"Console {message.type}: {message.text}")
        
    def _handle_page_error(self, error):
        """Handle page errors."""
        logger.error(f"Page error: {error}")
        
    def _handle_request(self, request):
        """Handle page requests."""
        logger.debug(f"Request: {request.method} {request.url}")
        
    def _handle_response(self, response):
        """Handle page responses."""
        logger.debug(f"Response: {response.status} {response.url}") 