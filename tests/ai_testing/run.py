#!/usr/bin/env python3
"""
AI Testing Framework Runner

This script provides a command-line interface to run tests with the AI testing framework,
with support for different test types and debugging features.
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Fix the import path issue
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, project_root)

# Now import the modules
from tests.ai_testing.config import settings
from tests.ai_testing.tools.debugging_tools import tracer, deterministic_test, visualizer, observability
from tests.ai_testing.agents.debuggable_ui_agent import EnhancedUIAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOGS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ai_testing_runner")

async def run_ui_tests(args):
    """Run UI tests with debugging features."""
    logger.info("Starting UI tests with debugging")
    
    # Initialize an EnhancedUIAgent with debugging features
    agent = EnhancedUIAgent(
        name="UITester", 
        model_type=args.model,
        record_mode=args.record,
        auto_instrument=True
    )
    
    try:
        # Setup the agent
        await agent.setup()
        logger.info("Agent setup complete")
        
        # Navigate to the application
        await agent.navigate(settings.FRONTEND_URL)
        logger.info(f"Navigated to {settings.FRONTEND_URL}")
        
        # Take a screenshot of the initial state
        await agent.take_screenshot("initial_state")
        
        # Analyze some components with debugging
        components_to_test = [
            "login form",
            "signup button",
            "file upload",
            "navigation menu",
            "search bar"
        ]
        
        test_results = []
        
        for component in components_to_test:
            logger.info(f"Testing component: {component}")
            
            # Use smart_interaction with full debugging
            result = await agent.smart_interaction(
                component_name=component,
                action="click"
            )
            
            test_results.append({
                "component": component,
                "result": result,
                "passed": result.get("success", False)
            })
            
            # Add some intentional delay to see the interactions
            await asyncio.sleep(1)
        
        # Perform an accessibility test
        accessibility_results = await agent.perform_accessibility_test()
        
        # Generate a comprehensive debug report
        debug_report = await agent.generate_debug_report()
        
        # Generate a timeline report of all component changes
        timeline_report = await agent.generate_timeline_report()
        
        # Visualize the traces
        visualizations = agent._debugger.visualize_traces() if hasattr(agent, "_debugger") else []
        
        # Generate a summary report
        summary = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "ui",
            "components_tested": len(components_to_test),
            "passed": sum(1 for r in test_results if r.get("passed", False)),
            "failed": sum(1 for r in test_results if not r.get("passed", False)),
            "accessibility_issues": len(accessibility_results.get("violations", [])),
            "visualizations": [str(v) for v in visualizations],
            "debug_report": str(debug_report),
            "timeline_report": str(timeline_report)
        }
        
        # Save the summary
        summary_path = settings.RESULTS_DIR / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Test summary saved to {summary_path}")
        logger.info(f"Tests complete: {summary['passed']}/{summary['components_tested']} passed")
        
    except Exception as e:
        logger.error(f"Error running UI tests: {str(e)}")
        raise
    finally:
        # Make sure to close the agent to release resources
        await agent.close()
        logger.info("Agent closed")

async def run_backend_tests(args):
    """Run backend API tests with debugging features."""
    logger.info("Backend tests not implemented yet")
    # This would use a DebuggableAPIAgent to test backend APIs

async def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run AI tests with debugging features")
    parser.add_argument("--tests", choices=["ui", "backend", "all"], default="all", help="Tests to run")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--record", action="store_true", help="Record LLM responses for deterministic testing")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations")
    parser.add_argument("--deterministic", action="store_true", help="Run in deterministic mode using recorded responses")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--model", choices=["gemini", "openai", "anthropic"], default=settings.AGENT_TYPE, help="AI model to use")
    
    args = parser.parse_args()
    
    # Override settings based on arguments
    settings.DEBUG_MODE = args.debug
    settings.HEADLESS = args.headless
    settings.RECORD_MODE = args.record
    settings.DETERMINISTIC_TESTING = args.deterministic
    settings.VISUALIZATION_ENABLED = args.visualize
    settings.AGENT_TYPE = args.model
    
    logger.info(f"Starting tests with: debug={args.debug}, record={args.record}, "
               f"visualize={args.visualize}, deterministic={args.deterministic}, "
               f"model={args.model}")
    
    tasks = []
    
    if args.tests in ["ui", "all"]:
        tasks.append(run_ui_tests(args))
        
    if args.tests in ["backend", "all"]:
        tasks.append(run_backend_tests(args))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main()) 