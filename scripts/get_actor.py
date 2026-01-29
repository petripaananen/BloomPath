"""Get details of a specific actor."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from middleware.special_agent import CLIENT

def get_actor(name: str):
    result = CLIENT.call_tool('world/get_actor', {'actor_name': name})
    content = result.get('content', [])
    if not content:
        print("No content returned")
        return
    
    text = content[0].get('text', '{}')
    data = json.loads(text)
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "PlayerStart"
    get_actor(name)
