
import asyncio
import logging
from middleware.special_agent import CLIENT as AGENT

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    print("🔍 Scanning Current Level via Special Agent...")
    
    script = """
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
print(f"Found {len(all_actors)} actors in level: {world.get_name()}")

found_grower = False
for a in all_actors:
    name = a.get_name()
    path = a.get_path_name()
    if "Grower" in name or "Garden" in path:
        print(f"🌿 MATCH: {name} => {path}")
        # Check tags
        tags = [str(t) for t in a.tags]
        print(f"   Tags: {tags}")
        if "GrowerActor" in tags:
            found_grower = True
            
if found_grower:
    print("✅ SUCCESS: GrowerActor with correct TAG found!")
else:
    print("⚠️  WARNING: No actor with tag 'GrowerActor' found.")
"""
    try:
        output = AGENT.execute_python(script)
        print("--- UE5 Output ---")
        print(output)
        print("------------------")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
