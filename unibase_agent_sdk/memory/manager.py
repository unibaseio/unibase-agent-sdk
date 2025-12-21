"""Memory Manager with middleware support."""
from typing import List, Optional, Dict, Any
from ..core.base_memory import BaseMemory
from ..core.types import MemoryRecord, DAUploadResult
from ..core.exceptions import MemoryError, MiddlewareError
from ..utils.logger import get_logger
from .membase_client import MembaseClient
from .da_uploader import DAUploader

# Use TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .middlewares.base import TransparentMemoryMiddleware

logger = get_logger("memory.manager")


class MemoryManager(BaseMemory):
    """
    Enhanced Memory Manager.
    Supports multiple middlewares + Membase + DA upload.
    """
    
    def __init__(
        self,
        membase_endpoint: str,
        da_endpoint: str,
        agent_id: str,
        middlewares: Optional[List['TransparentMemoryMiddleware']] = None
    ):
        self.agent_id = agent_id
        self.membase = MembaseClient(membase_endpoint)
        self.da_uploader = DAUploader(da_endpoint)
        
        # Support multiple middlewares
        self.middlewares: List['TransparentMemoryMiddleware'] = middlewares or []
        self._local_cache: List[MemoryRecord] = []
    
    def add_middleware(self, middleware: 'TransparentMemoryMiddleware') -> None:
        """Add a memory middleware."""
        self.middlewares.append(middleware)
    
    async def save(
        self,
        record: MemoryRecord,
        use_middleware: bool = True
    ) -> str:
        """
        Save a record.
        
        Args:
            record: Memory record
            use_middleware: Whether to also save to middlewares
        
        Returns:
            Record ID
        """
        # Save to Membase
        record_id = await self.membase.store(record)
        
        # Also save to all middlewares
        if use_middleware:
            for middleware in self.middlewares:
                try:
                    await middleware.add(
                        content=str(record.content),
                        metadata=record.metadata
                    )
                except Exception as e:
                    logger.warning(
                        f"Middleware save failed: {middleware.get_middleware_name()}",
                        exc_info=True
                    )
        
        # Add to local cache
        self._local_cache.append(record)
        
        return record_id
    
    async def retrieve(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """Retrieve from Membase."""
        return await self.membase.query(
            agent_id=self.agent_id,
            session_id=session_id,
            limit=limit
        )
    
    async def upload_to_da(self) -> DAUploadResult:
        """
        Upload to Unibase DA.

        Returns:
            Upload result
        """
        records = self._local_cache.copy()

        # Serialize and upload
        serialized = self._serialize_records(records)
        result = await self.da_uploader.upload(serialized)

        # Clear cache
        self._local_cache.clear()

        return result
    
    def _serialize_records(self, records: List[MemoryRecord]) -> bytes:
        """Serialize records."""
        import json
        data = [
            {
                "session_id": r.session_id,
                "agent_id": r.agent_id,
                "content": r.content,
                "timestamp": r.timestamp,
                "metadata": r.metadata
            }
            for r in records
        ]
        return json.dumps(data, ensure_ascii=False).encode()
