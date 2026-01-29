"""Find available static mesh assets in UE5."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from middleware.special_agent import CLIENT

def main():
    # Find assets with "Cube" in the name
    result = CLIENT.call_tool('assets/find', {'name': 'Cube'})
    content = result.get('content', [])
    if not content:
        print("No content returned")
        return
    
    text = content[0].get('text', '{}')
    data = json.loads(text)
    assets = data.get('assets', [])
    
    print(f"Found {data.get('count', len(assets))} assets matching 'Cube':\n")
    for asset in assets[:20]:
        print(f"  - {asset.get('path', asset.get('name', 'Unknown'))}")

if __name__ == "__main__":
    main()
