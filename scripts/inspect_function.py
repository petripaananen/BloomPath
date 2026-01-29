
import logging
from middleware.special_agent import CLIENT as AGENT

logging.basicConfig(level=logging.INFO)

def main():
    print("🔍 Inspecting Grow_Leaves signature...")
    
    script = """
import unreal

def inspect():
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.GameplayStatics.get_all_actors_with_tag(world, "GrowerActor")
    if not actors:
        print("No GrowerActor found")
        return

    actor = actors[0]
    func_name = "Grow_Leaves"
    func = actor.get_class().find_function_by_name(func_name)
    
    if not func:
        print(f"Function {func_name} not found on actor class")
        return
        
    print(f"--- Signature for {func_name} ---")
    
    # Iterate properties using reflection (FProperty)
    # Note: In Python API, we loop internal fields if exposed, or rely on heuristics
    # Actually, let's try to just print the property names and their classes
    
    # Standard UFunction iteration
    for prop in unreal.UserDefinedStruct(func).get_editor_property("child_properties"): # This assumes python wrapper structure
         # fallback for unknown API version
         pass
         
    # Reliable way:
    # A UFunction is a UStruct. We can iterate its children.
    # In recent Unreal Python:
    
    child = func.get_child_properties() # This might fail if not exposed
    # Let's try explicit loop if child_properties is not a list
    
    # ALTERNATIVE: Use the Reflection Library if available, or just guess execution
    
    # Let's try iterating via `params` logic manually
    import inspect
    # This won't work on UObjects wrappers easily.
    
    # Let's try to just print the Child Param names using internal linked list if possible
    # or just print the Function object, sometimes it dumps info
    print(f"Function Object: {func}")
    
    # Try getting FProperties
    # properties = unreal.SystemLibrary.get_object_property_names(func) # No
    
    # Let's try 'GetMetaData'
    
    # Ok, deeper reflection:
    # It seems 'args' for call_method must match.
    # We really need to know the order.
    # Let's try to look at 'editor_properties' of the UFunction if it's a BP Function
    
    pass

# Simplified Approach: 
# Just try to dump the function parameters using a known hack or loop
# In Unreal Python, `func.children` is not iteratable directly sometimes.

# Try this:
actors = unreal.GameplayStatics.get_all_actors_with_tag(unreal.EditorLevelLibrary.get_editor_world(), "GrowerActor")
if actors:
    actor = actors[0]
    # We can try to get the function from the class
    cls = actor.get_class()
    # There isn't a great "list_params" in Python API standard.
    # BUT, we can try to confirm if 'Growth_Type' is what it thinks it is.
    
    print("Actor Class:", cls.get_name())
    
    # Another trick: Try to call it with NO args and see the error?
    # Usually gives "Missing arg X" which tells us the name!
    try:
        actor.call_method("Grow_Leaves")
    except Exception as e:
        print(f"Signature Hint: {e}")

inspect()
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
