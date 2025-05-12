import pytest
from src.agents.self_improving.learning_orchestrator import LearningOrchestrator, get_learning_orchestrator
from src.agents.self_improving.feedback_processor import get_feedback_processor
from src.agents.self_improving.performance_monitor import get_performance_monitor
import src.agents.self_improving.learning_orchestrator as lo_module
import src.agents.self_improving.reinforcement_learner as rl_module
import src.agents.self_improving.parameter_optimizer as po_module
import src.agents.self_improving.experience_replay as er_module


@pytest.fixture(autouse=True)
def reset_components():
    """Reset all components and singletons before each test"""
    get_feedback_processor().feedback_entries.clear()
    get_performance_monitor().metrics.clear()
    lo_module._orchestrator = None
    rl_module._learner = None
    po_module._optimizer = None
    er_module._replay = None


def test_learning_orchestrator_initialization():
    """Test that the orchestrator properly initializes with all components"""
    orchestrator = LearningOrchestrator()
    
    # Should have initialized all required components
    assert orchestrator.processor is not None
    assert orchestrator.monitor is not None
    assert orchestrator.learner is not None
    assert orchestrator.optimizer is not None
    assert orchestrator.replay is not None


def test_orchestrator_run_cycle_with_feedback():
    """Test that run_cycle processes feedback and returns expected structure"""
    fp = get_feedback_processor()
    
    # Add some test feedback
    fp.add_feedback(user_id="test_user", agent_id="test_agent", 
                    feedback_text="positive feedback", rating=5)
    fp.add_feedback(user_id="test_user", agent_id="test_agent", 
                    feedback_text="negative implicit", implicit=True)
    
    # Run a learning cycle
    orchestrator = get_learning_orchestrator()
    result = orchestrator.run_cycle(episodes=2)
    
    # Verify result structure
    assert isinstance(result, dict)
    assert "q_table" in result
    assert "best_config" in result
    
    # Check if feedback was processed into q_table
    q_table = result["q_table"]
    assert len(q_table) >= 2  # Should have entries for both feedback items


def test_orchestrator_with_performance_metrics():
    """Test that orchestrator uses performance metrics for parameter optimization"""
    monitor = get_performance_monitor()
    optimizer = po_module.get_parameter_optimizer()
    
    # Register a test parameter and record metrics
    optimizer.register_parameter("test_param", 10)
    monitor.record_metric("response_time", 100)
    
    # Run cycle with this metric
    orchestrator = get_learning_orchestrator()
    result = orchestrator.run_cycle(metric_name="response_time")
    
    # Should have recorded the performance
    assert result["best_config"] is not None
    
    # Record a better metric and run again
    monitor.record_metric("response_time", 50)  # Lower is better
    optimizer.update_parameter("test_param", 20)
    
    result2 = orchestrator.run_cycle(metric_name="response_time")
    assert result2["best_config"]["test_param"] == 20


def test_orchestrator_stores_experiences():
    """Test that orchestrator stores feedback in experience replay"""
    fp = get_feedback_processor()
    replay = er_module.get_experience_replay()
    
    # Add feedback and verify it's empty in replay initially
    feedback = fp.add_feedback(user_id="u", agent_id="a", feedback_text="test")
    assert len(replay.sample(10)) == 0
    
    # Run cycle and check if experiences were added
    orchestrator = get_learning_orchestrator()
    orchestrator.run_cycle()
    
    # Experience replay should now contain the feedback
    experiences = replay.sample(10)
    assert len(experiences) >= 1
    
    # Check if feedback was added to experiences
    found = False
    for exp in experiences:
        if exp.get('id') == feedback['id']:
            found = True
            break
    assert found is True


def test_get_learning_orchestrator_singleton():
    """Test that get_learning_orchestrator returns a singleton"""
    orch1 = get_learning_orchestrator()
    orch2 = get_learning_orchestrator()
    
    # Should be the same instance
    assert orch1 is orch2
