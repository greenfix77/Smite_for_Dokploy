"""Client for panel to communicate with nodes"""
import httpx
import ssl
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Node, Settings

logger = logging.getLogger(__name__)


class NodeClient:
    """Client to send requests to nodes via HTTP/HTTPS or FRP"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
    
    async def _get_frp_settings(self) -> Optional[Dict[str, Any]]:
        """Get FRP communication settings"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Settings).where(Settings.key == "frp"))
            setting = result.scalar_one_or_none()
            if setting and setting.value and setting.value.get("enabled"):
                return setting.value
        return None
    
    async def _get_node_address(self, node: Node) -> Tuple[str, bool]:
        """
        Get node address (direct or via FRP)
        Returns: (address, using_frp)
        """
        frp_settings = await self._get_frp_settings()
        
        if frp_settings and frp_settings.get("enabled"):
            frp_remote_port = node.node_metadata.get("frp_remote_port") if node.node_metadata else None
            if frp_remote_port:
                # FRP is enabled and node has reported its remote port - use FRP only
                logger.info(f"[FRP] Using FRP tunnel to communicate with node {node.id} (remote_port={frp_remote_port})")
                return (f"http://127.0.0.1:{frp_remote_port}", True)
            else:
                # FRP is enabled but node hasn't reported its remote port yet (during initial setup)
                logger.warning(f"[HTTP] FRP enabled but node {node.id} has no frp_remote_port yet, temporarily using HTTP")
                logger.warning(f"[HTTP] This should only happen during node registration. After FRP setup, all communication will use FRP.")
        
        # FRP is not enabled - use HTTP
        node_address = node.node_metadata.get("api_address", f"http://localhost:8888") if node.node_metadata else f"http://localhost:8888"
        if not node_address.startswith("http"):
            node_address = f"http://{node_address}"
        logger.info(f"[HTTP] Using direct HTTP to communicate with node {node.id} at {node_address}")
        return (node_address, False)
    
    async def send_to_node(self, node_id: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request to node via HTTPS or FRP
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()
            
            if not node:
                return {"status": "error", "message": f"Node {node_id} not found"}
            
            node_address, using_frp = await self._get_node_address(node)
            url = f"{node_address.rstrip('/')}{endpoint}"
            
            comm_type = "FRP" if using_frp else "HTTP"
            logger.debug(f"[{comm_type}] Sending request to node {node_id}: {endpoint}")
            
            # For FRP connections, verify the tunnel is ready with a quick health check
            if using_frp:
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0), verify=False) as test_client:
                        test_url = f"{node_address.rstrip('/')}/api/agent/status"
                        await test_client.get(test_url)
                except Exception as e:
                    logger.warning(f"[FRP] Tunnel health check failed for node {node_id}, will retry: {e}")
            
            try:
                # Retry logic for FRP connections which may need a moment to stabilize
                max_retries = 3 if using_frp else 1
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                            response = await client.post(url, json=data)
                            response.raise_for_status()
                            return response.json()
                    except httpx.RequestError as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1.0)  # Longer delay for FRP retries
                            logger.debug(f"[{comm_type}] Retry {attempt + 1}/{max_retries} for node {node_id}")
                            continue
                        else:
                            error_msg = f"Network error: {str(e)}"
                            if using_frp:
                                error_msg += f" (FRP tunnel may not be ready, tried {max_retries} times)"
                            return {"status": "error", "message": error_msg}
                
                # Should not reach here, but just in case
                return {"status": "error", "message": f"Network error: {str(last_error)}"}
            except httpx.HTTPStatusError as e:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except:
                    error_detail = str(e)
                return {"status": "error", "message": f"Node error (HTTP {e.response.status_code}): {error_detail}"}
            except Exception as e:
                return {"status": "error", "message": f"Error: {str(e)}"}
    
    async def get_tunnel_status(self, node_id: str, tunnel_id: str = "") -> Dict[str, Any]:
        """Get tunnel status from node"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Node).where(Node.id == node_id))
            node = result.scalar_one_or_none()
            
            if not node:
                return {"status": "error", "message": f"Node {node_id} not found"}
            
            node_address, using_frp = await self._get_node_address(node)
            url = f"{node_address.rstrip('/')}/api/agent/status"
            
            comm_type = "FRP" if using_frp else "HTTP"
            logger.debug(f"[{comm_type}] Getting tunnel status from node {node_id}")
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.json()
            except httpx.RequestError as e:
                return {"status": "error", "message": f"Network error: {str(e)}"}
            except httpx.HTTPStatusError as e:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except:
                    error_detail = str(e)
                return {"status": "error", "message": f"Node error (HTTP {e.response.status_code}): {error_detail}"}
            except Exception as e:
                return {"status": "error", "message": f"Error: {str(e)}"}
    
    async def apply_tunnel(self, node_id: str, tunnel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply tunnel to node"""
        return await self.send_to_node(node_id, "/api/agent/tunnels/apply", tunnel_data)
