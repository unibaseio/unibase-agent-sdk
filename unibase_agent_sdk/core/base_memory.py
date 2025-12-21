# Memory base class
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .types import MemoryRecord, DAUploadResult

class BaseMemory(ABC):
    """Base class for memory backends"""
    
    @abstractmethod
    async def save(self, record: MemoryRecord) -> str:
        """Save a memory record"""
        pass
    
    @abstractmethod
    async def retrieve(self, session_id: str, limit: int = 10) -> List[MemoryRecord]:
        """Fetch memory records"""
        pass
    
    @abstractmethod
    async def upload_to_da(self, records: List[MemoryRecord]) -> DAUploadResult:
        """Upload memory records to Unibase DA"""
        pass
