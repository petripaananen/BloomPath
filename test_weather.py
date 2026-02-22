import traceback
from middleware.special_agent import CLIENT

script = """
import unreal
import sys
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "GrowerActor")
if actors:
    actor = actors[0]
    try:
        actor.call_method("SetWeather", ("storm",))
        print("SetWeather('storm') invoked.")
        actor.call_method("Set_Time_Of_Day", (0.5,))
        print("Set_Time_Of_Day(0.5) invoked.")
    except Exception as e:
        print(f"Error calling UE5 methods: {e}")
else:
    print("No actors found with tag GrowerActor")
"""

try:
    print("Executing weather test...")
    res = CLIENT.execute_python(script)
    print("Result:")
    print(res)
except Exception as e:
    print("Failed:")
    traceback.print_exc()
