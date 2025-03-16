import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime
from .base_agent import TestAgent
from .file_processing_agent import FileProcessingAgent
from .matching_agent import MatchingAgent

class TestOrchestrator(TestAgent):
    """Orchestrates and coordinates all test agents"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.agents = {
            "file_processing": FileProcessingAgent(base_url),
            "matching": MatchingAgent(base_url)
        }
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
        Analyze all test results across different agents:
        {json.dumps(results, indent=2)}
        
        Provide a comprehensive analysis including:
        1. Overall system health
        2. Integration points between components
        3. System reliability and stability
        4. Performance characteristics
        5. Security considerations
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
        Generate a detailed test report from these results and analysis:
        Results: {json.dumps(results, indent=2)}
        Analysis: {json.dumps(analysis, indent=2)}
        
        Include:
        1. Executive Summary
        2. Test Coverage Overview
        3. Key Findings
        4. Component-wise Analysis
        5. Performance Metrics
        6. Risk Assessment
        7. Recommendations
        8. Next Steps
        
        Format the report in markdown.
        """
        try:
            return await self.think(prompt)
        except Exception as e:
            return f"""# Test Report

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
            "orchestrator_type": "TestOrchestrator",
            "timestamp": str(datetime.now()),
            "agent_results": {},
            "system_metrics": {
                "total_tests": 0,
                "completion_time": None,
                "component_status": {}
            }
        }
        
        try:
            # Run tests for each agent
            for agent_name in self.agents:
                results["agent_results"][agent_name] = await self.run_agent_tests(agent_name)
                results["system_metrics"]["component_status"][agent_name] = (
                    "error" if "error" in results["agent_results"][agent_name]
                    else "operational"
                )
            
            # Count total tests
            for agent_results in results["agent_results"].values():
                if "tests" in agent_results:
                    results["system_metrics"]["total_tests"] += len(agent_results["tests"])
            
            # Record completion time
            results["system_metrics"]["completion_time"] = str(datetime.now())
            
            # Generate comprehensive analysis
            try:
                results["analysis"] = await self.analyze_all_results(results)
            except Exception as e:
                results["analysis_error"] = str(e)
            
            # Generate human-readable report
            try:
                results["report"] = await self.generate_report(
                    results,
                    results.get("analysis", {"error": "Analysis failed"})
                )
            except Exception as e:
                results["report_error"] = str(e)
            
        except Exception as e:
            results["error"] = str(e)
        
        return results

async def run_test_suite(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Run the complete test suite"""
    orchestrator = TestOrchestrator(base_url)
    try:
        results = await orchestrator.run_tests()
        return results
    finally:
        await orchestrator.close()
        for agent in orchestrator.agents.values():
            await agent.close()

if __name__ == "__main__":
    import uvicorn
    import sys
    
    async def main():
        base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
        results = await run_test_suite(base_url)
        print(json.dumps(results, indent=2))
    
    asyncio.run(main()) 