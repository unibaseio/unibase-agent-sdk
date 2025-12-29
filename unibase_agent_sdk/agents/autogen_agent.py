"""
AutoGen Agent Wrappers

Wraps AutoGen's agent classes to add Unibase integration:
- AssistantAgent
- UserProxyAgent
- GroupChatManager

Usage:
    from unibase_agent_sdk.agents import AutoGenAssistant, AutoGenUserProxy
    
    # Use exactly like autogen.AssistantAgent
    assistant = AutoGenAssistant(
        name="coder",
        system_message="You are an expert coder.",
        registry=registry  # Auto-register with Unibase
    )
    
    user = AutoGenUserProxy(
        name="user",
        registry=registry
    )
    
    # Use normally!
    user.initiate_chat(assistant, message="Write a function")
"""
from typing import Any, Optional, Dict, List, TYPE_CHECKING
import hashlib
import time

if TYPE_CHECKING:
    from ..registry.registry import AgentRegistryClient
    from ..memory.manager import MemoryManager

# Try to import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent, GroupChatManager
    HAS_AUTOGEN = True
except ImportError:
    HAS_AUTOGEN = False
    AssistantAgent = object
    UserProxyAgent = object
    GroupChatManager = object


class UnibaseAgentMixin:
    """Mixin to add Unibase features to AutoGen agents"""
    
    _unibase_registry: 'AgentRegistryClient' = None
    _unibase_memory: 'MemoryManager' = None
    _unibase_identity = None
    
    def _register_with_unibase(self, agent_type: str):
        """Register this agent with Unibase"""
        if not self._unibase_registry:
            return
        
        try:
            agent_id = f"autogen_{hashlib.sha256(f'{self.name}_{time.time()}'.encode()).hexdigest()[:16]}"
            
            from ..core.types import AgentIdentity, AgentType
            
            self._unibase_identity = AgentIdentity(
                agent_id=agent_id,
                name=self.name,
                agent_type=AgentType.OPENAI,
                public_key=f"autogen_{agent_id}",
                metadata={
                    "framework": "autogen",
                    "agent_type": agent_type
                }
            )
            
            self._unibase_registry._identities[agent_id] = self._unibase_identity
            self._unibase_registry._agents[agent_id] = self
            
            print(f"✅ AutoGen Agent registered: {self.name} ({agent_id})")
            
        except Exception as e:
            print(f"⚠️ Failed to register AutoGen agent: {e}")
    
    @property
    def unibase_identity(self):
        return self._unibase_identity
    
    @property
    def unibase_agent_id(self) -> Optional[str]:
        return self._unibase_identity.agent_id if self._unibase_identity else None


class AutoGenAssistant(UnibaseAgentMixin, AssistantAgent if HAS_AUTOGEN else object):
    """
    AutoGen AssistantAgent with Unibase integration.
    
    Use exactly like autogen.AssistantAgent!
    """
    
    def __init__(
        self,
        name: str,
        system_message: str = None,
        registry: 'AgentRegistryClient' = None,
        memory_manager: 'MemoryManager' = None,
        **kwargs
    ):
        if not HAS_AUTOGEN:
            raise ImportError("Please install autogen: pip install pyautogen")
        
        self._unibase_registry = registry
        self._unibase_memory = memory_manager
        
        super().__init__(
            name=name,
            system_message=system_message or "You are a helpful AI assistant.",
            **kwargs
        )
        
        if registry:
            self._register_with_unibase("assistant")


class AutoGenUserProxy(UnibaseAgentMixin, UserProxyAgent if HAS_AUTOGEN else object):
    """
    AutoGen UserProxyAgent with Unibase integration.
    
    Use exactly like autogen.UserProxyAgent!
    """
    
    def __init__(
        self,
        name: str,
        registry: 'AgentRegistryClient' = None,
        memory_manager: 'MemoryManager' = None,
        **kwargs
    ):
        if not HAS_AUTOGEN:
            raise ImportError("Please install autogen: pip install pyautogen")
        
        self._unibase_registry = registry
        self._unibase_memory = memory_manager
        
        # Set sensible defaults
        kwargs.setdefault("human_input_mode", "NEVER")
        kwargs.setdefault("max_consecutive_auto_reply", 10)
        
        super().__init__(name=name, **kwargs)
        
        if registry:
            self._register_with_unibase("user_proxy")
