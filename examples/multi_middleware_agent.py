"""
Multi-Agent Collaboration Example
Demonstrates multiple agents collaborating on a task.
"""
import asyncio
import os
from unibase_agent_sdk import (
    AgentRegistry,
    MemoryManager,
    ClaudeAdapter,
    AgentType
)


async def multi_agent_collaboration():
    """Multiple agents collaborating on a task"""
    
    print("=" * 60)
    print("🤝 Unibase Agent Framework - Multi-Agent Collaboration")
    print("=" * 60)
    
    # Create registry ()
    print("\n📋 Creating Registry...")
    registry = AgentRegistry(
        aip_endpoint="https://aip.unibase.io",
        membase_endpoint="https://membase.unibase.io",
    )
    print("✅ Registry created ()")
    
    # Register multiple specialized agents
    print("\n📋 Registering specialized agents...")
    
    coordinator_identity = await registry.register_agent(
        name="Coordinator",
        agent_type=AgentType.CLAUDE,
        metadata={"role": "coordinator", "description": "Manages task distribution"}
    )
    print(f"✅ Coordinator: {coordinator_identity.agent_id}")
    
    analyzer_identity = await registry.register_agent(
        name="DataAnalyzer",
        agent_type=AgentType.LANGCHAIN,
        metadata={"role": "analyzer", "description": "Analyzes data and trends"}
    )
    print(f"✅ DataAnalyzer: {analyzer_identity.agent_id}")
    
    writer_identity = await registry.register_agent(
        name="ReportWriter",
        agent_type=AgentType.CLAUDE,
        metadata={"role": "writer", "description": "Writes reports and summaries"}
    )
    print(f"✅ ReportWriter: {writer_identity.agent_id}")
    
    # Create Memory Manager for the coordinator
    print("\n📋 Setting up Memory for Coordinator...")
    coordinator_memory = MemoryManager(
        membase_endpoint="https://membase.unibase.io",
        da_endpoint="https://da.unibase.io",
        agent_id=coordinator_identity.agent_id
    )
    print("✅ Memory Manager initialized")
    
    # Create the coordinator agent
    print("\n📋 Initializing Coordinator...")
    coordinator = ClaudeAdapter(
        identity=coordinator_identity,
        registry=registry,
        memory_manager=coordinator_memory
    )
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        await coordinator.initialize(api_key=api_key)
        print("✅ Coordinator initialized with API key")
    else:
        print("⚠️ Coordinator created (demo mode - no API key)")
    
    # Coordinator inspects all available agents
    print("\n📋 Coordinator checking available agents...")
    all_agents = await coordinator.list_all_agents()
    print(f"✅ Available agents:")
    for agent in all_agents:
        role = agent.metadata.get('role', 'unknown')
        desc = agent.metadata.get('description', 'N/A')
        print(f"   - {agent.name} ({role}): {desc}")
    
    # Simulate task assignment
    print("\n📋 Coordinator assigning tasks...")
    
    # Coordinator assigns a task to the analyzer
    print("\n   📤 Sending analysis task to DataAnalyzer...")
    analysis_task = await coordinator.send_to_agent(
        to_agent_id=analyzer_identity.agent_id,
        message={
            "task": "analyze",
            "data": {
                "sales": [100, 150, 200, 180, 220],
                "period": "Q1 2024",
                "metrics": ["growth", "trend", "forecast"]
            }
        }
    )
    print(f"   ✅ Analysis task sent: {analysis_task.get('status', 'unknown')}")
    
    # Coordinator assigns a task to the writer
    print("\n   📤 Sending writing task to ReportWriter...")
    writing_task = await coordinator.send_to_agent(
        to_agent_id=writer_identity.agent_id,
        message={
            "task": "write_report",
            "analysis": {"result": "mock_analysis", "trend": "positive"},
            "format": "executive_summary"
        }
    )
    print(f"   ✅ Writing task sent: {writing_task.get('status', 'unknown')}")
    
    # Show collaboration stats
    print("\n📊 Collaboration Statistics:")
    print(f"   Total Agents: {len(all_agents)}")
    print(f"   Tasks Distributed: 2")
    print(f"   Memory Records: {len(coordinator_memory._local_cache)}")
    
    # Cleanup
    await registry.close()
    
    print("\n" + "=" * 60)
    print("🎉 Multi-Agent Collaboration completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(multi_agent_collaboration())
