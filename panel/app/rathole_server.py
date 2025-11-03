"""Rathole server management for panel"""
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RatholeServerManager:
    """Manages Rathole server processes on the panel"""
    
    def __init__(self):
        self.config_dir = Path("/app/data/rathole")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.active_servers: Dict[str, subprocess.Popen] = {}  # tunnel_id -> process
        self.server_configs: Dict[str, dict] = {}  # tunnel_id -> config
    
    def start_server(self, tunnel_id: str, remote_addr: str, token: str, proxy_port: int) -> bool:
        """
        Start a Rathole server for a tunnel
        
        Args:
            tunnel_id: Unique tunnel identifier (used as service name)
            remote_addr: Panel address where server listens for client connections (e.g., "0.0.0.0:23333")
            token: Authentication token
            proxy_port: Port where clients will connect to access the tunneled service (e.g., 8989)
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Parse remote_addr to get bind address
            # Format: "panel.example.com:23333" or "0.0.0.0:23333"
            if ":" in remote_addr:
                bind_addr = f"0.0.0.0:{remote_addr.split(':')[1]}"
            else:
                raise ValueError(f"Invalid remote_addr format: {remote_addr}")
            
            # Stop existing server if any
            if tunnel_id in self.active_servers:
                logger.warning(f"Rathole server for tunnel {tunnel_id} already exists, stopping it first")
                self.stop_server(tunnel_id)
            
            # Create TOML configuration
            config = f"""[server]
bind_addr = "{bind_addr}"
token = "{token}"

[server.services.{tunnel_id}]
bind_addr = "0.0.0.0:{proxy_port}"
"""
            
            config_path = self.config_dir / f"{tunnel_id}.toml"
            with open(config_path, "w") as f:
                f.write(config)
            
            # Store config
            self.server_configs[tunnel_id] = {
                "remote_addr": remote_addr,
                "token": token,
                "proxy_port": proxy_port,
                "bind_addr": bind_addr,
                "config_path": str(config_path)
            }
            
            # Start rathole server
            try:
                proc = subprocess.Popen(
                    ["/usr/local/bin/rathole", "-s", str(config_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.config_dir)
                )
            except FileNotFoundError:
                # Fallback to system rathole if installed
                proc = subprocess.Popen(
                    ["rathole", "-s", str(config_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.config_dir)
                )
            
            self.active_servers[tunnel_id] = proc
            
            # Wait a moment to check if process started successfully
            time.sleep(0.5)
            if proc.poll() is not None:
                # Process died immediately
                stderr = proc.stderr.read().decode() if proc.stderr else "Unknown error"
                stdout = proc.stdout.read().decode() if proc.stdout else ""
                error_msg = f"rathole server failed to start: {stderr or stdout}"
                logger.error(error_msg)
                del self.active_servers[tunnel_id]
                if tunnel_id in self.server_configs:
                    del self.server_configs[tunnel_id]
                raise RuntimeError(error_msg)
            
            logger.info(f"✅ Started Rathole server for tunnel {tunnel_id} on {bind_addr}, proxy port: {proxy_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Rathole server for tunnel {tunnel_id}: {e}")
            # Re-raise the exception so caller can get the error message
            raise
    
    def stop_server(self, tunnel_id: str):
        """Stop Rathole server for a tunnel"""
        if tunnel_id in self.active_servers:
            proc = self.active_servers[tunnel_id]
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            except Exception as e:
                logger.warning(f"Error stopping Rathole server for tunnel {tunnel_id}: {e}")
            finally:
                del self.active_servers[tunnel_id]
            
            logger.info(f"Stopped Rathole server for tunnel {tunnel_id}")
        
        # Clean up config file
        if tunnel_id in self.server_configs:
            config_path = Path(self.server_configs[tunnel_id]["config_path"])
            if config_path.exists():
                try:
                    config_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete config file {config_path}: {e}")
            del self.server_configs[tunnel_id]
    
    def is_running(self, tunnel_id: str) -> bool:
        """Check if server is running for a tunnel"""
        if tunnel_id not in self.active_servers:
            return False
        proc = self.active_servers[tunnel_id]
        return proc.poll() is None
    
    def get_active_servers(self) -> list:
        """Get list of tunnel IDs with active servers"""
        # Filter out dead processes
        active = []
        for tunnel_id, proc in list(self.active_servers.items()):
            if proc.poll() is None:
                active.append(tunnel_id)
            else:
                # Clean up dead process
                del self.active_servers[tunnel_id]
                if tunnel_id in self.server_configs:
                    del self.server_configs[tunnel_id]
        return active
    
    def cleanup_all(self):
        """Stop all Rathole servers"""
        tunnel_ids = list(self.active_servers.keys())
        for tunnel_id in tunnel_ids:
            self.stop_server(tunnel_id)


# Global manager instance
rathole_server_manager = RatholeServerManager()

