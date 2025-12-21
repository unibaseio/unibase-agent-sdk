"""
ChromaDB Transparent Memory Middleware

Usage:
    # Initialize
    chroma = ChromaDBMiddleware(
        agent_id="my-agent",
        collection_name="memories",
        persist_directory="./chroma_db"  # Optional
    )
    await chroma.initialize()
    
    # Use native ChromaDB API directly!
    # Add documents
    chroma.add(
        documents=["User likes Python", "User works at startup"],
        metadatas=[{"category": "preference"}, {"category": "work"}],
        ids=["mem1", "mem2"]
    )
    
    # Query similar documents
    results = chroma.query(
        query_texts=["What does user like?"],
        n_results=5
    )
    
    # Get specific documents
    docs = chroma.get(ids=["mem1", "mem2"])
    
    # Update documents
    chroma.update(ids=["mem1"], documents=["User loves Python"])
    
    # Delete documents
    chroma.delete(ids=["mem1"])
    
    # Count documents
    count = chroma.count()
    
    All native ChromaDB Collection APIs are available!
"""
from typing import Any
from .base import TransparentMemoryMiddleware
from ...core.exceptions import MiddlewareNotAvailableError

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class ChromaDBMiddleware(TransparentMemoryMiddleware):
    """
    ChromaDB transparent adapter

    You can use it just like a native ChromaDB Collection:
    - add(documents, metadatas, ids, embeddings)
    - query(query_texts, n_results, where, where_document)
    - get(ids, where, where_document, include)
    - update(ids, documents, metadatas, embeddings)
    - delete(ids, where, where_document)
    - count()
    - peek()
    - modify(name, metadata)

    All native ChromaDB APIs remain available.
    """
    
    def __init__(self, agent_id: str, collection_name: str = None, **config):
        super().__init__(agent_id, **config)
        self.collection_name = collection_name or f"agent_{agent_id}_memories"
        self._client = None
    
    async def _initialize_middleware(self) -> Any:
        """Initialize the ChromaDB collection"""
        if not HAS_CHROMADB:
            raise MiddlewareNotAvailableError("chromadb", "pip install chromadb")
        
        persist_directory = self.config.get("persist_directory")
        
        if persist_directory:
            # Persistent storage
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            # In-memory (ephemeral)
            self._client = chromadb.Client()
        
        # Get or create collection
        collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata=self.config.get("collection_metadata", {"agent_id": self.agent_id})
        )
        
        return collection
    
    def get_client(self) -> Any:
        """Return the ChromaDB client (for advanced operations)"""
        return self._client
