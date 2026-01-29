"""List all actors in the current UE5 level via Special Agent MCP."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from middleware.special_agent import CLIENT

def main():
    result = CLIENT.call_tool('world/list_actors', {})
    content = result.get('content', [])
    if not content:
        print("No content returned")
        return
    
    text = content[0].get('text', '{}')
    data = json.loads(text)
    actors = data.get('actors', [])
    
    print(f"Total actors: {data.get('count', len(actors))}\n")
    print(f"{'Name':<45} | {'Class'}")
    print("-" * 80)
    
    # Group by class for better overview
    class_groups = {}
    for actor in actors:
        cls = actor.get('class', 'Unknown')
        if cls not in class_groups:
            class_groups[cls] = []
        class_groups[cls].append(actor.get('name', 'Unnamed'))
    
    for cls, names in sorted(class_groups.items()):
        print(f"\n[{cls}] ({len(names)} actors)")
        for name in names[:5]:  # Show first 5 of each class
            print(f"  - {name}")
        if len(names) > 5:
            print(f"  ... and {len(names) - 5} more")

if __name__ == "__main__":
    main()
