"""
XAI Visualization Components.

This module provides visualization components for displaying explanations
from the XAI layer in an interactive, user-friendly format.
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# Path to templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


@dataclass
class ExplanationVisualizationConfig:
    """Configuration for explanation visualizations."""
    
    title: str = "RecruitPro AI Explanation"
    show_factors: bool = True
    show_strengths: bool = True
    show_improvements: bool = True
    show_metadata: bool = False
    theme: str = "light"  # "light" or "dark"
    chart_colors: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.chart_colors is None:
            self.chart_colors = ["#4285F4", "#EA4335", "#FBBC05", "#34A853", "#FF6D01"]


def generate_explanation_html(explanation_data: Dict[str, Any], config: Optional[ExplanationVisualizationConfig] = None) -> str:
    """
    Generate HTML visualization for an explanation.
    
    Args:
        explanation_data: Explanation data from XAI module
        config: Visualization configuration
        
    Returns:
        HTML string containing the visualization
    """
    if config is None:
        config = ExplanationVisualizationConfig()
    
    # Extract key information from explanation data
    agent_type = explanation_data.get("agent_type", "unknown")
    explanation_text = explanation_data.get("explanation", "No explanation available")
    score = explanation_data.get("score", 0.0)
    factors = explanation_data.get("factors", {})
    metadata = explanation_data.get("metadata", {})
    
    # Extract optional data
    factor_explanations = metadata.get("factor_explanations", {})
    strengths = metadata.get("strengths", [])
    improvement_areas = metadata.get("improvement_areas", [])
    
    # Load the base HTML template
    html_template = _load_template("explanation_base.html")
    
    # Format the explanation text with proper styling
    formatted_explanation = _format_markdown_text(explanation_text)
    
    # Generate the factors chart if needed
    factors_chart = ""
    if config.show_factors and factors:
        factors_chart = _generate_factors_chart(factors, factor_explanations, config)
    
    # Generate strengths and improvements sections if needed
    strengths_section = ""
    if config.show_strengths and strengths:
        strengths_section = _generate_list_section("Strengths", strengths, "strengths-section")
    
    improvements_section = ""
    if config.show_improvements and improvement_areas:
        improvements_section = _generate_list_section("Areas for Improvement", improvement_areas, "improvements-section")
    
    # Generate metadata section if needed
    metadata_section = ""
    if config.show_metadata and metadata:
        filtered_metadata = {k: v for k, v in metadata.items() 
                             if k not in ["factor_explanations", "strengths", "improvement_areas"]}
        if filtered_metadata:
            metadata_section = _generate_metadata_section(filtered_metadata)
    
    # Replace placeholders in the template
    html = html_template.replace("{{TITLE}}", config.title)
    html = html.replace("{{AGENT_TYPE}}", agent_type.title())
    html = html.replace("{{THEME_CLASS}}", f"theme-{config.theme}")
    html = html.replace("{{EXPLANATION_TEXT}}", formatted_explanation)
    html = html.replace("{{OVERALL_SCORE}}", f"{score:.1f}")
    html = html.replace("{{FACTORS_CHART}}", factors_chart)
    html = html.replace("{{STRENGTHS_SECTION}}", strengths_section)
    html = html.replace("{{IMPROVEMENTS_SECTION}}", improvements_section)
    html = html.replace("{{METADATA_SECTION}}", metadata_section)
    
    return html


def _load_template(template_name: str) -> str:
    """
    Load an HTML template from the templates directory.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        Template content as string
    """
    try:
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        
        # Check if template file exists
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Read the template file
        with open(template_path, "r") as f:
            return f.read()
    except Exception as e:
        # If there's an error loading the template, return a simple fallback
        print(f"Error loading template {template_name}: {e}")
        return f"""<!DOCTYPE html>
<html>
<head><title>{{TITLE}}</title></head>
<body>
    <h1>{{TITLE}}</h1>
    <div>{{EXPLANATION_TEXT}}</div>
    <div>Score: {{OVERALL_SCORE}}</div>
    <div>{{FACTORS_CHART}}</div>
    <div>{{STRENGTHS_SECTION}}</div>
    <div>{{IMPROVEMENTS_SECTION}}</div>
    <div>{{METADATA_SECTION}}</div>
    <p>Note: Error loading template - using fallback</p>
</body>
</html>"""


def _format_markdown_text(text: str) -> str:
    """
    Format markdown-like text to HTML for the explanation.
    
    Args:
        text: Markdown-formatted text
        
    Returns:
        HTML-formatted text
    """
    # Basic markdown formatting
    # Bold
    text = text.replace("**", "<strong>", 1)
    while "**" in text:
        text = text.replace("**", "</strong>", 1)
        if "**" in text:
            text = text.replace("**", "<strong>", 1)
    
    # Italic
    text = text.replace("*", "<em>", 1)
    while "*" in text:
        text = text.replace("*", "</em>", 1)
        if "*" in text:
            text = text.replace("*", "<em>", 1)
    
    # Lists
    lines = text.split("\n")
    in_list = False
    formatted_lines = []
    
    for line in lines:
        if line.strip().startswith("- "):
            if not in_list:
                formatted_lines.append("<ul>")
                in_list = True
            formatted_lines.append(f"<li>{line.strip()[2:]}</li>")
        else:
            if in_list:
                formatted_lines.append("</ul>")
                in_list = False
            formatted_lines.append(line)
    
    if in_list:
        formatted_lines.append("</ul>")
    
    # Convert line breaks to paragraphs
    text = "<p>" + "</p><p>".join([line for line in formatted_lines if line.strip()]) + "</p>"
    text = text.replace("<p><ul>", "<ul>").replace("</ul></p>", "</ul>")
    
    return text


def _generate_factors_chart(factors: Dict[str, float], factor_explanations: Dict[str, str], config: ExplanationVisualizationConfig) -> str:
    """
    Generate HTML for the factors chart.
    
    Args:
        factors: Dictionary of factor names and scores
        factor_explanations: Dictionary of factor explanations
        config: Visualization configuration
        
    Returns:
        HTML string for factors chart
    """
    if not factors:
        return ""
    
    # Start the factors chart section
    html = '<div class="factors-chart">\n'
    html += '    <h3 class="section-title">Factor Analysis</h3>\n'
    
    # Generate a bar for each factor
    for i, (factor_name, factor_score) in enumerate(factors.items()):
        color_index = i % len(config.chart_colors)
        color = config.chart_colors[color_index]
        
        # Get explanation for this factor if available
        explanation = factor_explanations.get(factor_name, "")
        explanation_html = f'<div class="factor-explanation">{explanation}</div>' if explanation else ""
        
        # Generate the factor bar
        html += f'''    <div class="factor-bar">
        <div class="factor-header">
            <span class="factor-name">{factor_name}</span>
            <span class="factor-score">{factor_score:.1f}</span>
        </div>
        <div class="factor-bar-outer">
            <div class="factor-bar-inner" style="width: {min(100, max(0, factor_score))}%; background-color: {color};"></div>
        </div>
        {explanation_html}
    </div>\n'''
    
    html += '</div>'
    return html


def _generate_list_section(title: str, items: List[str], css_class: str) -> str:
    """
    Generate HTML for a list section (strengths or improvements).
    
    Args:
        title: Section title
        items: List items to display
        css_class: CSS class for styling
        
    Returns:
        HTML string for list section
    """
    if not items:
        return ""
    
    html = f'<div class="{css_class}">\n'
    html += f'    <h3 class="section-title">{title}</h3>\n'
    html += '    <ul>\n'
    
    for item in items:
        item_class = "strength-item" if css_class == "strengths-section" else "improvement-item"
        html += f'        <li class="{item_class}">{item}</li>\n'
    
    html += '    </ul>\n'
    html += '</div>'
    
    return html


def _generate_metadata_section(metadata: Dict[str, Any]) -> str:
    """
    Generate HTML for metadata section.
    
    Args:
        metadata: Dictionary of metadata
        
    Returns:
        HTML string for metadata section
    """
    if not metadata:
        return ""
    
    html = '<div class="metadata-section">\n'
    html += '    <h3 class="section-title">Additional Details</h3>\n'
    html += '    <table class="metadata-table">\n'
    
    for key, value in metadata.items():
        # Format the key for display
        display_key = key.replace("_", " ").title()
        
        # Format the value based on its type
        if key == "decision" and isinstance(value, str):
            decision_class = "decision-pass" if value.upper() == "PASS" else \
                            "decision-hold" if value.upper() == "HOLD" else \
                            "decision-reject"
            display_value = f'<span class="decision-badge {decision_class}">{value.upper()}</span>'
        elif key == "top_candidates" and isinstance(value, list):
            display_value = '<div class="candidate-list">'
            for candidate in value:
                if isinstance(candidate, dict):
                    # Format candidate as a mini-card
                    candidate_name = candidate.get("name", "Unknown")
                    candidate_score = candidate.get("score", 0)
                    display_value += f'<div class="candidate-item">{candidate_name} ({candidate_score:.1f})</div>'
                else:
                    display_value += f'<div class="candidate-item">{str(candidate)}</div>'
            display_value += '</div>'
        elif isinstance(value, dict):
            display_value = "<pre>" + json.dumps(value, indent=2) + "</pre>"
        elif isinstance(value, list):
            display_value = "<ul>" + "".join([f"<li>{item}</li>" for item in value]) + "</ul>"
        else:
            display_value = str(value)
        
        html += f'        <tr><th>{display_key}</th><td>{display_value}</td></tr>\n'
    
    html += '    </table>\n'
    html += '</div>'
    
    return html
