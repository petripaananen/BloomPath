"""
Build a small wooden cabin in UE5 via Special Agent MCP.
Based on Linear issue WFM-8: "Small wooded cabin"
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from middleware.special_agent import CLIENT

# Cabin base position (near the garden area)
BASE_X = -400
BASE_Y = 300
BASE_Z = 92

def spawn_static_mesh(name: str, mesh_path: str, location: tuple, scale: tuple, rotation: tuple = (0, 0, 0)):
    """Spawn a StaticMeshActor with the given mesh and transform."""
    script = f"""
import unreal

# Load the mesh
mesh = unreal.EditorAssetLibrary.load_asset('{mesh_path}')
if not mesh:
    print(f"ERROR: Could not load mesh {mesh_path}")
else:
    # Spawn the actor
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # Create a StaticMeshActor
    actor_class = unreal.StaticMeshActor
    location = unreal.Vector({location[0]}, {location[1]}, {location[2]})
    rotation = unreal.Rotator({rotation[0]}, {rotation[1]}, {rotation[2]})
    
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)
    
    if actor:
        # Set the mesh
        actor.static_mesh_component.set_static_mesh(mesh)
        
        # Set scale
        actor.set_actor_scale3d(unreal.Vector({scale[0]}, {scale[1]}, {scale[2]}))
        
        # Rename the actor
        actor.set_actor_label('{name}')
        
        # Add a tag for easy identification
        actor.tags.append('Cabin_WFM8')
        
        print(f"SUCCESS: Spawned {name}")
    else:
        print(f"ERROR: Failed to spawn {name}")
"""
    result = CLIENT.execute_python(script)
    print(f"  {name}: {result}")
    return result

def build_cabin():
    """Build all cabin components."""
    print("🏠 Building Wooden Cabin (WFM-8)...\n")
    
    cube_path = '/Engine/BasicShapes/Cube'
    cone_path = '/Engine/BasicShapes/Cone'
    
    # Component definitions: (name, mesh, location_offset, scale)
    components = [
        # Floor - flat cube as foundation
        ("Cabin_Floor", cube_path, (0, 0, 10), (3.0, 3.0, 0.2)),
        
        # Walls - tall thin cubes
        ("Cabin_Wall_Front", cube_path, (0, -140, 110), (3.0, 0.2, 2.0)),
        ("Cabin_Wall_Back", cube_path, (0, 140, 110), (3.0, 0.2, 2.0)),
        ("Cabin_Wall_Left", cube_path, (-140, 0, 110), (0.2, 3.0, 2.0)),
        ("Cabin_Wall_Right", cube_path, (140, 0, 110), (0.2, 3.0, 2.0)),
        
        # Roof - cone on top
        ("Cabin_Roof", cone_path, (0, 0, 260), (3.5, 3.5, 1.5)),
        
        # Door - small cube on front wall (darker to simulate opening)
        ("Cabin_Door", cube_path, (0, -145, 70), (0.6, 0.25, 1.2)),
    ]
    
    for name, mesh, offset, scale in components:
        # Calculate world position
        world_pos = (BASE_X + offset[0], BASE_Y + offset[1], BASE_Z + offset[2])
        spawn_static_mesh(name, mesh, world_pos, scale)
    
    print("\n✅ Cabin construction complete!")
    print(f"   Location: ({BASE_X}, {BASE_Y}, {BASE_Z})")

if __name__ == "__main__":
    build_cabin()
