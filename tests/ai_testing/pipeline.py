"""
Pipeline orchestrator that coordinates the execution of AI-powered testing agents.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tests.ai_testing.agents.ui_agent import UIAgent
from tests.ai_testing.agents.api_agent import APIAgent
from tests.ai_testing.agents.performance_agent import PerformanceAgent
from tests.ai_testing.config import settings

# Configure logging
os.makedirs(settings.LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(settings.LOGS_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AI-Testing-Pipeline")

class TestingPipeline:
    """Orchestrates the execution of AI-powered testing agents."""
    
    def __init__(self):
        self.ui_agent = None
        self.api_agent = None
        self.performance_agent = None
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # Create necessary directories
        os.makedirs(settings.LOGS_DIR, exist_ok=True)
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
        os.makedirs(os.path.join(settings.RESULTS_DIR, "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(settings.RESULTS_DIR, "videos"), exist_ok=True)
        
        logger.info("Testing pipeline initialized")
    
    async def setup_agents(self):
        """Initialize all testing agents."""
        logger.info("Setting up testing agents")
        
        try:
            # Initialize UI Agent
            logger.info("Initializing UI Agent")
            self.ui_agent = UIAgent(name="UITester", model_type=settings.AGENT_TYPE)
            logger.info("UI Agent initialized, calling setup")
            await self.ui_agent.setup()
            logger.info("UI Agent setup completed")
            
            # Initialize API Agent
            logger.info("Initializing API Agent")
            self.api_agent = APIAgent(name="APITester", model_type=settings.AGENT_TYPE)
            logger.info("API Agent initialized, calling setup")
            await self.api_agent.setup()
            logger.info("API Agent setup completed")
            
            # Initialize Performance Agent
            logger.info("Initializing Performance Agent")
            self.performance_agent = PerformanceAgent(name="PerformanceTester", model_type=settings.AGENT_TYPE)
            logger.info("Performance Agent initialized, calling setup")
            await self.performance_agent.setup()
            logger.info("Performance Agent setup completed")
            
            logger.info("All agents are ready")
        except Exception as e:
            logger.error(f"Error in setup_agents: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def close_agents(self):
        """Close all agents and release resources."""
        logger.info("Closing all agents")
        
        if self.ui_agent:
            await self.ui_agent.close()
        
        if self.api_agent:
            await self.api_agent.close()
        
        if self.performance_agent:
            await self.performance_agent.close()
        
        logger.info("All agents closed")
    
    async def run_frontend_tests(self):
        """Run frontend tests using the UI Agent."""
        logger.info("Starting frontend tests")
        
        try:
            # Test core UI components
            ui_components = [
                "header",
                "navigation",
                "footer",
                "job-list",
                "candidate-list",
                "match-results",
                "upload-form",
                "search-bar",
                "filters",
                "pagination"
            ]
            
            ui_results = {}
            
            for component in ui_components:
                logger.info(f"Testing UI component: {component}")
                result = await self.ui_agent.analyze_component(component)
                ui_results[component] = result
            
            # Test user workflows
            workflows = [
                {
                    "name": "job-search",
                    "steps": [
                        {"action": "navigate", "url": settings.FRONTEND_URL},
                        {"action": "click", "selector": "nav a[href='/jobs']"},
                        {"action": "wait_for_selector", "selector": ".job-list"},
                        {"action": "type", "selector": ".search-bar input", "text": "Python Developer"},
                        {"action": "click", "selector": ".search-button"},
                        {"action": "wait_for_selector", "selector": ".job-results"}
                    ]
                },
                {
                    "name": "resume-upload",
                    "steps": [
                        {"action": "navigate", "url": settings.FRONTEND_URL},
                        {"action": "click", "selector": "nav a[href='/candidates']"},
                        {"action": "wait_for_selector", "selector": ".upload-section"},
                        {"action": "upload", "selector": "input[type='file']", "file_path": "tests/ai_testing/fixtures/sample_resume.pdf"},
                        {"action": "wait_for_selector", "selector": ".analysis-results"}
                    ]
                }
            ]
            
            workflow_results = {}
            
            for workflow in workflows:
                logger.info(f"Testing workflow: {workflow['name']}")
                result = await self.ui_agent.execute_workflow(workflow["steps"])
                workflow_results[workflow["name"]] = result
            
            # Test accessibility
            logger.info("Testing accessibility")
            pages_to_test = [
                settings.FRONTEND_URL,
                f"{settings.FRONTEND_URL}/jobs",
                f"{settings.FRONTEND_URL}/candidates",
                f"{settings.FRONTEND_URL}/matches"
            ]
            
            accessibility_results = {}
            
            for page_url in pages_to_test:
                logger.info(f"Testing accessibility for page: {page_url}")
                result = await self.ui_agent.test_accessibility(page_url)
                page_key = page_url.replace(settings.FRONTEND_URL, "").strip("/") or "homepage"
                accessibility_results[page_key] = result
            
            # Combine all frontend results
            frontend_results = {
                "components": ui_results,
                "workflows": workflow_results,
                "accessibility": accessibility_results,
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate a report
            await self.ui_agent.generate_report(
                title="Frontend Test Results",
                data=frontend_results
            )
            
            self.results["frontend"] = frontend_results
            logger.info("Frontend tests completed")
            
            return frontend_results
            
        except Exception as e:
            logger.error(f"Error during frontend tests: {str(e)}")
            self.results["frontend"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def run_backend_tests(self):
        """Run backend tests using the API Agent."""
        logger.info("Starting backend tests")
        
        try:
            # Run API tests
            api_results = await self.api_agent.run_tests()
            
            self.results["backend"] = api_results
            logger.info("Backend tests completed")
            
            return api_results
            
        except Exception as e:
            logger.error(f"Error during backend tests: {str(e)}")
            self.results["backend"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def run_performance_tests(self):
        """Run performance tests using the Performance Agent."""
        logger.info("Starting performance tests")
        
        try:
            # Run performance tests
            performance_results = await self.performance_agent.run_performance_tests()
            
            self.results["performance"] = performance_results
            logger.info("Performance tests completed")
            
            return performance_results
            
        except Exception as e:
            logger.error(f"Error during performance tests: {str(e)}")
            self.results["performance"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def generate_final_report(self):
        """Generate a comprehensive final report combining all test results."""
        logger.info("Generating final report")
        
        try:
            # Calculate overall metrics
            total_tests = 0
            passed_tests = 0
            failed_tests = 0
            
            # Count frontend tests
            frontend_results = self.results.get("frontend", {})
            if "components" in frontend_results:
                for component, result in frontend_results["components"].items():
                    total_tests += 1
                    if result.get("success") == True:
                        passed_tests += 1
                    else:
                        failed_tests += 1
            
            # Count workflow tests
            if "workflows" in frontend_results:
                for workflow, result in frontend_results["workflows"].items():
                    total_tests += 1
                    if result.get("success") == True:
                        passed_tests += 1
                    else:
                        failed_tests += 1
            
            # Count backend tests
            backend_results = self.results.get("backend", {})
            if "api_endpoints_tested" in backend_results:
                for endpoint_test in backend_results.get("api_endpoints_tested", []):
                    total_tests += 1
                    if endpoint_test.get("success") == True:
                        passed_tests += 1
                    else:
                        failed_tests += 1
            
            # Calculate test duration
            duration_seconds = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None
            
            # Create final report
            final_report = {
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                    "duration_seconds": duration_seconds,
                    "start_time": self.start_time.isoformat() if self.start_time else None,
                    "end_time": self.end_time.isoformat() if self.end_time else None
                },
                "results": self.results,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save the report to file
            report_path = os.path.join(settings.RESULTS_DIR, f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_path, 'w') as f:
                json.dump(final_report, f, indent=2)
            
            # Generate a markdown report
            md_report_path = os.path.join(settings.RESULTS_DIR, f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            
            with open(md_report_path, 'w') as f:
                f.write(f"# AI Testing Framework Report\n\n")
                f.write(f"## Summary\n\n")
                f.write(f"- **Total Tests:** {total_tests}\n")
                f.write(f"- **Passed Tests:** {passed_tests}\n")
                f.write(f"- **Failed Tests:** {failed_tests}\n")
                f.write(f"- **Pass Rate:** {(passed_tests / total_tests) * 100 if total_tests > 0 else 0:.2f}%\n")
                f.write(f"- **Duration:** {duration_seconds:.2f} seconds\n")
                f.write(f"- **Start Time:** {self.start_time.isoformat() if self.start_time else 'N/A'}\n")
                f.write(f"- **End Time:** {self.end_time.isoformat() if self.end_time else 'N/A'}\n\n")
                
                # Frontend results
                f.write(f"## Frontend Test Results\n\n")
                if "error" in frontend_results:
                    f.write(f"**Error:** {frontend_results['error']}\n\n")
                else:
                    # Components
                    if "components" in frontend_results:
                        f.write(f"### UI Components\n\n")
                        for component, result in frontend_results["components"].items():
                            status = "✅ Passed" if result.get("success") == True else "❌ Failed"
                            f.write(f"- **{component}:** {status}\n")
                            if "issues" in result and result["issues"]:
                                f.write(f"  - Issues: {', '.join(result['issues'])}\n")
                        f.write(f"\n")
                    
                    # Workflows
                    if "workflows" in frontend_results:
                        f.write(f"### User Workflows\n\n")
                        for workflow, result in frontend_results["workflows"].items():
                            status = "✅ Passed" if result.get("success") == True else "❌ Failed"
                            f.write(f"- **{workflow}:** {status}\n")
                            if "issues" in result and result["issues"]:
                                f.write(f"  - Issues: {', '.join(result['issues'])}\n")
                        f.write(f"\n")
                    
                    # Accessibility
                    if "accessibility" in frontend_results:
                        f.write(f"### Accessibility\n\n")
                        for page, result in frontend_results["accessibility"].items():
                            violations_count = len(result.get("violations", []))
                            status = "✅ Passed" if violations_count == 0 else f"❌ Failed ({violations_count} violations)"
                            f.write(f"- **{page}:** {status}\n")
                        f.write(f"\n")
                
                # Backend results
                f.write(f"## Backend Test Results\n\n")
                if "error" in backend_results:
                    f.write(f"**Error:** {backend_results['error']}\n\n")
                else:
                    # API endpoints
                    if "api_endpoints_tested" in backend_results:
                        f.write(f"### API Endpoints\n\n")
                        for endpoint_test in backend_results.get("api_endpoints_tested", []):
                            method = endpoint_test.get("method", "")
                            endpoint = endpoint_test.get("endpoint", "")
                            status = "✅ Passed" if endpoint_test.get("success") == True else "❌ Failed"
                            status_code = endpoint_test.get("status_code", "")
                            f.write(f"- **{method} {endpoint}:** {status} (Status Code: {status_code})\n")
                            if "error" in endpoint_test:
                                f.write(f"  - Error: {endpoint_test['error']}\n")
                        f.write(f"\n")
                
                # Performance results
                f.write(f"## Performance Test Results\n\n")
                performance_results = self.results.get("performance", {})
                if "error" in performance_results:
                    f.write(f"**Error:** {performance_results['error']}\n\n")
                else:
                    # Frontend performance
                    if "performance_metrics" in performance_results and "frontend" in performance_results["performance_metrics"]:
                        f.write(f"### Frontend Performance\n\n")
                        frontend_metrics = performance_results["performance_metrics"]["frontend"]
                        for page, metrics in frontend_metrics.items():
                            f.write(f"#### {page}\n\n")
                            if "metrics" in metrics and metrics["metrics"]:
                                f.write(f"- **Mean Load Time:** {metrics['metrics'].get('mean_ms', 'N/A'):.2f} ms\n")
                                f.write(f"- **Median Load Time:** {metrics['metrics'].get('median_ms', 'N/A'):.2f} ms\n")
                                f.write(f"- **Min Load Time:** {metrics['metrics'].get('min_ms', 'N/A'):.2f} ms\n")
                                f.write(f"- **Max Load Time:** {metrics['metrics'].get('max_ms', 'N/A'):.2f} ms\n")
                                if metrics['metrics'].get('std_dev_ms') is not None:
                                    f.write(f"- **Std Dev:** {metrics['metrics'].get('std_dev_ms'):.2f} ms\n")
                                f.write(f"- **Success Rate:** {metrics.get('success_rate', 'N/A'):.2f}%\n")
                                f.write(f"\n")
                    
                    # Backend performance
                    if "performance_metrics" in performance_results and "backend" in performance_results["performance_metrics"]:
                        f.write(f"### Backend Performance\n\n")
                        backend_metrics = performance_results["performance_metrics"]["backend"]
                        for endpoint, metrics in backend_metrics.items():
                            f.write(f"#### {endpoint}\n\n")
                            if "metrics" in metrics and metrics["metrics"]:
                                f.write(f"- **Mean Response Time:** {metrics['metrics'].get('mean_ms', 'N/A'):.2f} ms\n")
                                f.write(f"- **Median Response Time:** {metrics['metrics'].get('median_ms', 'N/A'):.2f} ms\n")
                                f.write(f"- **Min Response Time:** {metrics['metrics'].get('min_ms', 'N/A'):.2f} ms\n")
                                f.write(f"- **Max Response Time:** {metrics['metrics'].get('max_ms', 'N/A'):.2f} ms\n")
                                if metrics['metrics'].get('std_dev_ms') is not None:
                                    f.write(f"- **Std Dev:** {metrics['metrics'].get('std_dev_ms'):.2f} ms\n")
                                f.write(f"- **Success Rate:** {metrics.get('success_rate', 'N/A'):.2f}%\n")
                                f.write(f"\n")
                    
                    # Bottleneck analysis
                    if "bottleneck_analysis" in performance_results:
                        f.write(f"### Performance Bottlenecks\n\n")
                        bottleneck = performance_results["bottleneck_analysis"].get("bottleneck_analysis", {})
                        
                        if "identified_bottlenecks" in bottleneck:
                            f.write(f"#### Identified Bottlenecks\n\n")
                            for bottleneck_item in bottleneck["identified_bottlenecks"]:
                                f.write(f"- {bottleneck_item}\n")
                            f.write(f"\n")
                        
                        if "potential_causes" in bottleneck:
                            f.write(f"#### Potential Causes\n\n")
                            for cause in bottleneck["potential_causes"]:
                                f.write(f"- {cause}\n")
                            f.write(f"\n")
                        
                        if "recommended_actions" in bottleneck:
                            f.write(f"#### Recommended Actions\n\n")
                            for action in bottleneck["recommended_actions"]:
                                f.write(f"- {action}\n")
                            f.write(f"\n")
            
            logger.info(f"Final report generated at {report_path}")
            logger.info(f"Markdown report generated at {md_report_path}")
            
            return {
                "report_path": report_path,
                "md_report_path": md_report_path,
                "summary": final_report["summary"]
            }
            
        except Exception as e:
            logger.error(f"Error generating final report: {str(e)}")
            return {"error": str(e)}
    
    async def run_pipeline(self, tests_to_run=None):
        """
        Run the full testing pipeline.
        
        Args:
            tests_to_run: List of tests to run (default: all tests)
        """
        logger.info("Starting testing pipeline")
        self.start_time = datetime.now()
        
        try:
            # Setup agents
            await self.setup_agents()
            
            # Determine which tests to run
            if tests_to_run is None:
                tests_to_run = ["frontend", "backend", "performance"]
            
            # Run tests in parallel
            tasks = []
            
            if "frontend" in tests_to_run:
                tasks.append(self.run_frontend_tests())
            
            if "backend" in tests_to_run:
                tasks.append(self.run_backend_tests())
            
            if "performance" in tests_to_run:
                tasks.append(self.run_performance_tests())
            
            # Wait for all tests to complete
            await asyncio.gather(*tasks)
            
            # Generate final report
            self.end_time = datetime.now()
            final_report = await self.generate_final_report()
            
            logger.info("Testing pipeline completed")
            return final_report
            
        except Exception as e:
            logger.error(f"Error in testing pipeline: {str(e)}")
            self.end_time = datetime.now()
            return {"error": str(e)}
        finally:
            # Close agents
            await self.close_agents()

async def main():
    """Entry point for the AI testing pipeline."""
    parser = argparse.ArgumentParser(description="Run AI testing pipeline")
    parser.add_argument(
        "--tests",
        type=str,
        choices=["frontend", "backend", "performance", "all"],
        default="all",
        help="Which tests to run (default: all)"
    )
    args = parser.parse_args()
    
    # Determine which tests to run
    if args.tests == "all":
        tests_to_run = ["frontend", "backend", "performance"]
    else:
        tests_to_run = [args.tests]
    
    # Run the pipeline
    pipeline = TestingPipeline()
    result = await pipeline.run_pipeline(tests_to_run)
    
    if "error" in result:
        logger.error(f"Pipeline failed: {result['error']}")
        return 1
    
    logger.info(f"Pipeline completed successfully")
    summary = result.get("summary", {})
    logger.info(f"Total Tests: {summary.get('total_tests', 0)}")
    logger.info(f"Passed Tests: {summary.get('passed_tests', 0)}")
    logger.info(f"Failed Tests: {summary.get('failed_tests', 0)}")
    logger.info(f"Pass Rate: {summary.get('pass_rate', 0):.2f}%")
    logger.info(f"Duration: {summary.get('duration_seconds', 0):.2f} seconds")
    
    return 0

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result) 