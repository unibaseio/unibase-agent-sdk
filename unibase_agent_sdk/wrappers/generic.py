"""Generic Agent Wrapper."""

from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    List,
    AsyncIterator,
    Awaitable,
    Union,
)
import json
import asyncio
import inspect
import os

# Import directly from Google A2A SDK
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    Task,
    Message,
    Role,
)
from a2a.utils.message import get_message_text
from a2a.client.helpers import create_text_message_object

# Import Unibase extensions
from unibase_agent_sdk.a2a.server import A2AServer
from unibase_agent_sdk.a2a.types import StreamResponse, AgentMessage
from unibase_agent_sdk.utils.logger import get_logger

# Import CostModel from SDK
from aip_sdk.types import CostModel

logger = get_logger("wrappers.generic")


def parse_agent_message(message: Message) -> AgentMessage:
    """Parse an A2A Message into AgentMessage format."""
    # First try the standard method
    # return AgentMessage.from_a2a_message(message)
    # if agent_msg.intent:
    #     return agent_msg

    # If intent is empty, it might be due to RootModel parts (a2a-sdk v0.3+)
    # We manually extract text here
    
    text_parts = []
    print(f"DEBUG: message.parts type: {type(message.parts)}")
    for i, part in enumerate(message.parts):
        print(f"DEBUG: part[{i}] type: {type(part)}")
        print(f"DEBUG: part[{i}] dir: {dir(part)}")
        
        # Handle Pydantic RootModel (part.root)
        target = part.root if hasattr(part, "root") else part
        print(f"DEBUG: target type: {type(target)}")
        if hasattr(target, "root"):
             print("DEBUG: target still has root attribute")

        if hasattr(target, "text"):
            val = getattr(target, "text")
            print(f"DEBUG: target.text: {val}")
            if val:
                text_parts.append(val)
        else:
             print("DEBUG: target has no 'text' attribute")
            
    text = " ".join(text_parts)
    print(f"DEBUG: Extracted text: '{text}'")
    
    # Logic similar to AgentMessage.from_a2a_message
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "intent" in data and "context" in data:
                return AgentMessage.from_dict(data)
                
            if "task" in data:
                # Handle task payload format if present
                # (Simplified version of what logic exists in aip_sdk)
                pass
                
            # If valid JSON but not a standard envelope, treat as structured data?
            # Or just fall through to text intent if it's not a special format.
    except (json.JSONDecodeError, TypeError):
        pass

    # Default: Treat text as intent
    # Use message_id as run_id if available, to ensure we have some context
    from aip_sdk.types import MessageContext
    
    return AgentMessage(
        intent=text,
        context=MessageContext(
            run_id=getattr(message, "message_id", "") or "",
            caller_id="unknown"
        )
    )


def _get_default_aip_endpoint() -> str:
    """Get default AIP endpoint from deployment config or environment."""
    env_url = os.environ.get("AIP_ENDPOINT")
    if env_url:
        return env_url

    try:
        from aip.core.config import get_config
        config = get_config()
        return config.aip.public_url
    except Exception:
        return "http://api.aip.unibase.com"


# Type aliases
SyncHandler = Callable[[str], str]
AsyncHandler = Callable[[str], Awaitable[str]]
Handler = Union[SyncHandler, AsyncHandler]

SyncStreamHandler = Callable[[str], List[str]]
AsyncStreamHandler = Callable[[str], AsyncIterator[str]]
StreamHandler = Union[SyncStreamHandler, AsyncStreamHandler]


def _create_task_handler(
    handler: Handler,
    streaming: bool = False,
) -> Callable[[Task, Message], AsyncIterator[StreamResponse]]:
    """Create an A2A task handler from a simple function.

    The handler receives the raw user intent from the AgentMessage format.
    For more control, agents can use the AgentMessage type directly.
    """

    is_async = asyncio.iscoroutinefunction(handler)
    is_async_gen = inspect.isasyncgenfunction(handler)

    async def task_handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        # Parse message using AgentMessage format
        # Use our local helper which handles RootModel parts correctly
        agent_message = parse_agent_message(message)

        # Pass the intent to the handler (the raw user request)
        input_text = agent_message.intent

        # Log context for debugging
        logger.debug(
            "Processing request",
            extra={
                "intent": input_text[:100] if input_text else None,
                "run_id": agent_message.context.run_id,
                "caller": agent_message.context.caller_id,
                "has_hints": agent_message.hints is not None,
            }
        )

        if streaming:
            # Streaming handler
            if is_async_gen:
                async for chunk in handler(input_text):
                    response_msg = create_text_message_object(Role.agent, chunk)
                    yield StreamResponse(message=response_msg)
            elif is_async:
                # Limit case: async function returning iterable? (unlikely for streaming)
                # But if so, await it first
                result = await handler(input_text)
                for chunk in result:
                     response_msg = create_text_message_object(Role.agent, chunk)
                     yield StreamResponse(message=response_msg)
            else:
                # Sync streaming (returns list)
                for chunk in handler(input_text):
                    response_msg = create_text_message_object(Role.agent, chunk)
                    yield StreamResponse(message=response_msg)
        else:
            # Non-streaming handler
            if is_async:
                result = await handler(input_text)
            else:
                # Run sync function in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, handler, input_text)

            response_msg = create_text_message_object(Role.agent, str(result))
            yield StreamResponse(message=response_msg)

    return task_handler


def expose_as_a2a(
    name: str,
    handler: Handler,
    *,
    port: int = 8000,
    host: str = "0.0.0.0",
    description: str = None,
    skills: List[AgentSkill] = None,
    streaming: bool = False,
    version: str = "1.0.0",
    # Account integration
    user_id: str = None,
    aip_endpoint: str = None,
    handle: str = None,
    auto_register: bool = True,
    # Pricing via cost_model
    cost_model: CostModel = None,
    currency: str = "USD",
    **kwargs,
) -> A2AServer:
    """Expose ANY callable as an A2A-compatible agent service.

    Args:
        name: Agent name
        handler: The callable to expose (sync or async function)
        port: Port to listen on (default: 8000)
        host: Host to bind to (default: 0.0.0.0)
        description: Agent description
        skills: List of AgentSkill definitions
        streaming: Enable streaming responses
        version: Agent version string
        user_id: AIP platform user ID for registration
        aip_endpoint: AIP platform endpoint URL
        handle: Agent handle (auto-generated from name if not provided)
        auto_register: Whether to auto-register with AIP platform
        cost_model: Pricing model (use CostModel(base_call_fee=0.05) for $0.05/call)
        currency: Currency for pricing (default: USD)
        **kwargs: Additional arguments passed to AgentCard

    Returns:
        A2AServer instance ready to run

    Example:
        server = expose_as_a2a(
            "Calculator",
            my_handler,
            cost_model=CostModel(base_call_fee=0.05),  # $0.05 per call
            user_id="user:0x123...",
        )
    """
    # Create default description
    if description is None:
        description = f"{name} agent"

    # Create default skill if not provided
    if skills is None:
        skill_id = name.lower().replace(" ", "_")
        skills = [
            AgentSkill(
                id=skill_id,
                name=name,
                description=description,
                tags=[],
            )
        ]

    # Generate handle from name if not provided
    if handle is None:
        handle = name.lower().replace(" ", ".").replace("_", ".")

    # Build Agent Card with Google A2A types
    agent_card = AgentCard(
        name=name,
        description=description,
        url=f"http://{host}:{port}",
        version=version,
        skills=skills,
        capabilities=AgentCapabilities(streaming=streaming),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"],
        **kwargs,
    )

    # Create task handler
    task_handler = _create_task_handler(handler, streaming=streaming)

    # Resolve account integration settings
    resolved_user_id = user_id or os.getenv("AIP_USER_ID")
    resolved_aip_endpoint = aip_endpoint or _get_default_aip_endpoint()

    # Use default cost_model if not provided
    resolved_cost_model = cost_model or CostModel(base_call_fee=0.001)

    # Create registration config if user_id is provided
    registration_config = None
    if resolved_user_id and auto_register:
        registration_config = {
            "user_id": resolved_user_id,
            "aip_endpoint": resolved_aip_endpoint,
            "handle": handle,
            "name": name,
            "description": description,
            "skills": [{"id": s.id, "name": s.name, "description": s.description} for s in skills],
            "cost_model": resolved_cost_model.to_dict(),
            "currency": currency,
        }

    # Create and return server
    return A2AServer(
        agent_card=agent_card,
        task_handler=task_handler,
        host=host,
        port=port,
        registration_config=registration_config,
    )


class AgentWrapper:
    """Wrapper for class-based agents."""

    def __init__(
        self,
        agent: Any,
        name: str,
        *,
        method: str = None,
        skill_methods: dict[str, str] = None,
        description: str = None,
        version: str = "1.0.0",
    ):
        """Initialize agent wrapper."""
        self.agent = agent
        self.name = name
        self.description = description or f"{name} agent"
        self.version = version

        if method and skill_methods:
            raise ValueError("Cannot specify both 'method' and 'skill_methods'")

        if skill_methods:
            self.skill_methods = skill_methods
        elif method:
            skill_id = name.lower().replace(" ", "_")
            self.skill_methods = {skill_id: method}
        else:
            # Auto-detect public methods
            self.skill_methods = self._auto_detect_methods()

        self._validate_methods()

    def _auto_detect_methods(self) -> dict[str, str]:
        """Auto-detect public methods that could be skills."""
        methods = {}
        for attr_name in dir(self.agent):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self.agent, attr_name)
            if callable(attr) and not isinstance(attr, type):
                # Check if it looks like a handler (takes string, returns string)
                sig = inspect.signature(attr)
                params = list(sig.parameters.values())
                # Accept methods with 1 required param (besides self)
                required_params = [p for p in params if p.default is inspect.Parameter.empty]
                if len(required_params) <= 1:
                    methods[attr_name] = attr_name
        return methods

    def _validate_methods(self):
        """Validate that all specified methods exist."""
        for skill_id, method_name in self.skill_methods.items():
            if not hasattr(self.agent, method_name):
                raise ValueError(
                    f"Agent has no method '{method_name}' for skill '{skill_id}'"
                )

    def _build_skills(self) -> List[AgentSkill]:
        """Build AgentSkill list from skill_methods."""
        skills = []
        for skill_id, method_name in self.skill_methods.items():
            method = getattr(self.agent, method_name)
            doc = method.__doc__ or f"{method_name} skill"
            skills.append(
                AgentSkill(
                    id=skill_id,
                    name=method_name.replace("_", " ").title(),
                    description=doc.strip(),
                    tags=[],
                )
            )
        return skills

    async def _handle_task(self, task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        """Route task to appropriate method."""
        # Parse message using new AgentMessage format
        agent_message = AgentMessage.from_a2a_message(message)
        input_text = agent_message.intent

        # Log context for debugging
        logger.debug(
            "AgentWrapper processing request",
            extra={
                "agent": self.name,
                "intent": input_text[:100] if input_text else None,
                "run_id": agent_message.context.run_id,
                "caller": agent_message.context.caller_id,
            }
        )

        # For single-skill agents, use the only method
        if len(self.skill_methods) == 1:
            method_name = list(self.skill_methods.values())[0]
        else:
            # Check if hints suggest a specific skill
            if agent_message.hints and agent_message.hints.suggested_task:
                suggested = agent_message.hints.suggested_task
                if suggested in self.skill_methods:
                    method_name = self.skill_methods[suggested]
                else:
                    method_name = list(self.skill_methods.values())[0]
            else:
                method_name = list(self.skill_methods.values())[0]

        method = getattr(self.agent, method_name)

        # Call the method
        if asyncio.iscoroutinefunction(method):
            result = await method(input_text)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, method, input_text)

        response_msg = create_text_message_object(Role.agent, str(result))
        yield StreamResponse(message=response_msg)

    def to_server(self, port: int = 8000, host: str = "0.0.0.0") -> A2AServer:
        """Create an A2AServer for this wrapped agent."""
        agent_card = AgentCard(
            name=self.name,
            description=self.description,
            url=f"http://{host}:{port}",
            version=self.version,
            skills=self._build_skills(),
            capabilities=AgentCapabilities(),
            default_input_modes=["text/plain", "application/json"],
            default_output_modes=["text/plain", "application/json"],
        )

        return A2AServer(
            agent_card=agent_card,
            task_handler=self._handle_task,
            host=host,
            port=port,
        )

    async def serve(self, port: int = 8000, host: str = "0.0.0.0"):
        """Start serving the agent as an A2A service."""
        server = self.to_server(port=port, host=host)
        await server.run()

    def serve_sync(self, port: int = 8000, host: str = "0.0.0.0"):
        """Start serving the agent synchronously."""
        asyncio.run(self.serve(port=port, host=host))


def wrap_agent(
    agent: Any,
    name: str = None,
    method: str = None,
    **kwargs,
) -> AgentWrapper:
    """Convenience function to wrap an agent instance."""
    if name is None:
        name = agent.__class__.__name__

    return AgentWrapper(agent=agent, name=name, method=method, **kwargs)
