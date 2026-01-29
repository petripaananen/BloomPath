
import asyncio
import json
import httpx
import sys
import argparse
from typing import Optional

# Configuration
MCP_SERVER_URL = "http://localhost:8767/sse"
MCP_POST_URL = "http://localhost:8767/message" # Usually SSE endpoint provides the POST URL in the first event, but checking README, it might be separate. 
# Re-reading README: "url": "http://localhost:8767/sse" -> It uses standard MCP SSE transport.
# We will use a simple implementation to list tools and call them.

async def list_tools():
    """Connects to SSE, performs handshake, and requests tools/list."""
    async with httpx.AsyncClient() as client:
        # 1. Start SSE Session
        async with client.stream("GET", MCP_SERVER_URL) as response:
            async for line in response.aiter_lines():
                if line.startswith("event: endpoint"):
                   # Verify we got the endpoint event
                   pass
                if line.startswith("data:"):
                    print(f"DEBUG RAW: {line}", file=sys.stderr)
                    payload_str = line[5:].strip()
                    if not payload_str: continue # Skip empty data lines (keep-alives)
                    try:
                        data = json.loads(payload_str)
                    except json.JSONDecodeError:
                        # Fallback: Treat as raw string (it's likely the sessionId URL)
                        data = payload_str

                    post_uri = data # The data IS the URI, usually relative or absolute
                    
                    # If relative, append to base
                    if not post_uri.startswith("http"):
                        session_id_url = f"http://localhost:8767{post_uri}"
                    else:
                        session_id_url = post_uri
                        
                    # 2. Send Initialize Request
                    init_payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "Antigravity", "version": "1.0"}
                        }
                    }
                    await client.post(session_id_url, json=init_payload)
                    
                    # 3. Wait for Initialized confirmation (skipped for brevity in this script, assuming success)
                    await client.post(session_id_url, json={
                        "jsonrpc": "2.0", 
                        "id": 2, 
                        "method": "notifications/initialized"
                    })

                    # 4. List Tools
                    tools_payload = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/list"
                    }
                    tools_resp = await client.post(session_id_url, json=tools_payload)
                    print(json.dumps(tools_resp.json(), indent=2))
                    return

async def call_tool(tool_name: str, arguments: dict):
    """Calls a specific tool."""
    async with httpx.AsyncClient() as client:
        # Same handshake dance (inefficient for one-off, but robust for CLI)
        async with client.stream("GET", MCP_SERVER_URL) as response:
             async for line in response.aiter_lines():
                if line.startswith("data:"):
                    # print(f"DEBUG RAW: {line}", file=sys.stderr)
                    payload_str = line[5:].strip()
                    if not payload_str: continue 
                    try:
                        data = json.loads(payload_str)
                    except json.JSONDecodeError:
                        data = payload_str
                    
                    if not data.startswith("http"):
                        session_id_url = f"http://localhost:8767{data}"
                    else:
                        session_id_url = data
                    
                    # Initialize
                    await client.post(session_id_url, json={
                        "jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "Antigravity", "version": "1.0"}}
                    })
                    await client.post(session_id_url, json={"jsonrpc": "2.0", "id": 2, "method": "notifications/initialized"})

                    # Call Tool
                    call_payload = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }
                    resp = await client.post(session_id_url, json=call_payload)
                    print(json.dumps(resp.json(), indent=2))
                    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["list", "call"])
    parser.add_argument("--tool", help="Name of tool to call")
    parser.add_argument("--args", help="JSON string of arguments")
    
    args = parser.parse_args()
    
    if args.mode == "list":
        asyncio.run(list_tools())
    elif args.mode == "call":
        if not args.tool:
             print("Error: --tool required for call mode")
             sys.exit(1)
        arguments = json.loads(args.args) if args.args else {}
        asyncio.run(call_tool(args.tool, arguments))
