"""
XAI Visualization Demo module.

This module provides a route to serve the XAI visualization demo page.
"""
import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from http import HTTPStatus

# Configure logging
logger = logging.getLogger(__name__)

# Get path to templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Create API router for demo endpoint
demo_router = APIRouter(prefix="/demo", tags=["XAI Demo"])


@demo_router.get("/", response_class=HTMLResponse)
async def get_visualization_demo() -> HTMLResponse:
    """
    Serve the XAI visualization demo page.
    
    Returns:
        HTMLResponse: Demo page for testing XAI visualizations
    """
    try:
        # Path to the demo HTML file
        demo_file_path = os.path.join(TEMPLATES_DIR, "xai_demo.html")
        
        # Check if file exists
        if not os.path.exists(demo_file_path):
            logger.error(f"Demo file not found at {demo_file_path}")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="XAI demo page not found"
            )
        
        # Read the HTML file
        with open(demo_file_path, "r") as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error serving XAI demo page: {e}")
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )
