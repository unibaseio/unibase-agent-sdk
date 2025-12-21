"""
Agent with mem0 Memory Middleware Example
Demonstrates using mem0 for intelligent memory management.
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


async def agent_with_mem0_example():
    """Agent example using the mem0 middleware"""
    
    print("=" * 60)
    print("🧠 Unibase Agent Framework - mem0 Memory Example")
    print("=" * 60)
    
    # Check environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("\n⚠️ OPENAI_API_KEY not set!")
        print("   mem0 requires OpenAI API key for embeddings.")
        print("   Set it with: export OPENAI_API_KEY='your-key'")
    
    # Create registry
    print("\n📋 Creating Registry...")
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )
    print("✅ Registry created ()")
    
    # Register agent
    print("\n📋 Registering Agent...")
    identity = await registry.register_agent(
        name="MemoryAssistant",
        agent_type=AgentType.CLAUDE,
        metadata={"purpose": "personal assistant with memory"}
    )
    print(f"✅ Agent registered: {identity.agent_id}")
    
    # Create Memory Manager
    print("\n📋 Setting up Memory Manager...")
    memory_manager = MemoryManager(
        membase_endpoint="https://membase.unibase.io",
        da_endpoint="https://da.unibase.io",
        agent_id=identity.agent_id
    )
    print("✅ Memory Manager initialized")
    
    # Add mem0 middleware
    print("\n📋 Checking mem0 middleware...")
    mem0_available = False
    mem0 = None
    
    if openai_key:
        try:
            from unibase_agent_sdk.memory.middlewares import Mem0Middleware
            
            # Simple initialization (uses in-memory storage by default)
            mem0 = Mem0Middleware(agent_id=identity.agent_id)
            await mem0.initialize()
            memory_manager.add_middleware(mem0)
            mem0_available = True
            print("✅ mem0 middleware added")
            
            # Add memories via the native mem0 API
            print("\n📋 Adding memories via mem0...")
            native_mem0 = mem0._middleware_instance
            
            try:
                # Add memory 1
                result = native_mem0.add(
                    "Alice's favorite programming language is Python",
                    user_id=identity.agent_id,
                    metadata={"category": "preference"}
                )
                print(f"   ✅ Added: Alice likes Python")
                
                # Add memory 2
                result = native_mem0.add(
                    "Alice works at a tech startup",
                    user_id=identity.agent_id,
                    metadata={"category": "work"}
                )
                print(f"   ✅ Added: Alice's workplace")
                
                # Search memories
                print("\n📋 Searching memories...")
                results = native_mem0.search(
                    "What does Alice like?",
                    user_id=identity.agent_id,
                    limit=5
                )
                print(f"   Found {len(results)} results")
                
                # Get all memories
                print("\n📋 Getting all memories...")
                all_memories = native_mem0.get_all(user_id=identity.agent_id)
                print(f"   Total memories: {len(all_memories)}")
                
            except Exception as api_error:
                error_msg = str(api_error)
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"\n⚠️ OpenAI API quota exceeded!")
                    print("   The API key has exceeded its usage quota.")
                    print("   Please check your OpenAI billing at: https://platform.openai.com/usage")
                else:
                    print(f"\n⚠️ mem0 API error: {api_error}")
            
        except ImportError as e:
            print(f"⚠️ mem0 not installed: {e}")
            print("   Install with: pip install mem0ai")
        except Exception as e:
            print(f"⚠️ mem0 initialization error: {e}")
    else:
        print("⚠️ Skipping mem0 (OPENAI_API_KEY not set)")
    
    # Create the agent
    print("\n📋 Creating Agent...")
    agent = ClaudeAdapter(
        identity=identity,
        registry=registry,
        memory_manager=memory_manager
    )
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        await agent.initialize(api_key=api_key)
        print("✅ Agent initialized")
    else:
        print("⚠️ Agent created (no ANTHROPIC_API_KEY)")
    
    # Display status
    print("\n📊 Status Summary:")
    print(f"   Agent ID: {identity.agent_id}")
    print(f"   Memory middlewares: {len(memory_manager.middlewares)}")
    print(f"   mem0 available: {mem0_available}")
    
    # Cleanup
    await registry.close()
    
    print("\n" + "=" * 60)
    print("🎉 mem0 Memory Example completed!")
    print("=" * 60)
    
    if not openai_key or "429" in str(mem0_available):
        print("\n📖 Next steps:")
        print("   1. Get a valid OpenAI API key with available quota")
        print("   2. Set OPENAI_API_KEY in your .env file")
        print("   3. Run this example again")


if __name__ == "__main__":
    asyncio.run(agent_with_mem0_example())
