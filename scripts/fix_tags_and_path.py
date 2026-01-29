
import logging
from middleware.special_agent import CLIENT as AGENT

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    print("🔧 Attempting to fix Tags for GrowerActor...")
    
    script = """
import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
target_tag = "GrowerActor"
fixed_count = 0

print(f"Scanning {len(all_actors)} actors for potential GrowerActor candidates...")

for a in all_actors:
    name = a.get_name()
    # Heuristic: Look for "Grower" in the name (e.g., BP_GrowerActor_C_1)
    if "Grower" in name or "BP_Grower" in name:
        tags = [str(t) for t in a.tags]
        if target_tag not in tags:
            print(f"🛠️ FIXING: Found candidate {name} without tag. Adding '{target_tag}'...")
            a.tags.append(target_tag)
            fixed_count += 1
        else:
            print(f"✅ OK: Candidate {name} already has tag.")

if fixed_count > 0:
    print(f"SUCCESS: Added tag to {fixed_count} actors.")
else:
    print("INFO: No new actors needed tagging.")
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
