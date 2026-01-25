import requests
import os

# Confirmed Port
URL = "http://localhost:30010/remote/object/call"

# Base variations
LEVEL_NAMES = ["Garden", "Main", "ThirdPersonMap"]
ACTOR_NAMES = ["BP_GrowerActor", "GrowerActor", "BP_GrowerActor_C_1", "BP_GrowerActor2"]

def check_path(path):
    # Try to call a non-existent function just to see if the OBJECT exists.
    # If Object exists but function doesn't, we usually get a specific error or 400.
    # If Object doesn't exist, we definitely get "Object ... does not exist" in logs
    # BUT checking response code: 
    # 400 usually means Object found (deserialized) but call failed.
    # 404 might be returned for bad route, but bad object is often 400 with message.
    
    # Let's try to call 'GetActorLabel' or simple function that might exist, 
    # or our known 'Load_Generated_Level'.
    
    payload = {
        "objectPath": path,
        "functionName": "Load_Generated_Level", 
        "parameters": { "File_Path": "TEST_SCAN" },
        "generateTransaction": True
    }
    
    try:
        response = requests.put(URL, json=payload, timeout=2)
        # If we get 200, we struck gold.
        if response.status_code == 200:
            print(f"✅ FOUND! {path}")
            return True
        elif response.status_code == 400:
            # Ambiguous. Could be "Object not found" OR "Function signature mismatch".
            # UE5 unfortunately sends 400 for both often. We rely on the User Log normally.
            print(f"⚠️  400 for {path} (Might be right path, wrong signature?)")
            return False
        else:
            print(f"❌ {response.status_code} for {path}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print(f"🔍 Scanning UE5 Actor Paths on {URL}...")
    
    # Construct common paths
    paths_to_try = []
    
    for level in LEVEL_NAMES:
        # Standard: /Game/Maps/Level.Level:PersistentLevel.Actor
        base_1 = f"/Game/Maps/{level}.{level}:PersistentLevel"
        # Folder? /Game/Level/Level.Level...
        base_2 = f"/Game/{level}/{level}.{level}:PersistentLevel"
        
        for base in [base_1, base_2]:
            for actor in ACTOR_NAMES:
                paths_to_try.append(f"{base}.{actor}")
                
    # Manual Override based on user screenshot hints if any
    paths_to_try.append("/Game/Maps/Garden/Garden.Garden:PersistentLevel.BP_GrowerActor")

    found = False
    for path in paths_to_try:
        if check_path(path):
            found = True
            break
            
    if not found:
        print("\n❌ Scanner finished. No exact 200 OK match found.")
        print("Please use 'Right Click -> Copy Object Path' in UE5 to be sure.")

if __name__ == "__main__":
    main()
