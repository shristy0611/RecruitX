"""Test Analyzer Agent that analyzes test results and provides insights."""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from .base_test_agent import BaseTestAgent, TestResult

logger = logging.getLogger(__name__)

class TestAnalyzerAgent(BaseTestAgent):
    """Analyzes test results and provides insights."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the test analyzer.
        
        Args:
            db_path: Path to SQLite database for test results
        """
        super().__init__('test_analyzer', db_path)
        
    async def _run_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Not implemented for analyzer agent."""
        raise NotImplementedError("Analyzer agent does not run tests")
    
    async def analyze_results(
        self,
        time_window: Optional[timedelta] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze test results within a time window.
        
        Args:
            time_window: Optional time window to analyze
            categories: Optional list of test categories to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        # Get test results from database
        results = self._get_test_results(time_window, categories)
        if not results:
            return {
                'status': 'error',
                'message': 'No test results found for analysis'
            }
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)
        
        # Basic statistics
        basic_stats = self._calculate_basic_stats(df)
        
        # Performance analysis
        perf_analysis = self._analyze_performance(df)
        
        # Failure patterns
        failure_patterns = self._analyze_failure_patterns(df)
        
        # Coverage trends
        coverage_trends = self._analyze_coverage_trends(df)
        
        # Resource usage patterns
        resource_patterns = self._analyze_resource_usage(df)
        
        # Generate insights
        insights = self._generate_insights(
            basic_stats,
            perf_analysis,
            failure_patterns,
            coverage_trends,
            resource_patterns
        )
        
        return {
            'status': 'success',
            'timestamp': datetime.now(),
            'analysis_window': str(time_window) if time_window else 'all time',
            'categories': categories if categories else 'all',
            'basic_stats': basic_stats,
            'performance_analysis': perf_analysis,
            'failure_patterns': failure_patterns,
            'coverage_trends': coverage_trends,
            'resource_patterns': resource_patterns,
            'insights': insights
        }
    
    def _get_test_results(
        self,
        time_window: Optional[timedelta] = None,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get test results from database.
        
        Args:
            time_window: Optional time window to filter results
            categories: Optional list of categories to filter results
            
        Returns:
            List of test result dictionaries
        """
        query = "SELECT * FROM test_results"
        params = []
        
        # Add time window filter
        if time_window:
            cutoff = datetime.now() - time_window
            query += " WHERE timestamp >= ?"
            params.append(cutoff)
        
        # Add category filter
        if categories:
            if 'WHERE' in query:
                query += " AND"
            else:
                query += " WHERE"
            placeholders = ','.join('?' * len(categories))
            query += f" category IN ({placeholders})"
            params.extend(categories)
        
        # Execute query
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic test statistics.
        
        Args:
            df: DataFrame containing test results
            
        Returns:
            Dictionary containing basic statistics
        """
        total_tests = len(df)
        passed_tests = len(df[df['status'] == 'pass'])
        failed_tests = len(df[df['status'] == 'fail'])
        error_tests = len(df[df['status'] == 'error'])
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'avg_duration': df['duration'].mean(),
            'median_duration': df['duration'].median(),
            'std_duration': df['duration'].std(),
            'categories': df['category'].value_counts().to_dict(),
            'agents': df['agent_id'].value_counts().to_dict()
        }
    
    def _analyze_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze test performance patterns.
        
        Args:
            df: DataFrame containing test results
            
        Returns:
            Dictionary containing performance analysis
        """
        # Calculate performance metrics
        performance_by_category = df.groupby('category').agg({
            'duration': ['mean', 'median', 'std', 'count']
        }).to_dict()
        
        # Identify slow tests
        slow_threshold = df['duration'].mean() + 2 * df['duration'].std()
        slow_tests = df[df['duration'] > slow_threshold]
        
        # Analyze performance trends
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        performance_trend = df.set_index('timestamp')['duration'].resample('D').mean()
        
        return {
            'performance_by_category': performance_by_category,
            'slow_tests': slow_tests[['test_id', 'duration', 'category']].to_dict('records'),
            'performance_trend': performance_trend.to_dict(),
            'slow_threshold': slow_threshold
        }
    
    def _analyze_failure_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze test failure patterns.
        
        Args:
            df: DataFrame containing test results
            
        Returns:
            Dictionary containing failure pattern analysis
        """
        # Get failed tests
        failed_df = df[df['status'].isin(['fail', 'error'])]
        
        # Analyze failure frequency by category
        failure_by_category = failed_df['category'].value_counts().to_dict()
        
        # Analyze common error messages
        error_patterns = failed_df['error_message'].value_counts().head(10).to_dict()
        
        # Identify flaky tests (tests that both pass and fail)
        test_results = df.groupby('test_id')['status'].agg(list)
        flaky_tests = test_results[test_results.apply(
            lambda x: 'pass' in x and ('fail' in x or 'error' in x)
        )].index.tolist()
        
        return {
            'failure_by_category': failure_by_category,
            'error_patterns': error_patterns,
            'flaky_tests': flaky_tests,
            'total_failures': len(failed_df)
        }
    
    def _analyze_coverage_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze code coverage trends.
        
        Args:
            df: DataFrame containing test results
            
        Returns:
            Dictionary containing coverage trend analysis
        """
        # Extract coverage from details
        df['coverage'] = df['details'].apply(
            lambda x: x.get('coverage', 0) if isinstance(x, dict) else 0
        )
        
        # Calculate coverage trends
        coverage_by_date = df.set_index('timestamp').resample('D')['coverage'].mean()
        
        # Calculate coverage by category
        coverage_by_category = df.groupby('category')['coverage'].agg([
            'mean', 'min', 'max'
        ]).to_dict()
        
        return {
            'coverage_trend': coverage_by_date.to_dict(),
            'coverage_by_category': coverage_by_category,
            'overall_coverage': df['coverage'].mean(),
            'coverage_std': df['coverage'].std()
        }
    
    def _analyze_resource_usage(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze resource usage patterns.
        
        Args:
            df: DataFrame containing test results
            
        Returns:
            Dictionary containing resource usage analysis
        """
        # Extract resource usage metrics
        df['memory_mb'] = df['memory_usage']
        df['cpu_percent'] = df['cpu_usage']
        
        # Calculate resource usage by category
        resource_by_category = df.groupby('category').agg({
            'memory_mb': ['mean', 'max'],
            'cpu_percent': ['mean', 'max']
        }).to_dict()
        
        # Identify resource-intensive tests
        memory_threshold = df['memory_mb'].mean() + 2 * df['memory_mb'].std()
        cpu_threshold = df['cpu_percent'].mean() + 2 * df['cpu_percent'].std()
        
        resource_intensive = df[
            (df['memory_mb'] > memory_threshold) |
            (df['cpu_percent'] > cpu_threshold)
        ]
        
        # Cluster tests by resource usage
        X = StandardScaler().fit_transform(
            df[['memory_mb', 'cpu_percent']].fillna(0)
        )
        clusters = DBSCAN(eps=0.5, min_samples=5).fit(X)
        
        return {
            'resource_by_category': resource_by_category,
            'resource_intensive_tests': resource_intensive[
                ['test_id', 'memory_mb', 'cpu_percent']
            ].to_dict('records'),
            'memory_threshold': memory_threshold,
            'cpu_threshold': cpu_threshold,
            'resource_clusters': len(set(clusters.labels_)) - (1 if -1 in clusters.labels_ else 0)
        }
    
    def _generate_insights(
        self,
        basic_stats: Dict[str, Any],
        perf_analysis: Dict[str, Any],
        failure_patterns: Dict[str, Any],
        coverage_trends: Dict[str, Any],
        resource_patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from analysis results.
        
        Args:
            basic_stats: Basic test statistics
            perf_analysis: Performance analysis results
            failure_patterns: Failure pattern analysis
            coverage_trends: Coverage trend analysis
            resource_patterns: Resource usage analysis
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Test health insights
        pass_rate = basic_stats['pass_rate']
        if pass_rate < 0.9:
            insights.append(
                f"Low pass rate ({pass_rate:.1%}). Consider investigating "
                f"common failure patterns in {failure_patterns['error_patterns']}"
            )
        
        # Performance insights
        if perf_analysis['slow_tests']:
            insights.append(
                f"Found {len(perf_analysis['slow_tests'])} slow tests. "
                "Consider optimizing or parallelizing these tests."
            )
        
        # Coverage insights
        coverage = coverage_trends['overall_coverage']
        if coverage < 80:
            insights.append(
                f"Low code coverage ({coverage:.1f}%). Consider adding more "
                "test cases to improve coverage."
            )
        
        # Resource usage insights
        resource_intensive = resource_patterns['resource_intensive_tests']
        if resource_intensive:
            insights.append(
                f"Found {len(resource_intensive)} resource-intensive tests. "
                "Consider optimizing resource usage or running these tests separately."
            )
        
        # Flaky test insights
        flaky_tests = failure_patterns['flaky_tests']
        if flaky_tests:
            insights.append(
                f"Found {len(flaky_tests)} flaky tests. Consider investigating "
                "and stabilizing these tests."
            )
        
        return insights
    
    async def generate_report(
        self,
        analysis_results: Dict[str, Any],
        format: str = 'markdown'
    ) -> str:
        """Generate a formatted report from analysis results.
        
        Args:
            analysis_results: Dictionary containing analysis results
            format: Output format ('markdown' or 'html')
            
        Returns:
            Formatted report string
        """
        if format == 'markdown':
            return self._generate_markdown_report(analysis_results)
        elif format == 'html':
            return self._generate_html_report(analysis_results)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report from analysis results.
        
        Args:
            results: Dictionary containing analysis results
            
        Returns:
            Markdown formatted report
        """
        report = []
        
        # Header
        report.append("# Test Analysis Report")
        report.append(f"Generated on: {results['timestamp']}")
        report.append(f"Analysis window: {results['analysis_window']}")
        report.append("")
        
        # Basic stats
        report.append("## Test Statistics")
        stats = results['basic_stats']
        report.append(f"- Total tests: {stats['total_tests']}")
        report.append(f"- Pass rate: {stats['pass_rate']:.1%}")
        report.append(f"- Average duration: {stats['avg_duration']:.2f}s")
        report.append("")
        
        # Performance
        report.append("## Performance Analysis")
        perf = results['performance_analysis']
        report.append(f"- Slow tests identified: {len(perf['slow_tests'])}")
        report.append("### Slow Tests")
        for test in perf['slow_tests'][:5]:  # Show top 5
            report.append(f"- {test['test_id']}: {test['duration']:.2f}s")
        report.append("")
        
        # Failures
        report.append("## Failure Analysis")
        failures = results['failure_patterns']
        report.append(f"- Total failures: {failures['total_failures']}")
        report.append(f"- Flaky tests: {len(failures['flaky_tests'])}")
        report.append("### Common Error Patterns")
        for error, count in list(failures['error_patterns'].items())[:5]:
            report.append(f"- {error}: {count} occurrences")
        report.append("")
        
        # Coverage
        report.append("## Coverage Analysis")
        coverage = results['coverage_trends']
        report.append(f"- Overall coverage: {coverage['overall_coverage']:.1f}%")
        report.append("### Coverage by Category")
        for category, stats in coverage['coverage_by_category'].items():
            report.append(f"- {category}: {stats['mean']:.1f}%")
        report.append("")
        
        # Resource usage
        report.append("## Resource Usage")
        resources = results['resource_patterns']
        report.append(
            f"- Resource-intensive tests: {len(resources['resource_intensive_tests'])}"
        )
        report.append("### Top Resource Consumers")
        for test in resources['resource_intensive_tests'][:5]:
            report.append(
                f"- {test['test_id']}: {test['memory_mb']:.1f}MB, "
                f"{test['cpu_percent']:.1f}% CPU"
            )
        report.append("")
        
        # Insights
        report.append("## Insights")
        for insight in results['insights']:
            report.append(f"- {insight}")
        
        return "\n".join(report)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML report from analysis results.
        
        Args:
            results: Dictionary containing analysis results
            
        Returns:
            HTML formatted report
        """
        # Convert markdown to HTML
        import markdown
        return markdown.markdown(self._generate_markdown_report(results))
    
    async def cleanup(self):
        """Cleanup any resources."""
        pass 