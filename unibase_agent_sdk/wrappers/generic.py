"""
Generic Agent Wrapper

Provides utilities to wrap ANY agent/callable as an A2A-compatible service.
No framework-specific code required.

Usage Examples:

1. Simple function (standalone, no account):
    ```python
    from unibase_agent_sdk import expose_as_a2a

    def echo(text: str) -> str:
        return f"Echo: {text}"

    server = expose_as_a2a("EchoAgent", echo, port=8100)
    await server.run()
    ```

2. With account registration (connects to AIP platform):
    ```python
    server = expose_as_a2a(
        "MyAgent",
        handler,
        port=8100,
        # Account integration
        user_id="user:0x1234...",
        # aip_endpoint auto-detected from AIP_ENVIRONMENT config
    )
    await server.run()  # Registers agent on startup
    ```

3. Async function:
    ```python
    async def process(text: str) -> str:
        result = await some_llm_call(text)
        return result

    server = expose_as_a2a("ProcessorAgent", process, port=8100)
    await server.run()
    ```

4. Existing agent object:
    ```python
    from langchain.agents import AgentExecutor

    agent = AgentExecutor(...)

    server = expose_as_a2a(
        "LangChainAgent",
        lambda text: agent.invoke({"input": text})["output"],
        port=8100
    )
    await server.run()
    ```

5. Class-based agent with AgentWrapper:
    ```python
    class MyAgent:
        def run(self, text: str) -> str:
            return f"Result: {text}"

    wrapper = AgentWrapper(
        agent=MyAgent(),
        name="MyAgent",
        method="run",
    )
    await wrapper.serve(port=8100)
    ```
"""

from typing import (
    Any,
    Callable,
    Optional,
    List,
    Union,
    AsyncIterator,
    Awaitable,
)
import asyncio
import inspect
import os

from unibase_agent_sdk.a2a.server import A2AServer
from unibase_agent_sdk.a2a.types import (
    AgentCard,
    Skill,
    Task,
    Message,
    StreamResponse,
    TextPart,
)
from unibase_agent_sdk.utils.logger import get_logger

logger = get_logger("wrappers.generic")


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
        return "http://localhost:8001"


# Type aliases
SyncHandler = Callable[[str], str]
AsyncHandler = Callable[[str], Awaitable[str]]
Handler = Union[SyncHandler, AsyncHandler]

SyncStreamHandler = Callable[[str], List[str]]
AsyncStreamHandler = Callable[[str], AsyncIterator[str]]
StreamHandler = Union[SyncStreamHandler, AsyncStreamHandler]


def _extract_text(message: Message) -> str:
    """Extract text content from a Message."""
    parts = []
    for part in message.parts:
        if isinstance(part, TextPart):
            parts.append(part.text)
        elif hasattr(part, "text"):
            parts.append(part.text)
    return "".join(parts)


def _create_task_handler(
    handler: Handler,
    streaming: bool = False,
) -> Callable[[Task, Message], AsyncIterator[StreamResponse]]:
    """Create an A2A task handler from a simple function."""

    is_async = asyncio.iscoroutinefunction(handler)

    async def task_handler(task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        input_text = _extract_text(message)

        if streaming:
            # Streaming handler
            if is_async:
                async for chunk in handler(input_text):
                    yield StreamResponse(message=Message.agent(chunk))
            else:
                # Sync streaming (returns list)
                for chunk in handler(input_text):
                    yield StreamResponse(message=Message.agent(chunk))
        else:
            # Non-streaming handler
            if is_async:
                result = await handler(input_text)
            else:
                # Run sync function in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, handler, input_text)

            yield StreamResponse(message=Message.agent(str(result)))

    return task_handler


def expose_as_a2a(
    name: str,
    handler: Handler,
    *,
    port: int = 8000,
    host: str = "0.0.0.0",
    description: str = None,
    skills: List[Skill] = None,
    streaming: bool = False,
    version: str = "1.0.0",
    # Account integration
    user_id: str = None,
    aip_endpoint: str = None,
    handle: str = None,
    auto_register: bool = True,
    **kwargs,
) -> A2AServer:
    """
    Expose ANY callable as an A2A-compatible agent service.

    This is the simplest way to create an A2A agent from existing code.
    Just provide a function that takes text input and returns text output.

    Args:
        name: Agent name (displayed in Agent Card)
        handler: Function that processes text input and returns text output.
                 Can be sync or async.
        port: Port to run the server on (default: 8000)
        host: Host to bind to (default: "0.0.0.0")
        description: Agent description (default: "{name} agent")
        skills: List of Skill objects describing agent capabilities.
                If not provided, creates a default skill.
        streaming: If True, handler should be a generator/async generator
                   yielding chunks instead of returning a single response.
        version: Agent version string (default: "1.0.0")
        user_id: User ID who owns this agent (e.g., "user:0x1234...").
                 If provided, the agent will be registered with AIP platform.
                 Can also be set via AIP_USER_ID environment variable.
        aip_endpoint: AIP platform endpoint URL for agent registration.
                      Auto-detected from AIP_ENDPOINT env var or deployment config.
        handle: Agent handle for registration (default: derived from name).
                The agent will be registered as "erc8004:{handle}".
        auto_register: If True (default), automatically register with AIP
                       platform on server startup when user_id is provided.
        **kwargs: Additional arguments passed to AgentCard

    Returns:
        A2AServer instance (call .run() or .run_sync() to start)

    Examples:
        # Simple sync function (standalone, no registration)
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        server = expose_as_a2a("Greeter", greet, port=8100)
        await server.run()

        # With AIP platform registration (aip_endpoint auto-detected)
        server = expose_as_a2a(
            "MyAgent",
            handler,
            port=8100,
            user_id="user:0x1234...",
        )
        await server.run()  # Registers agent on startup

        # Wrap existing LangChain agent
        agent = AgentExecutor(...)
        server = expose_as_a2a(
            "LangChainBot",
            lambda text: agent.invoke({"input": text})["output"],
            port=8100,
            user_id="user:0x1234...",
        )
        await server.run()
    """
    # Create default description
    if description is None:
        description = f"{name} agent"

    # Create default skill if not provided
    if skills is None:
        skill_id = name.lower().replace(" ", "_")
        skills = [
            Skill(
                id=skill_id,
                name=name,
                description=description,
            )
        ]

    # Generate handle from name if not provided
    if handle is None:
        handle = name.lower().replace(" ", ".").replace("_", ".")

    # Build Agent Card
    agent_card = AgentCard(
        name=name,
        description=description,
        url=f"http://{host}:{port}",
        version=version,
        skills=skills,
        **kwargs,
    )

    # Create task handler
    task_handler = _create_task_handler(handler, streaming=streaming)

    # Resolve account integration settings
    resolved_user_id = user_id or os.getenv("AIP_USER_ID")
    resolved_aip_endpoint = aip_endpoint or _get_default_aip_endpoint()

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
    """
    Wrapper for class-based agents.

    Provides more control than expose_as_a2a() for complex agents
    that need initialization, state, or multiple methods.

    Example:
        class MyAgent:
            def __init__(self, model: str):
                self.llm = LLM(model)

            def chat(self, message: str) -> str:
                return self.llm.complete(message)

            def summarize(self, text: str) -> str:
                return self.llm.complete(f"Summarize: {text}")

        # Wrap with specific method
        wrapper = AgentWrapper(
            agent=MyAgent("gpt-4"),
            name="ChatAgent",
            method="chat",
        )
        await wrapper.serve(port=8100)

        # Or use skill routing
        wrapper = AgentWrapper(
            agent=MyAgent("gpt-4"),
            name="MultiSkillAgent",
            skill_methods={
                "chat": "chat",
                "summarize": "summarize",
            },
        )
        await wrapper.serve(port=8100)
    """

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
        """
        Initialize agent wrapper.

        Args:
            agent: The agent instance to wrap
            name: Agent name for the Agent Card
            method: Single method to use as handler (mutually exclusive with skill_methods)
            skill_methods: Dict mapping skill IDs to method names for multi-skill agents
            description: Agent description
            version: Agent version
        """
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

    def _build_skills(self) -> List[Skill]:
        """Build Skill list from skill_methods."""
        skills = []
        for skill_id, method_name in self.skill_methods.items():
            method = getattr(self.agent, method_name)
            doc = method.__doc__ or f"{method_name} skill"
            skills.append(
                Skill(
                    id=skill_id,
                    name=method_name.replace("_", " ").title(),
                    description=doc.strip(),
                )
            )
        return skills

    async def _handle_task(self, task: Task, message: Message) -> AsyncIterator[StreamResponse]:
        """Route task to appropriate method."""
        input_text = _extract_text(message)

        # For single-skill agents, use the only method
        if len(self.skill_methods) == 1:
            method_name = list(self.skill_methods.values())[0]
        else:
            # TODO: Could use task metadata or message to route to specific skill
            # For now, default to first skill
            method_name = list(self.skill_methods.values())[0]

        method = getattr(self.agent, method_name)

        # Call the method
        if asyncio.iscoroutinefunction(method):
            result = await method(input_text)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, method, input_text)

        yield StreamResponse(message=Message.agent(str(result)))

    def to_server(self, port: int = 8000, host: str = "0.0.0.0") -> A2AServer:
        """Create an A2AServer for this wrapped agent."""
        agent_card = AgentCard(
            name=self.name,
            description=self.description,
            url=f"http://{host}:{port}",
            version=self.version,
            skills=self._build_skills(),
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
    """
    Convenience function to wrap an agent instance.

    Args:
        agent: The agent instance to wrap
        name: Agent name (default: class name)
        method: Method to use as handler (default: auto-detect)
        **kwargs: Additional arguments for AgentWrapper

    Returns:
        AgentWrapper instance

    Example:
        from langchain.agents import AgentExecutor

        agent = AgentExecutor(...)
        wrapper = wrap_agent(agent, method="invoke")
        await wrapper.serve(port=8100)
    """
    if name is None:
        name = agent.__class__.__name__

    return AgentWrapper(agent=agent, name=name, method=method, **kwargs)
