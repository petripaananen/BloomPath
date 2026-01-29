
import logging
from middleware.special_agent import CLIENT as AGENT
import json

logging.basicConfig(level=logging.ERROR) # Less noise

def main():
    script = """
import unreal
try:
    actors = unreal.GameplayStatics.get_all_actors_with_tag(unreal.EditorLevelLibrary.get_editor_world(), "GrowerActor")
    if actors:
        actor = actors[0]
        try:
            print("Testing Kwargs: target_branch_id + color_r")
            # If target_branch_id satisfied Arg0, and Arg1 is optional...
            # Providing color_r should make it complain about color_g?
            actor.call_method("Grow_Leaves", kwargs={"target_branch_id": "TEST", "color_r": 0.5}) 
        except Exception as e:
            # The exception usually lists the arguments!
            e_str = str(e)
            print(f"HINT: {e_str}")
            
except Exception as outer_e:
    print(f"OUTER_ERROR: {outer_e}")
"""
    try:
        output = AGENT.execute_python(script)
        # Manually parse the JSON output to get the clean printed text
        # (The tool wrapper returns a string, but it might be the raw JSON from the MCP if not parsed)
        print(output)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
