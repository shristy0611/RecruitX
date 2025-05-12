import pytest
from src.agents.self_improving.reinforcement_learner import ReinforcementLearner
from src.agents.self_improving.feedback_processor import get_feedback_processor

@pytest.fixture(autouse=True)
def clear_feedback():
    """Clear feedback before each test"""
    fp = get_feedback_processor()
    fp.feedback_entries.clear()


def test_learn_updates_q_table():
    """Test that learning updates Q-table with correct values"""
    fp = get_feedback_processor()
    entry = fp.add_feedback(
        user_id="u1", agent_id="a1", feedback_text="test feedback", rating=4, implicit=False
    )
    learner = ReinforcementLearner(learning_rate=0.5)
    
    # Before learning, Q-table should be empty
    assert learner.get_policy() == {}
    
    learner.learn(episodes=1)
    policy = learner.get_policy()
    key = f"{entry['agent_id']}:{entry['text']}"
    
    # Check Q-value calculation: Q(s,a) = Q(s,a) + α * (r - Q(s,a))
    # New Q = 0 + 0.5 * (4 - 0) = 2.0
    assert key in policy
    assert policy[key] == pytest.approx(2.0)


def test_multiple_episodes():
    """Test that multiple episodes update Q-values correctly"""
    fp = get_feedback_processor()
    entry = fp.add_feedback(
        user_id="u1", agent_id="a1", feedback_text="test feedback", rating=4, implicit=False
    )
    learner = ReinforcementLearner(learning_rate=0.5)
    
    # First episode: Q = 0 + 0.5 * (4 - 0) = 2.0
    # Second episode: Q = 2.0 + 0.5 * (4 - 2.0) = 3.0
    # Third episode: Q = 3.0 + 0.5 * (4 - 3.0) = 3.5
    learner.learn(episodes=3)
    
    policy = learner.get_policy()
    key = f"{entry['agent_id']}:{entry['text']}"
    assert policy[key] == pytest.approx(3.5)


def test_implicit_feedback_negative_reward():
    """Test that implicit feedback is treated as negative reward"""
    fp = get_feedback_processor()
    entry = fp.add_feedback(
        user_id="u2", agent_id="a2", feedback_text="implicit issue", implicit=True
    )
    learner = ReinforcementLearner(learning_rate=1.0)
    learner.learn(episodes=1)
    
    policy = learner.get_policy()
    key = f"{entry['agent_id']}:{entry['text']}"
    
    # Implicit feedback yields a reward of -1 with learning rate 1.0
    assert policy[key] == pytest.approx(-1.0)
