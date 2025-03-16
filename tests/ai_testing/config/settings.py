"""
Configuration settings for the AI testing framework.
"""

import os
from pathlib import Path
from datetime import datetime

# Base paths
BASE_DIR = Path(__file__).parent.parent
WORKSPACE_DIR = BASE_DIR.parent.parent

# Application URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# API Keys (should be moved to environment variables in production)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Test settings
HEADLESS = os.getenv("TEST_HEADLESS", "true").lower() == "true"
SCREENSHOT_ON_FAILURE = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
TEST_TIMEOUT = int(os.getenv("TEST_TIMEOUT", "30"))  # seconds
RETRY_COUNT = int(os.getenv("TEST_RETRIES", "3"))

# Agent settings
AGENT_TYPE = os.getenv("AGENT_TYPE", "gemini")
RECORD_MODE = os.getenv("RECORD_MODE", "false").lower() == "true"
DETERMINISTIC_TESTING = os.getenv("DETERMINISTIC_TESTING", "false").lower() == "true"
AUTO_INSTRUMENT = os.getenv("AUTO_INSTRUMENT", "true").lower() == "true"

# Debug settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
VISUALIZATION_ENABLED = os.getenv("VISUALIZATION_ENABLED", "true").lower() == "true"

# Directory structure
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = RESULTS_DIR / "logs"
SCREENSHOTS_DIR = RESULTS_DIR / "screenshots"
TRACES_DIR = RESULTS_DIR / "traces"
RECORDINGS_DIR = RESULTS_DIR / "recordings"
VISUALIZATIONS_DIR = RESULTS_DIR / "visualizations"
DEBUG_DIR = RESULTS_DIR / "debug"
REPORTS_DIR = RESULTS_DIR / "reports"

# Create directories if they don't exist
for directory in [
    RESULTS_DIR,
    LOGS_DIR,
    SCREENSHOTS_DIR,
    TRACES_DIR,
    RECORDINGS_DIR,
    VISUALIZATIONS_DIR,
    DEBUG_DIR,
    REPORTS_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# AI Agent settings
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.2"))
MAX_TOKENS_OUTPUT = int(os.getenv("MAX_TOKENS_OUTPUT", "4096"))
AGENT_VERBOSE = os.getenv("AGENT_VERBOSE", "true").lower() == "true"

# Test settings
BROWSER = os.getenv("BROWSER", "chromium")  # Options: chromium, firefox, webkit
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))  # milliseconds
VIDEO_RECORDING = os.getenv("VIDEO_RECORDING", "true").lower() == "true"

# Debug settings
TRACE_ALL_METHODS = os.getenv("TRACE_ALL_METHODS", "true").lower() == "true"

# Report settings
REPORT_FORMAT = os.getenv("REPORT_FORMAT", "md")  # Options: md, json, html
INCLUDE_SCREENSHOTS_IN_REPORT = os.getenv("INCLUDE_SCREENSHOTS_IN_REPORT", "true").lower() == "true"
INCLUDE_TRACES_IN_REPORT = os.getenv("INCLUDE_TRACES_IN_REPORT", "true").lower() == "true"

# Function to get a timestamp string
def get_timestamp():
    """Return a formatted timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Function to get a results filepath with timestamp
def get_results_filepath(prefix, extension):
    """Get a timestamped filepath in the results directory."""
    return RESULTS_DIR / f"{prefix}_{get_timestamp()}.{extension}" 