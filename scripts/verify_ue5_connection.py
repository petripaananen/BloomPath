import os
from ue5_interface import trigger_ue5_load_level, trigger_ue5_growth

def main():
    print("🧪 Testing UE5 Connection...")
    
    # 1. Test Growth (Confirmed to exist)
    try:
        print("  > Triggering Growth (Connection Test)...")
        # Using a dummy ID for connection test
        trigger_ue5_growth("TEST-123", growth_type="leaf")
        print("  ✅ Growth Command Sent (Connection Confirmed)")
    except Exception as e:
        print(f"  ❌ Growth Command Failed: {e}")

    # 2. Test Level Load (The new function)
    # We'll use a fake path just to see if UE5 receives the call (it might error on file not found, but connection works)
    fake_path = os.path.join(os.getcwd(), "content", "generated", "test_level.gltf")
    
    try:
        print(f"  > Triggering Level Load: {fake_path}")
        trigger_ue5_load_level(fake_path)
        print("  ✅ Load Command Sent")
    except Exception as e:
        print(f"  ❌ Load Command Failed: {e}")
        print("\nNOTE: Failure expected if 'Load_Generated_Level' function is missing in BP_GrowerActor.")

if __name__ == "__main__":
    main()
