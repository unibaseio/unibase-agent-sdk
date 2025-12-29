"""Type definitions for the framework."""
from typing import TypedDict, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class AgentType(Enum):
    """Agent type enumeration."""
    AIP = "aip"
    CLAUDE = "claude"
    LANGCHAIN = "langchain"
    OPENAI = "openai"
    CUSTOM = "custom"


@dataclass
class AgentIdentity:
    """Agent identity information."""
    agent_id: str
    name: str
    agent_type: AgentType
    public_key: Optional[str] = None
    wallet_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "public_key": self.public_key,
            "wallet_address": self.wallet_address,
            "metadata": self.metadata
        }


@dataclass
class MemoryRecord:
    """Memory record."""
    session_id: str
    agent_id: str
    content: Dict[str, Any]
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class DAUploadResult:
    """DA upload result."""
    transaction_hash: str
    da_url: str
    size: int
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transaction_hash": self.transaction_hash,
            "da_url": self.da_url,
            "size": self.size,
            "timestamp": self.timestamp
        }


# Config types
class LLMProviderConfig(TypedDict, total=False):
    """LLM provider configuration for adapters (Claude, OpenAI, LangChain).

    Note: For agent registration config, use aip_sdk.types.AgentConfig instead.
    """
    api_key: str
    base_url: str
    model: str
    timeout: float
    extra_params: Dict[str, Any]



class MemoryConfig(TypedDict, total=False):
    """Memory configuration."""
    membase_endpoint: str
    da_endpoint: str
    api_key: str
    encryption: bool
    retention_policy: str


class RegistryConfig(TypedDict, total=False):
    """Registry configuration."""
    aip_endpoint: str
    membase_endpoint: str
    web3_rpc_url: str
