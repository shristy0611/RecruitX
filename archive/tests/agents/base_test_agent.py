"""Base class for all test agents in the agentic testing framework."""

import asyncio
import logging
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.utils.gemini_manager import GeminiKeyManager

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Structured test result data."""
    test_id: str
    agent_id: str
    status: str  # 'pass', 'fail', 'error', 'skip'
    name: str
    category: str
    duration: float
    timestamp: datetime
    details: Dict[str, Any]
    error_message: Optional[str] = None
    stacktrace: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

class BaseTestAgent(ABC):
    """Base class for all test agents in the system."""
    
    def __init__(self, agent_id: str, db_path: Optional[Path] = None):
        """Initialize the test agent.
        
        Args:
            agent_id: Unique identifier for this agent
            db_path: Path to SQLite database for test results
        """
        self.agent_id = agent_id
        self.db_path = db_path or Path(__file__).parent.parent.parent / 'data' / 'test.db'
        self.gemini = GeminiKeyManager()
        self._setup_database()
        
    def _setup_database(self):
        """Initialize the test results database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                status TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                duration FLOAT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                error_message TEXT,
                stacktrace TEXT,
                memory_usage FLOAT,
                cpu_usage FLOAT
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_results_test_id 
            ON test_results(test_id)
        ''')
        
        conn.commit()
        conn.close()
    
    async def execute_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Execute a test and record the result.
        
        Args:
            test_data: Dictionary containing test parameters
            
        Returns:
            TestResult object containing the test outcome
        """
        start_time = datetime.now()
        result = None
        
        try:
            # Execute the actual test
            result = await self._run_test(test_data)
            
        except Exception as e:
            logger.error(f"Error in test execution: {str(e)}", exc_info=True)
            result = TestResult(
                test_id=test_data.get('test_id', 'unknown'),
                agent_id=self.agent_id,
                status='error',
                name=test_data.get('name', 'unknown'),
                category=test_data.get('category', 'unknown'),
                duration=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                details={},
                error_message=str(e),
                stacktrace=logging.traceback.format_exc()
            )
        
        finally:
            # Record the result
            if result:
                self._save_result(result)
            
        return result
    
    def _save_result(self, result: TestResult):
        """Save test result to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_results (
                    test_id, agent_id, status, name, category,
                    duration, timestamp, details, error_message,
                    stacktrace, memory_usage, cpu_usage
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.test_id,
                result.agent_id,
                result.status,
                result.name,
                result.category,
                result.duration,
                result.timestamp,
                str(result.details),
                result.error_message,
                result.stacktrace,
                result.memory_usage,
                result.cpu_usage
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save test result: {str(e)}")
            
        finally:
            conn.close()
    
    @abstractmethod
    async def _run_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Execute the actual test logic.
        
        This method must be implemented by each specific test agent.
        
        Args:
            test_data: Dictionary containing test parameters
            
        Returns:
            TestResult object containing the test outcome
        """
        pass
    
    async def get_test_history(
        self, 
        test_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[TestResult]:
        """Retrieve test execution history with optional filters.
        
        Args:
            test_id: Filter by specific test ID
            category: Filter by test category
            status: Filter by test status
            limit: Maximum number of results to return
            
        Returns:
            List of TestResult objects matching the filters
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM test_results WHERE 1=1"
        params = []
        
        if test_id:
            query += " AND test_id = ?"
            params.append(test_id)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append(TestResult(
                test_id=row[1],
                agent_id=row[2],
                status=row[3],
                name=row[4],
                category=row[5],
                duration=row[6],
                timestamp=row[7],
                details=eval(row[8]) if row[8] else {},
                error_message=row[9],
                stacktrace=row[10],
                memory_usage=row[11],
                cpu_usage=row[12]
            ))
        
        return results
    
    async def analyze_test_patterns(self) -> Dict[str, Any]:
        """Analyze test execution patterns and statistics.
        
        Returns:
            Dictionary containing analysis results:
            - success_rate: Overall test success rate
            - common_failures: Most common failure patterns
            - avg_duration: Average test duration
            - performance_trends: Performance trends over time
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get overall statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passed,
                AVG(duration) as avg_duration,
                AVG(memory_usage) as avg_memory,
                AVG(cpu_usage) as avg_cpu
            FROM test_results
        ''')
        
        total, passed, avg_duration, avg_memory, avg_cpu = cursor.fetchone()
        
        # Get common failure patterns
        cursor.execute('''
            SELECT error_message, COUNT(*) as count
            FROM test_results
            WHERE status = 'fail'
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        common_failures = [
            {'message': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]
        
        # Get performance trends
        cursor.execute('''
            SELECT 
                date(timestamp) as test_date,
                AVG(duration) as avg_duration
            FROM test_results
            GROUP BY test_date
            ORDER BY test_date DESC
            LIMIT 7
        ''')
        
        performance_trends = [
            {'date': row[0], 'avg_duration': row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'total_tests': total,
            'passed_tests': passed,
            'avg_duration': avg_duration,
            'avg_memory_usage': avg_memory,
            'avg_cpu_usage': avg_cpu,
            'common_failures': common_failures,
            'performance_trends': performance_trends
        }
    
    async def cleanup(self):
        """Cleanup resources used by the agent."""
        pass  # Override in specific agents if needed 