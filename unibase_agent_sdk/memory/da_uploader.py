# Unibase DA uploader
from typing import Optional, Dict, Any
from ..core.types import DAUploadResult
import httpx
import time

class DAUploader:
    """Uploader client for Unibase DA"""
    
    def __init__(self, da_endpoint: str, api_key: Optional[str] = None):
        self.da_endpoint = da_endpoint
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def upload(
        self,
        data: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DAUploadResult:
        """
        Upload data to Unibase DA
        
        Args:
            data: Raw bytes to upload
            metadata: Optional metadata
        
        Returns:
            DAUploadResult: Upload result details
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Upload to DA
        response = await self.client.post(
            f"{self.da_endpoint}/upload",
            content=data,
            headers=headers,
            json={"metadata": metadata} if metadata else None
        )
        
        response.raise_for_status()
        result = response.json()
        
        return DAUploadResult(
            transaction_hash=result["tx_hash"],
            da_url=result["url"],
            size=len(data),
            timestamp=time.time()
        )
    
    async def verify(self, transaction_hash: str) -> bool:
        """Verify an upload stored in DA"""
        response = await self.client.get(
            f"{self.da_endpoint}/verify/{transaction_hash}"
        )
        return response.json()["verified"]
