"""
Base AI Agent class that provides core functionality for all testing agents.
"""

import os
import time
import json
import logging
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import google.generativeai as genai
import openai
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from tests.ai_testing.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.AGENT_VERBOSE else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.RESULTS_DIR / "logs" / f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

class BaseAgent(ABC):
    """Base class for all AI testing agents."""
    
    def __init__(self, name: str, model_type: str = settings.AGENT_TYPE):
        """Initialize the base agent."""
        self.name = name
        self.model_type = model_type
        self.logger = logging.getLogger(f"agent.{name}")
        self.memory = []  # Store context and history
        self.observations = []  # Store agent observations
        self.execution_steps = []  # Store executed steps
        self.start_time = time.time()
        self.setup_ai_model()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        self.logger.info(f"Initialized {self.name} agent with {self.model_type} model")
    
    async def setup(self):
        """Base setup method that can be overridden by subclasses."""
        self.logger.info(f"Setting up {self.name} agent")
        # This is a base implementation that can be extended by subclasses
        return True
    
    def setup_ai_model(self):
        """Setup the AI model based on the specified type."""
        if self.model_type == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not found in environment variables.")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config={
                    "temperature": settings.AGENT_TEMPERATURE,
                    "max_output_tokens": settings.MAX_TOKENS_OUTPUT,
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )
            self.logger.info("Gemini AI model initialized")
        elif self.model_type == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in environment variables.")
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.logger.info("OpenAI model initialized")
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    async def setup_browser(self):
        """Initialize the browser for web testing."""
        self.logger.info("Setting up browser")
        try:
            self.logger.info("Starting playwright")
            self.playwright = await async_playwright().start()
            self.logger.info(f"Playwright started: {self.playwright}")
            
            self.logger.info(f"Getting browser type: {settings.BROWSER}")
            browser_type = getattr(self.playwright, settings.BROWSER)
            self.logger.info(f"Browser type: {browser_type}")
            
            self.logger.info(f"Launching browser with headless={settings.HEADLESS}")
            self.browser = await browser_type.launch(headless=settings.HEADLESS)
            self.logger.info(f"Browser launched: {self.browser}")
            
            # Create a browser context with video recording if enabled
            context_options = {}
            if settings.VIDEO_RECORDING:
                self.logger.info(f"Setting up video recording at {settings.RESULTS_DIR / 'videos'}")
                context_options["record_video_dir"] = str(settings.RESULTS_DIR / "videos")
            
            self.logger.info("Creating browser context")
            self.context = await self.browser.new_context(**context_options)
            self.logger.info(f"Browser context created: {self.context}")
            
            self.logger.info("Creating new page")
            self.page = await self.context.new_page()
            self.logger.info(f"Page created: {self.page}")
            
            if self.page:
                self.logger.info(f"Setting default timeout to {settings.TIMEOUT}ms")
                await self.page.set_default_timeout(settings.TIMEOUT)
                self.logger.info(f"Browser setup complete: {settings.BROWSER}")
            else:
                self.logger.error("Failed to create page")
                raise Exception("Failed to create page")
        except Exception as e:
            self.logger.error(f"Error setting up browser: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Clean up any resources that were created
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            raise
    
    async def navigate(self, url: str) -> bool:
        """Navigate to a URL and return success status."""
        if not self.page:
            await self.setup_browser()
        
        self.logger.info(f"Navigating to: {url}")
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            success = response and response.ok
            if success:
                self.logger.info(f"Successfully navigated to {url}")
                return True
            else:
                self.logger.warning(f"Navigation to {url} failed or returned non-OK status")
                return False
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            if settings.SCREENSHOT_ON_FAILURE:
                await self.take_screenshot(f"navigation_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            return False
    
    async def take_screenshot(self, name: str) -> str:
        """Take a screenshot of the current page."""
        if not self.page:
            self.logger.warning("Cannot take screenshot: Browser not initialized")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = settings.RESULTS_DIR / "screenshots" / filename
        
        try:
            await self.page.screenshot(path=str(filepath), full_page=True)
            self.logger.info(f"Screenshot saved: {filename}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return ""
    
    async def think(self, prompt: str) -> str:
        """Generate a response using the AI model."""
        self.logger.info(f"Thinking about: {prompt[:100]}...")
        
        # Add to memory for context
        self.memory.append({"role": "user", "content": prompt})
        
        try:
            if self.model_type == "gemini":
                response = await asyncio.to_thread(
                    lambda: self.model.generate_content(prompt).text
                )
            elif self.model_type == "openai":
                completion = await asyncio.to_thread(
                    lambda: self.client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=settings.AGENT_TEMPERATURE,
                        max_tokens=settings.MAX_TOKENS_OUTPUT
                    )
                )
                response = completion.choices[0].message.content
            
            # Add to memory
            self.memory.append({"role": "assistant", "content": response})
            self.logger.debug(f"Generated response: {response[:100]}...")
            return response
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"Error: {str(e)}"
    
    async def observe(self, description: str = None) -> Dict[str, Any]:
        """
        Observe the current state of the application.
        Returns a dictionary of observations.
        """
        if not self.page:
            self.logger.warning("Cannot observe: Browser not initialized")
            return {"error": "Browser not initialized"}
        
        observation = {
            "timestamp": datetime.now().isoformat(),
            "url": self.page.url,
            "title": await self.page.title(),
        }
        
        if description:
            observation["description"] = description
        
        try:
            # Get the page content
            html_content = await self.page.content()
            observation["html_length"] = len(html_content)
            
            # Take a screenshot
            screenshot_path = await self.take_screenshot(f"observation_{len(self.observations)}")
            observation["screenshot"] = screenshot_path
            
            # Store the observation
            self.observations.append(observation)
            self.logger.info(f"Observation recorded: {observation['url']}")
            
            return observation
        except Exception as e:
            self.logger.error(f"Error during observation: {str(e)}")
            observation["error"] = str(e)
            self.observations.append(observation)
            return observation
    
    async def execute_step(self, step_description: str, action_fn) -> Dict[str, Any]:
        """
        Execute a testing step and record the results.
        
        Args:
            step_description: Description of the step
            action_fn: Async function to execute
            
        Returns:
            Dictionary with step results
        """
        self.logger.info(f"Executing step: {step_description}")
        
        step_result = {
            "description": step_description,
            "start_time": datetime.now().isoformat(),
            "status": "started"
        }
        
        try:
            result = await action_fn()
            step_result["result"] = result
            step_result["status"] = "completed"
            self.logger.info(f"Step completed successfully: {step_description}")
        except Exception as e:
            step_result["error"] = str(e)
            step_result["status"] = "failed"
            self.logger.error(f"Step failed: {step_description} - Error: {str(e)}")
            if settings.SCREENSHOT_ON_FAILURE and self.page:
                screenshot_path = await self.take_screenshot(f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                step_result["error_screenshot"] = screenshot_path
        finally:
            step_result["end_time"] = datetime.now().isoformat()
            self.execution_steps.append(step_result)
        
        return step_result
    
    async def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the test execution.
        """
        duration = time.time() - self.start_time
        passed_steps = sum(1 for step in self.execution_steps if step["status"] == "completed")
        failed_steps = sum(1 for step in self.execution_steps if step["status"] == "failed")
        
        report = {
            "agent_name": self.name,
            "model_type": self.model_type,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": duration,
            "total_steps": len(self.execution_steps),
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "success_rate": passed_steps / len(self.execution_steps) if self.execution_steps else 0,
            "observations": len(self.observations),
            "steps": self.execution_steps
        }
        
        # Save report to file
        report_path = settings.RESULTS_DIR / "reports" / f"report_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Report generated and saved to {report_path}")
        return report
    
    async def close(self):
        """Close all resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        self.logger.info("All resources closed")
    
    @abstractmethod
    async def run_tests(self) -> Dict[str, Any]:
        """
        Run the agent's test suite.
        Must be implemented by subclasses.
        """
        pass 