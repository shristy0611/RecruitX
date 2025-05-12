import pytest
from src.agents.self_improving.experience_replay import ExperienceReplay, get_experience_replay
import src.agents.self_improving.experience_replay as er_module


@pytest.fixture(autouse=True)
def reset_experience_replay():
    """Reset the experience replay singleton before each test"""
    er_module._replay = None


def test_add_experience():
    """Test adding experiences to the buffer"""
    replay = ExperienceReplay(capacity=3)
    
    # Add experiences
    replay.add_experience({"id": 1, "value": "exp1"})
    replay.add_experience({"id": 2, "value": "exp2"})
    
    # Should contain both experiences
    experiences = replay.sample(10)
    assert len(experiences) == 2
    assert experiences[0]["id"] == 1
    assert experiences[1]["id"] == 2


def test_capacity_limit():
    """Test that buffer respects capacity limit"""
    replay = ExperienceReplay(capacity=2)
    
    # Add experiences beyond capacity
    replay.add_experience("e1")
    replay.add_experience("e2")
    replay.add_experience("e3")
    
    # Should only contain the most recent experiences
    experiences = replay.sample(10)
    assert len(experiences) == 2
    assert "e1" not in experiences
    assert "e2" in experiences
    assert "e3" in experiences


def test_sample_batch_size():
    """Test sampling respects batch size"""
    replay = ExperienceReplay(capacity=10)
    
    # Add 5 experiences
    for i in range(5):
        replay.add_experience(f"exp{i}")
    
    # Sample with different batch sizes
    batch1 = replay.sample(2)
    assert len(batch1) == 2
    
    batch2 = replay.sample(10)
    assert len(batch2) == 5  # Only 5 experiences exist


def test_clear_buffer():
    """Test clearing the buffer"""
    replay = ExperienceReplay()
    
    # Add experiences
    replay.add_experience("test1")
    replay.add_experience("test2")
    
    # Clear buffer
    replay.clear()
    
    # Buffer should be empty
    assert len(replay.sample(10)) == 0


def test_get_experience_replay_singleton():
    """Test that get_experience_replay returns a singleton"""
    replay1 = get_experience_replay()
    replay2 = get_experience_replay()
    
    # Should be the same instance
    assert replay1 is replay2
    
    # Operations on one affect the other
    replay1.add_experience("shared_experience")
    samples = replay2.sample(10)
    assert "shared_experience" in samples
