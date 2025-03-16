"""
Debuggable Agent

This module extends the BaseAgent class with advanced debugging capabilities.
It integrates the debugging tools to provide improved visibility, diagnostics,
and reproducibility for AI agent testing.
"""

import os
import sys
import time
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from tests.ai_testing.config import settings
from tests.ai_testing.agents.base_agent import BaseAgent
from tests.ai_testing.tools.debugging_tools import (
    tracer, 
    deterministic_test, 
    visualizer, 
    observability
)
from tests.ai_testing.tools.agent_debugger import instrument_agent

class DebuggableAgent(BaseAgent):
    """
    A version of BaseAgent with enhanced debugging capabilities.
    
    This class extends BaseAgent with tools for debugging, tracing,
    visualization, deterministic testing, and observability.
    """
    
    def __init__(self, name: str, model_type: str = settings.AGENT_TYPE, 
                auto_instrument: bool = True, record_mode: bool = False):
        """
        Initialize the debuggable agent.
        
        Args:
            name: Name of the agent
            model_type: Type of AI model to use (gemini, openai)
            auto_instrument: Whether to automatically instrument the agent methods
            record_mode: Whether to record LLM responses for deterministic testing
        """
        super().__init__(name, model_type)
        
        # Set up additional logging for debugging
        self.debug_logger = logging.getLogger(f"debug.{name}")
        debug_handler = logging.FileHandler(settings.LOGS_DIR / f"debug_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        debug_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        debug_handler.setFormatter(debug_formatter)
        self.debug_logger.addHandler(debug_handler)
        self.debug_logger.setLevel(logging.DEBUG)
        
        # Create debug directories
        self.debug_dir = settings.RESULTS_DIR / "debug" / name
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Create visualization directories
        self.visualization_dir = settings.RESULTS_DIR / "visualizations" / name
        os.makedirs(self.visualization_dir, exist_ok=True)
        
        # Initialize debugging components
        self.debug_mode = True
        self.step_traces = {}  # Map step descriptions to trace IDs
        self.decision_points = []  # Store agent decision points
        self.record_mode = record_mode
        
        # Auto-instrument if requested
        if auto_instrument:
            self = instrument_agent(self, name)
            
        # Start recording if in record mode
        if self.record_mode:
            recording_file = self.debug_dir / f"recordings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            deterministic_test.start_recording(recording_file)
            self.debug_logger.info(f"Started recording to {recording_file}")
            
        self.debug_logger.info(f"Initialized {self.name} debuggable agent")
    
    async def setup(self):
        """Set up the agent with debugging instrumentation."""
        self.debug_logger.info("Setting up debuggable agent")
        
        # Start a trace for the setup process
        with tracer.trace(f"{self.name}.setup") as (trace_id, add_step):
            try:
                # Execute the superclass setup
                add_step("Calling Base Setup", {})
                result = await super().setup()
                
                # Record the result
                add_step("Base Setup Result", {"result": result})
                
                # Additional setup for debugging
                add_step("Debug Setup", {
                    "debug_mode": self.debug_mode,
                    "record_mode": self.record_mode
                })
                
                return result
            except Exception as e:
                add_step("Setup Error", {"error": str(e)})
                self.debug_logger.error(f"Error in setup: {str(e)}")
                raise
    
    async def think(self, prompt: str) -> str:
        """
        Generate a response using the AI model with debugging.
        
        This overrides the base think method to add deterministic testing
        and advanced tracing.
        
        Args:
            prompt: The prompt to send to the AI model
            
        Returns:
            The AI model's response
        """
        # Use a unique identifier for this prompt
        request_id = f"{self.name}_{hash(prompt)}"
        
        # Start a trace for this thinking process
        with tracer.trace(f"{self.name}.think", {"prompt": prompt[:100] + "..."}) as (trace_id, add_step):
            self.debug_logger.info(f"Thinking with prompt: {prompt[:100]}...")
            
            # Check if we have a recorded response
            if self.record_mode:
                recorded_response = deterministic_test.get_recorded_response(request_id, prompt)
                if recorded_response:
                    self.debug_logger.info("Using recorded response")
                    add_step("Using Recorded Response", {"request_id": request_id})
                    return recorded_response
            
            # Add to memory for context
            self.memory.append({"role": "user", "content": prompt})
            
            try:
                # Record metrics for this thinking process
                observability.record_metric("think_call", 1, {
                    "agent": self.name,
                    "model": self.model_type,
                    "prompt_length": len(prompt)
                })
                
                start_time = time.time()
                
                if self.model_type == "gemini":
                    add_step("Calling Gemini API", {"prompt_length": len(prompt)})
                    response = await asyncio.to_thread(
                        lambda: self.model.generate_content(prompt).text
                    )
                elif self.model_type == "openai":
                    add_step("Calling OpenAI API", {"prompt_length": len(prompt)})
                    completion = await asyncio.to_thread(
                        lambda: self.client.chat.completions.create(
                            model="gpt-4-turbo",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=settings.AGENT_TEMPERATURE,
                            max_tokens=settings.MAX_TOKENS_OUTPUT
                        )
                    )
                    response = completion.choices[0].message.content
                
                duration = time.time() - start_time
                
                # Record timing metrics
                observability.record_metric("think_duration", duration, {
                    "agent": self.name,
                    "model": self.model_type
                })
                
                # Record the response
                add_step("AI Response", {
                    "response_length": len(response),
                    "duration": duration,
                    "preview": response[:100] + "..."
                })
                
                # Add to memory
                self.memory.append({"role": "assistant", "content": response})
                
                # If in recording mode, save this response
                if self.record_mode:
                    deterministic_test.record_response(request_id, prompt, response)
                    add_step("Recorded Response", {"request_id": request_id})
                
                return response
            except Exception as e:
                # Record the error
                add_step("Error Generating Response", {"error": str(e)})
                observability.create_alert(
                    f"Error in {self.name}.think",
                    str(e),
                    "error"
                )
                self.debug_logger.error(f"Error generating response: {str(e)}")
                return f"Error: {str(e)}"
    
    async def execute_step(self, step_description: str, action_fn) -> Dict[str, Any]:
        """
        Execute a testing step with debugging instrumentation.
        
        Args:
            step_description: Description of the step
            action_fn: Async function to execute
            
        Returns:
            Dictionary with step results
        """
        # Start a trace for this step
        with tracer.trace(f"{self.name}.execute_step", {"step": step_description}) as (trace_id, add_step):
            self.debug_logger.info(f"Executing step with tracing: {step_description}")
            self.step_traces[step_description] = trace_id
            
            step_result = {
                "description": step_description,
                "start_time": datetime.now().isoformat(),
                "status": "started",
                "trace_id": trace_id
            }
            
            try:
                # Record the start of the step
                add_step("Step Started", {"description": step_description})
                observability.record_event("step_started", {"step": step_description})
                
                # Execute the action function
                result = await action_fn()
                
                # Record successful completion
                step_result["result"] = result
                step_result["status"] = "completed"
                
                add_step("Step Completed", {
                    "result_summary": str(result)[:100] + "..." if isinstance(result, str) and len(str(result)) > 100 else str(result)
                })
                
                observability.record_event("step_completed", {"step": step_description})
                self.debug_logger.info(f"Step completed successfully: {step_description}")
                
            except Exception as e:
                # Record the error
                step_result["error"] = str(e)
                step_result["status"] = "failed"
                
                add_step("Step Failed", {"error": str(e)})
                observability.record_event("step_failed", {"step": step_description, "error": str(e)})
                observability.create_alert(f"Step failed: {step_description}", str(e), "error")
                
                self.debug_logger.error(f"Step failed: {step_description} - Error: {str(e)}")
                
                if settings.SCREENSHOT_ON_FAILURE and self.page:
                    screenshot_path = await self.take_screenshot(f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    step_result["error_screenshot"] = screenshot_path
                    add_step("Error Screenshot", {"path": screenshot_path})
            finally:
                step_result["end_time"] = datetime.now().isoformat()
                self.execution_steps.append(step_result)
            
            return step_result
    
    async def decide(self, question: str, options: List[str], reasoning_prompt: str = None) -> str:
        """
        Make a decision with reasoning and debugging.
        
        Args:
            question: The decision question
            options: List of possible options
            reasoning_prompt: Optional prompt to guide the reasoning process
            
        Returns:
            The chosen option
        """
        with tracer.trace(f"{self.name}.decide", {"question": question}) as (trace_id, add_step):
            self.debug_logger.info(f"Making decision: {question}")
            
            # Construct the prompt
            if reasoning_prompt:
                prompt = f"{reasoning_prompt}\n\nQuestion: {question}\n\nOptions:\n"
            else:
                prompt = f"You need to make a decision.\n\nQuestion: {question}\n\nOptions:\n"
                
            for i, option in enumerate(options):
                prompt += f"{i+1}. {option}\n"
                
            prompt += "\nAnalyze each option carefully. Provide your reasoning for choosing one option over the others. Then, clearly state your chosen option in the format 'Chosen option: <option text>'"
            
            add_step("Decision Prompt", {"prompt": prompt})
            
            # Get the AI's reasoning and decision
            response = await self.think(prompt)
            add_step("Decision Response", {"response": response})
            
            # Extract the chosen option
            chosen_option = None
            for option in options:
                if f"Chosen option: {option}" in response:
                    chosen_option = option
                    break
                    
            # If we couldn't find the chosen option, take the first one
            if not chosen_option and options:
                chosen_option = options[0]
                self.debug_logger.warning(f"Could not extract chosen option from response, defaulting to: {chosen_option}")
                add_step("Default Choice", {"default_option": chosen_option})
            
            # Record the decision
            decision_point = {
                "question": question,
                "options": options,
                "chosen": chosen_option,
                "reasoning": response,
                "timestamp": datetime.now().isoformat(),
                "trace_id": trace_id
            }
            
            self.decision_points.append(decision_point)
            add_step("Decision Made", {"chosen": chosen_option})
            
            self.debug_logger.info(f"Decision made: {chosen_option}")
            return chosen_option
    
    async def generate_debug_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive debug report.
        
        Returns:
            Dictionary with debug report
        """
        self.debug_logger.info("Generating debug report")
        
        # Get the standard report
        standard_report = await self.generate_report()
        
        # Add debugging information
        debug_report = {
            **standard_report,
            "debug_info": {
                "traces": list(self.step_traces.values()),
                "decisions": self.decision_points,
                "metrics": observability.get_metrics(),
                "events": observability.get_events(),
                "alerts": observability.get_alerts()
            }
        }
        
        # Generate visualizations
        visualizations = []
        for description, trace_id in self.step_traces.items():
            trace_files = list(Path(settings.RESULTS_DIR / "traces").glob(f"trace_*_{trace_id}.json"))
            
            if not trace_files:
                continue
                
            trace_file = trace_files[0]
            
            with open(trace_file, 'r') as f:
                trace_data = json.load(f)
                
            # Create visualizations
            graph_path = visualizer.create_execution_graph(
                trace_data, 
                self.visualization_dir / f"execution_{description.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            
            visualizations.append({
                "description": description,
                "trace_id": trace_id,
                "execution_graph": str(graph_path)
            })
            
        debug_report["debug_info"]["visualizations"] = visualizations
        
        # Save report to file
        report_path = settings.RESULTS_DIR / "debug" / f"debug_report_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(debug_report, f, indent=2)
        
        self.debug_logger.info(f"Debug report generated and saved to {report_path}")
        return debug_report
    
    async def close(self):
        """Close all resources and finalize debugging."""
        self.debug_logger.info("Closing debuggable agent")
        
        # Stop recording if in record mode
        if self.record_mode:
            deterministic_test.stop_recording()
            self.debug_logger.info("Stopped recording")
        
        # Close resources from the base class
        await super().close()
        
        self.debug_logger.info("Debuggable agent closed")


# Helper function to create a debuggable version of any agent class
def make_debuggable(agent_class):
    """
    Create a debuggable version of any agent class.
    
    Args:
        agent_class: The agent class to make debuggable
        
    Returns:
        A new class that inherits from both the agent_class and DebuggableAgent
    """
    class DebuggableAgentWrapper(agent_class, DebuggableAgent):
        def __init__(self, name, model_type=settings.AGENT_TYPE, auto_instrument=True, record_mode=False):
            # Initialize DebuggableAgent first
            DebuggableAgent.__init__(self, name, model_type, auto_instrument, record_mode)
            
            # Skip the constructor of the base agent_class since DebuggableAgent already initialized BaseAgent
            # but call any additional setup from agent_class.__init__ without calling BaseAgent.__init__ again
            
            # Extract any custom initialization from agent_class.__init__
            # This is a bit of a hack, but it allows us to inherit from both classes
            # Without calling BaseAgent.__init__ twice
            
            # Override with any method overrides from agent_class
            for attr_name in dir(agent_class):
                if attr_name.startswith('__') or attr_name in ('__init__', 'setup', 'close'):
                    continue
                    
                attr = getattr(agent_class, attr_name)
                if callable(attr) and not attr_name.startswith('_'):
                    setattr(self, attr_name, attr.__get__(self, self.__class__))
    
    return DebuggableAgentWrapper 