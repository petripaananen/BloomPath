import traceback
from middleware.special_agent import CLIENT

script = """
import unreal
import sys
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "GrowerActor")
if actors:
    actor = actors[0]
    print(f"Actor found: {actor.get_name()}")
    try:
        actor.call_method("Load_Generated_Level", (r"C:/fake/path.gltf",))
        print("Call method invoked.")
    except Exception as e:
        print(f"Error calling Load_Generated_Level: {e}")
else:
    print("No actors found with tag GrowerActor")
"""

try:
    print("Executing script...")
    res = CLIENT.execute_python(script)
    print("Result:")
    print(res)
except Exception as e:
    print("Failed:")
    traceback.print_exc()
