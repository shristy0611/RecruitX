"""
Advanced debugging tools for AI agents.

This module provides state-of-the-art debugging capabilities for AI agents, including:
- Tracing and instrumentation
- Deterministic testing
- Visualization
- Observability
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from tests.ai_testing.config import settings

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class TraceEvent:
    """Represents a single trace event in the agent's execution."""
    timestamp: str
    event_type: str
    agent_id: str
    action: str
    context: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentTracer:
    """Traces agent actions and decisions for debugging."""
    
    def __init__(self, trace_dir: Path):
        self.trace_dir = trace_dir
        self.traces: List[TraceEvent] = []
        self.current_trace_file = None
        
        # Ensure trace directory exists
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        
    def start_trace(self, agent_id: str):
        """Start a new trace session."""
        self.current_trace_file = self.trace_dir / f"trace_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        logger.info(f"Starting trace for agent {agent_id}")
        
    def add_event(self, event: TraceEvent):
        """Add a trace event."""
        self.traces.append(event)
        self._save_trace()
        
    def _save_trace(self):
        """Save the current trace to file."""
        if self.current_trace_file:
            with open(self.current_trace_file, 'w') as f:
                json.dump([asdict(t) for t in self.traces], f, indent=2)

class DeterministicTesting:
    """Enables deterministic testing by recording and replaying agent responses."""
    
    def __init__(self, recording_dir: Path):
        self.recording_dir = recording_dir
        self.recordings: Dict[str, List[Dict[str, Any]]] = {}
        self.playback_mode = False
        
        # Ensure recording directory exists
        self.recording_dir.mkdir(parents=True, exist_ok=True)
        
    def start_recording(self, test_id: str):
        """Start recording agent responses."""
        self.recordings[test_id] = []
        
    def record_response(self, test_id: str, prompt: str, response: Dict[str, Any]):
        """Record an agent's response."""
        if test_id in self.recordings:
            self.recordings[test_id].append({
                "prompt": prompt,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
            self._save_recording(test_id)
            
    def get_recorded_response(self, test_id: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Get a previously recorded response in playback mode."""
        if not self.playback_mode:
            return None
            
        recording_file = self.recording_dir / f"{test_id}.json"
        if recording_file.exists():
            with open(recording_file, 'r') as f:
                recordings = json.load(f)
                for record in recordings:
                    if record["prompt"] == prompt:
                        return record["response"]
        return None
        
    def _save_recording(self, test_id: str):
        """Save recordings to file."""
        recording_file = self.recording_dir / f"{test_id}.json"
        with open(recording_file, 'w') as f:
            json.dump(self.recordings[test_id], f, indent=2)

class AgentVisualizer:
    """Generates visualizations of agent behavior and test results."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def create_timeline_view(self, traces: List[TraceEvent]) -> str:
        """Create a timeline visualization of agent actions."""
        timeline_file = self.output_dir / f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Generate timeline HTML
        timeline_html = self._generate_timeline_html(traces)
        
        with open(timeline_file, 'w') as f:
            f.write(timeline_html)
            
        return str(timeline_file)
        
    async def create_decision_tree(self, traces: List[TraceEvent]) -> str:
        """Create a decision tree visualization of agent logic."""
        tree_file = self.output_dir / f"decision_tree_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Generate decision tree HTML
        tree_html = self._generate_decision_tree_html(traces)
        
        with open(tree_file, 'w') as f:
            f.write(tree_html)
            
        return str(tree_file)
        
    def _generate_timeline_html(self, traces: List[TraceEvent]) -> str:
        """Generate HTML for timeline visualization."""
        # Implementation would use a visualization library like vis.js
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Agent Timeline</title>
            <script src="https://visjs.github.io/vis-timeline/dist/vis-timeline-graph2d.min.js"></script>
            <link href="https://visjs.github.io/vis-timeline/dist/vis-timeline-graph2d.min.css" rel="stylesheet" type="text/css" />
        </head>
        <body>
            <div id="timeline"></div>
            <script>
                // Timeline visualization code would go here
            </script>
        </body>
        </html>
        """
        
    def _generate_decision_tree_html(self, traces: List[TraceEvent]) -> str:
        """Generate HTML for decision tree visualization."""
        # Implementation would use a visualization library like d3.js
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Agent Decision Tree</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
        </head>
        <body>
            <div id="tree"></div>
            <script>
                // Decision tree visualization code would go here
            </script>
        </body>
        </html>
        """

class AgentObservability:
    """Provides observability into agent behavior and performance."""
    
    def __init__(self, metrics_dir: Path):
        self.metrics_dir = metrics_dir
        self.current_metrics: Dict[str, Any] = {}
        
        # Ensure metrics directory exists
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
    def record_metric(self, name: str, value: Any):
        """Record a metric."""
        self.current_metrics[name] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_metrics()
        
    def get_metric(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the current value of a metric."""
        return self.current_metrics.get(name)
        
    def _save_metrics(self):
        """Save current metrics to file."""
        metrics_file = self.metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.current_metrics, f, indent=2)

class AgentDebugger:
    """Main debugger interface that coordinates all debugging features."""
    
    def __init__(self, debug_dir: Path):
        self.debug_dir = debug_dir
        
        # Ensure debug directory exists
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.tracer = AgentTracer(debug_dir / "traces")
        self.deterministic = DeterministicTesting(debug_dir / "recordings")
        self.visualizer = AgentVisualizer(debug_dir / "visualizations")
        self.observability = AgentObservability(debug_dir / "metrics")
        
    async def start_debugging_session(self, agent_id: str):
        """Start a new debugging session."""
        self.tracer.start_trace(agent_id)
        logger.info(f"Started debugging session for agent {agent_id}")
        
    async def record_event(self, event: TraceEvent):
        """Record a debugging event."""
        self.tracer.add_event(event)
        
    async def visualize_traces(self) -> List[str]:
        """Generate visualizations from traces."""
        timeline = await self.visualizer.create_timeline_view(self.tracer.traces)
        decision_tree = await self.visualizer.create_decision_tree(self.tracer.traces)
        return [timeline, decision_tree]
        
    async def generate_debug_report(self) -> Dict[str, Any]:
        """Generate a comprehensive debug report."""
        return {
            "traces": [asdict(t) for t in self.tracer.traces],
            "metrics": self.observability.current_metrics,
            "visualizations": await self.visualize_traces()
        }

# Create a global debugger instance with absolute paths
debugger = AgentDebugger(settings.DEBUG_DIR)