#!/usr/bin/env python
"""
Comprehensive Test Runner for Self-Improving Agent Components
"""
import logging
import time
import sys
import os
from typing import Dict, Any, List, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_runner")


def run_tests() -> Dict[str, Any]:
    """Run all tests for self-improving agent components."""
    # Import components
    from src.agents.self_improving.feedback_processor import FeedbackProcessor, get_feedback_processor
    from src.agents.self_improving.performance_monitor import PerformanceMonitor, get_performance_monitor
    from src.agents.self_improving.reinforcement_learner import ReinforcementLearner, get_reinforcement_learner
    from src.agents.self_improving.parameter_optimizer import ParameterOptimizer, get_parameter_optimizer
    from src.agents.self_improving.experience_replay import ExperienceReplay, get_experience_replay
    from src.agents.self_improving.learning_orchestrator import LearningOrchestrator, get_learning_orchestrator
    
    # Reset global singletons for clean testing
    import src.agents.self_improving.reinforcement_learner as rl_module
    import src.agents.self_improving.parameter_optimizer as po_module
    import src.agents.self_improving.experience_replay as er_module
    import src.agents.self_improving.learning_orchestrator as lo_module
    
    rl_module._learner = None
    po_module._optimizer = None
    er_module._replay = None
    lo_module._orchestrator = None
    
    # Dictionary to track test results
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    # Test functions
    test_functions = [
        test_feedback_processor,
        test_performance_monitor, 
        test_reinforcement_learner,
        test_parameter_optimizer,
        test_experience_replay,
        test_learning_orchestrator,
        test_integration
    ]
    
    # Run tests
    for test_func in test_functions:
        test_name = test_func.__name__
        logger.info(f"Running {test_name}...")
        try:
            results["total"] += 1
            test_func()
            results["passed"] += 1
            logger.info(f"✅ {test_name} PASSED")
        except Exception as e:
            results["failed"] += 1
            error_info = {
                "test": test_name,
                "error": str(e),
                "type": type(e).__name__
            }
            results["errors"].append(error_info)
            logger.error(f"❌ {test_name} FAILED: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    return results


def test_feedback_processor():
    """Test the feedback processor functionality."""
    from src.agents.self_improving.feedback_processor import get_feedback_processor
    
    # Get singleton and clear previous data
    fp = get_feedback_processor()
    fp.feedback_entries.clear()
    
    # Test adding feedback
    entry1 = fp.add_feedback(
        user_id="test_user_1",
        agent_id="agent_1",
        feedback_text="This agent performed well",
        rating=4,
        implicit=False
    )
    
    entry2 = fp.add_feedback(
        user_id="test_user_2",
        agent_id="agent_1",
        feedback_text="I didn't like the response",
        rating=2,
        implicit=False
    )
    
    entry3 = fp.add_feedback(
        user_id="test_user_3",
        agent_id="agent_2",
        feedback_text="Poor engagement",
        implicit=True
    )
    
    # Test retrieval
    all_feedback = fp.get_all_feedback()
    assert len(all_feedback) == 3, f"Expected 3 feedback entries, got {len(all_feedback)}"
    
    # Test summarization
    summary = fp.summarize_feedback()
    assert summary["total"] == 3, f"Expected 3 total feedback, got {summary['total']}"
    assert summary["explicit"] == 2, f"Expected 2 explicit feedback, got {summary['explicit']}"
    assert summary["implicit"] == 1, f"Expected 1 implicit feedback, got {summary['implicit']}"
    
    # Verify average rating calculation
    assert summary["average_rating"] == 3.0, f"Expected average rating of 3.0, got {summary['average_rating']}"


def test_performance_monitor():
    """Test the performance monitor functionality."""
    from src.agents.self_improving.performance_monitor import get_performance_monitor
    
    # Get singleton and register metrics
    pm = get_performance_monitor()
    
    # Register new metrics
    pm.register_metric(
        name="response_time",
        description="Time to generate a response",
        unit="ms"
    )
    
    pm.register_metric(
        name="accuracy",
        description="Accuracy of agent responses",
        unit="%"
    )
    
    # Record values
    # Response times: 100ms, 150ms, 200ms
    pm.record_metric("response_time", 100)
    pm.record_metric("response_time", 150)
    pm.record_metric("response_time", 200)
    
    # Accuracy: 85%, 90%, 95%
    pm.record_metric("accuracy", 85)
    pm.record_metric("accuracy", 90)
    pm.record_metric("accuracy", 95)
    
    # Verify statistics
    response_stats = pm.get_metric_stats("response_time")
    assert response_stats is not None, "Expected response_time stats, got None"
    assert response_stats.get("last_value") is not None, "Missing last_value in response_time stats"
    assert response_stats.get("total_count") == 3, f"Expected 3 response_time data points, got {response_stats.get('total_count')}"
    
    # Check the most recent value is 200
    assert response_stats.get("last_value") == 200, f"Expected last_value of 200, got {response_stats.get('last_value')}"
    
    accuracy_stats = pm.get_metric_stats("accuracy") 
    assert accuracy_stats is not None, "Expected accuracy stats, got None"
    assert accuracy_stats.get("total_count") == 3, f"Expected 3 accuracy data points, got {accuracy_stats.get('total_count')}"
    assert accuracy_stats.get("last_value") == 95, f"Expected last accuracy value of 95, got {accuracy_stats.get('last_value')}"


def test_reinforcement_learner():
    """Test the reinforcement learner functionality."""
    from src.agents.self_improving.reinforcement_learner import get_reinforcement_learner
    from src.agents.self_improving.feedback_processor import get_feedback_processor
    
    # Reset and prepare
    fp = get_feedback_processor()
    fp.feedback_entries.clear()
    
    # Add some feedback
    fp.add_feedback(
        user_id="user1",
        agent_id="agent1",
        feedback_text="good response",
        rating=5,
        implicit=False
    )
    
    fp.add_feedback(
        user_id="user2",
        agent_id="agent1",
        feedback_text="poor response",
        rating=1,
        implicit=False
    )
    
    fp.add_feedback(
        user_id="user3",
        agent_id="agent2",
        feedback_text="did not engage",
        implicit=True
    )
    
    # Get the learner and run learning
    learner = get_reinforcement_learner()
    learner.learn(episodes=3)
    
    # Check Q-table entries
    policy = learner.get_policy()
    assert len(policy) == 3, f"Expected 3 Q-table entries, got {len(policy)}"
    
    # Check explicit feedback with positive rating
    assert "agent1:good response" in policy, "Missing positive feedback entry in Q-table"
    assert policy["agent1:good response"] > 0, "Positive feedback should have positive Q-value"
    
    # Check explicit feedback with negative rating
    assert "agent1:poor response" in policy, "Missing negative feedback entry in Q-table"
    assert policy["agent1:poor response"] < 5, "Negative feedback should have lower Q-value"
    
    # Check implicit feedback (should be negative)
    assert "agent2:did not engage" in policy, "Missing implicit feedback entry in Q-table"
    assert policy["agent2:did not engage"] < 0, "Implicit feedback should have negative Q-value"


def test_parameter_optimizer():
    """Test the parameter optimizer functionality."""
    from src.agents.self_improving.parameter_optimizer import get_parameter_optimizer
    
    # Get optimizer
    optimizer = get_parameter_optimizer()
    
    # Register parameters
    optimizer.register_parameter("learning_rate", 0.1)
    optimizer.register_parameter("batch_size", 32)
    optimizer.register_parameter("epochs", 10)
    
    # Check initial parameters
    params = optimizer.get_parameters()
    assert "learning_rate" in params, "Missing learning_rate parameter"
    assert params["learning_rate"] == 0.1, f"Expected learning_rate=0.1, got {params['learning_rate']}"
    assert "batch_size" in params, "Missing batch_size parameter"
    assert params["batch_size"] == 32, f"Expected batch_size=32, got {params['batch_size']}"
    
    # Update parameters
    optimizer.update_parameter("learning_rate", 0.05)
    optimizer.update_parameter("batch_size", 64)
    
    # Check updated parameters
    params = optimizer.get_parameters()
    assert params["learning_rate"] == 0.05, f"Expected learning_rate=0.05, got {params['learning_rate']}"
    assert params["batch_size"] == 64, f"Expected batch_size=64, got {params['batch_size']}"
    
    # Record performance with different configurations
    config1 = optimizer.get_parameters()
    optimizer.record_performance(0.75, config1)
    
    # Update one parameter and record better performance
    optimizer.update_parameter("batch_size", 128)
    config2 = optimizer.get_parameters()
    optimizer.record_performance(0.85, config2)
    
    # Get best configuration (should be config2)
    best_config = optimizer.get_best_configuration()
    assert best_config is not None, "Expected best_config to be non-None"
    assert best_config["batch_size"] == 128, f"Expected best batch_size=128, got {best_config.get('batch_size')}"
    
    # Record worse performance (should not update best config)
    optimizer.update_parameter("epochs", 5)
    config3 = optimizer.get_parameters()
    optimizer.record_performance(0.80, config3)
    
    best_config = optimizer.get_best_configuration()
    assert best_config["batch_size"] == 128, "Best config should not have changed"
    assert best_config["epochs"] == 10, "Best config should not have updated epochs"


def test_experience_replay():
    """Test the experience replay functionality."""
    from src.agents.self_improving.experience_replay import get_experience_replay
    
    # Get replay buffer with small capacity
    replay = get_experience_replay()
    replay.buffer.clear()
    
    # Test with custom capacity
    small_replay = get_experience_replay()
    small_replay.buffer.clear()
    small_replay.buffer = type(small_replay.buffer)(maxlen=3)
    
    # Add experiences
    experiences = [
        {"id": 1, "data": "exp1"},
        {"id": 2, "data": "exp2"},
        {"id": 3, "data": "exp3"},
        {"id": 4, "data": "exp4"},
        {"id": 5, "data": "exp5"}
    ]
    
    for exp in experiences:
        small_replay.add_experience(exp)
    
    # Test sampling with limited capacity (should only have last 3)
    samples = small_replay.sample(10)
    assert len(samples) == 3, f"Expected 3 experiences (capacity limit), got {len(samples)}"
    
    # Verify most recent experiences are kept
    exp_ids = [exp["id"] for exp in samples]
    assert 3 in exp_ids, "Experience with id=3 should be in buffer"
    assert 4 in exp_ids, "Experience with id=4 should be in buffer"
    assert 5 in exp_ids, "Experience with id=5 should be in buffer"
    assert 1 not in exp_ids, "Experience with id=1 should have been dropped"
    assert 2 not in exp_ids, "Experience with id=2 should have been dropped"
    
    # Test batch size limiting
    small_samples = small_replay.sample(2)
    assert len(small_samples) == 2, f"Expected 2 samples (batch size limit), got {len(small_samples)}"
    
    # Test clear
    small_replay.clear()
    empty_samples = small_replay.sample(10)
    assert len(empty_samples) == 0, f"Expected 0 samples after clear, got {len(empty_samples)}"


def test_learning_orchestrator():
    """Test the learning orchestrator functionality."""
    from src.agents.self_improving.learning_orchestrator import get_learning_orchestrator
    from src.agents.self_improving.feedback_processor import get_feedback_processor
    from src.agents.self_improving.performance_monitor import get_performance_monitor
    
    # Prepare test data
    fp = get_feedback_processor()
    fp.feedback_entries.clear()
    
    pm = get_performance_monitor()
    pm.register_metric("response_time", "Response time in ms", "ms")
    pm.record_metric("response_time", 120)
    
    # Add feedback data
    fp.add_feedback(
        user_id="user1",
        agent_id="agent1",
        feedback_text="good job",
        rating=5,
        implicit=False
    )
    
    fp.add_feedback(
        user_id="user2",
        agent_id="agent1",
        feedback_text="bad response",
        rating=1,
        implicit=False
    )
    
    # Get orchestrator and run a learning cycle
    orchestrator = get_learning_orchestrator()
    result = orchestrator.run_cycle(episodes=2, metric_name="response_time")
    
    # Verify result structure
    assert "q_table" in result, "Expected q_table in result"
    assert "best_config" in result, "Expected best_config in result"
    
    # Verify Q-table entries
    q_table = result["q_table"]
    assert len(q_table) > 0, f"Expected non-empty Q-table entries, got empty table"
    
    # Verify important Q-table entries exist
    assert "agent1:good job" in q_table, "Missing positive feedback entry in Q-table"
    assert "agent1:bad response" in q_table, "Missing negative feedback entry in Q-table"


def test_integration():
    """Test the integration of all components."""
    import src.agents.self_improving.reinforcement_learner as rl_module
    import src.agents.self_improving.parameter_optimizer as po_module
    import src.agents.self_improving.experience_replay as er_module
    import src.agents.self_improving.learning_orchestrator as lo_module
    from src.agents.self_improving.learning_orchestrator import get_learning_orchestrator
    from src.agents.self_improving.feedback_processor import get_feedback_processor
    from src.agents.self_improving.performance_monitor import get_performance_monitor
    
    # Reset singletons
    rl_module._learner = None
    po_module._optimizer = None
    er_module._replay = None
    lo_module._orchestrator = None
    
    # Prepare test data
    fp = get_feedback_processor()
    fp.feedback_entries.clear()
    
    pm = get_performance_monitor()
    # Register metrics
    pm.register_metric("response_time", "Response time in ms", "ms")
    pm.register_metric("accuracy", "Response accuracy", "%")
    pm.register_metric("engagement", "User engagement", "score")
    
    # Record metrics
    pm.record_metric("response_time", 150)
    pm.record_metric("accuracy", 92)
    pm.record_metric("engagement", 4.5)
    
    # Add varied feedback
    for i in range(10):
        rating = 5 if i % 3 == 0 else (3 if i % 3 == 1 else 1)
        implicit = i % 4 == 0
        
        fp.add_feedback(
            user_id=f"user{i}",
            agent_id=f"agent{i % 3}",
            feedback_text=f"feedback {i}",
            rating=rating if not implicit else None,
            implicit=implicit
        )
    
    # Get parameter optimizer and register parameters
    optimizer = po_module.get_parameter_optimizer()
    optimizer.register_parameter("learning_rate", 0.1)
    optimizer.register_parameter("temperature", 0.7)
    optimizer.register_parameter("max_tokens", 1024)
    
    # Run learning cycle
    orchestrator = get_learning_orchestrator()
    result = orchestrator.run_cycle(episodes=3, metric_name="accuracy")
    
    # Check components after cycle
    assert result["q_table"], "Q-table should not be empty after learning cycle"
    
    # Verify experience replay has stored experiences
    replay = er_module.get_experience_replay()
    experiences = replay.sample(100)
    assert len(experiences) > 0, "Experience replay should have stored feedback"
    
    # Verify learning had an effect on Q-values
    learner = rl_module.get_reinforcement_learner()
    policy = learner.get_policy()
    assert len(policy) > 0, "Policy should not be empty after learning"
    
    # Verify parameter optimization
    best_config = result["best_config"]
    assert best_config is not None, "Should have a best configuration"
    assert "learning_rate" in best_config, "Best config should include learning_rate"
    assert "temperature" in best_config, "Best config should include temperature"
    assert "max_tokens" in best_config, "Best config should include max_tokens"


if __name__ == "__main__":
    start_time = time.time()
    logger.info("Starting Self-Improving Agent Component Tests")
    
    results = run_tests()
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("=" * 70)
    logger.info(f"Test Results Summary:")
    logger.info(f"Total Tests: {results['total']}")
    logger.info(f"Passed: {results['passed']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Duration: {duration:.2f} seconds")
    
    if results['failed'] > 0:
        logger.error("The following tests failed:")
        for error in results['errors']:
            logger.error(f"  - {error['test']}: {error['type']}: {error['error']}")
        sys.exit(1)
    else:
        logger.info("✅ All tests passed!")
        sys.exit(0)
