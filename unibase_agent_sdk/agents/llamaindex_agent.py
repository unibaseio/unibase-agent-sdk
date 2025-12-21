"""
LlamaIndex Agent Wrapper

Wraps LlamaIndex's agent classes to add Unibase integration.

Usage:
    from unibase_agent_sdk.agents import LlamaAgent
    
    # Use exactly like llama_index agent
    agent = LlamaAgent.from_tools(
        tools=[...],
        llm=llm,
        registry=registry  # Auto-register with Unibase
    )
    
    # Use normally!
    response = agent.chat("What's the answer?")
"""
from typing import Any, Optional, List, TYPE_CHECKING
import hashlib
import time

if TYPE_CHECKING:
    from ..agent.registry import AgentRegistry
    from ..memory.manager import MemoryManager

# Try to import LlamaIndex
try:
    from llama_index.core.agent import ReActAgent
    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False
    ReActAgent = object


class LlamaAgent(ReActAgent if HAS_LLAMAINDEX else object):
    """
    LlamaIndex ReActAgent with Unibase integration.
    
    Use exactly like llama_index.core.agent.ReActAgent!
    """
    
    _unibase_registry: 'AgentRegistry' = None
    _unibase_memory: 'MemoryManager' = None
    _unibase_identity = None
    
    @classmethod
    def from_tools(
        cls,
        tools: List = None,
        registry: 'AgentRegistry' = None,
        memory_manager: 'MemoryManager' = None,
        **kwargs
    ):
        """Create agent from tools with Unibase integration"""
        if not HAS_LLAMAINDEX:
            raise ImportError(
                "Please install llama-index: pip install llama-index"
            )
        
        # Create native agent
        agent = super().from_tools(tools=tools or [], **kwargs)
        
        # Add Unibase integration
        agent._unibase_registry = registry
        agent._unibase_memory = memory_manager
        
        if registry:
            agent._register_with_unibase()
        
        return agent
    
    def _register_with_unibase(self):
        """Register this agent with Unibase"""
        if not self._unibase_registry:
            return
        
        try:
            agent_id = f"llama_{hashlib.sha256(f'llamaagent_{time.time()}'.encode()).hexdigest()[:16]}"
            
            from ..core.types import AgentIdentity, AgentType
            
            self._unibase_identity = AgentIdentity(
                agent_id=agent_id,
                name="LlamaIndex Agent",
                agent_type=AgentType.LANGCHAIN,
                public_key=f"llama_{agent_id}",
                metadata={
                    "framework": "llamaindex"
                }
            )
            
            self._unibase_registry._identities[agent_id] = self._unibase_identity
            self._unibase_registry._agents[agent_id] = self
            
            print(f"✅ LlamaIndex Agent registered: ({agent_id})")
            
        except Exception as e:
            print(f"⚠️ Failed to register LlamaIndex agent: {e}")
    
    @property
    def unibase_identity(self):
        return self._unibase_identity
    
    @property
    def unibase_agent_id(self) -> Optional[str]:
        return self._unibase_identity.agent_id if self._unibase_identity else None
