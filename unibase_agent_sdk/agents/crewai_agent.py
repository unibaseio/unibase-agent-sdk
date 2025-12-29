"""
CrewAI Agent Wrapper

Wraps CrewAI's Agent class to add Unibase integration.

Usage:
    from unibase_agent_sdk.agents import create_crewai_agent
    
    # Use the factory function - it returns a real crewai.Agent!
    researcher = create_crewai_agent(
        role="Researcher",
        goal="Research AI topics",
        backstory="Expert researcher",
        registry=registry  # Auto-register with Unibase
    )
    
    # researcher is a real crewai.Agent - use it normally!
    crew = Crew(agents=[researcher], tasks=[...])
    result = crew.kickoff()
"""
from typing import Any, Optional, List, TYPE_CHECKING
import hashlib
import time

if TYPE_CHECKING:
    from ..registry.registry import AgentRegistryClient
    from ..memory.manager import MemoryManager

# Try to import CrewAI
try:
    from crewai import Agent as NativeCrewAIAgent
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    NativeCrewAIAgent = None


def create_crewai_agent(
    role: str,
    goal: str,
    backstory: str = None,
    registry: 'AgentRegistryClient' = None,
    memory_manager: 'MemoryManager' = None,
    **kwargs
) -> 'NativeCrewAIAgent':
    """
    Create a CrewAI Agent with Unibase integration.
    
    Returns a real crewai.Agent with additional Unibase attributes!
    
    Args:
        role: Agent's role
        goal: Agent's goal
        backstory: Agent's backstory
        registry: Unibase AgentRegistry for auto-registration
        memory_manager: Unibase MemoryManager
        **kwargs: Additional arguments for crewai.Agent
    
    Returns:
        crewai.Agent with Unibase integration
    """
    if not HAS_CREWAI:
        raise ImportError("Please install crewai: pip install crewai")
    
    # Create native CrewAI Agent
    agent = NativeCrewAIAgent(
        role=role,
        goal=goal,
        backstory=backstory or f"An expert {role}",
        **kwargs
    )
    
    # Add Unibase attributes
    agent._unibase_registry = registry
    agent._unibase_memory = memory_manager
    agent._unibase_identity = None
    
    # Register with Unibase if registry provided
    if registry:
        _register_agent_with_unibase(agent, registry)
    
    # Note: Can't add properties to Pydantic models
    # Access via agent._unibase_identity directly
    
    return agent


def _register_agent_with_unibase(agent, registry: 'AgentRegistryClient'):
    """Register a CrewAI agent with Unibase"""
    try:
        agent_id = f"crewai_{hashlib.sha256(f'{agent.role}_{time.time()}'.encode()).hexdigest()[:16]}"
        
        from ..core.types import AgentIdentity, AgentType
        
        identity = AgentIdentity(
            agent_id=agent_id,
            name=agent.role,
            agent_type=AgentType.LANGCHAIN,
            public_key=f"crewai_{agent_id}",
            metadata={
                "framework": "crewai",
                "role": agent.role,
                "goal": agent.goal,
            }
        )
        
        agent._unibase_identity = identity
        registry._identities[agent_id] = identity
        registry._agents[agent_id] = agent
        
        print(f"✅ CrewAI Agent registered: {agent.role} ({agent_id})")
        
    except Exception as e:
        print(f"⚠️ Failed to register CrewAI agent: {e}")


# Alias for convenience - class-like name
CrewAIAgent = create_crewai_agent
