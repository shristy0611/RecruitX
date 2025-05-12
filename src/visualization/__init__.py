"""
Visualization module for RecruitPro AI.

This module provides visualization components for displaying
explanations from the XAI layer in a user-friendly format.
"""

from src.visualization.xai_visualizer import generate_explanation_html, ExplanationVisualizationConfig

__all__ = [
    'generate_explanation_html',
    'ExplanationVisualizationConfig',
]
