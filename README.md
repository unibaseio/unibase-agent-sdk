# Unibase Agent SDK

Framework for building A2A-compatible AI agents.

## Installation

```bash
pip install unibase-agent-sdk
```

## Development

```bash
uv pip install -e .
```

For local development with both SDKs, update `pyproject.toml`:

```toml
[tool.uv.sources]
unibase-aip-sdk = { path = "../unibase-aip-sdk", editable = true }
```

> **Note:** This package depends on `a2a-sdk` (Google's Agent-to-Agent Protocol SDK). If you have an unrelated package named `a2a` (v0.44) installed, it will conflict. Uninstall it first with `pip uninstall a2a`.

## Quick Start

### Expose a Function

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

### Async Handler

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

### Streaming

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

## Platform Registration

```python
server = expose_as_a2a(
    name="My Agent",
    handler=my_handler,
    port=8100,
    user_id="user:0x123...",
    auto_register=True
)
```

## Agent-to-Agent Calling

```python
from aip_sdk.types import AgentContext

async def handle_task(task: Task, message: Message, context: AgentContext):
    agent_message = AgentMessage.from_a2a_message(message)

    # Call another agent
    result = await context.call_agent_with_intent(
        agent_id="weather.forecast",
        intent="Get weather for Tokyo",
        reason="User requested weather information"
    )

    return result.output
```

## A2A Protocol Endpoints

When you expose an agent, these endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/.well-known/agent.json` | GET | Agent Card (discovery) |
| `/a2a` | POST | Execute task (JSON-RPC) |
| `/a2a/stream` | POST | Stream task (SSE) |
| `/health` | GET | Health check |

## License

MIT
