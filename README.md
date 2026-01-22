# Unibase Agent SDK

**Build production-ready AI agents with A2A protocol compliance**

The Agent SDK provides a zero-boilerplate framework for exposing any Python function, class, or existing AI agent as a standardized A2A-compatible service that integrates seamlessly with the Unibase ecosystem.

## What Problem Does This Solve?

Building interoperable AI agents is complex. You need to:
- ❌ Implement protocol-compliant endpoints (JSON-RPC, SSE)
- ❌ Handle agent card discovery (`.well-known/agent.json`)
- ❌ Manage registration with agent platforms
- ❌ Deal with streaming, serialization, error handling
- ❌ Learn framework-specific abstractions

**Agent SDK eliminates all of this.** Wrap your code in one function call and get a production-ready, A2A-compliant agent server.

## Key Value Propositions

### 1. **Zero Boilerplate**
```python
# Your existing code
def translate(text: str, target_lang: str) -> str:
    return my_translation_model(text, target_lang)

# Expose as A2A agent - ONE function call
from unibase_agent_sdk import expose_as_a2a

server = expose_as_a2a("Translator", translate, port=8100)
server.run_sync()

# That's it. Your agent is now:
# ✓ A2A protocol compliant
# ✓ Auto-discoverable
# ✓ Integrated with AIP platform
# ✓ Ready for production
```

### 2. **Framework Agnostic**
Works with ANY Python code - no lock-in:
- ✅ Plain Python functions
- ✅ OpenAI, Anthropic, Google SDKs
- ✅ LangChain, LangGraph agents
- ✅ Custom ML models
- ✅ Existing agent frameworks

### 3. **A2A Protocol Compliance**
Automatic implementation of:
- Google A2A Agent Card (`.well-known/agent.json`)
- JSON-RPC 2.0 endpoints (`/a2a`)
- Server-Sent Events for streaming (`/a2a/stream`)
- Task and skill definitions
- Error handling and status codes

### 4. **Platform Integration**
Seamless integration with Unibase AIP:
- Auto-registration with agent registry
- Payment collection via X402
- Execution tracking and logging
- Gateway routing for remote access

## Installation

Install from source:

```bash
# Clone the SDK repository
git clone https://github.com/unibaseio/unibase-agent-sdk.git
cd unibase-agent-sdk

# Install in editable mode
uv pip install -e .
```

## Quick Start

### Expose Any Function

```python
from unibase_agent_sdk import expose_as_a2a

def calculator(expression: str) -> str:
    """Safe calculator that evaluates math expressions."""
    result = eval(expression, {"__builtins__": {}}, {})
    return f"Result: {result}"

# One line to create an A2A agent server
server = expose_as_a2a(
    name="Calculator",
    handler=calculator,
    description="Evaluates mathematical expressions",
    port=8100
)

server.run_sync()
```

**Your agent is now live at:**
- `http://localhost:8100/.well-known/agent.json` - Agent Card
- `http://localhost:8100/a2a` - JSON-RPC endpoint
- `http://localhost:8100/health` - Health check

### Async & Streaming Support

```python
from typing import AsyncIterator

# Async handler
async def llm_agent(prompt: str) -> str:
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

server = expose_as_a2a("LLM Agent", llm_agent, port=8100)
await server.run()

# Streaming handler
async def streaming_agent(text: str) -> AsyncIterator[str]:
    for word in text.split():
        yield word + " "
        await asyncio.sleep(0.1)

server = expose_as_a2a(
    "Streaming Agent",
    streaming_agent,
    streaming=True,
    port=8100
)
```

### Register with AIP Platform

```python
# Automatic platform registration
server = expose_as_a2a(
    name="My Agent",
    handler=my_handler,
    port=8100,
    user_id="user:0x123...",        # Your user ID
    auto_register=True               # Auto-register with AIP
)

# Now discoverable via AIP platform:
# - Other applications can find your agent
# - Automatic payment collection enabled
# - Execution metrics tracked
```

## Core Concepts

### 1. Wrap Any Code

The SDK provides multiple wrapping strategies:

**Functions:**
```python
def process(text: str) -> str:
    return text.upper()

expose_as_a2a("Processor", process)
```

**Classes:**
```python
class MyAgent:
    def process(self, text: str) -> str:
        return text.upper()

agent = MyAgent()
wrapper = wrap_agent(agent, "MyAgent", method="process")
wrapper.serve_sync(port=8100)
```

**Existing LLM SDKs:**
```python
# Works with OpenAI, Anthropic, Google, etc.
async def claude_handler(prompt: str) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

expose_as_a2a("Claude Agent", claude_handler)
```

### 2. A2A Protocol Endpoints

Every agent automatically gets:

| Endpoint | Protocol | Purpose |
|----------|----------|---------|
| `/.well-known/agent.json` | GET | Agent Card (discovery) |
| `/a2a` | POST | Execute task (JSON-RPC 2.0) |
| `/a2a/stream` | POST | Stream task (SSE) |
| `/health` | GET | Health check |

### 3. Agent-to-Agent Communication

Agents can call other agents through AIP:

```python
from aip_sdk.types import AgentContext

async def handle_task(task: Task, message: Message, context: AgentContext):
    # Call another agent
    result = await context.call_agent_with_intent(
        agent_id="weather.forecast",
        intent="Get weather for Tokyo",
        reason="User requested weather information"
    )

    # All calls go through AIP for:
    # - Payment tracking
    # - Caller chain tracking
    # - Automatic logging

    return result.output
```

## Advanced Usage

### Multiple Skills

```python
class MultiSkillAgent:
    def translate(self, text: str, lang: str) -> str:
        return f"Translated to {lang}: {text}"

    def summarize(self, text: str) -> str:
        return f"Summary: {text[:100]}"

agent = MultiSkillAgent()
wrapper = wrap_agent(
    agent,
    "Multi-Skill Agent",
    methods=["translate", "summarize"]  # Expose multiple skills
)
wrapper.serve_sync(port=8100)
```

### Custom Skills Definition

```python
from a2a.types import AgentSkill

skills = [
    AgentSkill(
        id="weather.forecast",
        name="Weather Forecast",
        description="Get weather forecast for a location",
        tags=["weather", "forecast"],
        examples=["Weather in NYC", "Forecast for London"]
    )
]

server = expose_as_a2a(
    name="Weather Agent",
    handler=weather_handler,
    skills=skills
)
```

### Pricing Configuration

```python
from aip_sdk.types import CostModel

server = expose_as_a2a(
    name="Premium Agent",
    handler=handler,
    cost_model=CostModel(
        base_call_fee=0.05,              # $0.05 per call
        input_cost_per_token=0.00001,
        output_cost_per_token=0.00003
    ),
    user_id="user:0x123...",
    auto_register=True
)
```

## A2A Client (Consuming Agents)

The SDK also includes a client for consuming other A2A agents:

```python
from unibase_agent_sdk import A2AClient
from a2a.types import Message, Role, TextPart

async with A2AClient() as client:
    # Discover agent
    agent = await client.discover_agent("http://localhost:8100")
    print(f"Agent: {agent.name}")
    print(f"Skills: {agent.skills}")

    # Execute task
    message = Message(
        role=Role.USER,
        parts=[TextPart(text="Calculate 2 + 2")]
    )
    task = await client.send_task(
        agent_url="http://localhost:8100",
        message=message
    )

    # Stream execution
    async for response in client.stream_task(
        agent_url="http://localhost:8100",
        message=message
    ):
        if response.message:
            print(response.message)
```

## Architecture

```
┌──────────────────────────────────────┐
│  Your Code (function/class/agent)   │
└───────────────┬──────────────────────┘
                │
                │ expose_as_a2a() / wrap_agent()
                │
                ▼
┌──────────────────────────────────────┐
│     Agent SDK (This Package)         │
│  ✓ A2A Protocol Implementation       │
│  ✓ JSON-RPC 2.0 Server               │
│  ✓ SSE Streaming                     │
│  ✓ Agent Card Generation             │
└───────────────┬──────────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
┌─────────────┐     ┌──────────────┐
│  A2A Client │     │ AIP Platform │
│  (Direct)   │     │ (Registry)   │
└─────────────┘     └──────────────┘
```

## API Reference

### Core Functions

```python
expose_as_a2a(
    name: str,              # Agent name
    handler: Callable,      # Your function/handler
    port: int = 8000,       # Server port
    description: str = None,
    skills: List[AgentSkill] = None,
    streaming: bool = False,
    user_id: str = None,    # For AIP registration
    auto_register: bool = True,
    cost_model: CostModel = None
) -> A2AServer

wrap_agent(
    agent: Any,            # Your agent instance
    name: str,             # Agent name
    method: str = None,    # Single method to expose
    methods: List[str] = None  # Multiple methods
) -> AgentWrapper
```

### Classes

- `A2AServer` - A2A protocol server
- `A2AClient` - Client for consuming A2A agents
- `AgentWrapper` - Wrapper for class-based agents
- `StreamResponse` - Streaming response wrapper

## Development

```bash
# Install in editable mode
uv pip install -e .

# With AIP SDK dependency (local development)
# Edit pyproject.toml:
[tool.uv.sources]
unibase-aip-sdk = { path = "../unibase-aip-sdk", editable = true }
```

## Examples

See `examples/` directory:
- `wrap_any_agent.py` - Wrapping functions and classes
- `streaming_agent.py` - Streaming responses with SSE
- `a2a_client.py` - Consuming A2A agents
- `llm_sdk_integrations.py` - OpenAI, Anthropic, Google integrations
- `agent_message_format.py` - Working with AgentMessage format
- `agent_registration_direct_mode.py` - AIP platform registration

## Why Use This SDK?

| Without Agent SDK | With Agent SDK |
|-------------------|----------------|
| Implement JSON-RPC server | ✅ Automatic |
| Create SSE streaming | ✅ Automatic |
| Generate Agent Card | ✅ Automatic |
| Handle A2A protocol | ✅ Automatic |
| Register with AIP | ✅ One parameter |
| Framework-specific code | ✅ Framework agnostic |
| Days of development | ✅ Minutes |

## Learn More

- [Unibase Documentation](https://docs.unibase.com)
- [A2A Protocol Specification](https://docs.google.com/document/d/1pKUa_stglbV7cPLftp7m700dTPz6u7hVNZGEDNjBqRk)
- [Agent Development Guide](https://docs.unibase.com/agents)
- [AIP Platform Integration](https://docs.unibase.com/aip)

## License

MIT
