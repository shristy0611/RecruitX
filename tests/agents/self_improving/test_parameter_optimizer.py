import pytest
from src.agents.self_improving.parameter_optimizer import ParameterOptimizer, get_parameter_optimizer
import src.agents.self_improving.parameter_optimizer as po_module

@pytest.fixture(autouse=True)
def reset_optimizer():
    """Reset the parameter optimizer singleton before each test"""
    po_module._optimizer = None


def test_register_update_parameters():
    """Test registering and updating parameters"""
    optimizer = ParameterOptimizer()
    
    # Register new parameter
    optimizer.register_parameter("learning_rate", 0.1)
    params = optimizer.get_parameters()
    assert "learning_rate" in params
    assert params["learning_rate"] == 0.1
    
    # Update existing parameter
    optimizer.update_parameter("learning_rate", 0.2)
    params = optimizer.get_parameters()
    assert params["learning_rate"] == 0.2
    
    # Update non-existent parameter (should be ignored)
    optimizer.update_parameter("nonexistent", 100)
    params = optimizer.get_parameters()
    assert "nonexistent" not in params


def test_record_performance_best_config():
    """Test recording performance updates best configuration"""
    optimizer = ParameterOptimizer()
    
    # Initial state
    assert optimizer.get_best_configuration() is None
    
    # Register parameters
    optimizer.register_parameter("batch_size", 32)
    optimizer.register_parameter("epochs", 10)
    
    # Record first performance
    config1 = optimizer.get_parameters()
    optimizer.record_performance(0.75, config1)
    best = optimizer.get_best_configuration()
    assert best == {"batch_size": 32, "epochs": 10}
    
    # Update parameters
    optimizer.update_parameter("batch_size", 64)
    config2 = optimizer.get_parameters()
    
    # Record worse performance (should not update best)
    optimizer.record_performance(0.70, config2)
    best = optimizer.get_best_configuration()
    assert best == {"batch_size": 32, "epochs": 10}
    
    # Record better performance (should update best)
    optimizer.record_performance(0.80, config2)
    best = optimizer.get_best_configuration()
    assert best == {"batch_size": 64, "epochs": 10}


def test_get_parameter_optimizer_singleton():
    """Test that get_parameter_optimizer returns a singleton"""
    optimizer1 = get_parameter_optimizer()
    optimizer2 = get_parameter_optimizer()
    
    # Should be the same instance
    assert optimizer1 is optimizer2
    
    # Modify through one instance, see in the other
    optimizer1.register_parameter("test_param", "value")
    params = optimizer2.get_parameters()
    assert "test_param" in params
    assert params["test_param"] == "value"
