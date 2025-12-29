# Unibase Agent Framework

A transparent SDK for building AI agents with integrated memory management and multi-SDK support.

## Features

- 🔄 **Transparent SDK Proxies**: Use Claude, OpenAI, LangChain as if using their native SDKs
- 📋 **Agent Registry**: Global management and discovery of agents via Unibase AIP SDK
- 🧠 **Unified Memory Management**: Integrate mem0, LangChain Memory, Zep, and more
- 📤 **Automatic DA Upload**: All memories automatically uploaded to Unibase DA
- 🔐 **Web3 Wallet Integration**: Built-in wallet creation and on-chain registration
- 🤝 **Agent Communication**: Agents can communicate via AIP protocol
- 🌐 **A2A Protocol**: Standard Agent-to-Agent communication with external agents
- ⚡ **Zero Redundancy**: Leverages Unibase AIP SDK for platform communication
- 📐 **Type Standardization**: A2A Protocol types as canonical standard for tasks, skills, and messages

## Installation

```bash
# Basic installation (includes AIP SDK dependency)
pip install unibase-agent-framework

# With Claude support
pip install unibase-agent-framework[claude]

# With all AI SDKs
pip install unibase-agent-framework[all]

# Development installation
pip install -e ".[dev]"
```

**Important Notes**:
- The framework uses the **Unibase AIP SDK** for agent registration and platform communication
- **A2A Protocol types** are the canonical standard for tasks, skills, and messages (see [TYPE_STANDARDIZATION.md](TYPE_STANDARDIZATION.md))

## Quick Start

```python
import asyncio
from unibase_agent_sdk import (
    AgentRegistry,
    MemoryManager,
    ClaudeAdapter,
    AgentType
)

async def main():
    # 1. Create Registry
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io"
    )
    
    # 2. Register Agent
    identity = await registry.register_agent(
        name="my-agent",
        agent_type=AgentType.CLAUDE,
        auto_create_wallet=True
    )
    
    # 3. Create Memory Manager
    memory = MemoryManager(
        membase_endpoint="https://membase.unibase.io",
        da_endpoint="https://da.unibase.io",
        agent_id=identity.agent_id
    )
    
    # 4. Create Agent
    agent = ClaudeAdapter(
        identity=identity,
        registry=registry,
        memory_manager=memory
    )
    await agent.initialize(api_key="sk-xxx")
    
    # 5. Use Native API (transparent!)
    response = await agent.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.content[0].text)
    
    # 6. Upload Memory to DA
    await memory.upload_to_da()
    
    await registry.close()

asyncio.run(main())
```

## Architecture

```
unibase_agent_sdk/
├── core/           # Base classes and types
├── registry/       # Agent registry, identity, wallet (uses AIP SDK for auth)
├── agents/         # Framework wrappers (CrewAI, AutoGen, Phidata, LlamaIndex)
├── memory/         # Memory management and middlewares
├── adapters/       # LLM adapters (Claude, OpenAI, LangChain)
├── a2a/            # A2A Protocol implementation
└── utils/          # Configuration and logging
```

### Dependencies

- **Unibase AIP SDK** (`aip.sdk`): Handles agent registration, discovery, and platform communication
- **httpx**: Direct HTTP communication for Membase and other services
- **pydantic**: Data validation and settings management

## Memory Middlewares

Add intelligent memory using various providers:

```python
from unibase_agent_sdk.memory.middlewares import Mem0Middleware

# Add mem0 for semantic memory
mem0 = Mem0Middleware(agent_id=identity.agent_id)
await mem0.initialize()
memory_manager.add_middleware(mem0)

# Use native mem0 API!
mem0.add("User prefers dark mode", user_id=identity.agent_id)
```

## Agent Communication

Agents can communicate via AIP protocol:

```python
# Alice sends message to Bob
response = await alice.send_to_agent(
    to_agent_id=bob.agent_id,
    message={"type": "question", "content": "Hello!"}
)
```

## A2A Protocol Support

Communicate with external agents using the standard [A2A protocol](https://a2a-protocol.org):

```python
from unibase_agent_sdk.a2a import A2AServer, Message, AgentCard

# Discover external A2A agents
card = await registry.discover_a2a_agent("https://agent.example.com")
print(f"Found: {card.name} with skills: {[s.name for s in card.skills]}")

# Send tasks to A2A agents
message = Message.user("What's the weather?")
task = await registry.send_a2a_task("https://agent.example.com", message)

# Expose your agent as A2A server
# Use your agent's public URL (from config or environment)
import os
agent_url = os.environ.get("AGENT_ENDPOINT_URL", "http://localhost:8000")
agent_card = registry.generate_agent_card_for(identity.agent_id, agent_url)
server = A2AServer(agent_card=agent_card, task_handler=my_handler)
await server.run()  # Serves /.well-known/agent.json
```

## Examples

See the `examples/` directory for complete examples:

### Framework Examples
- `basic_agent_registration.py` - Basic registration workflow
- `agent_with_mem0.py` - Using mem0 memory
- `agent_with_langchain_memory.py` - Using LangChain memory
- `multi_middleware_agent.py` - Multi-agent collaboration
- `full_workflow.py` - Agent communication
- `a2a_agent_example.py` - A2A protocol server/client

### AIP-Compatible Agents (`examples/aip_agents/`)
Production-ready example agents compatible with Unibase AIP:

- **Weather Agent** 🌤️ - Weather forecasting with A2A protocol support
- **Research Agent** 🔍 - Topic research with structured findings
- **Travel Agent** ✈️ - Travel planning with itinerary generation
- **Calculator Agent** 🔢 - Mathematical computation and evaluation

Run individual agents or launch all together:
```bash
# Run single agent
python examples/aip_agents/weather_agent.py

# Run all agents
python examples/aip_agents/launch_all_agents.py
```

Each agent runs as a standalone A2A server and can be discovered via `/.well-known/agent.json`. See [examples/aip_agents/README.md](examples/aip_agents/README.md) for details.

## License

MIT License
