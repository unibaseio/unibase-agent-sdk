"""
Agent with LangChain Memory Middleware Example
Demonstrates using LangChain's memory system with the framework.
"""
import asyncio
import os
from unibase_agent_sdk import (
    AgentRegistry,
    MemoryManager,
    AgentType
)


async def agent_with_langchain_memory():
    """Agent example using the LangChain Memory middleware"""
    
    print("=" * 60)
    print("🔗 Unibase Agent Framework - LangChain Memory Example")
    print("=" * 60)
    
    # Create registry
    print("\n📋 Creating Registry...")
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io"
    )
    print("✅ Registry created")
    
    # Register agent
    print("\n📋 Registering Agent...")
    identity = await registry.register_agent(
        name="LangChainAssistant",
        agent_type=AgentType.LANGCHAIN,
        metadata={"purpose": "conversational assistant"}
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
    
    # Add LangChain Memory middleware
    print("\n📋 Checking LangChain Memory middleware...")
    lc_available = False
    
    try:
        from unibase_agent_sdk.memory.middlewares import LangChainMemoryMiddleware
        
        lc_memory = LangChainMemoryMiddleware(
            agent_id=identity.agent_id,
            memory_type="buffer",
            session_id="session_001"
        )
        await lc_memory.initialize()
        memory_manager.add_middleware(lc_memory)
        lc_available = True
        print("✅ LangChain Memory middleware added")
        
        # Use the native LangChain Memory API
        print("\n📋 Saving conversation context...")
        lc_memory.save_context(
            {"input": "Hi, I'm Alice"},
            {"output": "Hello Alice! How can I help you today?"}
        )
        print("   ✅ Saved: Introduction")
        
        lc_memory.save_context(
            {"input": "I need help with Python programming"},
            {"output": "I'd be happy to help with Python! What specific topic?"}
        )
        print("   ✅ Saved: Python help request")
        
        lc_memory.save_context(
            {"input": "How do I use async/await?"},
            {"output": "Async/await in Python allows you to write asynchronous code..."}
        )
        print("   ✅ Saved: Async question")
        
        # Load memory variables
        print("\n📋 Loading memory variables...")
        memory_vars = lc_memory.load_memory_variables({})
        chat_history = memory_vars.get("chat_history", [])
        print(f"   Chat history has {len(chat_history)} messages")
        
        for msg in chat_history:
            role = type(msg).__name__
            content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"   - {role}: {content}")


    except ImportError as e:
        print(f"⚠️ LangChain not installed: {e}")
        print("   Install with: pip install langchain")
    except Exception as e:
        print(f"⚠️ LangChain Memory error: {e}")
    
    # Create the agent (requires LangChain)
    print("\n📋 Creating LangChain Agent...")
    try:
        from unibase_agent_sdk import LangChainAdapter
        
        agent = LangChainAdapter(
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
            
    except ImportError as e:
        print(f"⚠️ LangChain adapter error: {e}")
    
    # Display status
    print("\n📊 Status Summary:")
    print(f"   Agent ID: {identity.agent_id}")
    print(f"   Memory middlewares: {len(memory_manager.middlewares)}")
    print(f"   LangChain available: {lc_available}")
    
    # Cleanup
    await registry.close()
    
    print("\n" + "=" * 60)
    print("🎉 LangChain Memory Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(agent_with_langchain_memory())
