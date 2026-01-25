import os
from ue5_interface import trigger_ue5_load_level

def main():
    print("🧪 Testing UE5 Load_Generated_Level ONLY...")
    
    fake_path = os.path.join(os.getcwd(), "content", "generated", "test_level.gltf")
    
    # Try variations of the parameter name
    param_variations = ["File_Path", "File Path", "FilePath", "aaa"] # 'aaa' just in case user didn't rename default
    
    for param_name in param_variations:
        print(f"\n🔍 Testing Parameter Name: '{param_name}'")
        try:
            # Manually construct payload here to override the function's default 'File_Path'
            import requests
            # Re-import to ensure we have vars
            from ue5_interface import UE5_ACTOR_PATH, UE5_REMOTE_CONTROL_URL, UE5_LOAD_LEVEL_FUNCTION
            
            payload = {
                "objectPath": UE5_ACTOR_PATH,
                "functionName": UE5_LOAD_LEVEL_FUNCTION,
                "parameters": {
                    param_name: fake_path
                },
                "generateTransaction": False
            }
            
            response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=2)
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS! The correct parameter name is: '{param_name}'")
                return
            else:
                 print(f"  ❌ Failed ({response.status_code})")
                 
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n❌ All parameter variations failed.")
    print("Suggestion: Check 'Call In Editor' in Blueprint or rename Input to 'File_Path'.")
    print("  2. It has ONE input named 'File_Path' (String)")

if __name__ == "__main__":
    main()
