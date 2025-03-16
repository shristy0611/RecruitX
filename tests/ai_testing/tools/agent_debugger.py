"""
Agent Debugger

This module provides a simple interface to connect the debugging tools with the
existing agent framework. It acts as a bridge between the agent implementations
and the debugging tools.
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from tests.ai_testing.config import settings
from tests.ai_testing.tools.debugging_tools import (
    tracer, 
    deterministic_test, 
    visualizer, 
    observability,
    verify_agent_behavior
)

# Configure logger
logger = logging.getLogger("agent_debugger")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AgentDebugger:
    """
    A debugger for AI agents that integrates tracing, observability, visualization,
    and deterministic testing.
    """
    
    def __init__(self, agent_name: str, agent_type: str):
        """
        Initialize the debugger.
        
        Args:
            agent_name: Name of the agent (e.g., "UIAgent-1")
            agent_type: Type of the agent (e.g., "UIAgent", "PerformanceAgent")
        """
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.active_trace_id = None
        self.traces = []
        self.metrics = {}
        
        # Create debug directories if they don't exist
        self.debug_dir = settings.RESULTS_DIR / "debug" / agent_type / agent_name
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Recording path for deterministic tests
        self.recording_path = self.debug_dir / "recordings.json"
        
    async def wrap_method(self, method: Callable, method_name: str, *args, **kwargs) -> Any:
        """
        Wrap a method call with debugging instrumentation.
        
        Args:
            method: The method to wrap
            method_name: Name of the method
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method
            
        Returns:
            The result of the method call
        """
        # Start a trace for this method call
        if self.active_trace_id is None:
            # This is a top-level method call
            with tracer.trace(f"{self.agent_type}.{method_name}", inputs=kwargs) as (trace_id, add_step):
                self.active_trace_id = trace_id
                
                # Record the method call
                add_step("Method Call", {
                    "method": method_name,
                    "args": [repr(arg) for arg in args],
                    "kwargs": {k: repr(v) for k, v in kwargs.items()}
                })
                
                # Record metrics
                observability.record_metric("method_call", 1, {
                    "agent_type": self.agent_type,
                    "agent_name": self.agent_name,
                    "method": method_name
                })
                
                try:
                    # Execute the method
                    start_time = observability.metrics.get("method_duration", [])[-1]["timestamp"] if "method_duration" in observability.metrics else None
                    result = await method(*args, **kwargs)
                    
                    # Record the result
                    add_step("Method Result", {
                        "result": repr(result)
                    })
                    
                    if start_time:
                        duration = observability.metrics.get("method_duration", [])[-1]["timestamp"] - start_time
                        observability.record_metric("method_duration", duration, {
                            "agent_type": self.agent_type,
                            "agent_name": self.agent_name,
                            "method": method_name
                        })
                    
                    return result
                except Exception as e:
                    # Record the error
                    add_step("Method Error", {
                        "error": str(e),
                        "type": type(e).__name__
                    })
                    
                    # Create an alert
                    observability.create_alert(
                        f"Error in {self.agent_type}.{method_name}",
                        str(e),
                        "error"
                    )
                    
                    # Re-raise the exception
                    raise
                finally:
                    # Store the trace ID
                    self.traces.append(self.active_trace_id)
                    self.active_trace_id = None
        else:
            # This is a nested method call
            step_id = tracer.add_step(self.active_trace_id, f"Nested Method: {method_name}", {
                "method": method_name,
                "args": [repr(arg) for arg in args],
                "kwargs": {k: repr(v) for k, v in kwargs.items()}
            })
            
            try:
                # Execute the method
                result = await method(*args, **kwargs)
                
                # Record the result
                tracer.add_step(self.active_trace_id, f"Nested Method Result: {method_name}", {
                    "result": repr(result)
                })
                
                return result
            except Exception as e:
                # Record the error
                tracer.add_step(self.active_trace_id, f"Nested Method Error: {method_name}", {
                    "error": str(e),
                    "type": type(e).__name__
                })
                
                # Re-raise the exception
                raise
    
    def wrap_llm_call(self, prompt_text: str, request_id: str = None) -> Optional[str]:
        """
        Wrap a call to an LLM for deterministic testing.
        
        Args:
            prompt_text: The prompt text
            request_id: Unique identifier for the request (will be generated if not provided)
            
        Returns:
            The recorded response if in playback mode, None otherwise
        """
        if not request_id:
            request_id = f"{self.agent_type}_{self.agent_name}_{hash(prompt_text)}"
            
        # Check if we have a recorded response
        return deterministic_test.get_recorded_response(request_id, prompt_text)
    
    def record_llm_response(self, prompt_text: str, response: str, request_id: str = None):
        """
        Record an LLM response for deterministic testing.
        
        Args:
            prompt_text: The prompt text
            response: The response from the LLM
            request_id: Unique identifier for the request (will be generated if not provided)
        """
        if not request_id:
            request_id = f"{self.agent_type}_{self.agent_name}_{hash(prompt_text)}"
            
        deterministic_test.record_response(request_id, prompt_text, response)
    
    def start_recording(self):
        """Start recording LLM responses for deterministic testing."""
        deterministic_test.start_recording(self.recording_path)
        logger.info(f"Started recording to {self.recording_path}")
    
    def stop_recording(self):
        """Stop recording LLM responses and save them."""
        deterministic_test.stop_recording()
        logger.info("Stopped recording")
    
    def visualize_traces(self):
        """Visualize the recorded traces."""
        visualizations = []
        
        for trace_id in self.traces:
            # Get the trace data
            trace_path = settings.RESULTS_DIR / "traces" / f"trace_*_{trace_id}.json"
            trace_files = list(Path(settings.RESULTS_DIR / "traces").glob(f"trace_*_{trace_id}.json"))
            
            if not trace_files:
                logger.warning(f"Trace file not found for trace ID {trace_id}")
                continue
                
            trace_file = trace_files[0]
            
            with open(trace_file, 'r') as f:
                trace_data = json.load(f)
                
            # Create visualizations
            execution_graph = visualizer.create_execution_graph(trace_data)
            decision_tree = visualizer.create_decision_tree(trace_data)
            
            visualizations.append({
                "trace_id": trace_id,
                "execution_graph": str(execution_graph),
                "decision_tree": str(decision_tree)
            })
            
            logger.info(f"Created visualizations for trace {trace_id}")
        
        return visualizations
    
    def get_metrics(self, since: Optional[float] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get recorded metrics for this agent."""
        return observability.get_metrics(since=since)
    
    def get_events(self, since: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get recorded events for this agent."""
        return observability.get_events(since=since)
    
    def get_alerts(self, level: str = None, since: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get alerts for this agent."""
        return observability.get_alerts(level=level, since=since)


# Function to instrument an agent with debugging capabilities
def instrument_agent(agent, agent_name: str = None):
    """
    Instrument an agent with debugging capabilities.
    
    This function adds debugging capabilities to an agent by wrapping its methods
    with debugging instrumentation.
    
    Args:
        agent: The agent to instrument
        agent_name: Optional name for the agent (defaults to the agent's class name)
        
    Returns:
        The instrumented agent
    """
    if agent_name is None:
        agent_name = agent.__class__.__name__
        
    agent_type = agent.__class__.__name__
    
    # Create a debugger for this agent
    debugger = AgentDebugger(agent_name, agent_type)
    
    # Store the debugger on the agent
    agent._debugger = debugger
    
    # Get all methods that aren't private
    methods = [
        method_name for method_name in dir(agent) 
        if callable(getattr(agent, method_name)) and not method_name.startswith('_')
    ]
    
    # Wrap each method with debugging instrumentation
    for method_name in methods:
        # Skip methods that are already wrapped
        if hasattr(getattr(agent, method_name), '_wrapped'):
            continue
            
        # Get the original method
        original_method = getattr(agent, method_name)
        
        # Define a wrapper method
        async def wrapped_method(self, *args, original=original_method, name=method_name, **kwargs):
            return await self._debugger.wrap_method(original, name, *args, **kwargs)
        
        # Mark the wrapper as wrapped
        wrapped_method._wrapped = True
        
        # Replace the original method with the wrapper
        setattr(agent, method_name, wrapped_method.__get__(agent))
    
    return agent


# Helper function to create a test case
def create_test_case(inputs: Dict[str, Any], expected_outputs: Dict[str, Any], case_id: str = None) -> Dict[str, Any]:
    """
    Create a test case for an agent.
    
    Args:
        inputs: Inputs for the test case
        expected_outputs: Expected outputs for the test case
        case_id: Optional ID for the test case
        
    Returns:
        A test case dictionary
    """
    if case_id is None:
        case_id = f"test_case_{hash(json.dumps(inputs, sort_keys=True))}"
        
    return {
        "id": case_id,
        "inputs": inputs,
        "expected_outputs": expected_outputs
    }


# Export all symbols for easy import
__all__ = [
    'AgentDebugger',
    'instrument_agent',
    'create_test_case',
    'verify_agent_behavior'
] 