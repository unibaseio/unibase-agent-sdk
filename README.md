# Unibase Agent SDK

Framework for building A2A-compatible AI agents.

## Installation

```bash
pip install unibase-agent-sdk
```

> **Note:** This package depends on `a2a-sdk` (Google's Agent-to-Agent Protocol SDK). If you have an unrelated package named `a2a` (v0.44) installed, it will conflict. Uninstall it first with `pip uninstall a2a`.

## Quick Start

### Expose a Function as an Agent

```python
from unibase_agent_sdk import expose_as_a2a

def calculator(expression: str) -> str:
    result = eval(expression, {"__builtins__": {}}, {})
    return f"Result: {result}"

server = expose_as_a2a(
    name="Calculator",
    handler=calculator,
    description="Evaluates math expressions",
    port=8100
)
server.run_sync()
```

Your agent is now accessible at `http://localhost:8100` with A2A endpoints.

### Async Handlers

```python
async def llm_handler(prompt: str) -> str:
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

server = expose_as_a2a(
    name="LLM Agent",
    handler=llm_handler,
    port=8100
)
await server.run()
```

### Streaming Responses

```python
from typing import AsyncIterator

async def streaming_handler(text: str) -> AsyncIterator[str]:
    for word in text.split():
        yield word + " "
        await asyncio.sleep(0.1)

server = expose_as_a2a(
    name="Streaming Agent",
    handler=streaming_handler,
    streaming=True,
    port=8100
)
```

## Features

- **Zero Boilerplate** - Wrap any function as an A2A agent
- **A2A Protocol** - Full JSON-RPC 2.0 implementation
- **Streaming** - Server-Sent Events for real-time responses
- **Platform Integration** - Auto-register with Unibase AIP
- **Framework Agnostic** - Works with any Python code

## Wrapping Agents

### Wrap a Class

```python
from unibase_agent_sdk import wrap_agent

class MyAgent:
    def process(self, text: str) -> str:
        return text.upper()

    def analyze(self, data: dict) -> dict:
        return {"count": len(data)}

agent = MyAgent()

# Single method
wrapper = wrap_agent(agent, "MyAgent", method="process")

# Multiple methods as skills
wrapper = wrap_agent(agent, "MyAgent", methods=["process", "analyze"])

wrapper.serve_sync(port=8100)
```

### AgentWrapper Class

```python
from unibase_agent_sdk import AgentWrapper

class CustomAgent:
    async def run(self, input: str) -> str:
        return f"Processed: {input}"

agent = CustomAgent()
wrapper = AgentWrapper(
    agent=agent,
    name="Custom Agent",
    method_map={"default": "run"}
)

await wrapper.serve(port=8100)
```

## AgentMessage Format

When agents receive requests from the AIP platform, they receive messages in the `AgentMessage` format. This provides a clean separation: the platform handles routing/payment/logging, and agents handle understanding.

```python
from unibase_agent_sdk.a2a import AgentMessage

async def handle_task(task: Task, message: Message):
    # Parse the message into AgentMessage format
    agent_message = AgentMessage.from_a2a_message(message)

    # Get the user's intent (raw text or JSON)
    intent = agent_message.intent

    # Access context information
    print(f"Run ID: {agent_message.context.run_id}")
    print(f"Caller: {agent_message.context.caller_id}")

    # Use optional routing hints (agents can ignore these)
    if agent_message.hints:
        print(f"Detected category: {agent_message.hints.detected_category}")
        print(f"Extracted entities: {agent_message.hints.extracted_entities}")

    # Your agent is responsible for understanding the intent
    result = process_intent(intent)

    yield StreamResponse(message=create_text_message(result, Role.agent))
```

The `AgentMessage` format:
- **intent**: The raw user request (your agent interprets this)
- **context**: Platform-provided metadata (run_id, caller_id, conversation_id)
- **hints**: Optional routing suggestions (agents can use or ignore)
- **structured_data**: Optional structured parameters

This design allows agents to:
- Control their own input parsing
- Use LLM, regex, or structured parsing as needed
- Evolve independently of the platform

### Calling Other Agents

When your agent needs to call another agent, use the `AgentContext`:

```python
from aip_sdk.types import AgentContext

async def handle_task(task: Task, message: Message, context: AgentContext):
    agent_message = AgentMessage.from_a2a_message(message)

    # If we need weather data from another agent
    if "weather" in agent_message.intent.lower():
        result = await context.call_agent_with_intent(
            agent_id="weather.forecast",
            intent="Get weather for Tokyo",
            reason="User requested weather information"
        )
        # result.output contains the weather agent's response

    # Access caller chain for tracing
    caller_chain = agent_message.context.caller_chain
    # e.g., ["user:alice", "travel.planner", "weather.forecast"]
```

All inter-agent calls go through AIP for:
- Payment tracking (each agent call is charged)
- Caller chain accumulation (for audit trail)
- Logging to Membase
- Gateway routing for remote agents

## A2A Server

For more control, use `A2AServer` directly:

```python
from unibase_agent_sdk import A2AServer, StreamResponse, AgentMessage
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, Task, Message

async def handle_task(task: Task, message: Message):
    # Parse using AgentMessage (handles both new and legacy formats)
    agent_message = AgentMessage.from_a2a_message(message)
    intent = agent_message.intent

    # Process the intent
    response_msg = create_text_message("Processed: " + intent, Role.agent)
    yield StreamResponse(message=response_msg)

agent_card = AgentCard(
    name="My Agent",
    description="Does things",
    url="http://localhost:8100",
    version="1.0.0",
    skills=[
        AgentSkill(
            id="process",
            name="Process",
            description="Processes text",
            tags=["text"]
        )
    ],
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

server = A2AServer(
    agent_card=agent_card,
    task_handler=handle_task,
    host="0.0.0.0",
    port=8100
)

await server.run()
```

## A2A Client

Consume other A2A agents:

```python
from unibase_agent_sdk import A2AClient

async with A2AClient() as client:
    # Discover agent
    agent = await client.discover("http://localhost:8100")
    print(agent.name, agent.skills)

    # Execute task
    result = await client.execute(
        agent_url="http://localhost:8100",
        message="Calculate 2 + 2"
    )
    print(result)

    # Stream execution
    async for response in client.stream(
        agent_url="http://localhost:8100",
        message="Analyze this data"
    ):
        print(response)
```

## Platform Registration

Register your agent with the AIP platform:

```python
from unibase_agent_sdk import expose_as_a2a, RegistrationMode

server = expose_as_a2a(
    name="My Agent",
    handler=my_handler,
    port=8100,
    register=True,  # Enable registration
    registration_mode=RegistrationMode.DIRECT,  # or GATEWAY
    platform_url="http://localhost:8001",
    gateway_url="http://localhost:8080",
)
```

### Registration Modes

| Mode | Use Case |
|------|----------|
| `DIRECT` | Agent is publicly accessible via HTTP |
| `GATEWAY` | Agent behind NAT/firewall, polls gateway for tasks |

**How GATEWAY mode works:**
1. Agent registers with gateway as "external" (gets a poll URL)
2. Agent registers with AIP (no endpoint_url needed)
3. Agent continuously polls gateway for incoming tasks
4. When a task arrives, agent processes it and reports result back

```python
# Private agent behind firewall
server = expose_as_a2a(
    name="Private Agent",
    handler=my_handler,
    registration_mode=RegistrationMode.GATEWAY,
    gateway_url="http://gateway.example.com:8080",
    platform_url="http://aip.example.com:8001",
)
# Agent will poll gateway for tasks instead of listening for HTTP requests
await server.run()
```

## Agent Registry Client

For programmatic platform interaction:

```python
from unibase_agent_sdk import AgentRegistryClient, AgentType

registry = AgentRegistryClient(
    aip_endpoint="http://localhost:8001",
    mode=RegistrationMode.DIRECT
)

# Register agent
identity = await registry.register_agent(
    name="My Agent",
    agent_type=AgentType.AIP,
    metadata={"description": "My specialized agent"}
)

# Discover agents
agents = await registry.list_agents()
```

## Agent Groups with Intelligent Routing

Create groups of specialized agents where tasks are automatically routed to the most suitable agent using LLM-based routing:

```python
from unibase_agent_sdk import AgentRegistryClient

registry = AgentRegistryClient(aip_endpoint="http://localhost:8001")

# Create a group of specialized agents
result = await registry.register_agent_group(
    name="specialized_team",
    description="Team of specialized agents for different domains",
    member_agent_ids=[
        "erc8004:data_processor",   # Good at: data extraction, parsing
        "erc8004:ml_analyst",        # Good at: ML models, predictions
        "erc8004:report_generator",  # Good at: reports, summaries
        "erc8004:api_connector",     # Good at: API calls, integrations
        "erc8004:database_expert",   # Good at: SQL, queries
    ],
    price=0.0,  # Routing is free; charges happen at agent level
)

print(f"Group registered: {result['group_id']}")
```

### Usage Example

```python
from aip_sdk.platform import AsyncAIPClient

client = AsyncAIPClient(base_url="http://localhost:8001")

# Use the group - routing happens automatically
result = await client.run(
    objective="Extract data from CSV and generate summary report",
    agent="group:specialized_team",  # Use group ID
)

# Group automatically routes to: data_processor → report_generator
# Only 2 agents invoked (not all 5), saving 60% cost!
```

See [examples/agent_group_registration.py](examples/agent_group_registration.py) for a complete example.

## A2A Protocol Endpoints

When you expose an agent, these endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent.json` | GET | Agent Card (discovery) |
| `/a2a` | POST | Execute task (JSON-RPC) |
| `/a2a/stream` | POST | Stream task (SSE) |
| `/health` | GET | Health check |

## Types

```python
from unibase_agent_sdk import (
    # Agent types
    AgentType,        # AIP, CLAUDE, LANGCHAIN, OPENAI, CUSTOM
    AgentIdentity,    # Agent identity metadata

    # A2A
    A2AServer,        # Server implementation
    A2AClient,        # Client implementation
    StreamResponse,   # Streaming response wrapper

    # Wrappers
    expose_as_a2a,    # Function wrapper
    wrap_agent,       # Class wrapper
    AgentWrapper,     # Manual wrapper

    # Platform
    AgentRegistry,    # Registry client
    RegistrationMode, # DIRECT or GATEWAY
)
```

## Error Handling

```python
from unibase_agent_sdk import (
    UnibaseError,         # Base exception
    ConfigurationError,
    InitializationError,
    RegistryError,
    AgentNotFoundError,
    A2AProtocolError,
    AgentDiscoveryError,
    TaskExecutionError,
)

try:
    result = await client.execute(agent_url, message)
except AgentDiscoveryError:
    print("Could not discover agent")
except TaskExecutionError as e:
    print(f"Task failed: {e}")
```

## Examples

See the `examples/` directory:

- `wrap_any_agent.py` - Wrapping functions and classes
- `agent_message_format.py` - Working with AgentMessage format
- `streaming_agent.py` - Streaming responses
- `a2a_client.py` - Consuming agents
- `agent_registration_direct_mode.py` - Platform registration
- `agent_group_registration.py` - Creating agent groups with intelligent routing

## License

MIT
