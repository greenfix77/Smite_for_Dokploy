"""Client for panel to communicate with nodes"""
import httpx
import ssl
from typing import Dict, Any, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Node


class Hysteria2Client:
    """Client to send requests to nodes via HTTPS (mTLS)"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
    
    async def send_to_node(self, node_id: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request to node via HTTPS
        """
        # Get node info from database
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()
            
            if not node:
                return {"status": "error", "message": f"Node {node_id} not found"}
            
            # Extract node address from metadata or use default
            node_address = node.node_metadata.get("api_address", f"http://localhost:8888") if node.node_metadata else f"http://localhost:8888"
            
            # Construct full URL
            if not node_address.startswith("http"):
                node_address = f"http://{node_address}"
            
            url = f"{node_address.rstrip('/')}{endpoint}"
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                    response = await client.post(url, json=data)
                    response.raise_for_status()
                    return response.json()
            except httpx.RequestError as e:
                return {"status": "error", "message": f"Network error: {str(e)}"}
            except httpx.HTTPStatusError as e:
                # Try to get error details from response body
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except:
                    error_detail = str(e)
                return {"status": "error", "message": f"Node error (HTTP {e.response.status_code}): {error_detail}"}
            except Exception as e:
                return {"status": "error", "message": f"Error: {str(e)}"}
