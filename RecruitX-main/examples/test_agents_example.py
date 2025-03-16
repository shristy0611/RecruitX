import asyncio
from typing import List
from app.agent.test_agents.ui_test_agent import UITestAgent
from app.agent.test_agents.api_test_agent import APITestAgent


async def run_ui_tests() -> None:
    """Run UI component tests using the UITestAgent."""
    # Create a UI test agent for testing a login form
    login_form_agent = UITestAgent(
        name="login_form_test",
        test_name="Login Form Test",
        test_description="Test the login form component for accessibility and usability",
        component_name="LoginForm"
    )

    # Add test assertions
    login_form_agent.add_assertion(
        "Form should be keyboard accessible",
        "keyboard_navigation",
        True
    )
    login_form_agent.add_assertion(
        "Color contrast should meet WCAG 2.1 AA",
        "color_contrast",
        True
    )
    login_form_agent.add_assertion(
        "Form should be responsive on mobile",
        "responsive_mobile",
        True
    )

    # Run the test agent
    print("Running UI tests for login form...")
    results = await login_form_agent.run()
    print(f"UI Test Results:\n{results}")

    # Get detailed test report
    report = login_form_agent.get_test_report()
    print(f"\nDetailed Test Report:\n{report}")


async def run_api_tests() -> None:
    """Run API endpoint tests using the APITestAgent."""
    # Create an API test agent for testing login endpoint
    login_api_agent = APITestAgent(
        name="login_api_test",
        test_name="Login API Test",
        test_description="Test the login API endpoint for security and functionality",
        endpoint="/api/v1/auth/login"
    )

    # Add test assertions
    login_api_agent.add_assertion(
        "Should require authentication",
        "requires_auth",
        True
    )
    login_api_agent.add_assertion(
        "Should handle invalid credentials",
        "handles_invalid_creds",
        True
    )
    login_api_agent.add_assertion(
        "Should rate limit login attempts",
        "rate_limited",
        True
    )

    # Run the test agent
    print("\nRunning API tests for login endpoint...")
    results = await login_api_agent.run()
    print(f"API Test Results:\n{results}")

    # Get detailed test report
    report = login_api_agent.get_test_report()
    print(f"\nDetailed Test Report:\n{report}")


async def main() -> None:
    """Run all test agents."""
    print("Starting AI-powered test agents...")
    
    # Run tests concurrently
    await asyncio.gather(
        run_ui_tests(),
        run_api_tests()
    )

    print("\nAll tests completed!")


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main()) 