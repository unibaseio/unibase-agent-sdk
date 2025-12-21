"""
Comprehensive Test - All SDK Adapters and Memory Middlewares
Tests all available adapters and memory systems.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from unibase_agent_sdk import (
    AgentRegistry,
    MemoryManager,
    ClaudeAdapter,
    LangChainAdapter,
    OpenAIAdapter,
    AgentType,
    AgentIdentity,
)


async def test_all_adapters_and_memory():
    """Test all SDK adapters and memory middlewares"""
    
    print("=" * 70)
    print("🧪 COMPREHENSIVE TEST - All SDKs and Memory Middlewares")
    print("=" * 70)
    
    # Environment check
    print("\n📋 Environment Check:")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
    print(f"   ANTHROPIC_API_KEY: {'✅ Set' if anthropic_key else '❌ Not set'}")
    
    # Create Registry
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )
    
    results = {
        "adapters": {},
        "memory_middlewares": {}
    }
    
    # ============================================================
    # PART 1: Test all SDK Adapters
    # ============================================================
    print("\n" + "=" * 70)
    print("📦 PART 1: SDK ADAPTERS")
    print("=" * 70)
    
    # Test 1: Claude Adapter
    print("\n🔷 Testing Claude Adapter...")
    try:
        identity = await registry.register_agent(
            name="test-claude",
            agent_type=AgentType.CLAUDE
        )
        
        claude = ClaudeAdapter(
            identity=identity,
            registry=registry
        )
        
        if anthropic_key:
            await claude.initialize(api_key=anthropic_key)
            # Test API call
            try:
                response = await claude.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=50,
                    messages=[{"role": "user", "content": "Say 'Hello' in one word"}]
                )
                print(f"   ✅ Claude API works: {response.content[0].text}")
                results["adapters"]["Claude"] = "✅ Full API"
            except Exception as e:
                print(f"   ⚠️ Claude API error: {e}")
                results["adapters"]["Claude"] = "⚠️ Initialized but API failed"
        else:
            print("   ⚠️ Claude: No API key, adapter created in demo mode")
            results["adapters"]["Claude"] = "⚠️ Demo mode (no API key)"
    except Exception as e:
        print(f"   ❌ Claude Adapter failed: {e}")
        results["adapters"]["Claude"] = f"❌ Error: {e}"
    
    # Test 2: OpenAI Adapter
    print("\n🔷 Testing OpenAI Adapter...")
    try:
        identity = await registry.register_agent(
            name="test-openai",
            agent_type=AgentType.OPENAI
        )
        
        openai_adapter = OpenAIAdapter(
            identity=identity,
            registry=registry
        )
        
        if openai_key:
            await openai_adapter.initialize(api_key=openai_key)
            # Test API call
            try:
                response = await openai_adapter.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=50,
                    messages=[{"role": "user", "content": "Say 'Hello' in one word"}]
                )
                print(f"   ✅ OpenAI API works: {response.choices[0].message.content}")
                results["adapters"]["OpenAI"] = "✅ Full API"
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"   ⚠️ OpenAI quota exceeded")
                    results["adapters"]["OpenAI"] = "⚠️ Quota exceeded"
                else:
                    print(f"   ⚠️ OpenAI API error: {e}")
                    results["adapters"]["OpenAI"] = f"⚠️ API error"
        else:
            print("   ⚠️ OpenAI: No API key, adapter created in demo mode")
            results["adapters"]["OpenAI"] = "⚠️ Demo mode (no API key)"
    except ImportError as e:
        print(f"   ❌ OpenAI not installed: {e}")
        results["adapters"]["OpenAI"] = "❌ Not installed"
    except Exception as e:
        print(f"   ❌ OpenAI Adapter failed: {e}")
        results["adapters"]["OpenAI"] = f"❌ Error"
    
    # Test 3: LangChain Adapter
    print("\n🔷 Testing LangChain Adapter...")
    try:
        identity = await registry.register_agent(
            name="test-langchain",
            agent_type=AgentType.LANGCHAIN
        )
        
        langchain = LangChainAdapter(
            identity=identity,
            registry=registry,
            provider="openai"  # Use OpenAI instead of Anthropic
        )
        
        if openai_key:
            await langchain.initialize(api_key=openai_key, provider="openai")
            # Test API call
            try:
                from langchain.schema import HumanMessage
                response = await langchain.ainvoke([
                    HumanMessage(content="Say 'Hello' in one word")
                ])
                print(f"   ✅ LangChain API works: {response.content}")
                results["adapters"]["LangChain"] = "✅ Full API"
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"   ⚠️ LangChain: OpenAI quota exceeded")
                    results["adapters"]["LangChain"] = "⚠️ Quota exceeded"
                else:
                    print(f"   ⚠️ LangChain API error: {e}")
                    results["adapters"]["LangChain"] = "⚠️ Initialized but API failed"
        else:
            print("   ⚠️ LangChain: No OPENAI_API_KEY, adapter created in demo mode")
            results["adapters"]["LangChain"] = "⚠️ Demo mode (no API key)"
    except ImportError as e:
        print(f"   ❌ LangChain not installed: {e}")
        results["adapters"]["LangChain"] = "❌ Not installed"
    except Exception as e:
        print(f"   ❌ LangChain Adapter failed: {e}")
        results["adapters"]["LangChain"] = f"❌ Error"
    
    # ============================================================
    # PART 2: Test all Memory Middlewares
    # ============================================================
    print("\n" + "=" * 70)
    print("🧠 PART 2: MEMORY MIDDLEWARES")
    print("=" * 70)
    
    # Create Memory Manager for testing
    memory_manager = MemoryManager(
        membase_endpoint="https://membase.unibase.io",
        da_endpoint="https://da.unibase.io",
        agent_id="test-agent"
    )
    
    # Test 1: mem0 Middleware
    print("\n🔷 Testing mem0 Middleware...")
    try:
        from unibase_agent_sdk.memory.middlewares import Mem0Middleware
        
        mem0 = Mem0Middleware(agent_id="test-mem0")
        await mem0.initialize()
        
        # Test operations
        native = mem0._middleware_instance
        native.add("Test memory: User likes Python", user_id="test-mem0")
        results_search = native.search("Python", user_id="test-mem0", limit=5)
        all_memories = native.get_all(user_id="test-mem0")
        
        print(f"   ✅ mem0 works: Added 1, Found {len(results_search)}, Total {len(all_memories)}")
        results["memory_middlewares"]["mem0"] = "✅ Working"
        memory_manager.add_middleware(mem0)
    except ImportError as e:
        print(f"   ❌ mem0 not installed: {e}")
        results["memory_middlewares"]["mem0"] = "❌ Not installed"
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            print(f"   ⚠️ mem0: OpenAI quota exceeded")
            results["memory_middlewares"]["mem0"] = "⚠️ Quota exceeded"
        else:
            print(f"   ❌ mem0 error: {e}")
            results["memory_middlewares"]["mem0"] = f"❌ Error"
    
    # Test 2: LangChain Memory Middleware
    print("\n🔷 Testing LangChain Memory Middleware...")
    try:
        from unibase_agent_sdk.memory.middlewares import LangChainMemoryMiddleware
        
        lc_memory = LangChainMemoryMiddleware(
            agent_id="test-langchain-memory",
            memory_type="buffer"
        )
        await lc_memory.initialize()
        
        # Test operations
        lc_memory.save_context(
            {"input": "Hello"},
            {"output": "Hi there!"}
        )
        lc_memory.save_context(
            {"input": "How are you?"},
            {"output": "I'm doing well!"}
        )
        
        memory_vars = lc_memory.load_memory_variables({})
        chat_history = memory_vars.get("chat_history", [])

        print(f"   ✅ LangChain Memory works: {len(chat_history)} messages")
        results["memory_middlewares"]["LangChain Memory"] = "✅ Working"
        memory_manager.add_middleware(lc_memory)
    except ImportError as e:
        print(f"   ❌ LangChain Memory not installed: {e}")
        results["memory_middlewares"]["LangChain Memory"] = "❌ Not installed"
    except Exception as e:
        print(f"   ❌ LangChain Memory error: {e}")
        results["memory_middlewares"]["LangChain Memory"] = f"❌ Error: {e}"
    
    # Test 3: Zep Middleware
    print("\n🔷 Testing Zep Middleware...")
    try:
        from unibase_agent_sdk.memory.middlewares import ZepMiddleware
        
        # Zep requires either a running server or Cloud API key
        zep = ZepMiddleware(
            agent_id="test-zep",
            base_url="http://localhost:8000",
            api_key=os.getenv("ZEP_API_KEY", "")  # Optional API key
        )
        await zep.initialize()
        print(f"   ✅ Zep initialized")
        results["memory_middlewares"]["Zep"] = "✅ Initialized"
    except ImportError as e:
        print(f"   ⚠️ Zep not installed: pip install zep-python")
        results["memory_middlewares"]["Zep"] = "⚠️ Not installed"
    except Exception as e:
        error_str = str(e)
        if "Connection refused" in error_str:
            print(f"   ⚠️ Zep: No server running (needs: docker run -p 8000:8000 zepai/zep)")
            results["memory_middlewares"]["Zep"] = "⚠️ No server"
        elif "api_key" in error_str.lower() or "ZEP_API_KEY" in error_str:
            print(f"   ⚠️ Zep: Needs API key (set ZEP_API_KEY) or local server")
            results["memory_middlewares"]["Zep"] = "⚠️ Needs API key/server"
        else:
            print(f"   ⚠️ Zep: {e}")
            results["memory_middlewares"]["Zep"] = f"⚠️ Config needed"
    
    # Test 4: MemGPT Middleware
    print("\n🔷 Testing MemGPT Middleware...")
    try:
        from unibase_agent_sdk.memory.middlewares import MemGPTMiddleware
        
        memgpt = MemGPTMiddleware(
            agent_id="test-memgpt",
            base_url="http://localhost:8080"
        )
        await memgpt.initialize()
        print(f"   ✅ MemGPT initialized (requires MemGPT server)")
        results["memory_middlewares"]["MemGPT"] = "✅ Initialized"
    except ImportError as e:
        print(f"   ⚠️ MemGPT not installed: pip install pymemgpt")
        results["memory_middlewares"]["MemGPT"] = "⚠️ Not installed"
    except Exception as e:
        if "Connection refused" in str(e) or "No module" in str(e):
            print(f"   ⚠️ MemGPT: Not available (expected)")
            results["memory_middlewares"]["MemGPT"] = "⚠️ Not available"
        else:
            print(f"   ❌ MemGPT error: {e}")
            results["memory_middlewares"]["MemGPT"] = f"❌ Error"
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    print("\n🔹 SDK Adapters:")
    for name, status in results["adapters"].items():
        print(f"   {name:15} {status}")
    
    print("\n🔹 Memory Middlewares:")
    for name, status in results["memory_middlewares"].items():
        print(f"   {name:20} {status}")
    
    print("\n🔹 Combined Test:")
    print(f"   Memory Manager middlewares: {len(memory_manager.middlewares)}")
    print(f"   Registered agents: {len(await registry.list_agents())}")
    
    # Cleanup
    await registry.close()
    
    print("\n" + "=" * 70)
    print("🎉 Comprehensive Test Completed!")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_all_adapters_and_memory())
