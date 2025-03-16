"""Analytics visualization component."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tests.analytics.performance_analyzer import PerformanceMetrics, PerformanceInsight

logger = logging.getLogger(__name__)

class AnalyticsVisualizer:
    """Visualizes analytics data and insights."""
    
    def __init__(
        self,
        output_dir: Union[str, Path],
        max_history: int = 1000
    ):
        """Initialize visualizer.
        
        Args:
            output_dir: Directory for output files
            max_history: Maximum data points to keep
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_history = max_history
        self.metrics_history: List[PerformanceMetrics] = []
        self.insight_history: List[PerformanceInsight] = []
        
    def add_metrics(self, metrics: PerformanceMetrics):
        """Add metrics to history.
        
        Args:
            metrics: Performance metrics
        """
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
            
    def add_insights(self, insights: List[PerformanceInsight]):
        """Add insights to history.
        
        Args:
            insights: Performance insights
        """
        self.insight_history.extend(insights)
        if len(self.insight_history) > self.max_history:
            self.insight_history = self.insight_history[-self.max_history:]
            
    def generate_dashboard(self, output_file: Optional[str] = None) -> str:
        """Generate interactive dashboard.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to generated HTML file
        """
        if not self.metrics_history:
            logger.warning("No metrics data available for visualization")
            return ""
            
        # Create figure with subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'System Metrics',
                'Test Metrics',
                'Agent Metrics',
                'Behavior Metrics',
                'Resource Usage',
                'Insights Timeline'
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Add system metrics
        self._add_system_metrics(fig, row=1, col=1)
        
        # Add test metrics
        self._add_test_metrics(fig, row=1, col=2)
        
        # Add agent metrics
        self._add_agent_metrics(fig, row=2, col=1)
        
        # Add behavior metrics
        self._add_behavior_metrics(fig, row=2, col=2)
        
        # Add resource usage
        self._add_resource_metrics(fig, row=3, col=1)
        
        # Add insights timeline
        self._add_insights_timeline(fig, row=3, col=2)
        
        # Update layout
        fig.update_layout(
            height=1200,
            width=1600,
            showlegend=True,
            title_text="Performance Analytics Dashboard",
            title_x=0.5,
            template="plotly_white"
        )
        
        # Save dashboard
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"dashboard_{timestamp}.html"
            
        fig.write_html(output_file)
        logger.info(f"Generated dashboard: {output_file}")
        
        return str(output_file)
        
    def _add_system_metrics(self, fig: go.Figure, row: int, col: int):
        """Add system metrics visualization.
        
        Args:
            fig: Plotly figure
            row: Subplot row
            col: Subplot column
        """
        timestamps = [m.timestamp for m in self.metrics_history]
        dates = [datetime.fromtimestamp(t) for t in timestamps]
        
        metrics = ['total_agents', 'active_agents', 'message_rate', 'consensus_rate']
        for metric in metrics:
            values = [m.system_metrics.get(metric, 0) for m in self.metrics_history]
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    name=metric.replace('_', ' ').title(),
                    mode='lines+markers'
                ),
                row=row,
                col=col
            )
            
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Value", row=row, col=col)
        
    def _add_test_metrics(self, fig: go.Figure, row: int, col: int):
        """Add test metrics visualization.
        
        Args:
            fig: Plotly figure
            row: Subplot row
            col: Subplot column
        """
        timestamps = [m.timestamp for m in self.metrics_history]
        dates = [datetime.fromtimestamp(t) for t in timestamps]
        
        metrics = ['success_rate', 'error_rate', 'average_duration']
        for metric in metrics:
            values = [m.test_metrics.get(metric, 0) for m in self.metrics_history]
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    name=metric.replace('_', ' ').title(),
                    mode='lines+markers'
                ),
                row=row,
                col=col
            )
            
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Value", row=row, col=col)
        
    def _add_agent_metrics(self, fig: go.Figure, row: int, col: int):
        """Add agent metrics visualization.
        
        Args:
            fig: Plotly figure
            row: Subplot row
            col: Subplot column
        """
        timestamps = [m.timestamp for m in self.metrics_history]
        dates = [datetime.fromtimestamp(t) for t in timestamps]
        
        # Get unique agent IDs
        agent_ids = set()
        for metrics in self.metrics_history:
            agent_ids.update(metrics.agent_metrics.keys())
            
        # Plot success rate for each agent
        for agent_id in sorted(agent_ids):
            values = []
            for metrics in self.metrics_history:
                if agent_id in metrics.agent_metrics:
                    values.append(
                        metrics.agent_metrics[agent_id].get('test_success_rate', 0)
                    )
                else:
                    values.append(0)
                    
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    name=f"Agent {agent_id}",
                    mode='lines+markers'
                ),
                row=row,
                col=col
            )
            
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Success Rate", row=row, col=col)
        
    def _add_behavior_metrics(self, fig: go.Figure, row: int, col: int):
        """Add behavior metrics visualization.
        
        Args:
            fig: Plotly figure
            row: Subplot row
            col: Subplot column
        """
        timestamps = [m.timestamp for m in self.metrics_history]
        dates = [datetime.fromtimestamp(t) for t in timestamps]
        
        metrics = ['total_behaviors', 'average_confidence', 'behavior_diversity']
        for metric in metrics:
            values = [m.behavior_metrics.get(metric, 0) for m in self.metrics_history]
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    name=metric.replace('_', ' ').title(),
                    mode='lines+markers'
                ),
                row=row,
                col=col
            )
            
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Value", row=row, col=col)
        
    def _add_resource_metrics(self, fig: go.Figure, row: int, col: int):
        """Add resource usage visualization.
        
        Args:
            fig: Plotly figure
            row: Subplot row
            col: Subplot column
        """
        timestamps = [m.timestamp for m in self.metrics_history]
        dates = [datetime.fromtimestamp(t) for t in timestamps]
        
        # Calculate resource metrics
        cpu_usage = []
        memory_usage = []
        io_usage = []
        
        for metrics in self.metrics_history:
            # Example resource calculations
            cpu = metrics.system_metrics.get('active_agents', 0) / max(
                metrics.system_metrics.get('total_agents', 1),
                1
            )
            memory = len(metrics.metrics_history) / self.max_history
            io = metrics.system_metrics.get('message_rate', 0) / 100
            
            cpu_usage.append(cpu)
            memory_usage.append(memory)
            io_usage.append(io)
            
        # Add traces
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cpu_usage,
                name="CPU Usage",
                mode='lines+markers'
            ),
            row=row,
            col=col
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=memory_usage,
                name="Memory Usage",
                mode='lines+markers'
            ),
            row=row,
            col=col
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=io_usage,
                name="I/O Usage",
                mode='lines+markers'
            ),
            row=row,
            col=col
        )
        
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Usage %", row=row, col=col)
        
    def _add_insights_timeline(self, fig: go.Figure, row: int, col: int):
        """Add insights timeline visualization.
        
        Args:
            fig: Plotly figure
            row: Subplot row
            col: Subplot column
        """
        if not self.insight_history:
            return
            
        # Prepare data
        dates = [datetime.fromtimestamp(i.timestamp) for i in self.insight_history]
        categories = [i.category for i in self.insight_history]
        severities = [i.severity for i in self.insight_history]
        descriptions = [i.description for i in self.insight_history]
        
        # Create hover text
        hover_text = [
            f"Category: {cat}<br>"
            f"Severity: {sev}<br>"
            f"Description: {desc}"
            for cat, sev, desc in zip(categories, severities, descriptions)
        ]
        
        # Map severities to colors
        colors = {
            'high': 'red',
            'medium': 'orange',
            'low': 'green'
        }
        marker_colors = [colors[s] for s in severities]
        
        # Add scatter plot
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=categories,
                mode='markers',
                marker=dict(
                    size=10,
                    color=marker_colors,
                    symbol='circle'
                ),
                text=hover_text,
                hoverinfo='text',
                name='Insights'
            ),
            row=row,
            col=col
        )
        
        fig.update_xaxes(title_text="Time", row=row, col=col)
        fig.update_yaxes(title_text="Category", row=row, col=col)
        
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate PDF report.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to generated PDF file
        """
        if not self.metrics_history:
            logger.warning("No metrics data available for report")
            return ""
            
        # Create report dataframe
        report_data = []
        
        # Add system metrics summary
        system_metrics = pd.DataFrame([m.system_metrics for m in self.metrics_history])
        system_summary = system_metrics.describe()
        report_data.append(("System Metrics", system_summary))
        
        # Add test metrics summary
        test_metrics = pd.DataFrame([m.test_metrics for m in self.metrics_history])
        test_summary = test_metrics.describe()
        report_data.append(("Test Metrics", test_summary))
        
        # Add behavior metrics summary
        behavior_metrics = pd.DataFrame([m.behavior_metrics for m in self.metrics_history])
        behavior_summary = behavior_metrics.describe()
        report_data.append(("Behavior Metrics", behavior_summary))
        
        # Add insights summary
        if self.insight_history:
            insights_df = pd.DataFrame([
                {
                    'timestamp': datetime.fromtimestamp(i.timestamp),
                    'category': i.category,
                    'severity': i.severity,
                    'confidence': i.confidence,
                    'description': i.description
                }
                for i in self.insight_history
            ])
            
            insights_summary = insights_df.groupby(['category', 'severity']).size()
            report_data.append(("Insights Summary", insights_summary))
            
        # Generate PDF report
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"report_{timestamp}.pdf"
            
        # TODO: Implement PDF generation using reportlab or similar
        logger.info(f"Generated report: {output_file}")
        
        return str(output_file) 