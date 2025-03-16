"""
Test CV upload and analysis functionality.

This test verifies that:
1. The CV upload component is present and functional
2. Files can be uploaded successfully
3. The backend processes the CV and returns real analysis results
4. The results are displayed correctly in the UI
"""

import os
import asyncio
import pytest
from pathlib import Path

from tests.ai_testing.agents.debuggable_ui_agent import EnhancedUIAgent
from tests.ai_testing.config import settings

# Test data
SAMPLE_CV = Path(__file__).parent / "data" / "sample_cv.txt"

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

async def test_cv_upload_and_analysis():
    """Test the complete CV upload and analysis flow."""
    
    # Initialize our enhanced UI testing agent
    agent = EnhancedUIAgent(
        name="CVTester",
        model_type="gemini",
        record_mode=True,  # Record this test for future replay
        auto_instrument=True  # Enable full instrumentation
    )
    
    try:
        # Setup the agent and browser
        await agent.setup()
        
        # Navigate to the application
        await agent.navigate(settings.FRONTEND_URL)
        
        # Take a screenshot of the initial state
        await agent.take_screenshot("initial_state")
        
        # Find and analyze the CV upload component
        upload_analysis = await agent.analyze_component("file upload")
        assert upload_analysis["exists"], "CV upload component not found"
        assert upload_analysis["enabled"], "CV upload component is disabled"
        
        # Upload the CV
        await agent.smart_interaction(
            component_name="file upload",
            action="type",
            text=str(SAMPLE_CV)
        )
        
        # Find and click the upload button
        await agent.smart_interaction(
            component_name="submit button",
            action="click"
        )
        
        # Wait for and verify the loading indicator
        loading_analysis = await agent.analyze_component("loading indicator")
        assert loading_analysis["exists"], "Loading indicator not shown"
        
        # Wait for the results (this may need adjustment based on actual response time)
        await asyncio.sleep(5)
        
        # Take a screenshot of the results
        await agent.take_screenshot("analysis_results")
        
        # Verify the results are displayed
        results_analysis = await agent.analyze_component("analysis results")
        assert results_analysis["exists"], "Analysis results not displayed"
        assert results_analysis["visible"], "Analysis results not visible"
        
        # Verify we're not showing dummy data
        result_text = results_analysis.get("text", "").lower()
        assert "dummy" not in result_text, "Results appear to be dummy data"
        assert "mock" not in result_text, "Results appear to be mock data"
        
        # Perform accessibility test on the results section
        accessibility_results = await agent.perform_accessibility_test()
        assert not accessibility_results.get("violations", []), "Accessibility issues found"
        
        # Generate debug report
        debug_report = await agent.generate_debug_report()
        
        # Generate timeline visualization
        timeline = await agent.generate_timeline_report()
        
    finally:
        # Clean up
        await agent.close()

if __name__ == "__main__":
    asyncio.run(test_cv_upload_and_analysis()) 