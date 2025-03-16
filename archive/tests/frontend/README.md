# Frontend Testing Framework

This directory contains an AI-powered frontend testing framework for the RecruitX application. The framework uses Playwright and Google Gemini to automatically test UI components, performance, and the overall user experience.

## Features

- **UI Component Testing**: Automatically tests rendering, interactions, and API calls for all frontend components
- **Performance Testing**: Measures page load times, paint metrics, and interaction responsiveness
- **AI-Powered Analysis**: Uses Google Gemini to analyze test results and provide detailed insights
- **Comprehensive Reporting**: Generates detailed reports with recommendations and next steps

## Directory Structure

```
tests/frontend/
├── test_agents/             # Test agent implementation
│   ├── base_agent.py        # Base agent with shared functionality
│   ├── ui_component_agent.py # UI component testing agent
│   ├── performance_agent.py # Performance testing agent
│   └── orchestrator.py      # Test orchestration
├── test_results/            # Generated test results and reports
│   ├── screenshots/         # UI screenshots
│   ├── videos/              # UI interaction recordings
│   ├── traces/              # Performance traces
│   └── har/                 # HTTP Archive files
├── run_tests.py             # Main test runner script
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## Setup

1. Install dependencies:

```bash
pip install -r tests/frontend/requirements.txt
```

2. Install Playwright browsers:

```bash
playwright install
```

3. Set up environment variables in `.env` file:

```
GEMINI_API_KEY_1=your_gemini_api_key_here
FRONTEND_URL=http://localhost:5173
API_URL=http://localhost:8000
```

## Running Tests

To run all frontend tests:

```bash
python tests/frontend/run_tests.py
```

Options:

- `--base-url`: Frontend application URL (default: http://localhost:5173)
- `--api-url`: API URL (default: http://localhost:8000)
- `--output`: Custom output file path for results
- `--verbose`: Enable verbose logging

## Test Results

After running tests, the following outputs are generated:

1. JSON results file: `tests/frontend/test_results/frontend_test_results_TIMESTAMP.json`
2. Markdown report: `tests/frontend/test_results/frontend_test_results_TIMESTAMP.md`
3. Screenshots: `tests/frontend/test_results/screenshots/`
4. Performance traces: `tests/frontend/test_results/traces/`

## Extending the Framework

### Adding New UI Components to Test

Edit `tests/frontend/test_agents/ui_component_agent.py` and add entries to the `COMPONENTS_TO_TEST` list:

```python
COMPONENTS_TO_TEST = [
    {"name": "NewComponent", "route": "/new-route", "selectors": [".new-component"]},
    # ...
]
```

### Adding New Routes for Performance Testing

Edit `tests/frontend/test_agents/performance_agent.py` and add entries to the `ROUTES_TO_TEST` list:

```python
ROUTES_TO_TEST = [
    {"name": "NewRoute", "route": "/new-route"},
    # ...
]
```

### Adding a New Test Agent

1. Create a new agent file in `tests/frontend/test_agents/`
2. Extend the `FrontendTestAgent` base class
3. Implement the `run_tests()` method
4. Add the agent to `orchestrator.py`

## CI/CD Integration

Add this to your CI/CD workflow:

```yaml
# Example GitHub Actions workflow
jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r tests/frontend/requirements.txt
          playwright install
      - name: Run frontend tests
        run: python tests/frontend/run_tests.py
        env:
          GEMINI_API_KEY_1: ${{ secrets.GEMINI_API_KEY_1 }}
          FRONTEND_URL: http://localhost:5173
          API_URL: http://localhost:8000
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: frontend-test-results
          path: tests/frontend/test_results/
``` 