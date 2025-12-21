"""
Weaviate Transparent Memory Middleware

Usage:
    # Initialize with local server
    weaviate = WeaviateMiddleware(
        agent_id="my-agent",
        url="http://localhost:8080"
    )
    await weaviate.initialize()
    
    # Or use embedded (no server needed)
    weaviate = WeaviateMiddleware(
        agent_id="my-agent",
        embedded=True
    )
    await weaviate.initialize()
    
    # Use native Weaviate v4 API!
    # Insert objects
    collection = weaviate.collections.get("Memory")
    collection.data.insert({"text": "User likes Python", "category": "preference"})
    
    # Query objects
    response = collection.query.fetch_objects(limit=10)
    
    All native Weaviate v4 Client APIs are available!
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError


# Try to import Weaviate v4
try:
    import weaviate
    from weaviate.classes.config import Configure, Property, DataType
    HAS_WEAVIATE = True
    WEAVIATE_V4 = True
except ImportError:
    try:
        import weaviate
        HAS_WEAVIATE = True
        WEAVIATE_V4 = False
    except ImportError:
        HAS_WEAVIATE = False
        WEAVIATE_V4 = False


class WeaviateMiddleware(TransparentMemoryMiddleware):
    """
    Weaviate transparent adapter (v4)

    You can use it just like the native Weaviate client:
    - collections.get/create/delete
    - collection.data.insert/replace/update/delete
    - collection.query.fetch_objects/near_text/near_vector

    All native Weaviate APIs remain available.
    """
    
    def __init__(self, agent_id: str, class_name: str = None, **config):
        super().__init__(agent_id, **config)
        self.class_name = class_name or f"AgentMemory"
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the Weaviate client"""
        if not HAS_WEAVIATE:
            raise MiddlewareNotAvailableError("weaviate", "pip install weaviate-client")
        
        url = self.config.get("url")
        embedded = self.config.get("embedded", False)
        api_key = self.config.get("api_key")
        
        if WEAVIATE_V4:
            # Weaviate v4 API
            if embedded:
                client = weaviate.connect_to_embedded()
            elif url:
                if api_key:
                    client = weaviate.connect_to_custom(
                        http_host=url.replace("http://", "").replace("https://", "").split(":")[0],
                        http_port=int(url.split(":")[-1]) if ":" in url else 8080,
                        http_secure=url.startswith("https"),
                        auth_credentials=weaviate.auth.AuthApiKey(api_key)
                    )
                else:
                    client = weaviate.connect_to_local(
                        host=url.replace("http://", "").replace("https://", "").split(":")[0],
                        port=int(url.split(":")[-1]) if ":" in url else 8080
                    )
            else:
                # Default to local
                client = weaviate.connect_to_local()
            
            # Ensure collection exists
            if not client.collections.exists(self.class_name):
                client.collections.create(
                    name=self.class_name,
                    properties=[
                        Property(name="text", data_type=DataType.TEXT),
                        Property(name="category", data_type=DataType.TEXT),
                        Property(name="timestamp", data_type=DataType.NUMBER),
                        Property(name="agentId", data_type=DataType.TEXT),
                    ]
                )
            
            return client
        else:
            # Weaviate v3 fallback
            if api_key:
                auth_config = weaviate.AuthApiKey(api_key=api_key)
                client = weaviate.Client(url=url or "http://localhost:8080", auth_client_secret=auth_config)
            else:
                client = weaviate.Client(url=url or "http://localhost:8080")
            return client
    
