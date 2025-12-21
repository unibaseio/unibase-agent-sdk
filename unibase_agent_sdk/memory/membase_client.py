"""Membase client for memory storage."""
from typing import List, Optional, Dict, Any
from ..core.types import MemoryRecord
import httpx
import time


class MembaseClient:
    """Membase storage client"""
    
    def __init__(self, endpoint: str, api_key: Optional[str] = None):
        self.endpoint = endpoint
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30.0)
        self._local_store: Dict[str, List[MemoryRecord]] = {}  # For offline mode
    
    async def store(self, record: MemoryRecord) -> str:
        """
        Store a memory record
        
        Args:
            record: Memory record
        
        Returns:
            str: Record ID
        """
        record_id = f"mem_{int(time.time() * 1000)}_{record.agent_id[:8]}"
        
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await self._client.post(
                f"{self.endpoint}/memories",
                json={
                    "id": record_id,
                    "session_id": record.session_id,
                    "agent_id": record.agent_id,
                    "content": record.content,
                    "timestamp": record.timestamp,
                    "metadata": record.metadata
                },
                headers=headers
            )
            response.raise_for_status()
            return response.json().get("id", record_id)
            
        except Exception as e:
            print(f"⚠️ Membase store failed, using local storage: {e}")
            # Fallback to local storage
            if record.agent_id not in self._local_store:
                self._local_store[record.agent_id] = []
            self._local_store[record.agent_id].append(record)
            return record_id
    
    async def query(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """
        Query memory records
        
        Args:
            agent_id: Agent ID
            session_id: Session ID (optional)
            limit: Maximum number of results
        
        Returns:
            List[MemoryRecord]: List of records
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            params = {
                "agent_id": agent_id,
                "limit": limit
            }
            if session_id:
                params["session_id"] = session_id
            
            response = await self._client.get(
                f"{self.endpoint}/memories",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                MemoryRecord(
                    session_id=item["session_id"],
                    agent_id=item["agent_id"],
                    content=item["content"],
                    timestamp=item["timestamp"],
                    metadata=item.get("metadata")
                )
                for item in data.get("memories", [])
            ]
            
        except Exception as e:
            print(f"⚠️ Membase query failed, using local storage: {e}")
            # Fallback to local storage
            records = self._local_store.get(agent_id, [])
            if session_id:
                records = [r for r in records if r.session_id == session_id]
            return records[:limit]
    
    async def delete(self, record_id: str) -> bool:
        """Delete a record"""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await self._client.delete(
                f"{self.endpoint}/memories/{record_id}",
                headers=headers
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def search(
        self,
        agent_id: str,
        query: str,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """
        Semantic search memory
        
        Args:
            agent_id: Agent ID
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List[MemoryRecord]: Matching records
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await self._client.post(
                f"{self.endpoint}/memories/search",
                json={
                    "agent_id": agent_id,
                    "query": query,
                    "limit": limit
                },
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                MemoryRecord(
                    session_id=item["session_id"],
                    agent_id=item["agent_id"],
                    content=item["content"],
                    timestamp=item["timestamp"],
                    metadata=item.get("metadata")
                )
                for item in data.get("results", [])
            ]
            
        except Exception as e:
            print(f"⚠️ Membase search failed: {e}")
            return []
    
    async def close(self):
        """Close the client"""
        await self._client.aclose()
