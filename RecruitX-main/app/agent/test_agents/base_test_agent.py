from typing import Any, Dict, List, Optional
from app.agent.base import BaseAgent
from app.schema import AgentState, Message
from pydantic import Field


class BaseTestAgent(BaseAgent):
    """Base class for all test agents with testing-specific functionality."""

    test_name: str = Field(..., description="Name of the test being executed")
    test_description: str = Field(..., description="Description of what is being tested")
    test_assertions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of assertions to verify during testing"
    )
    test_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of test results and observations"
    )
    test_artifacts: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary to store any artifacts generated during testing"
    )

    def __init__(self, **data):
        super().__init__(**data)
        self.system_prompt = f"""You are an AI test agent responsible for {self.test_description}.
Your goal is to thoroughly test the specified functionality and report any issues found.
You should:
1. Plan and execute test cases
2. Make observations and collect evidence
3. Verify assertions
4. Document any failures or unexpected behavior
5. Suggest improvements when issues are found

Current test: {self.test_name}
"""

    async def step(self) -> str:
        """Execute a single test step."""
        # Get the next action from the LLM
        system_msgs = [Message.system_message(self.system_prompt)]
        response = await self.llm.ask(
            messages=self.messages,
            system_msgs=system_msgs,
            stream=False
        )

        # Update agent's memory with the response
        self.update_memory("assistant", response)

        # Process the response and update test results
        await self._process_test_step(response)

        return response

    async def _process_test_step(self, step_result: str) -> None:
        """Process the results of a test step and update test state."""
        # Add the step result to test_results
        self.test_results.append({
            "step": self.current_step,
            "result": step_result,
            "state": self.state.value
        })

        # Check if test is complete
        if self._is_test_complete():
            self.state = AgentState.FINISHED

    def _is_test_complete(self) -> bool:
        """Check if all test assertions have been verified."""
        return all(assertion.get("verified", False) for assertion in self.test_assertions)

    def add_assertion(self, description: str, condition: Any, expected: Any) -> None:
        """Add a new assertion to be verified during testing."""
        self.test_assertions.append({
            "description": description,
            "condition": condition,
            "expected": expected,
            "verified": False,
            "actual": None
        })

    def verify_assertion(self, index: int, actual: Any) -> bool:
        """Verify a specific assertion with an actual value."""
        if 0 <= index < len(self.test_assertions):
            assertion = self.test_assertions[index]
            assertion["actual"] = actual
            assertion["verified"] = assertion["expected"] == actual
            return assertion["verified"]
        return False

    def get_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        return {
            "test_name": self.test_name,
            "description": self.test_description,
            "total_steps": self.current_step,
            "assertions": self.test_assertions,
            "results": self.test_results,
            "artifacts": self.test_artifacts,
            "status": "PASSED" if self._is_test_complete() else "FAILED"
        }