import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime
from pathlib import Path
from .base_agent import FrontendTestAgent
from .ui_component_agent import UIComponentAgent
from .performance_agent import PerformanceAgent

class FrontendTestOrchestrator(FrontendTestAgent):
    """Orchestrates and coordinates all frontend test agents"""
    
    def __init__(self, base_url: str = "http://localhost:5173"):
        super().__init__(base_url)
        self.agents = {
            "ui_component": UIComponentAgent(base_url),
            "performance": PerformanceAgent(base_url)
        }
        self.results_dir = Path("tests/frontend/test_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = 3
        self.retry_delay = 1
    
    async def run_agent_tests(self, agent_name: str) -> Dict[str, Any]:
        """Run tests for a specific agent with retry logic"""
        agent = self.agents[agent_name]
        for attempt in range(self.max_retries):
            try:
                results = await agent.run_tests()
                return results
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        "agent_type": agent_name,
                        "timestamp": str(datetime.now()),
                        "error": str(e)
                    }
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
    
    async def analyze_all_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis of all test results"""
        prompt = f"""
        Analyze all frontend test results across different agents:
        {json.dumps(results, indent=2)}
        
        Provide a comprehensive analysis including:
        1. Overall frontend health
        2. UI component status and issues
        3. Performance characteristics
        4. User experience assessment
        5. Accessibility considerations
        6. Areas needing improvement
        7. Recommendations for enhancement
        
        Return a detailed JSON analysis.
        """
        try:
            return json.loads(await self.think(prompt))
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": str(datetime.now()),
                "status": "analysis_failed"
            }
    
    async def generate_report(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate a human-readable test report"""
        prompt = f"""
        Generate a detailed frontend test report from these results and analysis:
        Results: {json.dumps(results, indent=2)}
        Analysis: {json.dumps(analysis, indent=2)}
        
        Include:
        1. Executive Summary
        2. Test Coverage Overview
        3. UI Component Status
        4. Performance Metrics
        5. User Experience Evaluation
        6. Accessibility Assessment
        7. Risk Assessment
        8. Recommendations
        9. Next Steps
        
        Format the report in markdown with sections and subsections.
        """
        try:
            return await self.think(prompt)
        except Exception as e:
            return f"""# Frontend Test Report

## Error Generating Report
{str(e)}

## Raw Results
{json.dumps(results, indent=2)}

## Raw Analysis
{json.dumps(analysis, indent=2)}
"""
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run all tests across all agents"""
        results = {
            "orchestrator_type": "FrontendTestOrchestrator",
            "timestamp": str(datetime.now()),
            "agent_results": {},
            "system_metrics": {
                "total_components_tested": 0,
                "total_routes_tested": 0,
                "completion_time": None,
                "component_status": {}
            }
        }
        
        try:
            # Run tests for each agent
            for agent_name in self.agents:
                results["agent_results"][agent_name] = await self.run_agent_tests(agent_name)
                
                # Update component status
                if agent_name == "ui_component":
                    ui_results = results["agent_results"][agent_name]
                    if "components_tested" in ui_results:
                        results["system_metrics"]["total_components_tested"] += ui_results["components_tested"]
                    if "components_passed" in ui_results and "components_tested" in ui_results:
                        results["system_metrics"]["component_status"]["ui_components"] = (
                            f"{ui_results['components_passed']}/{ui_results['components_tested']} passed"
                        )
                        
                # Update route status
                if agent_name == "performance":
                    perf_results = results["agent_results"][agent_name]
                    if "routes_tested" in perf_results:
                        results["system_metrics"]["total_routes_tested"] += perf_results["routes_tested"]
            
            # Record completion time
            results["system_metrics"]["completion_time"] = str(datetime.now())
            
            # Save raw results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.results_dir / f"frontend_test_results_{timestamp}.json"
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            
            # Generate comprehensive analysis
            try:
                results["analysis"] = await self.analyze_all_results(results)
            except Exception as e:
                results["analysis_error"] = str(e)
            
            # Generate human-readable report
            try:
                report = await self.generate_report(
                    results,
                    results.get("analysis", {"error": "Analysis failed"})
                )
                results["report"] = report
                
                # Save report to file
                report_file = self.results_dir / f"frontend_test_report_{timestamp}.md"
                with open(report_file, "w") as f:
                    f.write(report)
                    
            except Exception as e:
                results["report_error"] = str(e)
            
        except Exception as e:
            results["error"] = str(e)
        
        return results

async def run_frontend_test_suite(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
    """Run the complete frontend test suite"""
    orchestrator = FrontendTestOrchestrator(base_url)
    try:
        results = await orchestrator.run_tests()
        return results
    finally:
        await orchestrator.close()
        for agent in orchestrator.agents.values():
            await agent.close()

if __name__ == "__main__":
    import sys
    
    async def main():
        base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
        results = await run_frontend_test_suite(base_url)
        print(json.dumps(results, indent=2))
    
    asyncio.run(main()) 