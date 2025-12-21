"""Agent Card generation from AgentIdentity.

Generates A2A-compliant Agent Cards from Unibase AgentIdentity objects,
enabling seamless discovery of Unibase agents by other A2A clients.
"""

from typing import Optional, List, Dict, Any
from .types import AgentCard, Skill, Capability, Provider, SupportedInterface
from ..core.types import AgentIdentity


def generate_agent_card(
    identity: AgentIdentity,
    base_url: str,
    description: Optional[str] = None,
    skills: Optional[List[Skill]] = None,
    capabilities: Optional[Capability] = None,
    provider: Optional[Provider] = None,
    version: str = "1.0.0",
    protocol_version: str = "0.3.0",
    protocol_bindings: Optional[List[str]] = None,
) -> AgentCard:
    """Generate an A2A Agent Card from AgentIdentity.
    
    This function bridges the Unibase identity system with the A2A
    protocol, allowing any registered Unibase agent to be discovered
    and communicated with via standard A2A mechanisms.
    
    Args:
        identity: Unibase AgentIdentity object
        base_url: Base URL where the agent's A2A endpoints are hosted
        description: Human-readable description (uses name if not provided)
        skills: List of Skill objects describing agent capabilities
        capabilities: Capability configuration (streaming, push, etc.)
        provider: Organization information
        version: Agent version string
        protocol_version: A2A protocol version (default: "0.3.0")
        protocol_bindings: List of protocol bindings to support 
                          (default: ["JSONRPC"])
    
    Returns:
        AgentCard: A2A-compliant agent card
        
    Example:
        >>> from unibase_agent_sdk import AgentIdentity, AgentType
        >>> from unibase_agent_sdk.a2a import generate_agent_card, Skill
        >>> 
        >>> identity = AgentIdentity(
        ...     agent_id="agent-123",
        ...     name="Research Agent",
        ...     agent_type=AgentType.CLAUDE
        ... )
        >>> 
        >>> skills = [
        ...     Skill(
        ...         id="research",
        ...         name="Web Research",
        ...         description="Research topics on the web"
        ...     )
        ... ]
        >>> 
        >>> card = generate_agent_card(
        ...     identity=identity,
        ...     base_url="https://my-agent.example.com",
        ...     skills=skills
        ... )
        >>> print(card.to_json())
    """
    # Normalize base URL (remove trailing slash)
    base_url = base_url.rstrip("/")
    
    # Default description from identity name
    if description is None:
        description = f"AI agent: {identity.name}"
        if identity.metadata.get("description"):
            description = identity.metadata["description"]
    
    # Default capabilities
    if capabilities is None:
        capabilities = Capability(
            streaming=True,
            push_notifications=False,
            state_transition_history=True
        )
    
    # Build supported interfaces
    bindings = protocol_bindings or ["JSONRPC"]
    interfaces = []
    for binding in bindings:
        if binding == "JSONRPC":
            interfaces.append(SupportedInterface(
                url=f"{base_url}/a2a",
                protocol_binding="JSONRPC"
            ))
        elif binding == "HTTP+JSON":
            interfaces.append(SupportedInterface(
                url=f"{base_url}/a2a/json",
                protocol_binding="HTTP+JSON"
            ))
    
    # Default skill from identity metadata if none provided
    if skills is None:
        skills = []
        # Check if identity has skill metadata
        if identity.metadata.get("skills"):
            for skill_data in identity.metadata["skills"]:
                skills.append(Skill(
                    id=skill_data.get("id", f"{identity.name.lower()}-skill"),
                    name=skill_data.get("name", identity.name),
                    description=skill_data.get("description", description),
                    tags=skill_data.get("tags", []),
                    examples=skill_data.get("examples", [])
                ))
        else:
            # Create a default skill
            skills.append(Skill(
                id=f"{identity.agent_id}-default",
                name=identity.name,
                description=description,
                tags=[identity.agent_type.value, "unibase"],
            ))
    
    # Build the agent card
    card = AgentCard(
        name=identity.name,
        description=description,
        url=base_url,
        version=version,
        protocol_version=protocol_version,
        supported_interfaces=interfaces,
        capabilities=capabilities,
        skills=skills,
        provider=provider,
    )
    
    return card


def agent_card_from_metadata(
    metadata: Dict[str, Any],
    base_url: str
) -> AgentCard:
    """Generate an Agent Card from raw metadata dictionary.
    
    Useful when agent configuration is loaded from external sources
    like configuration files or environment variables.
    
    Args:
        metadata: Dictionary containing agent metadata
        base_url: Base URL for the agent
    
    Returns:
        AgentCard: Generated agent card
    """
    skills = []
    for skill_data in metadata.get("skills", []):
        skills.append(Skill(
            id=skill_data["id"],
            name=skill_data["name"],
            description=skill_data["description"],
            tags=skill_data.get("tags", []),
            examples=skill_data.get("examples", []),
            input_modes=skill_data.get("input_modes", ["text/plain"]),
            output_modes=skill_data.get("output_modes", ["text/plain"])
        ))
    
    capabilities = Capability(
        streaming=metadata.get("capabilities", {}).get("streaming", True),
        push_notifications=metadata.get("capabilities", {}).get("push_notifications", False),
        state_transition_history=metadata.get("capabilities", {}).get("state_transition_history", True)
    )
    
    provider = None
    if metadata.get("provider"):
        provider = Provider(
            organization=metadata["provider"]["organization"],
            url=metadata["provider"].get("url")
        )
    
    return AgentCard(
        name=metadata["name"],
        description=metadata.get("description", f"AI agent: {metadata['name']}"),
        url=base_url,
        version=metadata.get("version", "1.0.0"),
        protocol_version=metadata.get("protocol_version", "0.3.0"),
        capabilities=capabilities,
        skills=skills,
        provider=provider,
        icon_url=metadata.get("icon_url"),
        documentation_url=metadata.get("documentation_url")
    )
