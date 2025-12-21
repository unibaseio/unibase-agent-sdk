"""
Test Agent Framework Wrappers

Demonstrates the correct approach: wrapping Agent classes,
not the entire framework.

Usage:
    # Instead of using native agents:
    from crewai import Agent
    agent = Agent(role="Researcher", goal="...")
    
    # Use Unibase-wrapped agents:
    from unibase_agent_sdk.agents import CrewAIAgent
    agent = CrewAIAgent(role="Researcher", goal="...", registry=registry)
    # Now the agent is automatically registered with Unibase!
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from unibase_agent_sdk import AgentRegistry


async def test_agent_wrappers():
    """Test all agent framework wrappers"""
    
    print("=" * 70)
    print("🧪 Testing Agent Framework Wrappers")
    print("=" * 70)
    
    # Create Registry
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )
    
    results = {}
    
    # ============================================================
    # Test CrewAI Agent Wrapper
    # ============================================================
    print("\n🔷 CrewAI Agent...")
    try:
        from unibase_agent_sdk.agents import create_crewai_agent
        
        # Use the factory function - returns a real crewai.Agent!
        researcher = create_crewai_agent(
            role="Researcher",
            goal="Research AI topics",
            backstory="Expert AI researcher",
            registry=registry  # Auto-register with Unibase
        )
        
        agent_id = researcher._unibase_identity.agent_id if researcher._unibase_identity else "N/A"
        print(f"   ✅ Created: {researcher.role}")
        print(f"   ✅ Unibase ID: {agent_id}")
        results["CrewAI"] = "✅"
        
    except ImportError as e:
        print(f"   ⚠️ Not installed: pip install crewai")
        results["CrewAI"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ Error: {str(e)[:50]}")
        results["CrewAI"] = "⚠️"
    
    # ============================================================
    # Test AutoGen Agent Wrappers
    # ============================================================
    print("\n🔷 AutoGen Agents...")
    try:
        from unibase_agent_sdk.agents import AutoGenAssistant, AutoGenUserProxy
        
        # Use exactly like autogen.AssistantAgent!
        assistant = AutoGenAssistant(
            name="coder",
            system_message="You are an expert Python coder.",
            registry=registry,  # Auto-register
            llm_config={"config_list": [{"model": "gpt-4o-mini", "api_key": os.getenv("OPENAI_API_KEY")}]}
        )
        
        user = AutoGenUserProxy(
            name="user",
            registry=registry  # Auto-register
        )
        
        print(f"   ✅ Assistant: {assistant.name} ({assistant.unibase_agent_id})")
        print(f"   ✅ UserProxy: {user.name} ({user.unibase_agent_id})")
        results["AutoGen"] = "✅"
        
    except ImportError as e:
        print(f"   ⚠️ Not installed: pip install pyautogen")
        results["AutoGen"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ Error: {str(e)[:50]}")
        results["AutoGen"] = "⚠️"
    
    # ============================================================
    # Test Phidata Agent Wrapper
    # ============================================================
    print("\n🔷 Phidata Agent...")
    try:
        from unibase_agent_sdk.agents import create_phi_agent
        
        # Use the factory function - returns a real phi.agent.Agent!
        agent = create_phi_agent(
            name="Web Researcher",
            registry=registry  # Auto-register
        )
        
        agent_id = agent._unibase_identity.agent_id if agent._unibase_identity else "N/A"
        print(f"   ✅ Created: {agent.name} ({agent_id})")
        results["Phidata"] = "✅"
        
    except ImportError as e:
        print(f"   ⚠️ Not installed: pip install phidata")
        results["Phidata"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ Error: {str(e)[:50]}")
        results["Phidata"] = "⚠️"
    
    # ============================================================
    # Test LlamaIndex Agent Wrapper
    # ============================================================
    print("\n🔷 LlamaIndex Agent...")
    try:
        from unibase_agent_sdk.agents import LlamaAgent
        from llama_index.llms.openai import OpenAI
        
        llm = OpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
        
        # Use exactly like llama_index ReActAgent.from_tools!
        agent = LlamaAgent.from_tools(
            tools=[],
            llm=llm,
            registry=registry  # Auto-register
        )
        
        print(f"   ✅ Created LlamaIndex Agent ({agent.unibase_agent_id})")
        results["LlamaIndex"] = "✅"
        
    except ImportError as e:
        print(f"   ⚠️ Not installed: pip install llama-index")
        results["LlamaIndex"] = "⚠️ (not installed)"
    except Exception as e:
        print(f"   ⚠️ Error: {str(e)[:50]}")
        results["LlamaIndex"] = "⚠️"
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 Registry Status")
    print("=" * 70)
    
    agents = await registry.list_agents()
    print(f"\n   Registered agents: {len(agents)}")
    for agent in agents:
        print(f"   - {agent.name} ({agent.agent_id[:20]}...)")
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    for name, status in results.items():
        print(f"   {name:15} {status}")
    
    working = sum(1 for v in results.values() if v.startswith("✅"))
    print(f"\n✨ Total: {working}/{len(results)} working")
    
    await registry.close()
    
    print("\n" + "=" * 70)
    print("🎉 Agent Wrapper Tests Completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_agent_wrappers())
