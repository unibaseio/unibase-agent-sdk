"""A2A Protocol Example - Complete Agent with A2A Support

This example demonstrates:
1. Creating a Unibase agent with A2A protocol support
2. Exposing it as an A2A server (discoverable at /.well-known/agent.json)
3. Connecting to external A2A agents
4. Sending tasks and receiving responses

Run this example:
    python examples/a2a_agent_example.py

Then test:
    # View Agent Card
    curl http://localhost:8000/.well-known/agent.json
    
    # Send a task (JSON-RPC)
    curl -X POST http://localhost:8000/a2a \\
        -H "Content-Type: application/json" \\
        -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"type":"text","text":"Hello!"}]}},"id":1}'
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from unibase_agent_sdk import AgentRegistry, AgentType

# Import A2A components
from unibase_agent_sdk.a2a import (
    A2AServer,
    A2AClient,
    AgentCard,
    Task,
    Message,
    TextPart,
    StreamResponse,
    Skill,
    Capability,
    generate_agent_card,
)


async def simple_echo_handler(task: Task, message: Message):
    """Simple task handler that echoes back the input.
    
    In a real agent, this would invoke your AI model
    or business logic to process the message.
    """
    # Extract text from message parts
    input_text = ""
    for part in message.parts:
        if isinstance(part, TextPart):
            input_text += part.text
    
    # Echo response
    response_text = f"Echo: {input_text}"
    
    # Yield response message
    yield StreamResponse(message=Message.agent(response_text))


async def main():
    print("=" * 70)
    print("🔷 A2A Protocol Example - Unibase Agent Framework")
    print("=" * 70)
    
    # ============================================================
    # 1. Create Registry and Register Agent
    # ============================================================
    print("\n📝 Creating Registry and Agent...")
    
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )
    
    identity = await registry.register_agent(
        name="Echo Agent",
        agent_type=AgentType.CUSTOM,
        metadata={
            "description": "A simple echo agent that returns your messages",
            "skills": [
                {
                    "id": "echo",
                    "name": "Echo",
                    "description": "Echoes back whatever you say",
                    "tags": ["echo", "test"],
                    "examples": ["Hello!", "What's up?"]
                }
            ]
        }
    )
    
    print(f"   ✅ Registered Agent: {identity.name} ({identity.agent_id})")
    
    # ============================================================
    # 2. Generate Agent Card
    # ============================================================
    print("\n📋 Generating Agent Card...")
    
    base_url = "http://localhost:8000"
    
    agent_card = registry.generate_agent_card_for(
        agent_id=identity.agent_id,
        base_url=base_url,
        capabilities=Capability(
            streaming=True,
            push_notifications=False,
            state_transition_history=True
        )
    )
    
    print(f"   ✅ Agent Card generated")
    print(f"   Name: {agent_card.name}")
    print(f"   Skills: {[s.name for s in agent_card.skills]}")
    print(f"   Capabilities: streaming={agent_card.capabilities.streaming}")
    
    # ============================================================
    # 3. Start A2A Server
    # ============================================================
    print("\n🚀 Starting A2A Server...")
    print(f"   URL: {base_url}")
    print(f"   Agent Card: {base_url}/.well-known/agent.json")
    print(f"   A2A Endpoint: {base_url}/a2a")
    print("\n   Press Ctrl+C to stop\n")
    
    server = A2AServer(
        agent_card=agent_card,
        task_handler=simple_echo_handler,
        host="0.0.0.0",
        port=8000
    )
    
    try:
        await server.run()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    
    await registry.close()


async def demo_a2a_client():
    """Demo: Connect to an A2A agent and send tasks."""
    print("=" * 70)
    print("🔷 A2A Client Demo")
    print("=" * 70)
    
    agent_url = "http://localhost:8000"
    
    async with A2AClient() as client:
        # Discover agent
        print("\n📋 Discovering agent...")
        try:
            card = await client.discover_agent(agent_url)
            print(f"   Name: {card.name}")
            print(f"   Description: {card.description}")
            print(f"   Skills: {[s.name for s in card.skills]}")
        except Exception as e:
            print(f"   ❌ Discovery failed: {e}")
            print("   Make sure the A2A server is running!")
            return
        
        # Send a task
        print("\n📤 Sending task...")
        message = Message.user("Hello, A2A agent!")
        
        try:
            task = await client.send_task(agent_url, message)
            print(f"   Task ID: {task.id}")
            print(f"   Status: {task.status.state.value}")
            
            # Get the response
            if task.history:
                last_message = task.history[-1]
                if last_message.role.value == "agent":
                    for part in last_message.parts:
                        if hasattr(part, "text"):
                            print(f"   Response: {part.text}")
        except Exception as e:
            print(f"   ❌ Task failed: {e}")
    
    print("\n✅ A2A Client demo completed!")


if __name__ == "__main__":
    import sys
    
    if "--client" in sys.argv:
        # Run client demo
        asyncio.run(demo_a2a_client())
    else:
        # Run server
        asyncio.run(main())
