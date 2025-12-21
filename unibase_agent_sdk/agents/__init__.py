"""
Unibase Agent Wrappers

Wraps popular agent framework Agent classes to add Unibase integration.
Each wrapper returns a real native agent with Unibase features!

Example:
    # Instead of:
    from crewai import Agent
    agent = Agent(role="Researcher", goal="...")
    
    # Use (returns a real crewai.Agent!):
    from unibase_agent_sdk.agents import create_crewai_agent
    agent = create_crewai_agent(role="Researcher", goal="...", registry=registry)
    # Now agent is registered with Unibase AND is a real crewai.Agent!
"""

# CrewAI
from .crewai_agent import create_crewai_agent, CrewAIAgent

# AutoGen
from .autogen_agent import AutoGenAssistant, AutoGenUserProxy

# Phidata
from .phidata_agent import create_phi_agent, PhiAgent

# LlamaIndex
from .llamaindex_agent import LlamaAgent

__all__ = [
    # CrewAI
    "create_crewai_agent",
    "CrewAIAgent",  # Alias for create_crewai_agent
    
    # AutoGen
    "AutoGenAssistant",
    "AutoGenUserProxy",
    
    # Phidata
    "create_phi_agent",
    "PhiAgent",  # Alias for create_phi_agent
    
    # LlamaIndex
    "LlamaAgent",
]
