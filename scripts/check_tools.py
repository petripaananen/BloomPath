import asyncio
import logging
from middleware.special_agent import SpecialAgentClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)

async def main():
    client = SpecialAgentClient()
    # Manually call list tools since the class doesn't expose it directly yet
    await client._ensure_connection()
    
    import httpx
    async with httpx.AsyncClient() as http:
        resp = await http.post(client.session_id_url, json={
            "jsonrpc": "2.0",
            "id": 99,
            "method": "tools/list"
        })
        print(resp.json())

if __name__ == "__main__":
    asyncio.run(main())
