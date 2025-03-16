"""AI-first test analyzer for analyzing test results and providing insights."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from tests.ai_pipeline.test_executor import TestResult
from tests.ai_pipeline.test_generator import GeneratedTest

logger = logging.getLogger(__name__)

@dataclass
class TestInsight:
    """Insight derived from test analysis."""
    category: str
    description: str
    severity: str  # 'low', 'medium', 'high'
    confidence: float
    related_tests: List[str]
    metadata: Dict[str, Any]

class AITestAnalyzer:
    """Analyzes test results and provides insights."""
    
    def __init__(self):
        """Initialize the test analyzer."""
        self.insights_cache: Dict[str, List[TestInsight]] = {}
        
    async def analyze_results(
        self,
        tests: List[GeneratedTest],
        results: List[TestResult],
        target: Any
    ) -> List[TestInsight]:
        """Analyze test results and generate insights.
        
        Args:
            tests: List of test cases
            results: List of test results
            target: Target being tested
            
        Returns:
            List of test insights
        """
        # Check cache
        cache_key = self._get_cache_key(tests, results, target)
        if cache_key in self.insights_cache:
            return self.insights_cache[cache_key]
        
        # Group tests and results by category
        grouped_data = self._group_data(tests, results)
        
        # Generate insights for each category
        insights = []
        for category, (category_tests, category_results) in grouped_data.items():
            # Performance analysis
            perf_insights = self._analyze_performance(
                category,
                category_tests,
                category_results
            )
            insights.extend(perf_insights)
            
            # Error pattern analysis
            error_insights = self._analyze_error_patterns(
                category,
                category_tests,
                category_results
            )
            insights.extend(error_insights)
            
            # Coverage analysis
            coverage_insights = self._analyze_coverage(
                category,
                category_tests,
                category_results,
                target
            )
            insights.extend(coverage_insights)
            
            # Edge case analysis
            edge_insights = self._analyze_edge_cases(
                category,
                category_tests,
                category_results
            )
            insights.extend(edge_insights)
        
        # Cache insights
        self.insights_cache[cache_key] = insights
        
        return insights
    
    def _get_cache_key(
        self,
        tests: List[GeneratedTest],
        results: List[TestResult],
        target: Any
    ) -> str:
        """Generate cache key for analysis.
        
        Args:
            tests: List of test cases
            results: List of test results
            target: Target being tested
            
        Returns:
            Cache key string
        """
        test_ids = sorted([test.test_id for test in tests])
        result_ids = sorted([result.test_id for result in results])
        target_hash = hash(str(target))
        return f"{target_hash}-{'-'.join(test_ids)}-{'-'.join(result_ids)}"
    
    def _group_data(
        self,
        tests: List[GeneratedTest],
        results: List[TestResult]
    ) -> Dict[str, Tuple[List[GeneratedTest], List[TestResult]]]:
        """Group tests and results by category.
        
        Args:
            tests: List of test cases
            results: List of test results
            
        Returns:
            Dictionary mapping categories to (tests, results) tuples
        """
        grouped: Dict[str, Tuple[List[GeneratedTest], List[TestResult]]] = {}
        
        # Create test ID to result mapping
        result_map = {r.test_id: r for r in results}
        
        for test in tests:
            if test.category not in grouped:
                grouped[test.category] = ([], [])
            
            grouped[test.category][0].append(test)
            if test.test_id in result_map:
                grouped[test.category][1].append(result_map[test.test_id])
                
        return grouped
    
    def _analyze_performance(
        self,
        category: str,
        tests: List[GeneratedTest],
        results: List[TestResult]
    ) -> List[TestInsight]:
        """Analyze test performance patterns.
        
        Args:
            category: Test category
            tests: List of test cases
            results: List of test results
            
        Returns:
            List of performance-related insights
        """
        insights = []
        
        if not results:
            return insights
            
        # Calculate performance statistics
        durations = [r.duration for r in results]
        mean_duration = np.mean(durations)
        std_duration = np.std(durations)
        
        # Identify slow tests (> 2 std dev)
        slow_tests = [
            (r.test_id, r.duration)
            for r in results
            if r.duration > mean_duration + 2 * std_duration
        ]
        
        if slow_tests:
            insights.append(
                TestInsight(
                    category=category,
                    description=f"Found {len(slow_tests)} slow tests that took significantly longer than average",
                    severity='medium',
                    confidence=0.8,
                    related_tests=[t[0] for t in slow_tests],
                    metadata={
                        'mean_duration': mean_duration,
                        'std_duration': std_duration,
                        'slow_test_durations': dict(slow_tests)
                    }
                )
            )
            
        # Identify performance clusters
        if len(durations) >= 5:
            # Normalize durations
            X = StandardScaler().fit_transform(
                np.array(durations).reshape(-1, 1)
            )
            
            # Cluster using DBSCAN
            clusters = DBSCAN(eps=0.5, min_samples=2).fit(X)
            
            # Analyze clusters
            n_clusters = len(set(clusters.labels_)) - (1 if -1 in clusters.labels_ else 0)
            if n_clusters > 1:
                insights.append(
                    TestInsight(
                        category=category,
                        description=f"Identified {n_clusters} distinct performance clusters",
                        severity='low',
                        confidence=0.7,
                        related_tests=[r.test_id for r in results],
                        metadata={
                            'n_clusters': n_clusters,
                            'cluster_labels': clusters.labels_.tolist()
                        }
                    )
                )
                
        return insights
    
    def _analyze_error_patterns(
        self,
        category: str,
        tests: List[GeneratedTest],
        results: List[TestResult]
    ) -> List[TestInsight]:
        """Analyze test error patterns.
        
        Args:
            category: Test category
            tests: List of test cases
            results: List of test results
            
        Returns:
            List of error-related insights
        """
        insights = []
        
        if not results:
            return insights
            
        # Group errors by type
        error_groups: Dict[str, List[Tuple[str, str]]] = {}
        for result in results:
            if not result.success and result.error:
                error_type = result.error.split(':')[0]
                if error_type not in error_groups:
                    error_groups[error_type] = []
                error_groups[error_type].append(
                    (result.test_id, result.error)
                )
                
        # Analyze each error group
        for error_type, errors in error_groups.items():
            if len(errors) >= 2:
                insights.append(
                    TestInsight(
                        category=category,
                        description=f"Found {len(errors)} tests failing with {error_type}",
                        severity='high',
                        confidence=0.9,
                        related_tests=[e[0] for e in errors],
                        metadata={
                            'error_type': error_type,
                            'error_details': dict(errors)
                        }
                    )
                )
                
        return insights
    
    def _analyze_coverage(
        self,
        category: str,
        tests: List[GeneratedTest],
        results: List[TestResult],
        target: Any
    ) -> List[TestInsight]:
        """Analyze test coverage patterns.
        
        Args:
            category: Test category
            tests: List of test cases
            results: List of test results
            target: Target being tested
            
        Returns:
            List of coverage-related insights
        """
        insights = []
        
        if not tests:
            return insights
            
        # Analyze input coverage
        input_coverage = set()
        for test in tests:
            input_coverage.update(test.inputs.keys())
            
        # Check target signature
        try:
            import inspect
            sig = inspect.signature(target)
            params = set(sig.parameters.keys())
            
            # Find uncovered parameters
            uncovered = params - input_coverage
            if uncovered:
                insights.append(
                    TestInsight(
                        category=category,
                        description=f"Found {len(uncovered)} uncovered parameters: {', '.join(uncovered)}",
                        severity='high',
                        confidence=0.9,
                        related_tests=[t.test_id for t in tests],
                        metadata={
                            'uncovered_params': list(uncovered),
                            'total_params': len(params)
                        }
                    )
                )
                
        except Exception as e:
            logger.warning(f"Error analyzing parameter coverage: {str(e)}")
            
        # Analyze assertion coverage
        assertion_types = set()
        for test in tests:
            for assertion in test.assertions:
                # Extract assertion type (e.g., 'assertEqual', 'assertRaises')
                if 'assert' in assertion:
                    assertion_type = assertion.split('(')[0].strip()
                    assertion_types.add(assertion_type)
                    
        if len(assertion_types) < 3:
            insights.append(
                TestInsight(
                    category=category,
                    description=f"Limited assertion variety: only using {len(assertion_types)} types",
                    severity='medium',
                    confidence=0.7,
                    related_tests=[t.test_id for t in tests],
                    metadata={
                        'assertion_types': list(assertion_types)
                    }
                )
            )
            
        return insights
    
    def _analyze_edge_cases(
        self,
        category: str,
        tests: List[GeneratedTest],
        results: List[TestResult]
    ) -> List[TestInsight]:
        """Analyze edge case coverage and patterns.
        
        Args:
            category: Test category
            tests: List of test cases
            results: List of test results
            
        Returns:
            List of edge case-related insights
        """
        insights = []
        
        if not tests:
            return insights
            
        # Count edge cases
        edge_cases = [t for t in tests if t.edge_case]
        edge_results = [
            r for r in results
            if r.test_id in {t.test_id for t in edge_cases}
        ]
        
        if not edge_cases:
            insights.append(
                TestInsight(
                    category=category,
                    description="No edge cases found in test suite",
                    severity='medium',
                    confidence=0.8,
                    related_tests=[t.test_id for t in tests],
                    metadata={
                        'total_tests': len(tests)
                    }
                )
            )
            return insights
            
        # Analyze edge case failures
        failed_edges = [
            r for r in edge_results
            if not r.success
        ]
        
        if failed_edges:
            insights.append(
                TestInsight(
                    category=category,
                    description=f"{len(failed_edges)} of {len(edge_cases)} edge cases failed",
                    severity='high',
                    confidence=0.9,
                    related_tests=[r.test_id for r in failed_edges],
                    metadata={
                        'total_edge_cases': len(edge_cases),
                        'failed_edge_cases': len(failed_edges),
                        'failure_rate': len(failed_edges) / len(edge_cases)
                    }
                )
            )
            
        return insights 