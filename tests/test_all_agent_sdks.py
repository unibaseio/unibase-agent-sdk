"""
Test All Agent SDK Adapters
Comprehensive test of all available agent SDKs.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from unibase_agent_sdk import AgentRegistry, AgentType


async def test_all_agent_sdks():
    """Test all agent SDK adapters"""
    
    print("=" * 70)
    print("🧪 Testing All Agent SDK Adapters")
    print("=" * 70)
    
    # Create Registry
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )
    
    results = {}
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"\n📋 Environment:")
    print(f"   OPENAI_API_KEY: {'✅' if openai_key else '❌'}")
    print(f"   ANTHROPIC_API_KEY: {'✅' if anthropic_key else '❌'}")
    
    # ============================================================
    # LLM Provider Adapters
    # ============================================================
    print("\n" + "=" * 70)
    print("🔌 LLM PROVIDER ADAPTERS")
    print("=" * 70)
    
    # Claude
    print("\n🔷 Claude Adapter...")
    try:
        from unibase_agent_sdk import ClaudeAdapter
        identity = await registry.register_agent(name="test-claude", agent_type=AgentType.CLAUDE)
        adapter = ClaudeAdapter(identity=identity, registry=registry)
        if anthropic_key:
            await adapter.initialize(api_key=anthropic_key)
            print(f"   ✅ Claude: initialized with API")
            results["Claude"] = "✅"
        else:
            print(f"   ⚠️ Claude: needs ANTHROPIC_API_KEY")
            results["Claude"] = "⚠️ (needs key)"
    except Exception as e:
        print(f"   ⚠️ Claude: {str(e)[:50]}")
        results["Claude"] = "⚠️"
    
    # OpenAI
    print("\n🔷 OpenAI Adapter...")
    try:
        from unibase_agent_sdk import OpenAIAdapter
        identity = await registry.register_agent(name="test-openai", agent_type=AgentType.OPENAI)
        adapter = OpenAIAdapter(identity=identity, registry=registry)
        if openai_key:
            await adapter.initialize(api_key=openai_key)
            response = await adapter.chat.completions.create(
                model="gpt-4o-mini", max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print(f"   ✅ OpenAI: API works - '{response.choices[0].message.content}'")
            results["OpenAI"] = "✅"
        else:
            print(f"   ⚠️ OpenAI: needs OPENAI_API_KEY")
            results["OpenAI"] = "⚠️ (needs key)"
    except Exception as e:
        print(f"   ⚠️ OpenAI: {str(e)[:50]}")
        results["OpenAI"] = "⚠️"
    
    # LangChain
    print("\n🔷 LangChain Adapter...")
    try:
        from unibase_agent_sdk import LangChainAdapter
        identity = await registry.register_agent(name="test-langchain", agent_type=AgentType.LANGCHAIN)
        adapter = LangChainAdapter(identity=identity, registry=registry, provider="openai")
        if openai_key:
            await adapter.initialize(api_key=openai_key)
            from langchain.schema import HumanMessage
            response = await adapter.ainvoke([HumanMessage(content="Hi")])
            print(f"   ✅ LangChain: API works - '{response.content[:20]}...'")
            results["LangChain"] = "✅"
        else:
            print(f"   ⚠️ LangChain: needs OPENAI_API_KEY")
            results["LangChain"] = "⚠️ (needs key)"
    except Exception as e:
        print(f"   ⚠️ LangChain: {str(e)[:50]}")
        results["LangChain"] = "⚠️"
    
    # ============================================================
    # Agent Framework Adapters
    # ============================================================
    print("\n" + "=" * 70)
    print("🤖 AGENT FRAMEWORK ADAPTERS")
    print("=" * 70)
    
    # CrewAI
    print("\n🔷 CrewAI Adapter...")
    try:
        from unibase_agent_sdk import CrewAIAdapter
        identity = await registry.register_agent(name="test-crewai", agent_type=AgentType.LANGCHAIN)
        adapter = CrewAIAdapter(identity=identity, registry=registry)
        await adapter.initialize(api_key=openai_key)
        
        # Test creating agents
        helper = adapter._sdk_instance
        researcher = helper.create_agent(
            role="Researcher",
            goal="Research topics",
            backstory="Expert researcher"
        )
        print(f"   ✅ CrewAI: create_agent() works - {researcher.role}")
        results["CrewAI"] = "✅"
    except ImportError as e:
        print(f"   ⚠️ CrewAI: not installed - pip install crewai")
        results["CrewAI"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ CrewAI: {str(e)[:50]}")
        results["CrewAI"] = "⚠️"
    
    # AutoGen
    print("\n🔷 AutoGen Adapter...")
    try:
        from unibase_agent_sdk import AutoGenAdapter
        identity = await registry.register_agent(name="test-autogen", agent_type=AgentType.LANGCHAIN)
        adapter = AutoGenAdapter(identity=identity, registry=registry)
        await adapter.initialize(api_key=openai_key)
        
        # Test creating agents
        assistant = adapter.AssistantAgent(
            name="assistant",
            system_message="You are helpful."
        )
        print(f"   ✅ AutoGen: AssistantAgent() works - {assistant.name}")
        results["AutoGen"] = "✅"
    except ImportError as e:
        print(f"   ⚠️ AutoGen: not installed - pip install pyautogen")
        results["AutoGen"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ AutoGen: {str(e)[:50]}")
        results["AutoGen"] = "⚠️"
    
    # LlamaIndex
    print("\n🔷 LlamaIndex Adapter...")
    try:
        from unibase_agent_sdk import LlamaIndexAdapter
        identity = await registry.register_agent(name="test-llamaindex", agent_type=AgentType.LANGCHAIN)
        adapter = LlamaIndexAdapter(identity=identity, registry=registry)
        await adapter.initialize(api_key=openai_key)
        
        # Test LLM
        if adapter.llm:
            print(f"   ✅ LlamaIndex: LLM initialized - {adapter.llm.model}")
            results["LlamaIndex"] = "✅"
        else:
            print(f"   ⚠️ LlamaIndex: needs OPENAI_API_KEY")
            results["LlamaIndex"] = "⚠️ (needs key)"
    except ImportError as e:
        print(f"   ⚠️ LlamaIndex: not installed - pip install llama-index")
        results["LlamaIndex"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ LlamaIndex: {str(e)[:50]}")
        results["LlamaIndex"] = "⚠️"
    
    # Phidata
    print("\n🔷 Phidata Adapter...")
    try:
        from unibase_agent_sdk import PhidataAdapter
        identity = await registry.register_agent(name="test-phidata", agent_type=AgentType.LANGCHAIN)
        adapter = PhidataAdapter(identity=identity, registry=registry)
        await adapter.initialize(api_key=openai_key)
        
        # Test creating agent
        agent = adapter.create_agent(name="test-agent")
        print(f"   ✅ Phidata: create_agent() works - {agent.name}")
        results["Phidata"] = "✅"
    except ImportError as e:
        print(f"   ⚠️ Phidata: not installed - pip install phidata")
        results["Phidata"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ Phidata: {str(e)[:50]}")
        results["Phidata"] = "⚠️"
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 SUMMARY - All Agent SDK Adapters")
    print("=" * 70)
    
    print("\n🔌 LLM Providers:")
    for name in ["Claude", "OpenAI", "LangChain"]:
        status = results.get(name, "❌")
        print(f"   {name:15} {status}")
    
    print("\n🤖 Agent Frameworks:")
    for name in ["CrewAI", "AutoGen", "LlamaIndex", "Phidata"]:
        status = results.get(name, "❌")
        print(f"   {name:15} {status}")
    
    working = sum(1 for v in results.values() if v.startswith("✅"))
    total = len(results)
    print(f"\n✨ Total: {working}/{total} adapters working")
    
    await registry.close()
    
    print("\n" + "=" * 70)
    print("🎉 All Agent SDK Tests Completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_agent_sdks())
