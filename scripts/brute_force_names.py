
import logging
from middleware.special_agent import CLIENT as AGENT

logging.basicConfig(level=logging.ERROR)

def main():
    print("🔍 Brute-forcing Param names...")
    
    script = """
import unreal

def test_name(name, val):
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "GrowerActor")
    actor = actors[0]
    
    kwargs = {"target_branch_id": "TEST", name: val}
    try:
        actor.call_method("Grow_Leaves", kwargs=kwargs)
        # If it doesn't raise TypeError (invalid kwarg), it might raise "Missing Argument" (color_r)
        # That means SUCCESS on the name!
        print(f"MATCH: {name}")
        return True
    except Exception as e:
        msg = str(e)
        if "Invalid keyword argument" in msg:
            # print(f"FAIL: {name}")
            pass
        elif "required argument" in msg:
            print(f"MATCH: {name} (Error: {msg})")
            return True
        else:
            print(f"UNKNOWN ERROR for {name}: {msg}")
            
    return False

candidates_type = ["growth_type", "type", "growth", "method", "mode", "style", "branch_type"]
candidates_mod = ["growth_modifier", "modifier", "scale", "size", "factor", "growth_scale", "growth_factor"]

print("--- Testing Pos 1 (Type) Candidates ---")
for c in candidates_type:
    test_name(c, "leaf")

print("--- Testing Pos 5 (Modifier) Candidates ---")
for c in candidates_mod:
    test_name(c, 1.0)
"""
    try:
        output = AGENT.execute_python(script)
        print(output)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
