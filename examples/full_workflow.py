"""
Agent Communication Example
Demonstrates two agents communicating through AIP protocol.
"""
import asyncio
import os
from unibase_agent_sdk import (
    AgentRegistry,
    ClaudeAdapter,
    LangChainAdapter,
    AgentType
)


async def agent_communication_example():
    """Two agents communicating via the AIP protocol"""
    
    print("=" * 60)
    print("🔄 Unibase Agent Framework - Agent Communication")
    print("=" * 60)
    
    # Create registry ()
    print("\n📋 Creating Registry...")
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )
    print("✅ Registry created ()")
    
    # Register two agents
    print("\n📋 Registering Alice (Claude) Agent...")
    alice_identity = await registry.register_agent(
        name="Alice",
        agent_type=AgentType.CLAUDE,
        metadata={"role": "assistant", "specialty": "conversation"}
    )
    print(f"✅ Alice registered: {alice_identity.agent_id}")
    
    print("\n📋 Registering Bob (LangChain) Agent...")
    bob_identity = await registry.register_agent(
        name="Bob",
        agent_type=AgentType.LANGCHAIN,
        metadata={"role": "analyst", "specialty": "data analysis"}
    )
    print(f"✅ Bob registered: {bob_identity.agent_id}")
    
    # Create Alice agent
    print("\n📋 Initializing Alice...")
    alice = ClaudeAdapter(
        identity=alice_identity,
        registry=registry
    )
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        await alice.initialize(api_key=api_key)
        print("✅ Alice initialized with API key")
    else:
        print("⚠️ Alice created (no API key - demo mode)")
    
    # Create Bob agent
    print("\n📋 Initializing Bob...")
    bob = LangChainAdapter(
        identity=bob_identity,
        registry=registry
    )
    try:
        if api_key:
            await bob.initialize(api_key=api_key)
            print("✅ Bob initialized")
        else:
            print("⚠️ Bob created (no API key - demo mode)")
    except ImportError as e:
        print(f"⚠️ LangChain not installed: {e}")
    
    # Alice sends a message to Bob via the AIP protocol
    print("\n📋 Alice sending message to Bob via AIP protocol...")
    response = await alice.send_to_agent(
        to_agent_id=bob.agent_id,
        message={
            "type": "question",
            "content": "Can you help me analyze this data?",
            "data": {"values": [1, 2, 3, 4, 5]}
        }
    )
    print(f"✅ Message delivery status: {response.get('status', 'unknown')}")
    
    # Alice fetches Bob's instance directly (if in the same process)
    print("\n📋 Alice getting Bob's instance directly...")
    bob_instance = await alice.get_other_agent(bob.agent_id)
    if bob_instance:
        print(f"✅ Got Bob instance: {bob_instance.identity.name}")
    else:
        print("⚠️ Bob instance not found in local registry")
    
    # List all agents
    print("\n📋 Listing all agents...")
    all_agents = await registry.list_agents()
    for agent in all_agents:
        print(f"   - {agent.name} ({agent.agent_type.value}): {agent.metadata}")
    
    # Cleanup
    await registry.close()
    
    print("\n" + "=" * 60)
    print("🎉 Agent Communication Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(agent_communication_example())
