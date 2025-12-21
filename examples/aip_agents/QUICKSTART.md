# Quick Start Guide - AIP Agents

Get started with the AIP-compatible example agents in 5 minutes.

## Step 1: Install Dependencies

```bash
cd /home/ubuntu/unibase-agent-sdk
pip install -e .
pip install fastapi uvicorn
```

## Step 2: Start the Agents

### Option A: Start All Agents at Once (Recommended)

```bash
python examples/aip_agents/launch_all_agents.py
```

This will start all 4 agents on ports 8001-8004.

### Option B: Start Individual Agents

```bash
# Terminal 1 - Weather Agent
python examples/aip_agents/weather_agent.py

# Terminal 2 - Research Agent
python examples/aip_agents/research_agent.py

# Terminal 3 - Travel Agent
python examples/aip_agents/travel_agent.py

# Terminal 4 - Calculator Agent
python examples/aip_agents/calculator_agent.py
```

## Step 3: Test the Agents

### Quick Test (All Agents)

In a new terminal:

```bash
python examples/aip_agents/test_agent_client.py
```

### Test Individual Agent

```bash
# Test weather agent
python examples/aip_agents/test_agent_client.py --agent weather

# Test calculator
python examples/aip_agents/test_agent_client.py --agent calculator
```

### Manual cURL Tests

```bash
# View Agent Card
curl http://localhost:8001/.well-known/agent.json | jq

# Send weather query
curl -X POST http://localhost:8001/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "Weather for Tokyo for 3 days"}]
      }
    },
    "id": 1
  }' | jq

# Calculate something
curl -X POST http://localhost:8004/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "Calculate sqrt(256) + 10"}]
      }
    },
    "id": 1
  }' | jq
```

## Step 4: Use in Python

```python
import asyncio
from unibase_agent_sdk.a2a import A2AClient, Message

async def main():
    async with A2AClient() as client:
        # Discover agent
        card = await client.discover_agent("http://localhost:8001")
        print(f"Found: {card.name}")

        # Send task
        message = Message.user("Weather for London for 5 days")
        task = await client.send_task("http://localhost:8001", message)

        # Get response
        for msg in task.history:
            if msg.role.value == "agent":
                for part in msg.parts:
                    if hasattr(part, "text"):
                        print(part.text)

asyncio.run(main())
```

## Agent Endpoints

Once running, agents are available at:

| Agent | Port | Agent Card | A2A Endpoint |
|-------|------|------------|--------------|
| Weather | 8001 | http://localhost:8001/.well-known/agent.json | http://localhost:8001/a2a |
| Research | 8002 | http://localhost:8002/.well-known/agent.json | http://localhost:8002/a2a |
| Travel | 8003 | http://localhost:8003/.well-known/agent.json | http://localhost:8003/a2a |
| Calculator | 8004 | http://localhost:8004/.well-known/agent.json | http://localhost:8004/a2a |

## Example Queries

### Weather Agent
- "Weather for New York for 3 days"
- "What's the weather in Tokyo?"
- "Weather forecast for Paris"

### Research Agent
- "Research quantum computing with detailed depth"
- "Investigate climate change"
- "Study blockchain technology"

### Travel Agent
- "Plan a trip to Barcelona in July with $2500 budget"
- "Travel to Tokyo for 7 days with food and culture interests"
- "Budget vacation to Thailand"

### Calculator Agent
- "Calculate 25 * 4 + sqrt(144)"
- "What is sin(pi/4)?"
- "Evaluate log(100) + e^2"

## Troubleshooting

### Port Already in Use

If you get "port already in use" error:

```bash
# Find process using port 8001
lsof -ti:8001

# Kill process
kill -9 $(lsof -ti:8001)
```

### Import Errors

Make sure you're in the SDK directory:

```bash
cd /home/ubuntu/unibase-agent-sdk
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Agent Not Responding

1. Check if agent is running: `curl http://localhost:8001/health`
2. View agent logs in the terminal where it's running
3. Restart the agent

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [integration examples](../../README.md#examples)
- Learn about [A2A Protocol](https://a2a-protocol.org)
- Explore the [Unibase AIP Documentation](https://docs.unibase.io)

## Support

For issues or questions:
- GitHub Issues: https://github.com/unibase/unibase-agent-sdk/issues
- Documentation: https://docs.unibase.io
