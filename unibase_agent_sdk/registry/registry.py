"""Agent Registry - thin wrapper around AIP SDK client for agent management."""
from typing import Dict, Optional, List, Any, Union, AsyncIterator
import uuid
import hashlib
import time
import os
from enum import Enum
from ..core.types import AgentIdentity, AgentType
from ..core.base_agent import TransparentAgentProxy
from ..core.exceptions import RegistryError, AgentNotFoundError, ConfigurationError
from ..utils.logger import get_logger
import httpx

# Import AIP SDK for agent registration and platform communication
from aip_sdk import AsyncAIPClient, AgentConfig as AIPAgentConfig, SkillConfig
from aip_sdk.exceptions import AIPError, RegistrationError as AIPRegistrationError
from aip_sdk.gateway_client import GatewayClient

logger = get_logger("registry.registry")


class RegistrationMode(Enum):
    """Agent registration mode."""
    DIRECT = "direct"  # Register directly with AIP platform
    GATEWAY = "gateway"  # Register through a gateway (for agents behind firewalls/NAT)

# A2A Protocol imports (canonical types for this framework)
from ..a2a.types import AgentCard, Task, Message, StreamResponse, Skill
from ..a2a.client import A2AClient
from ..a2a.agent_card import generate_agent_card

# Type adapters for AIP SDK <-> A2A conversion
from ..core.type_adapters import (
    aip_agent_config_skills_to_a2a,
    merge_agent_metadata,
    extract_a2a_capabilities_from_aip_config
)


class AgentRegistryClient:
    """
    Agent Registry Client - Wrapper around AIP SDK for agent management.

    This client provides additional functionality on top of the AIP SDK:
    - Identity management (keypairs, signing)
    - Web3 wallet integration
    - A2A protocol support for agent discovery and communication
    - Local agent instance tracking
    - Gateway mode support for agents behind firewalls

    Note: This is distinct from aip.core.agents.registry.AgentRegistry which
    is the platform's abstract interface. This class is a client implementation.
    """

    def __init__(
        self,
        aip_endpoint: Optional[str] = None,
        membase_endpoint: Optional[str] = None,
        mode: RegistrationMode = RegistrationMode.DIRECT,
        gateway_url: Optional[str] = None,
        agent_backend_url: Optional[str] = None
    ):
        """
        Initialize the Agent Registry.

        Args:
            aip_endpoint: AIP platform endpoint URL (optional, can use env var AIP_ENDPOINT)
            membase_endpoint: Membase service endpoint URL (optional, can use env var MEMBASE_ENDPOINT)
            mode: Registration mode (DIRECT or GATEWAY)
            gateway_url: Gateway URL when using GATEWAY mode (optional, can use env var GATEWAY_URL)
            agent_backend_url: Agent's backend URL when using GATEWAY mode (optional, can use env var AGENT_BACKEND_URL)
        """
        # Load from environment if not provided
        self.aip_endpoint = aip_endpoint or os.getenv("AIP_ENDPOINT", "http://localhost:8001")
        self.membase_endpoint = membase_endpoint or os.getenv("MEMBASE_ENDPOINT", "http://localhost:8002")
        self.mode = mode
        self.gateway_url = gateway_url or os.getenv("GATEWAY_URL")
        self.agent_backend_url = agent_backend_url or os.getenv("AGENT_BACKEND_URL")

        # Validate gateway mode configuration
        if self.mode == RegistrationMode.GATEWAY:
            if not self.gateway_url:
                raise ConfigurationError("gateway_url is required when using GATEWAY mode")
            if not self.agent_backend_url:
                raise ConfigurationError("agent_backend_url is required when using GATEWAY mode")

        # Local agent instance tracking
        self._agents: Dict[str, TransparentAgentProxy] = {}
        self._identities: Dict[str, AgentIdentity] = {}

        # AIP SDK Client (required for all platform communication)
        self._aip_client = AsyncAIPClient(base_url=self.aip_endpoint)

        # Gateway Client (for gateway mode)
        self._gateway_client: Optional[GatewayClient] = None
        if self.mode == RegistrationMode.GATEWAY:
            self._gateway_client = GatewayClient(self.gateway_url)

        # HTTP client for Membase communication (agent-sdk specific feature)
        self._http_client = httpx.AsyncClient(timeout=10.0)

        # A2A Protocol support (agent-sdk specific feature)
        self._a2a_client = A2AClient()
        self._discovered_agents: Dict[str, AgentCard] = {}

        logger.info(f"AgentRegistry initialized in {self.mode.value} mode")
        if self.mode == RegistrationMode.GATEWAY:
            logger.info(f"  Gateway URL: {self.gateway_url}")
            logger.info(f"  Agent Backend URL: {self.agent_backend_url}")
    
    async def register_agent(
        self,
        name: str,
        agent_type: AgentType,
        wallet_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: str = "system",
        force: bool = False
    ) -> AgentIdentity:
        """
        Register a new agent.

        Supports two modes:
        - DIRECT: Register directly with AIP platform
        - GATEWAY: Register with gateway, which proxies requests to agent backend

        Args:
            name: Agent name
            agent_type: Type of the agent
            wallet_address: Web3 wallet address (optional, managed by AIP SDK)
            metadata: Additional metadata
            user_id: User ID who owns this agent (default: "system")
            force: Force re-registration if agent already exists (default: False)

        Returns:
            AgentIdentity: The agent's identity information
        """
        # 1. Create AIP AgentConfig (used for both modes)
        agent_config = AIPAgentConfig(
            name=name,
            description=metadata.get("description", "") if metadata else "",
            handle=metadata.get("handle", name.lower().replace(" ", "_")) if metadata else name.lower().replace(" ", "_"),
            capabilities=metadata.get("capabilities", []) if metadata else [],
            metadata={
                "agent_type": agent_type.value,
                "wallet_address": wallet_address,
                "mode": self.mode.value,
                **(metadata or {})
            }
        )

        agent_id = None
        endpoint_url = None

        # 2a. GATEWAY MODE: Register with gateway first
        if self.mode == RegistrationMode.GATEWAY:
            try:
                gateway_result = await self._gateway_client.register_agent(
                    agent_name=name,
                    backend_url=self.agent_backend_url,
                    metadata={
                        "agent_type": agent_type.value,
                        **(metadata or {})
                    },
                    force=force
                )
                endpoint_url = gateway_result.get("gateway_url")
                logger.info(f"Agent registered with gateway: {endpoint_url}")

                # Update agent config with gateway endpoint
                agent_config.metadata["endpoint_url"] = endpoint_url
                agent_config.metadata["gateway_mode"] = True

            except Exception as e:
                logger.error(f"Gateway registration failed: {e}", exc_info=True)
                raise RegistryError(f"Failed to register agent with gateway: {e}")

        # 2b. Register with AIP platform (for both modes)
        try:
            result = await self._aip_client.register_agent(user_id, agent_config)
            agent_id = result.get("agent_id", self._generate_agent_id(name))
            logger.info(f"Agent registered with AIP platform: {agent_id}")
        except Exception as e:
            logger.warning(f"AIP registration failed, using local ID: {e}")
            agent_id = self._generate_agent_id(name)

        # 3. Create AgentIdentity
        identity = AgentIdentity(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            public_key=None,
            wallet_address=wallet_address,
            metadata={
                **(metadata or {}),
                "endpoint_url": endpoint_url,
                "mode": self.mode.value,
                "gateway_url": self.gateway_url if self.mode == RegistrationMode.GATEWAY else None,
                "backend_url": self.agent_backend_url if self.mode == RegistrationMode.GATEWAY else None
            }
        )

        # 4. Initialize memory space in Membase (skip in GATEWAY mode)
        if self.mode != RegistrationMode.GATEWAY:
            await self._initialize_membase(identity)

        # 5. Save to local registry
        self._identities[identity.agent_id] = identity

        logger.info(f"Agent registered successfully: {identity.agent_id} ({name}) in {self.mode.value} mode")
        if endpoint_url:
            logger.info(f"  Accessible at: {endpoint_url}")

        return identity
    
    def register_agent_instance(
        self,
        agent: TransparentAgentProxy
    ) -> None:
        """
        Register an agent instance to the registry (called after agent creation).
        
        Args:
            agent: Agent adapter instance
        """
        agent_id = agent.identity.agent_id
        self._agents[agent_id] = agent
        self._identities[agent_id] = agent.identity

        logger.info(f"Agent instance registered to Registry: {agent_id}")
    
    async def get_agent(self, agent_id: str) -> Optional[TransparentAgentProxy]:
        """Get a registered agent instance."""
        return self._agents.get(agent_id)
    
    async def get_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent identity information."""
        # Check local cache first
        if agent_id in self._identities:
            return self._identities[agent_id]

        # Query from AIP platform
        return await self._query_identity_from_aip(agent_id)
    
    async def list_agents(self, include_remote: bool = False) -> List[AgentIdentity]:
        """
        List all agents.

        Args:
            include_remote: Whether to include remote agents from AIP platform
        """
        local_agents = list(self._identities.values())

        if include_remote:
            # Query all registered agents from AIP platform
            remote_agents = await self._query_all_agents_from_aip()

            # Merge and deduplicate
            all_agents = {a.agent_id: a for a in local_agents}
            for agent in remote_agents:
                if agent.agent_id not in all_agents:
                    all_agents[agent.agent_id] = agent

            return list(all_agents.values())

        return local_agents
    
    async def send_message_to_agent(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message: Dict[str, Any],
        protocol: str = "aip"
    ) -> Dict[str, Any]:
        """
        Send a message to another agent.

        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Receiver agent ID
            message: Message content
            protocol: Protocol type (aip/grpc/mcp)

        Returns:
            Response message
        """
        # Validate sender
        if from_agent_id not in self._identities:
            raise AgentNotFoundError(from_agent_id)

        # Check if target agent is local - prefer local delivery
        target_agent = self._agents.get(to_agent_id)
        if target_agent:
            return {"status": "delivered_locally", "to": to_agent_id, "message": message}

        # Send via AIP SDK client (delegated to AIP SDK)
        try:
            return await self._aip_client.send_message(
                from_agent=from_agent_id,
                to_agent=to_agent_id,
                message=message,
                protocol=protocol
            )
        except Exception as e:
            logger.error(f"AIP message send failed: {e}", exc_info=True)
            raise RegistryError(f"Failed to send message to agent {to_agent_id}: {e}")
    
    async def update_agent_metadata(
        self,
        agent_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update agent metadata locally and sync to AIP platform."""
        if agent_id not in self._identities:
            raise AgentNotFoundError(agent_id)

        # Update local cache
        self._identities[agent_id].metadata.update(metadata)

        # Sync to AIP platform via AIP SDK client (delegated)
        try:
            await self._aip_client.update_agent_metadata(agent_id, metadata)
        except Exception as e:
            logger.warning(f"Metadata sync to AIP failed (local cache updated): {e}", exc_info=True)

    async def _initialize_membase(self, identity: AgentIdentity) -> None:
        """Initialize memory space in Membase."""
        try:
            response = await self._http_client.post(
                f"{self.membase_endpoint}/agents/init",
                json={
                    "agent_id": identity.agent_id,
                    "config": {
                        "retention_policy": "permanent",
                        "encryption": True
                    }
                }
            )
            response.raise_for_status()
            logger.info(f"Membase initialized for agent: {identity.agent_id}")
        except Exception as e:
            logger.warning(f"Membase initialization failed (continuing): {e}", exc_info=True)
    
    def _generate_agent_id(self, name: str) -> str:
        """Generate a unique agent ID."""
        unique_str = f"{name}_{time.time()}_{uuid.uuid4().hex[:8]}"
        hash_id = hashlib.sha256(unique_str.encode()).hexdigest()[:16]
        return f"agent_{hash_id}"
    
    async def _query_identity_from_aip(
        self,
        agent_id: str
    ) -> Optional[AgentIdentity]:
        """Query agent identity from AIP platform using AIP SDK."""
        try:
            # Use AIP SDK to get agent info
            agent_info = await self._aip_client.get_agent(agent_id)

            if not agent_info:
                return None

            # Convert to AgentIdentity
            return AgentIdentity(
                agent_id=agent_info.agent_id,
                name=agent_info.name,
                agent_type=AgentType.AIP,  # Assume AIP type for remote agents
                public_key=None,
                wallet_address=agent_info.identity_address,
                metadata={
                    "description": agent_info.description,
                    "handle": agent_info.handle,
                    "capabilities": agent_info.capabilities,
                    "skills": agent_info.skills,
                    "endpoint_url": agent_info.endpoint_url
                }
            )
        except Exception as e:
            logger.warning(f"Failed to query agent {agent_id} from AIP: {e}", exc_info=True)
            return None
    
    async def _query_all_agents_from_aip(self) -> List[AgentIdentity]:
        """Query all registered agents from AIP platform using AIP SDK."""
        try:
            # Use AIP SDK to list all agents
            agents_info = await self._aip_client.list_agents()

            # Convert to AgentIdentity list
            return [
                AgentIdentity(
                    agent_id=agent.agent_id,
                    name=agent.name,
                    agent_type=AgentType.AIP,  # Assume AIP type for remote agents
                    public_key=None,
                    wallet_address=agent.identity_address,
                    metadata={
                        "description": agent.description,
                        "handle": agent.handle,
                        "capabilities": agent.capabilities,
                        "skills": agent.skills,
                        "endpoint_url": agent.endpoint_url
                    }
                )
                for agent in agents_info
            ]
        except Exception as e:
            logger.warning(f"Failed to list agents from AIP: {e}", exc_info=True)
            return []
    
    async def close(self):
        """Close the registry and clean up resources."""
        if self._aip_client:
            await self._aip_client.close()
        await self._http_client.aclose()
        await self._a2a_client.close()
    
    # ============================================================
    # A2A Protocol Methods
    # ============================================================
    
    async def discover_a2a_agent(
        self,
        agent_url: str,
        force_refresh: bool = False
    ) -> AgentCard:
        """
        Discover an external agent via A2A protocol.
        
        Discover an external agent via A2A protocol by fetching
        its Agent Card from /.well-known/agent.json
        
        Args:
            agent_url: Base URL of the agent
            force_refresh: If True, bypass cache and fetch fresh data
        
        Returns:
            AgentCard describing the agent's capabilities
            
        Example:
            >>> card = await registry.discover_a2a_agent("https://agent.example.com")
            >>> print(f"Found agent: {card.name}")
            >>> print(f"Skills: {[s.name for s in card.skills]}")
        """
        card = await self._a2a_client.discover_agent(agent_url, force_refresh)
        self._discovered_agents[agent_url] = card
        logger.info(f"Discovered A2A Agent: {card.name} at {agent_url}")
        return card
    
    async def list_discovered_agents(self) -> List[AgentCard]:
        """List all discovered A2A agents."""
        return list(self._discovered_agents.values())
    
    async def send_a2a_task(
        self,
        agent_url: str,
        message: Message,
        stream: bool = False,
        task_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> Union[Task, AsyncIterator[StreamResponse]]:
        """
        Send a task to an A2A agent.
        
        Send a task to an A2A-compliant agent.
        
        Args:
            agent_url: A2A endpoint URL
            message: Message to send
            stream: If True, return an async iterator for streaming responses
            task_id: Optional task ID for continuing a task
            context_id: Optional context ID for grouping tasks
        
        Returns:
            If stream=False: Task with results
            If stream=True: AsyncIterator of StreamResponse objects
            
        Example:
            >>> from unibase_agent_sdk.a2a import Message
            >>> message = Message.user("What's the weather like?")
            >>> task = await registry.send_a2a_task("https://agent.example.com", message)
            >>> print(task.history[-1].parts[0].text)
        """
        if stream:
            return self._a2a_client.stream_task(
                agent_url, message, task_id, context_id
            )
        return await self._a2a_client.send_task(
            agent_url, message, task_id, context_id
        )
    
    async def get_a2a_task(
        self,
        agent_url: str,
        task_id: str
    ) -> Task:
        """Get A2A task status."""
        return await self._a2a_client.get_task(agent_url, task_id)
    
    async def cancel_a2a_task(
        self,
        agent_url: str,
        task_id: str
    ) -> Task:
        """Cancel an A2A task."""
        return await self._a2a_client.cancel_task(agent_url, task_id)
    
    def generate_agent_card_for(
        self,
        agent_id: str,
        base_url: str,
        **kwargs
    ) -> AgentCard:
        """
        Generate an A2A Agent Card for a local agent.
        
        Generate an A2A Agent Card for a locally registered agent.
        
        Args:
            agent_id: ID of the local agent
            base_url: Base URL where the agent will be exposed
            **kwargs: Additional arguments for generate_agent_card
        
        Returns:
            AgentCard for the agent
            
        Example:
            >>> card = registry.generate_agent_card_for(
            ...     agent_id="my-agent-123",
            ...     base_url="https://my-agent.example.com"
            ... )
            >>> print(card.to_json())
        """
        if agent_id not in self._identities:
            raise AgentNotFoundError(agent_id)

        identity = self._identities[agent_id]
        return generate_agent_card(identity, base_url, **kwargs)

