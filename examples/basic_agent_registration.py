"""
Basic Agent Registration Example with Registry
Demonstrates the core workflow of the Unibase Agent Framework.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from unibase_agent_sdk import (
    AgentRegistry,
    MemoryManager,
    ClaudeAdapter,
    AgentType
)


async def basic_example_with_registry():
    """Complete agent registration and usage example"""
    
    print("=" * 60)
    print("🚀 Unibase Agent Framework - Basic Example")
    print("=" * 60)
    
    # 1. Create the registry (global singleton)
    print("\n📋 Step 1: Creating AgentRegistry...")
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
        web3_rpc_url=os.getenv("WEB3_RPC_URL")
    )
    print("✅ Registry created")
    
    # 2. Register agent identity
    print("\n📋 Step 2: Registering Agent identity...")
    identity = await registry.register_agent(
        name="my-claude-agent",
        agent_type=AgentType.CLAUDE,
        auto_create_wallet=True,  # Automatically create a wallet
        metadata={"purpose": "customer service", "version": "1.0"}
    )
    print(f"✅ Agent registered: {identity.agent_id}")
    print(f"   Name: {identity.name}")
    print(f"   Wallet: {identity.wallet_address}")
    
    # 3. Initialize Memory
    print("\n📋 Step 3: Initializing MemoryManager...")
    memory_manager = MemoryManager(
        membase_endpoint="https://membase.unibase.io",
        da_endpoint="https://da.unibase.io",
        agent_id=identity.agent_id
    )
    print("✅ MemoryManager initialized")
    
    # 4. Add Memory middleware (optional - requires extra dependencies)
    print("\n📋 Step 4: Checking Memory middlewares...")
    try:
        from unibase_agent_sdk.memory.middlewares import Mem0Middleware
        
        # mem0 requires the OPENAI_API_KEY environment variable
        if os.getenv("OPENAI_API_KEY"):
            mem0 = Mem0Middleware(agent_id=identity.agent_id)
            await mem0.initialize()
            memory_manager.add_middleware(mem0)
            print("✅ Mem0 middleware added")
        else:
            print("⚠️ OPENAI_API_KEY not set, skipping mem0 middleware")
    except ImportError as e:
        print(f"⚠️ Mem0 not installed, skipping: {e}")
    except Exception as e:
        print(f"⚠️ Mem0 initialization failed, skipping: {e}")
    
    # 5. Create the Agent (pass in registry)
    print("\n📋 Step 5: Creating Claude Agent...")
    agent = ClaudeAdapter(
        identity=identity,
        registry=registry,
        memory_manager=memory_manager
    )
    
    # Initialize (requires a valid API key)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        await agent.initialize(api_key=api_key)
        print("✅ Agent initialized with API key")
    else:
        print("⚠️ ANTHROPIC_API_KEY not set, agent created but not initialized")
    
    # 6. Use native API (requires a real API key)
    print("\n📋 Step 6: Testing native API...")
    if api_key and agent._sdk_instance:
        try:
            response = await agent.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": "Hello! Say 'Hi' in one word."}]
            )
            print(f"✅ Response: {response.content[0].text}")
        except Exception as e:
            print(f"⚠️ API call failed: {e}")
    else:
        print("⚠️ Skipping API call (no API key)")
    
    # 7. Use registry features
    print("\n📋 Step 7: Using Registry features...")
    
    # Update metadata
    await agent.update_metadata({"status": "active", "last_used": "now"})
    print("✅ Metadata updated")
    
    # List all agents
    all_agents = await agent.list_all_agents()
    print(f"✅ All agents: {[a.name for a in all_agents]}")
    
    # 8. Upload memory to DA (demo)
    print("\n📋 Step 8: Memory DA upload (demo)...")
    print("⚠️ Skipping DA upload (no active DA service)")
    
    # Cleanup
    print("\n📋 Cleaning up...")
    await registry.close()
    print("✅ Done!")
    
    print("\n" + "=" * 60)
    print("🎉 Example completed successfully!")
    print("=" * 60)
    
    # Print usage notes
    print("\n📖 Usage notes:")
    print("   - Set ANTHROPIC_API_KEY to enable Claude API calls")
    print("   - Set OPENAI_API_KEY to enable mem0 middleware")
    print("   - Ensure AIP and Membase services are running and accessible")


if __name__ == "__main__":
    asyncio.run(basic_example_with_registry())
