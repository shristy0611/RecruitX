"""RecruitX agents package."""

from typing import Dict, Any, List, Optional

class AgentManager:
    """Manages test agents."""
    
    def __init__(self):
        """Initialize agent manager."""
        self.agents: Dict[str, Any] = {}
        
    def register_agent(self, name: str, agent: Any):
        """Register agent.
        
        Args:
            name: Agent name
            agent: Agent instance
        """
        self.agents[name] = agent
        
    def get_agent(self, name: str) -> Optional[Any]:
        """Get agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent if found, None otherwise
        """
        return self.agents.get(name)
        
    def list_agents(self) -> List[str]:
        """List registered agents.
        
        Returns:
            List of agent names
        """
        return list(self.agents.keys()) 