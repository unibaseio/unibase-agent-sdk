# Unibase Agent Framework
"""
Unibase Agent Framework - A transparent SDK for building AI agents
with integrated memory management and multi-SDK support.

Structure:
- adapters/: Transparent LLM providers (Claude, OpenAI, LangChain)
- agents/: Wrapped Agent classes from frameworks (CrewAI, AutoGen, Phidata, LlamaIndex)
- registry/: Agent registration, identity, auth, and wallet management
- memory/middlewares/: Transparent memory backends (mem0, ChromaDB, Redis, etc.)
"""

__version__ = "0.1.0"
__author__ = "Unibase Team"

# Core types
from unibase_agent_sdk.core.types import (
    AgentType,
    AgentIdentity,
    MemoryRecord,
    DAUploadResult,
)

# Canonical A2A Protocol types (use these for tasks, skills, messages)
from unibase_agent_sdk.a2a.types import (
    Task,
    TaskState,
    TaskStatus,
    Message,
    Skill,
    AgentCard,
    Artifact,
)

# Base classes
from unibase_agent_sdk.core.base_agent import TransparentAgentProxy
from unibase_agent_sdk.core.base_memory import BaseMemory

# Agent management
from unibase_agent_sdk.registry.registry import AgentRegistry

# Memory management
from unibase_agent_sdk.memory.manager import MemoryManager
from unibase_agent_sdk.memory.membase_client import MembaseClient
from unibase_agent_sdk.memory.da_uploader import DAUploader

# LLM Provider Adapters (transparent access to native SDKs)
from unibase_agent_sdk.adapters.claude_adapter import ClaudeAdapter
from unibase_agent_sdk.adapters.langchain_adapter import LangChainAdapter
from unibase_agent_sdk.adapters.openai_adapter import OpenAIAdapter

# Agent Framework Wrappers (wrapped Agent classes from each framework)
# Import from unibase_agent_sdk.agents instead
# from unibase_agent_sdk.agents import CrewAIAgent, AutoGenAssistant, PhiAgent, LlamaAgent

__all__ = [
    # Version
    "__version__",
    # Core Types
    "AgentType",
    "AgentIdentity",
    "MemoryRecord",
    "DAUploadResult",
    # A2A Protocol Types (canonical for tasks, skills, messages)
    "Task",
    "TaskState",
    "TaskStatus",
    "Message",
    "Skill",
    "AgentCard",
    "Artifact",
    # Base classes
    "TransparentAgentProxy",
    "BaseMemory",
    # Agent management
    "AgentRegistry",
    # Memory management
    "MemoryManager",
    "MembaseClient",
    "DAUploader",
    # LLM Provider Adapters
    "ClaudeAdapter",
    "LangChainAdapter",
    "OpenAIAdapter",
]
