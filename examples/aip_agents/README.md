# AIP-Compatible Example Agents

This directory contains example agents that are compatible with the Unibase AIP (Agent Integration Protocol) and implement the A2A (Agent-to-Agent) protocol specification.

## Overview

These agents demonstrate how to use the Unibase Agent SDK to create intelligent agents that can:

- Be discovered via the A2A protocol (Agent Cards at `/.well-known/agent.json`)
- Communicate using JSON-RPC 2.0 over HTTP
- Process tasks with streaming support
- Register with the Unibase Agent Registry
- Integrate with the broader AIP ecosystem

## Available Agents

### 🌤️ Weather Agent (`weather_agent.py`)

Provides weather forecasts and current conditions for locations.

- **Port:** 8001
- **Skills:** Weather forecasting
- **Example queries:**
  - "Weather for San Francisco for 5 days"
  - "What's the weather in Tokyo?"
  - "Weather forecast for London"

### 🔍 Research Agent (`research_agent.py`)

Researches topics and provides structured findings with sources and recommendations.

- **Port:** 8002
- **Skills:** Research & investigation
- **Example queries:**
  - "Research artificial intelligence with comprehensive depth"
  - "Investigate quantum computing"
  - "Study climate change in detail"

### ✈️ Travel Agent (`travel_agent.py`)

Plans travel itineraries including flights, hotels, and activities.

- **Port:** 8003
- **Skills:** Travel planning
- **Example queries:**
  - "Plan a trip to Paris in June with $3000 budget"
  - "Travel to Tokyo for 7 days with culture and food interests"
  - "Budget trip to Barcelona"

### 🔢 Calculator Agent (`calculator_agent.py`)

Performs mathematical calculations and evaluations.

- **Port:** 8004
- **Skills:** Mathematical computation
- **Example queries:**
  - "Calculate 2 + 2"
  - "What is sqrt(144)?"
  - "Evaluate sin(pi/2)"

## Running the Agents

### Prerequisites

```bash
# Install dependencies
pip install -e .

# Or install with A2A support
pip install fastapi uvicorn
```

### Option 1: Run Individual Agents

Run any agent independently:

```bash
# Weather Agent
python examples/aip_agents/weather_agent.py

# Research Agent
python examples/aip_agents/research_agent.py

# Travel Agent
python examples/aip_agents/travel_agent.py

# Calculator Agent
python examples/aip_agents/calculator_agent.py
```

### Option 2: Run All Agents Together

Launch all agents simultaneously:

```bash
python examples/aip_agents/launch_all_agents.py
```

This will start all four agents on different ports (8001-8004).

## Testing the Agents

### View Agent Card

Each agent publishes its capabilities via an Agent Card:

```bash
# Weather Agent
curl http://localhost:8001/.well-known/agent.json

# Research Agent
curl http://localhost:8002/.well-known/agent.json
```

### Send a Task (JSON-RPC)

Send a task to an agent using the A2A protocol:

```bash
# Send to Weather Agent
curl -X POST http://localhost:8001/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "Weather for New York for 3 days"
          }
        ]
      }
    },
    "id": 1
  }'

# Send to Calculator Agent
curl -X POST http://localhost:8004/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [
          {
            "type": "text",
            "text": "Calculate sqrt(144) + 5"
          }
        ]
      }
    },
    "id": 1
  }'
```

### Using the A2A Client

You can also use the Unibase A2A client to interact with agents:

```python
import asyncio
from unibase_agent_sdk.a2a import A2AClient, Message

async def test_agent():
    async with A2AClient() as client:
        # Discover agent
        card = await client.discover_agent("http://localhost:8001")
        print(f"Found: {card.name}")
        print(f"Skills: {[s.name for s in card.skills]}")

        # Send task
        message = Message.user("Weather for Seattle for 5 days")
        task = await client.send_task("http://localhost:8001", message)

        # Get response
        for msg in task.history:
            if msg.role.value == "agent":
                for part in msg.parts:
                    if hasattr(part, "text"):
                        print(part.text)

asyncio.run(test_agent())
```

## Integration with Unibase AIP

These agents are designed to work seamlessly with the Unibase AIP ecosystem:

### Registry Integration

All agents automatically register with the Unibase Agent Registry when started:

```python
from unibase_agent_sdk import AgentRegistry

registry = AgentRegistry(
    aip_endpoint="https://aip.unibase.io",
    membase_endpoint="https://membase.unibase.io"
)
```

### Agent-to-Agent Communication

Agents can discover and communicate with each other through the registry:

```python
# Weather agent can call research agent
other_agent = await registry.get_agent_by_skill("research.investigate")
result = await registry.send_message_to_agent(
    from_agent_id=weather_agent.agent_id,
    to_agent_id=other_agent.agent_id,
    message={"query": "Research weather patterns"}
)
```

### Memory Integration

Agents support memory middleware for persistent conversation history:

```python
from unibase_agent_sdk.memory import MemoryManager
from unibase_agent_sdk.memory.middlewares import Mem0Middleware

# Attach memory to agent
memory_manager = MemoryManager()
await memory_manager.add_middleware(Mem0Middleware(api_key="your-key"))

agent.attach_memory(memory_manager)
```

## Architecture

Each agent follows this structure:

```
Agent Class
  ├── __init__(agent_id)
  ├── handle_task(task, message) -> AsyncIterator[StreamResponse]
  │     └── Core agent logic
  ├── _extract_*() methods
  │     └── Parse user input
  └── _format_*() methods
        └── Format responses

Factory Function
  ├── create_*_agent(registry) -> (AgentCard, Agent)
  └── Returns agent card and instance

Main Function
  └── Standalone A2A server launcher
```

## Migration from AIP Examples

These agents were migrated from the original `unibase-aip/examples` and adapted to use:

1. **Unibase Agent SDK** instead of AIP domain classes
2. **A2A Protocol** for standardized agent communication
3. **AgentRegistry** for agent discovery and coordination
4. **Async/await** patterns throughout
5. **Streaming responses** via AsyncIterator

### Key Differences

| Original (AIP) | Migrated (SDK) |
|----------------|----------------|
| `Agent` base class | Agent class with `handle_task` |
| `perform_task()` | `handle_task()` with streaming |
| `AgentInvocationResult` | `StreamResponse` with `Message` |
| `ERC8004Identity` | `AgentIdentity` from registry |
| `ClaudeSkillTemplate` | A2A `Skill` in `AgentCard` |
| `AgentService` | `A2AServer` |

## Extending the Agents

To create your own AIP-compatible agent:

1. **Define Agent Class:**
```python
class MyAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def handle_task(self, task: Task, message: Message):
        # Process message
        input_text = extract_text(message)
        result = await self.process(input_text)

        # Yield response
        yield StreamResponse(message=Message.agent(result))
```

2. **Create Factory Function:**
```python
async def create_my_agent(registry):
    identity = await registry.register_agent(
        name="My Agent",
        agent_type=AgentType.CUSTOM,
        metadata={"description": "My custom agent"}
    )

    agent = MyAgent(identity.agent_id)

    agent_card = AgentCard(
        name="My Agent",
        description="Description",
        url="http://localhost:8005",
        skills=[Skill(id="my.skill", name="My Skill", ...)]
    )

    return agent_card, agent
```

3. **Add Main Function:**
```python
async def main():
    registry = AgentRegistry(offline_mode=True)
    agent_card, agent = await create_my_agent(registry)

    server = A2AServer(
        agent_card=agent_card,
        task_handler=agent.handle_task,
        port=8005
    )

    await server.run()
```

## Resources

- [A2A Protocol Specification](https://a2a-protocol.org)
- [Unibase Agent SDK Documentation](../../README.md)
- [Unibase AIP Documentation](https://docs.unibase.io)
- [Example Usage](../a2a_agent_example.py)

## License

These examples are part of the Unibase Agent SDK and follow the same license.
