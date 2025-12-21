"""
Qdrant Transparent Memory Middleware

Usage:
    # Initialize
    qdrant = QdrantMiddleware(
        agent_id="my-agent",
        collection_name="memories",
        url="http://localhost:6333"  # or use in-memory
    )
    await qdrant.initialize()
    
    # Use native Qdrant API directly!
    # Upsert points
    from qdrant_client.models import PointStruct
    
    qdrant.upsert(
        collection_name="memories",
        points=[
            PointStruct(id=1, vector=[...], payload={"text": "User likes Python"}),
            PointStruct(id=2, vector=[...], payload={"text": "User works at startup"})
        ]
    )
    
    # Search similar vectors
    results = qdrant.search(
        collection_name="memories",
        query_vector=[...],
        limit=5
    )
    
    # Get points
    points = qdrant.retrieve(
        collection_name="memories",
        ids=[1, 2]
    )
    
    # Delete points
    qdrant.delete(
        collection_name="memories",
        points_selector=PointIdsList(points=[1, 2])
    )
    
    All native Qdrant Client APIs are available!
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError


# Try to import Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False


class QdrantMiddleware(TransparentMemoryMiddleware):
    """
    Qdrant transparent adapter

    You can use it just like the native QdrantClient:
    - upsert(collection_name, points)
    - search(collection_name, query_vector, limit)
    - retrieve(collection_name, ids)
    - delete(collection_name, points_selector)
    - scroll(collection_name, limit)
    - get_collection(collection_name)
    - create_collection(collection_name, vectors_config)
    - delete_collection(collection_name)
    
    All native Qdrant APIs remain available.
    """
    
    def __init__(self, agent_id: str, collection_name: str = None, **config):
        super().__init__(agent_id, **config)
        self.collection_name = collection_name or f"agent_{agent_id}_memories"
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the Qdrant client"""
        if not HAS_QDRANT:
            raise MiddlewareNotAvailableError("qdrant", "pip install qdrant-client")
        
        url = self.config.get("url")
        
        if url:
            # Remote Qdrant server
            client = QdrantClient(
                url=url,
                api_key=self.config.get("api_key"),
                **self.config.get("extra_params", {})
            )
        else:
            # In-memory (for development)
            client = QdrantClient(":memory:")
        
        # Ensure collection exists
        collections = [c.name for c in client.get_collections().collections]
        
        if self.collection_name not in collections:
            dimension = self.config.get("dimension", 1536)
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
        
        return client
    
