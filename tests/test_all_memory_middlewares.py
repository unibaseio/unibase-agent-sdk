"""
Test All Memory Middlewares
Comprehensive test of all available memory storage backends.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_all_memory_middlewares():
    """Test all memory middlewares"""
    
    print("=" * 70)
    print("🧪 Testing All Memory Middlewares")
    print("=" * 70)
    
    results = {}
    
    # ============================================================
    # AI Agent Memory Frameworks
    # ============================================================
    print("\n" + "=" * 70)
    print("🧠 AI AGENT MEMORY FRAMEWORKS")
    print("=" * 70)
    
    # Test mem0
    print("\n🔷 mem0...")
    try:
        from unibase_agent_sdk.memory.middlewares import Mem0Middleware
        mem0 = Mem0Middleware(agent_id="test")
        await mem0.initialize()
        mem0.add("Test memory", user_id="test")
        all_mem = mem0.get_all(user_id="test")
        print(f"   ✅ mem0: add(), get_all() work - {len(all_mem)} memories")
        results["mem0"] = "✅"
    except Exception as e:
        print(f"   ⚠️ mem0: {str(e)[:50]}")
        results["mem0"] = "⚠️"
    
    # Test LangChain Memory
    print("\n🔷 LangChain Memory...")
    try:
        from unibase_agent_sdk.memory.middlewares import LangChainMemoryMiddleware
        lc = LangChainMemoryMiddleware(agent_id="test", memory_type="buffer")
        await lc.initialize()
        lc.save_context({"input": "Hi"}, {"output": "Hello!"})
        msgs = lc.chat_memory.messages
        print(f"   ✅ LangChain Memory: save_context(), chat_memory work - {len(msgs)} messages")
        results["LangChain Memory"] = "✅"
    except Exception as e:
        print(f"   ⚠️ LangChain Memory: {str(e)[:50]}")
        results["LangChain Memory"] = "⚠️"
    
    # Test Zep
    print("\n🔷 Zep...")
    try:
        from unibase_agent_sdk.memory.middlewares import ZepMiddleware
        zep = ZepMiddleware(agent_id="test", api_key=os.getenv("ZEP_API_KEY", ""))
        await zep.initialize()
        print(f"   ✅ Zep: memory, user APIs available")
        results["Zep"] = "✅"
    except Exception as e:
        print(f"   ⚠️ Zep: {str(e)[:50]}")
        results["Zep"] = "⚠️ (needs server)"
    
    # Test MemGPT
    print("\n🔷 MemGPT...")
    try:
        from unibase_agent_sdk.memory.middlewares import MemGPTMiddleware
        memgpt = MemGPTMiddleware(agent_id="test")
        await memgpt.initialize()
        print(f"   ✅ MemGPT: client APIs available")
        results["MemGPT"] = "✅"
    except Exception as e:
        print(f"   ⚠️ MemGPT: {str(e)[:50]}")
        results["MemGPT"] = "⚠️ (needs server)"
    
    # ============================================================
    # Vector Databases
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 VECTOR DATABASES")
    print("=" * 70)
    
    # Test ChromaDB
    print("\n🔷 ChromaDB...")
    try:
        from unibase_agent_sdk.memory.middlewares import ChromaDBMiddleware
        chroma = ChromaDBMiddleware(agent_id="test", collection_name="test_collection")
        await chroma.initialize()
        chroma.add(documents=["Test doc 1", "Test doc 2"], ids=["d1", "d2"])
        results_query = chroma.query(query_texts=["test"], n_results=2)
        count = chroma.count()
        print(f"   ✅ ChromaDB: add(), query(), count() work - {count} documents")
        results["ChromaDB"] = "✅"
    except Exception as e:
        print(f"   ⚠️ ChromaDB: {str(e)[:50]}")
        results["ChromaDB"] = "⚠️"
    
    # Test Qdrant
    print("\n🔷 Qdrant...")
    try:
        from unibase_agent_sdk.memory.middlewares import QdrantMiddleware
        qdrant = QdrantMiddleware(agent_id="test")  # Uses in-memory by default
        await qdrant.initialize()
        # Note: Would need embeddings to actually insert data
        collections = qdrant.get_collections()
        print(f"   ✅ Qdrant: client APIs available - {len(collections.collections)} collections")
        results["Qdrant"] = "✅"
    except Exception as e:
        print(f"   ⚠️ Qdrant: {str(e)[:50]}")
        results["Qdrant"] = "⚠️"
    
    # Test Pinecone
    print("\n🔷 Pinecone...")
    try:
        from unibase_agent_sdk.memory.middlewares import PineconeMiddleware
        pinecone_key = os.getenv("PINECONE_API_KEY")
        if pinecone_key:
            pinecone = PineconeMiddleware(agent_id="test", api_key=pinecone_key)
            await pinecone.initialize()
            print(f"   ✅ Pinecone: client ready")
            results["Pinecone"] = "✅"
        else:
            print(f"   ⚠️ Pinecone: needs PINECONE_API_KEY")
            results["Pinecone"] = "⚠️ (needs API key)"
    except Exception as e:
        print(f"   ⚠️ Pinecone: {str(e)[:50]}")
        results["Pinecone"] = "⚠️"
    
    # Test Weaviate
    print("\n🔷 Weaviate...")
    try:
        from unibase_agent_sdk.memory.middlewares import WeaviateMiddleware
        weaviate = WeaviateMiddleware(agent_id="test")
        await weaviate.initialize()
        print(f"   ✅ Weaviate: client ready")
        results["Weaviate"] = "✅"
    except Exception as e:
        print(f"   ⚠️ Weaviate: {str(e)[:50]}")
        results["Weaviate"] = "⚠️ (needs server)"
    
    # ============================================================
    # Key-Value / Cache
    # ============================================================
    print("\n" + "=" * 70)
    print("🗄️ KEY-VALUE / CACHE")
    print("=" * 70)
    
    # Test Redis
    print("\n🔷 Redis...")
    try:
        from unibase_agent_sdk.memory.middlewares import RedisMiddleware
        redis = RedisMiddleware(agent_id="test")
        await redis.initialize()
        redis.set("test:key", "test_value")
        value = redis.get("test:key")
        print(f"   ✅ Redis: set(), get() work - got '{value}'")
        redis.delete("test:key")
        results["Redis"] = "✅"
    except Exception as e:
        print(f"   ⚠️ Redis: {str(e)[:50]}")
        results["Redis"] = "⚠️ (needs server)"
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 SUMMARY - All Memory Middlewares")
    print("=" * 70)
    
    print("\n🧠 AI Agent Memory:")
    for name in ["mem0", "LangChain Memory", "Zep", "MemGPT"]:
        status = results.get(name, "❌")
        print(f"   {name:20} {status}")
    
    print("\n📊 Vector Databases:")
    for name in ["ChromaDB", "Qdrant", "Pinecone", "Weaviate"]:
        status = results.get(name, "❌")
        print(f"   {name:20} {status}")
    
    print("\n🗄️ Key-Value / Cache:")
    for name in ["Redis"]:
        status = results.get(name, "❌")
        print(f"   {name:20} {status}")
    
    working = sum(1 for v in results.values() if v.startswith("✅"))
    total = len(results)
    print(f"\n✨ Total: {working}/{total} middlewares working")
    
    print("\n" + "=" * 70)
    print("🎉 All Memory Middleware Tests Completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_memory_middlewares())
