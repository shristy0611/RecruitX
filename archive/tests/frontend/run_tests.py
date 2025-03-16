"""Frontend test runner script for RecruitX."""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.frontend.test_agents.orchestrator import run_frontend_test_suite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent / "test_results" / f"frontend_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
    ]
)

logger = logging.getLogger("frontend_tests")

async def main():
    """Run frontend tests and output results."""
    parser = argparse.ArgumentParser(description="Run frontend tests for RecruitX")
    parser.add_argument(
        "--base-url", 
        default=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        help="Base URL for the frontend application (default: http://localhost:5173)"
    )
    parser.add_argument(
        "--api-url", 
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="Base URL for the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--output", 
        default=str(Path(__file__).parent / "test_results" / f"frontend_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"),
        help="Output file path for test results"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Set environment variables
    os.environ["API_URL"] = args.api_url
    
    logger.info(f"Starting frontend tests with base URL: {args.base_url}")
    logger.info(f"API URL: {args.api_url}")
    
    try:
        # Create test results directory if it doesn't exist
        results_dir = Path(__file__).parent / "test_results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Run tests
        start_time = datetime.now()
        logger.info(f"Test execution started at {start_time}")
        
        results = await run_frontend_test_suite(args.base_url)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Test execution completed at {end_time} (duration: {duration:.2f} seconds)")
        
        # Save results to file
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Test results saved to {args.output}")
        
        # Output summary to console
        ui_result = "N/A"
        perf_result = "N/A"
        
        if "agent_results" in results:
            if "ui_component" in results["agent_results"]:
                ui_results = results["agent_results"]["ui_component"]
                if "components_passed" in ui_results and "components_tested" in ui_results:
                    pass_rate = (ui_results["components_passed"] / ui_results["components_tested"]) * 100 if ui_results["components_tested"] > 0 else 0
                    ui_result = f"{ui_results['components_passed']}/{ui_results['components_tested']} components passed ({pass_rate:.1f}%)"
            
            if "performance" in results["agent_results"]:
                perf_results = results["agent_results"]["performance"]
                if "summary" in perf_results:
                    if "avg_load_time_all_routes" in perf_results["summary"]:
                        perf_result = f"Avg load time: {perf_results['summary']['avg_load_time_all_routes']:.2f}s"
        
        logger.info("=== Frontend Test Summary ===")
        logger.info(f"UI Components: {ui_result}")
        logger.info(f"Performance: {perf_result}")
        
        # Check if report is available
        if "report" in results:
            report_file = Path(args.output).with_suffix(".md")
            with open(report_file, "w") as f:
                f.write(results["report"])
            logger.info(f"Detailed report available at {report_file}")
    
    except Exception as e:
        logger.error(f"Error running frontend tests: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 