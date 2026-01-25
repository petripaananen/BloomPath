import logging
import json
import httpx
import time
from typing import Any, Optional, Dict

logger = logging.getLogger("BloomPath.SpecialAgent")

class SpecialAgentClient:
    """
    Client for interacting with the SpecialAgent MCP Server (Unreal Engine 5).
    Uses HTTP/SSE for transport (Synchronous version for Flask compatibility).
    """
    
    def __init__(self, base_url: str = "http://localhost:8767"):
        self.base_url = base_url.rstrip("/")
        self.sse_url = f"{self.base_url}/sse"
        self.session_id_url: Optional[str] = None
        self._initialized = False

    def _ensure_connection(self):
        """
        Establishes the SSE handshake if not already active.
        """
        if self._initialized and self.session_id_url:
            return

        logger.debug(f"Connecting to SpecialAgent at {self.sse_url}...")
        
        with httpx.Client() as client:
            with client.stream("GET", self.sse_url, timeout=5.0) as response:
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        payload_str = line[5:].strip()
                        if not payload_str: continue
                        
                        try:
                            data = json.loads(payload_str)
                        except json.JSONDecodeError:
                            data = payload_str 
                        
                        if isinstance(data, str):
                            endpoint = data
                            if not endpoint.startswith("http"):
                                self.session_id_url = f"{self.base_url}{endpoint}"
                            else:
                                self.session_id_url = endpoint
                            
                            logger.info(f"SpecialAgent Session established: {self.session_id_url}")
                            self._initialize_session()
                            return

    def _initialize_session(self):
        """Sends the JSON-RPC initialize request."""
        with httpx.Client() as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", # MCP Version
                    "capabilities": {},
                    "clientInfo": {"name": "BloomPathMiddleware", "version": "1.0"}
                }
            }
            client.post(self.session_id_url, json=payload)
            
            # Notify initialized
            client.post(self.session_id_url, json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "notifications/initialized"
            })
            self._initialized = True

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls an MCP tool on the SpecialAgent server.
        """
        self._ensure_connection()
        
        if not self.session_id_url:
            raise ConnectionError("Failed to establish SpecialAgent session.")

        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self.session_id_url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            
            if "error" in result:
                logger.error(f"MCP Error: {result['error']}")
                raise Exception(f"MCP Tool Error: {result['error'].get('message', 'Unknown')}")
            
            return result.get("result", {})

    def execute_python(self, code: str) -> str:
        """
        Helper to execute raw Python code in UE5.
        Returns the stdout/result.
        """
        # The parameter name defined in PythonService.cpp is 'code'
        result = self.call_tool("python/execute", {"code": code})
        
        # Parse result text from content block
        content = result.get("content", [])
        output = ""
        for block in content:
            if block["type"] == "text":
                output += block["text"]
        return output

# Singleton instance
CLIENT = SpecialAgentClient()

