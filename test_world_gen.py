import os
import logging
from dotenv import load_dotenv
from world_client import WorldLabsClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_direct_client():
    load_dotenv()
    
    api_key = os.getenv("WORLD_LABS_API_KEY")
    if not api_key:
        print("Error: WORLD_LABS_API_KEY not found in environment.")
        return

    client = WorldLabsClient(api_key=api_key)
    
    # Test Prompt
    prompt = "A small low-poly floating island with a single tree"
    output_path = "test_output/island.gltf"
    
    print(f"Testing generation with prompt: '{prompt}'")
    
    result = client.generate_world(prompt, output_path)
    
    if result:
        print(f"SUCCESS: Generated world saved to {result}")
    else:
        print("FAILURE: Generation failed.")

if __name__ == "__main__":
    test_direct_client()
