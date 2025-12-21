"""
Pinecone Transparent Memory Middleware

Usage:
    # Initialize
    pinecone = PineconeMiddleware(
        agent_id="my-agent",
        api_key="xxx",  # or set PINECONE_API_KEY env var
        index_name="agent-memory"
    )
    await pinecone.initialize()
    
    # Use native Pinecone Index API directly!
    # Upsert vectors
    pinecone.upsert(
        vectors=[
            {"id": "mem1", "values": [...], "metadata": {"text": "User likes Python"}},
            {"id": "mem2", "values": [...], "metadata": {"text": "User works at startup"}}
        ]
    )
    
    # Query similar vectors
    results = pinecone.query(
        vector=[...],
        top_k=5,
        include_metadata=True
    )
    
    # Fetch specific vectors
    fetched = pinecone.fetch(ids=["mem1", "mem2"])
    
    # Delete vectors
    pinecone.delete(ids=["mem1"])
    
    # Describe index stats
    stats = pinecone.describe_index_stats()
    
    All native Pinecone Index APIs are available!
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError, ConfigurationError
import os

# Try to import Pinecone
try:
    from pinecone import Pinecone, ServerlessSpec
    HAS_PINECONE = True
except ImportError:
    HAS_PINECONE = False


class PineconeMiddleware(TransparentMemoryMiddleware):
    """
    Pinecone transparent adapter

    You can use it just like a native Pinecone Index:
    - upsert(vectors, namespace)
    - query(vector, top_k, include_metadata, filter)
    - fetch(ids, namespace)
    - delete(ids, delete_all, namespace, filter)
    - update(id, values, set_metadata)
    - describe_index_stats()
    
    All native Pinecone APIs remain available.
    """
    
    def __init__(self, agent_id: str, index_name: str = None, **config):
        super().__init__(agent_id, **config)
        self.index_name = index_name or f"agent-{agent_id}"
        self._client = None
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the Pinecone index"""
        if not HAS_PINECONE:
            raise MiddlewareNotAvailableError("pinecone", "pip install pinecone-client")

        api_key = self.config.get("api_key") or os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ConfigurationError("Pinecone API key required. Set PINECONE_API_KEY or pass api_key.")
        
        # Initialize Pinecone client
        self._client = Pinecone(api_key=api_key)
        
        # Get or create index
        existing_indexes = [idx.name for idx in self._client.list_indexes()]
        
        if self.index_name not in existing_indexes:
            # Create new index
            dimension = self.config.get("dimension", 1536)  # OpenAI embedding dimension
            metric = self.config.get("metric", "cosine")
            cloud = self.config.get("cloud", "aws")
            region = self.config.get("region", "us-east-1")
            
            self._client.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud=cloud, region=region)
            )
        
        # Return index for transparent access
        return self._client.Index(self.index_name)
    
    def get_client(self) -> Any:
        """Return the Pinecone client (for advanced operations)"""
        return self._client
