import asyncio
import json
from datetime import datetime
import os
from test_agents.orchestrator import TestOrchestrator

async def main():
    """Run the complete test suite and save results"""
    print("Starting AI-powered test suite...")
    
    # Create results directory if it doesn't exist
    results_dir = "test_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Initialize and run test orchestrator
    orchestrator = TestOrchestrator()
    try:
        results = await orchestrator.run_tests()
        
        # Generate timestamp for file names
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = os.path.join(results_dir, f"test_results_{timestamp}.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Save report if available
        if "report" in results:
            report_file = os.path.join(results_dir, f"test_report_{timestamp}.md")
            with open(report_file, "w") as f:
                f.write(results["report"])
            print(f"Report saved to: {report_file}")
        
        print(f"\nTest suite completed!")
        print(f"Results saved to: {results_file}")
        
        # Print summary
        print("\nTest Summary:")
        print("-" * 50)
        if "system_metrics" in results:
            metrics = results["system_metrics"]
            print(f"Total Tests: {metrics.get('total_tests', 'N/A')}")
            print(f"Components Tested: {', '.join(results.get('agent_results', {}).keys())}")
            print(f"Completion Time: {metrics.get('completion_time', 'N/A')}")
            print("\nComponent Status:")
            for component, status in metrics.get('component_status', {}).items():
                print(f"- {component}: {status}")
        else:
            print("No system metrics available in results")
            
    finally:
        await orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main()) 