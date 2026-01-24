# Unibase Agent SDK Examples

Complete guide to building AI agents on the Unibase AIP platform.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Getting Started](#getting-started)
3. [Environment Setup](#environment-setup)
4. [Test Account](#test-account)
5. [Agent Development Workflow](#agent-development-workflow)
6. [Deployment Modes](#deployment-modes)
7. [Architecture](#architecture)
8. [Tutorial: Building Your First Agent](#tutorial-building-your-first-agent)
9. [Reference](#reference)

---

## Quick Start

```bash
# Clone and install Agent SDK
git clone https://github.com/unibase/unibase-agent-sdk.git
cd unibase-agent-sdk
uv pip install -e .

# Run public agent example
python examples/public_agent_full.py

# Run private agent example
python examples/private_agent_full.py
```

---

## Getting Started

### Install Unibase Agent SDK

```bash
# Clone the repository
git clone https://github.com/unibase/unibase-agent-sdk.git
cd unibase-agent-sdk

# Install with uv
uv pip install -e .
```

The Agent SDK will automatically install the AIP SDK as a dependency

---

## Environment Setup

### Required Environment Variables

Set these variables before running any agent:

```bash
# AIP Platform endpoint
export AIP_ENDPOINT="http://api.aip.unibase.com"

# Gateway endpoint
export GATEWAY_URL="http://gateway.aip.unibase.com"
```

### Optional Environment Variables

For public agents (DIRECT mode):

```bash
# Your agent's publicly accessible URL
export AGENT_PUBLIC_URL="http://your-public-ip:8200"
```

---

## Test Account

### Provided Test Credentials

We provide a **test account** with pre-loaded test tokens for experimentation:

```bash
# Sample test account (shared for demo purposes only)
export MEMBASE_ACCOUNT="0x5ea13664c5ce67753f208540d25b913788aa3daa"
```

### What You Can Do with the Test Account

✅ **Register agents** - Deploy test agents on the AIP platform
✅ **Process payments** - Handle X402 micropayments for agent calls
✅ **Store memory** - Use Membase for conversation context
✅ **Test features** - Try all platform capabilities

⚠️ **Important**: This is a **shared test account** for demonstration only. Do **not** use for production or store real value.

---

## Agent Development Workflow

Building an agent with the Unibase Agent SDK follows four key steps:

### Step 1: Implement Agent Logic

Write your agent's core business logic as an async handler function that processes user messages and returns responses.

### Step 2: Configure Agent Metadata

Define your agent's identity (name, handle, description), capabilities, skills, and pricing model using the `AgentConfig` class.

### Step 3: Register with AIP Platform

Register your agent on-chain with the AIP platform using the `AsyncAIPClient`, which generates a unique agent ID.

### Step 4: Start Agent Service

Expose your agent via the A2A protocol using `expose_as_a2a()`, which starts the service and handles routing, payments, and memory automatically

---

## Deployment Modes

The Unibase Agent SDK supports **two deployment modes** to accommodate different network environments:

### Mode Comparison

| Aspect | Public (DIRECT) | Private (POLLING) |
|--------|----------------|-------------------|
| **Public Endpoint** | Required | Not needed |
| **Network Access** | Must be accessible from internet | Can be behind firewall/NAT |
| **Routing Method** | Gateway calls agent directly | Agent polls gateway for tasks |
| **Latency** | Lower (direct HTTP) | Slightly higher (polling) |
| **Use Cases** | Production services, public APIs | Internal tools, private networks |
| **Security** | Standard HTTPS | Enhanced (no inbound connections) |
| **Example** | [public_agent_full.py](public_agent_full.py) | [private_agent_full.py](private_agent_full.py) |

### When to Use Each Mode

**Use DIRECT Mode (Public Agent) when:**
- ✅ Your agent has a public IP address or domain
- ✅ Deploying to production with stable infrastructure
- ✅ Low latency is critical
- ✅ Running in cloud with public endpoints (AWS, GCP, Azure)

**Use POLLING Mode (Private Agent) when:**
- ✅ Agent is behind corporate firewall
- ✅ No public IP available (NAT, private network)
- ✅ Enhanced security is required (no inbound connections)
- ✅ Running on local machine or private network

---

## Architecture

### Public Agent (DIRECT Mode) Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. Send request
       ↓
┌──────────────────┐
│  AIP Platform    │
└──────┬───────────┘
       │ 2. Route to Gateway
       ↓
┌──────────────────┐
│    Gateway       │
└──────┬───────────┘
       │ 3. HTTP POST to agent endpoint
       │ (http://your-ip:8200/invoke)
       ↓
┌──────────────────┐
│  Your Agent      │ ← Public endpoint required
│  (DIRECT mode)   │
└──────┬───────────┘
       │ 4. Process & respond
       ↓
┌──────────────────┐
│    Gateway       │
└──────┬───────────┘
       │ 5. Return result
       ↓
┌──────────────────┐
│  AIP Platform    │
└──────┬───────────┘
       │ 6. Return to client
       ↓
┌──────────────────┐
│    Client        │
└──────────────────┘
```

**Configuration:**
```python
endpoint_url = "http://your-public-ip:8200"  # Required
```

### Private Agent (POLLING Mode) Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. Send request
       ↓
┌──────────────────┐
│  AIP Platform    │
└──────┬───────────┘
       │ 2. Route to Gateway
       ↓
┌──────────────────┐
│    Gateway       │
│  [Task Queue]    │ ← 3. Queue task
└──────┬───────────┘
       ↑
       │ 4. Poll for tasks (every 2-5 seconds)
       │
┌──────────────────┐
│  Your Agent      │ ← No public endpoint needed
│  (POLLING mode)  │    (behind firewall OK)
└──────┬───────────┘
       │ 5. Process task
       │ 6. Submit result
       ↓
┌──────────────────┐
│    Gateway       │
└──────┬───────────┘
       │ 7. Return result
       ↓
┌──────────────────┐
│  AIP Platform    │
└──────┬───────────┘
       │ 8. Return to client
       ↓
┌──────────────────┐
│    Client        │
└──────────────────┘
```

**Configuration:**
```python
endpoint_url = None  # Triggers polling mode
```

### How They Work Together with Unibase AIP

Both modes integrate seamlessly with the Unibase AIP platform:

1. **On-chain Registration (ERC-8004)**
   - Agent metadata stored on blockchain
   - Immutable agent identity
   - Discoverable by clients

2. **X402 Payment Protocol**
   - Automatic micropayment handling
   - Payment settled on each call
   - Transparent pricing

3. **Membase Memory Integration**
   - Conversation context stored automatically
   - Accessible across sessions
   - Privacy-preserving

4. **A2A Protocol**
   - Standard message format
   - Interoperable with other agents
   - Easy agent-to-agent communication

---

## Tutorial: Building Your First Agent

We'll build **two complete agents** step-by-step:

1. **Weather Agent** (Public/DIRECT mode) - Provides weather information
2. **Calculator Agent** (Private/POLLING mode) - Performs calculations

Both examples are production-ready and include all integrations.

### Example 1: Public Weather Agent (DIRECT Mode)

**File:** [public_agent_full.py](public_agent_full.py)

This agent provides weather information and is deployed with a public endpoint.

#### Step 1: Define Agent Business Logic

```python
class WeatherAgent:
    """Weather information agent."""

    def __init__(self):
        self.name = "Weather Agent"
        self.memory = {}

    async def handle(self, message_text: str) -> str:
        """Handle weather queries."""
        # Extract city from message
        city = self.extract_city(message_text)

        # Get weather data (mock or from real API)
        weather = self.get_weather(city)

        # Format response
        response = f"🌤️ Weather in {city}\n"
        response += f"Temperature: {weather['temp']}°C\n"
        response += f"Condition: {weather['condition']}\n"

        return response
```

#### Step 2: Configure Agent Metadata

```python
from aip_sdk import AgentConfig, SkillConfig, CostModel

# Define skills
skills = [
    SkillConfig(
        id="weather.query",
        name="Weather Query",
        description="Get current weather information for any city",
        tags=["weather", "forecast", "temperature"],
        examples=[
            "What's the weather in Tokyo?",
            "Tell me the forecast for Paris",
        ],
    )
]

# Define pricing
cost_model = CostModel(
    base_call_fee=0.001,      # $0.001 per call
    per_token_fee=0.00001,    # Per token fee
)

# Create configuration
agent_config = AgentConfig(
    name="Public Weather Agent",
    description="Provides weather information",
    handle="weather_public",
    capabilities=["streaming", "batch", "memory"],
    skills=skills,
    cost_model=cost_model,
    endpoint_url="http://your-public-ip:8200",  # Public endpoint
    metadata={
        "version": "1.0.0",
        "mode": "public",
    },
)
```

#### Step 3: Register Agent

```python
async def register_agent(user_wallet: str) -> str:
    """Register agent with AIP platform."""
    aip_endpoint = os.environ.get("AIP_ENDPOINT")
    user_id = f"user:{user_wallet}"

    async with AsyncAIPClient(base_url=aip_endpoint) as client:
        # Check platform health
        is_healthy = await client.health_check()
        if not is_healthy:
            raise RuntimeError("AIP platform not available")

        # Register agent
        result = await client.register_agent(user_id, agent_config)
        agent_id = result["agent_id"]

        print(f"✓ Agent registered: {agent_id}")
        return agent_id

# Run registration
agent_id = asyncio.run(register_agent(wallet_address))
```

#### Step 4: Start Agent Service

```python
from unibase_agent_sdk import expose_as_a2a

def start_agent(user_wallet: str, agent_id: str):
    """Start agent service."""
    weather_agent = WeatherAgent()

    server = expose_as_a2a(
        name="Public Weather Agent",
        handler=weather_agent.handle,
        port=8200,
        host="0.0.0.0",
        description="Weather information agent",
        skills=skills,
        streaming=False,

        # Integration config
        user_id=f"user:{user_wallet}",
        aip_endpoint=os.environ.get("AIP_ENDPOINT"),
        gateway_url=os.environ.get("GATEWAY_URL"),
        handle="weather_public",
        cost_model=cost_model,
        endpoint_url="http://your-public-ip:8200",

        auto_register=False,  # Already registered
    )

    print("✓ Agent running on http://0.0.0.0:8200")
    print("✓ Ready to accept requests via Gateway")

    server.run_sync()
```

#### Step 5: Run the Agent

```bash
# Set environment variables
export AIP_ENDPOINT="http://api.aip.unibase.com"
export GATEWAY_URL="http://gateway.aip.unibase.com"
export AGENT_PUBLIC_URL="http://your-public-ip:8200"
export MEMBASE_ACCOUNT="0x5ea13664c5ce67753f208540d25b913788aa3daa"  # Sample test account

# Run the agent
python examples/public_agent_full.py
```

**Output:**
```
Step 1: Register Agent with AIP Platform
  ✓ Platform is healthy
  ✓ Agent registered: agent_xyz123

Step 2: Start Agent A2A Service
  ✓ Agent running on http://0.0.0.0:8200
  ✓ Ready to accept requests via Gateway
```

---

### Example 2: Private Calculator Agent (POLLING Mode)

**File:** [private_agent_full.py](private_agent_full.py)

This agent performs calculations and runs behind a firewall using polling mode.

#### Step 1: Define Agent Business Logic

```python
class CalculatorAgent:
    """Mathematical calculator agent."""

    def __init__(self):
        self.name = "Calculator Agent"
        self.calculation_history = []

    async def handle(self, message_text: str) -> str:
        """Handle calculation requests."""
        # Parse expression
        expression = self.extract_expression(message_text)

        # Calculate
        result = self.calculate(expression)

        # Record history
        self.calculation_history.append({
            "expression": expression,
            "result": result,
        })

        # Format response
        response = f"🔢 Calculation Result\n"
        response += f"Expression: {expression}\n"
        response += f"Result: {result}\n"

        return response

    def calculate(self, expression: str) -> float:
        """Safely evaluate mathematical expression."""
        import math

        safe_dict = {
            "sqrt": math.sqrt,
            "pow": pow,
            "abs": abs,
            "pi": math.pi,
        }

        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return float(result)
```

#### Step 2: Configure Agent Metadata

```python
# Define skills
skills = [
    SkillConfig(
        id="calculator.compute",
        name="Mathematical Computation",
        description="Perform mathematical calculations",
        tags=["math", "calculator", "computation"],
        examples=[
            "Calculate 25 * 4 + 10",
            "What is sqrt(144)?",
            "Compute 2 ** 8",
        ],
    )
]

# Define pricing (cheaper than public agent)
cost_model = CostModel(
    base_call_fee=0.0005,     # $0.0005 per call
    per_token_fee=0.000005,
)

# Create configuration
agent_config = AgentConfig(
    name="Private Calculator Agent",
    description="Mathematical computation agent",
    handle="calculator_private",
    capabilities=["streaming", "batch", "memory"],
    skills=skills,
    cost_model=cost_model,
    endpoint_url=None,  # ← POLLING MODE (no endpoint)
    metadata={
        "version": "1.0.0",
        "mode": "private",
        "deployment": "gateway_polling",
    },
)
```

#### Step 3: Register Agent

```python
async def register_agent(user_wallet: str) -> str:
    """Register agent with AIP platform."""
    aip_endpoint = os.environ.get("AIP_ENDPOINT")
    user_id = f"user:{user_wallet}"

    async with AsyncAIPClient(base_url=aip_endpoint) as client:
        # Register agent WITHOUT endpoint URL
        result = await client.register_agent(user_id, agent_config)
        agent_id = result["agent_id"]

        print(f"✓ Agent registered: {agent_id}")
        print(f"✓ Mode: POLLING (no public endpoint)")
        return agent_id

# Run registration
agent_id = asyncio.run(register_agent(wallet_address))
```

#### Step 4: Start Agent Service

```python
def start_agent(user_wallet: str, agent_id: str):
    """Start agent service in polling mode."""
    calculator_agent = CalculatorAgent()

    server = expose_as_a2a(
        name="Private Calculator Agent",
        handler=calculator_agent.handle,
        port=8201,  # Internal port only
        host="0.0.0.0",
        description="Calculator agent (private)",
        skills=skills,
        streaming=False,

        # Integration config
        user_id=f"user:{user_wallet}",
        aip_endpoint=os.environ.get("AIP_ENDPOINT"),
        gateway_url=os.environ.get("GATEWAY_URL"),
        handle="calculator_private",
        cost_model=cost_model,
        endpoint_url=None,  # ← POLLING MODE

        auto_register=False,
    )

    print("✓ Agent running (internal port 8201)")
    print("✓ Polling Gateway for tasks...")
    print("✓ No public endpoint required")

    server.run_sync()
```

#### Step 5: Run the Agent

```bash
# Set environment variables (NO public URL needed!)
export AIP_ENDPOINT="http://api.aip.unibase.com"
export GATEWAY_URL="http://gateway.aip.unibase.com"
export MEMBASE_ACCOUNT="0x5ea13664c5ce67753f208540d25b913788aa3daa"  # Sample test account

# Run the agent
python examples/private_agent_full.py
```

**Output:**
```
Step 1: Register Agent with AIP Platform (Private Mode)
  ✓ Platform is healthy
  ✓ Agent registered: agent_abc456
  ✓ Mode: POLLING (no public endpoint)

Step 2: Start Agent A2A Service (Private Mode)
  ✓ Agent running (internal port 8201)
  ✓ Polling Gateway for tasks...
  ✓ No public endpoint required
```

---

## Reference

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AIP_ENDPOINT` | AIP platform URL | Yes | - |
| `GATEWAY_URL` | Gateway URL | Yes | - |
| `AGENT_PUBLIC_URL` | Public endpoint URL | Public agents only | - |
| `AGENT_HOST` | Bind host | No | `0.0.0.0` |
| `AGENT_PORT` | Bind port | No | `8200` |
| `MEMBASE_ACCOUNT` | Wallet address | No | - |

---

**Ready to build your agent?** Start with the [public agent example](public_agent_full.py) or [private agent example](private_agent_full.py)!
