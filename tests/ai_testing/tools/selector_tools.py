"""
Selector tools for finding UI elements.

This module provides utilities for finding the best CSS selectors for UI elements
based on natural language descriptions.
"""

import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import Page

async def find_best_selector(page: Page, component_description: str) -> Optional[str]:
    """
    Find the best CSS selector for a UI component based on its description.
    
    Args:
        page: The Playwright page object
        component_description: Natural language description of the component
        
    Returns:
        The best CSS selector for the component, or None if not found
    """
    # First, try to find common components by their typical selectors
    common_components = {
        "login form": "form:has(input[type='password'])",
        "login button": "button:has-text('Login'), button:has-text('Sign in')",
        "signup button": "button:has-text('Sign up'), button:has-text('Register')",
        "file upload": "input[type='file']",
        "navigation menu": "nav, .navigation, .navbar, header ul",
        "search bar": "input[type='search'], input[placeholder*='search' i]",
        "submit button": "button[type='submit'], input[type='submit']",
        "cancel button": "button:has-text('Cancel')",
        "profile picture": "img.avatar, img.profile-pic, .user-avatar",
        "dropdown menu": "select, .dropdown",
        "checkbox": "input[type='checkbox']",
        "radio button": "input[type='radio']",
        "date picker": "input[type='date']",
        "text input": "input[type='text']",
        "password input": "input[type='password']",
        "email input": "input[type='email']",
        "phone input": "input[type='tel']",
        "textarea": "textarea",
        "error message": ".error, .alert-danger, .invalid-feedback",
        "success message": ".success, .alert-success",
        "loading indicator": ".loading, .spinner, .loader",
        "pagination": ".pagination",
        "table": "table",
        "modal": ".modal, dialog",
        "tooltip": ".tooltip",
        "tab": ".tab, .nav-item",
        "accordion": ".accordion",
        "card": ".card",
        "footer": "footer",
        "header": "header",
        "sidebar": ".sidebar, aside",
        "breadcrumb": ".breadcrumb",
        "alert": ".alert",
        "badge": ".badge",
        "progress bar": "progress, .progress",
        "slider": "input[type='range']",
        "toggle": ".toggle, .switch",
        "rating": ".rating, .stars",
        "avatar": ".avatar",
        "tag": ".tag, .badge",
        "divider": "hr, .divider",
        "icon": ".icon, i[class*='icon'], svg",
        "link": "a",
        "image": "img",
        "video": "video",
        "audio": "audio",
        "map": ".map",
        "calendar": ".calendar",
        "notification": ".notification",
        "toast": ".toast",
        "stepper": ".stepper",
        "wizard": ".wizard",
        "timeline": ".timeline",
        "chart": ".chart",
        "graph": ".graph",
        "menu": "menu, .menu",
        "list": "ul, ol, .list",
        "grid": ".grid",
        "flex": ".flex",
        "container": ".container",
        "row": ".row",
        "column": ".col, .column",
        "section": "section",
        "article": "article",
        "main": "main",
        "aside": "aside",
        "nav": "nav",
        "dialog": "dialog",
        "form": "form",
        "fieldset": "fieldset",
        "legend": "legend",
        "label": "label",
        "button": "button",
        "select": "select",
        "option": "option",
        "input": "input",
        "output": "output",
        "details": "details",
        "summary": "summary",
        "figure": "figure",
        "figcaption": "figcaption",
        "picture": "picture",
        "source": "source",
        "track": "track",
        "embed": "embed",
        "object": "object",
        "param": "param",
        "canvas": "canvas",
        "script": "script",
        "noscript": "noscript",
        "template": "template",
        "slot": "slot",
        "portal": "portal"
    }
    
    # Check if the component description matches any common components
    for desc, selector in common_components.items():
        if desc.lower() in component_description.lower():
            # Try to find the element with this selector
            element = await page.query_selector(selector)
            if element:
                return selector
    
    # If no common component matched, try to find by text content
    words = component_description.lower().split()
    for word in words:
        if len(word) > 3:  # Only use words with more than 3 characters
            # Try to find elements containing this text
            selector = f":text-matches('{word}', 'i')"
            elements = await page.query_selector_all(selector)
            if elements and len(elements) > 0:
                # Return the first matching element's selector
                return selector
    
    # If all else fails, try some common selectors
    common_selectors = [
        "button", 
        "a", 
        "input", 
        "form", 
        ".btn", 
        ".button", 
        ".nav-item", 
        ".card", 
        ".container"
    ]
    
    for selector in common_selectors:
        element = await page.query_selector(selector)
        if element:
            return selector
    
    # If nothing found, return None
    return None 