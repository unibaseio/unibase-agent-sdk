# Unibase Agent SDK

Framework for building A2A-compatible AI agents.

## Installation

```bash
pip install unibase-agent-sdk
```

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

## A2A Server

For more control, use `A2AServer` directly:

```python
from unibase_agent_sdk import A2AServer, StreamResponse
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, Task, Message

async def handle_task(task: Task, message: Message):
    text = message.parts[0].text
    response_msg = create_text_message("Processed: " + text, Role.agent)
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
| `DIRECT` | Agent is publicly accessible |
| `GATEWAY` | Agent behind NAT/firewall, uses gateway routing |

## Agent Registry Client

For programmatic platform interaction:

```python
from unibase_agent_sdk import AgentRegistry

registry = AgentRegistry(
    platform_url="http://localhost:8001",
    gateway_url="http://localhost:8080"
)

# Register agent
await registry.register(
    agent_id="my.agent",
    name="My Agent",
    url="http://localhost:8100"
)

# Discover agents
agents = await registry.list_agents()

# Call another agent
result = await registry.call_agent(
    agent_id="other.agent",
    message="Hello"
)
```

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
- `streaming_agent.py` - Streaming responses
- `a2a_client.py` - Consuming agents
- `agent_registration_direct_mode.py` - Platform registration

## License

MIT
