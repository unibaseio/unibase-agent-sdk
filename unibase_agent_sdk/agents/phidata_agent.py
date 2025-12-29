"""
Phidata Agent Wrapper

Wraps Phidata's Agent class to add Unibase integration.

Usage:
    from unibase_agent_sdk.agents import create_phi_agent
    
    # Use the factory function - returns a real phi.agent.Agent!
    agent = create_phi_agent(
        name="Web Researcher",
        tools=[DuckDuckGo()],
        registry=registry  # Auto-register with Unibase
    )
    
    # Use normally!
    response = agent.run("What's happening in AI?")
"""
from typing import Any, Optional, List, TYPE_CHECKING
import hashlib
import time

if TYPE_CHECKING:
    from ..registry.registry import AgentRegistryClient
    from ..memory.manager import MemoryManager

# Try to import Phidata
try:
    from phi.agent import Agent as NativePhiAgent
    HAS_PHIDATA = True
except ImportError:
    HAS_PHIDATA = False
    NativePhiAgent = None


def create_phi_agent(
    name: str = None,
    registry: 'AgentRegistryClient' = None,
    memory_manager: 'MemoryManager' = None,
    **kwargs
) -> 'NativePhiAgent':
    """
    Create a Phidata Agent with Unibase integration.
    
    Returns a real phi.agent.Agent with additional Unibase attributes!
    
    Args:
        name: Agent name
        registry: Unibase AgentRegistry for auto-registration
        memory_manager: Unibase MemoryManager
        **kwargs: Additional arguments for phi.agent.Agent
    
    Returns:
        phi.agent.Agent with Unibase integration
    """
    if not HAS_PHIDATA:
        raise ImportError("Please install phidata: pip install phidata")
    
    # Create native Phidata Agent
    agent = NativePhiAgent(name=name, **kwargs)
    
    # Add Unibase attributes
    agent._unibase_registry = registry
    agent._unibase_memory = memory_manager
    agent._unibase_identity = None
    
    # Register with Unibase if registry provided
    if registry:
        _register_agent_with_unibase(agent, registry)
    
    return agent


def _register_agent_with_unibase(agent, registry: 'AgentRegistryClient'):
    """Register a Phidata agent with Unibase"""
    try:
        agent_name = agent.name or "phi_agent"
        agent_id = f"phi_{hashlib.sha256(f'{agent_name}_{time.time()}'.encode()).hexdigest()[:16]}"
        
        from ..core.types import AgentIdentity, AgentType
        
        identity = AgentIdentity(
            agent_id=agent_id,
            name=agent_name,
            agent_type=AgentType.OPENAI,
            public_key=f"phi_{agent_id}",
            metadata={
                "framework": "phidata"
            }
        )
        
        agent._unibase_identity = identity
        registry._identities[agent_id] = identity
        registry._agents[agent_id] = agent
        
        print(f"✅ Phidata Agent registered: {agent_name} ({agent_id})")
        
    except Exception as e:
        print(f"⚠️ Failed to register Phidata agent: {e}")


# Alias for class-like usage
PhiAgent = create_phi_agent
