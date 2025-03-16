# RecruitX AI Testing Framework

This framework provides state-of-the-art AI-powered testing capabilities for the RecruitX application, with advanced debugging features specifically designed for AI agents.

## Key Features

- **AI-Powered Testing**: Uses large language models to understand and test the application without predefined scripts
- **Agentic Testing**: Creates autonomous agents that can make decisions and adapt to application changes
- **Advanced Debugging**: Provides comprehensive tracing, visualization, and observability for AI agent behaviors
- **Deterministic Testing**: Supports recording and replaying agent behaviors for consistent testing

## Directory Structure

```
tests/ai_testing/
├── agents/                 # AI agent implementations
│   ├── base_agent.py       # Base agent class
│   ├── debuggable_agent.py # Base agent with debugging capabilities
│   ├── ui_agent.py         # Agent for UI testing
│   └── debuggable_ui_agent.py # UI agent with debugging capabilities
├── config/                 # Configuration settings
│   ├── __init__.py
│   └── settings.py         # Framework settings
├── prompts/                # Prompts for AI agents
├── results/                # Test results and artifacts
│   ├── debug/              # Debug information
│   ├── logs/               # Log files
│   ├── screenshots/        # Screenshots
│   ├── traces/             # Execution traces
│   ├── videos/             # Test videos
│   └── visualizations/     # Visualizations of agent behavior
├── tools/                  # Utility tools
│   ├── agent_debugger.py   # Debugging interface
│   ├── debugging_tools.py  # Core debugging tools
│   └── selector_tools.py   # Tools for finding UI selectors
└── README.md               # This file
```

## Debugging Tools

The framework provides several state-of-the-art debugging tools specifically designed for AI agents:

### 1. Tracing

The tracing system records the complete execution path of AI agents, including:
- Method calls and their parameters
- Decision points and reasoning
- LLM prompt inputs and outputs
- Errors and exceptions

```python
with tracer.trace("operation_name", {"context": "data"}) as (trace_id, add_step):
    # Add steps to the trace
    add_step("Step Name", {"data": "value"})
    
    # Code execution
    result = do_something()
    
    # Record the result
    add_step("Result", {"result": result})
```

### 2. Visualization

Create visual representations of agent execution flow and decision trees:

```python
# Create an execution graph visualization
graph_path = visualizer.create_execution_graph(trace_data)

# Create a decision tree visualization
tree_path = visualizer.create_decision_tree(trace_data)
```

### 3. Deterministic Testing

Record and replay LLM responses for consistent, deterministic testing:

```python
# Start recording mode
deterministic_test.start_recording("recordings.json")

# Record a response
deterministic_test.record_response("request_id", prompt, response)

# Get a recorded response
response = deterministic_test.get_recorded_response("request_id", prompt)

# Stop recording
deterministic_test.stop_recording()
```

### 4. Observability

Monitor and track metrics, events, and alerts during agent execution:

```python
# Record a metric
observability.record_metric("metric_name", value, {"tag": "value"})

# Record an event
observability.record_event("event_name", {"data": "value"})

# Create an alert
observability.create_alert("alert_name", "Alert message", "warning")

# Get metrics
metrics = observability.get_metrics(since=timestamp)
```

## Using Debuggable Agents

The framework provides two ways to create debuggable agents:

### 1. Use DebuggableAgent directly

```python
from tests.ai_testing.agents.debuggable_agent import DebuggableAgent

agent = DebuggableAgent("MyAgent", record_mode=True)
await agent.setup()

# Execute tests with full debugging
await agent.execute_step("Step description", lambda: agent.do_something())

# Generate a debug report
debug_report = await agent.generate_debug_report()
```

### 2. Make any agent class debuggable

```python
from tests.ai_testing.agents.debuggable_agent import make_debuggable
from tests.ai_testing.agents.ui_agent import UIAgent

# Create a debuggable version of UIAgent
DebuggableUIAgent = make_debuggable(UIAgent)

# Create an instance
agent = DebuggableUIAgent("MyUIAgent", record_mode=True)

# Use it like a normal UIAgent but with debugging capabilities
await agent.setup()
await agent.analyze_component("login_button")
```

### 3. Use the EnhancedUIAgent

The `EnhancedUIAgent` extends the debugging capabilities with UI-specific features:

```python
from tests.ai_testing.agents.debuggable_ui_agent import EnhancedUIAgent

agent = EnhancedUIAgent("MyEnhancedAgent")
await agent.setup()

# Smart component interaction
await agent.smart_interaction("login button", "click")

# Component state verification
verification = await agent.verify_component_state("login_form", {
    "visible": True,
    "enabled": True
})

# Generate timeline report
timeline = await agent.generate_timeline_report()
```

## Configuration

Configure the framework through environment variables or by modifying `config/settings.py`:

```
# AI Agent settings
AGENT_TYPE=gemini                 # Options: gemini, openai, anthropic
AGENT_TEMPERATURE=0.2             # Temperature for AI responses
MAX_TOKENS_OUTPUT=4096            # Maximum tokens for AI responses

# Debug settings
DEBUG_MODE=true                   # Enable debug mode
TRACE_ALL_METHODS=true            # Trace all agent methods
RECORD_MODE=false                 # Record LLM responses for deterministic testing
VISUALIZATION_ENABLED=true        # Enable visualization generation
```

## Running Tests

Execute tests with debugging enabled:

```bash
# Run UI tests with debugging
python run.py --tests ui --debug

# Run with deterministic replay
python run.py --tests ui --deterministic

# Generate visualizations
python run.py --tests ui --visualize
``` 