"""Test spawning a basic cube in UE5 via Special Agent MCP."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from middleware.special_agent import CLIENT

def test_spawn():
    script = """
import unreal

# Get the basic cube mesh from Engine
cube_mesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube')
print(f"Cube mesh: {cube_mesh}")

# Find all available BasicShapes
basic_shapes = unreal.EditorAssetLibrary.list_assets('/Engine/BasicShapes', recursive=True)
print("Available BasicShapes:")
for shape in basic_shapes:
    print(f"  - {shape}")
"""
    result = CLIENT.execute_python(script)
    print(result)

if __name__ == "__main__":
    test_spawn()
