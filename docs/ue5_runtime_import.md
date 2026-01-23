# UE5 Runtime Import Guide (glTFRuntime)

This guide explains how to import World Labs generated `.glb` files into Unreal Engine 5 at runtime.

## Prerequisites

1. **Install glTFRuntime Plugin**
   - Download from [Fab Marketplace](https://www.fab.com/listings/bde9c749-5f1a-4f8b-b7f4-67a134e45f00) (Free)
   - Or clone from [GitHub](https://github.com/rdeioris/glTFRuntime)
   - Place in `YourProject/Plugins/glTFRuntime/`
   - Restart UE5 Editor

2. **Enable Plugin**
   - Edit > Plugins > Search "glTFRuntime" > Enable
   - Restart Editor

---

## Step 1: Create Import Actor

1. Content Browser > Right-click > **Blueprint Class** > **Actor**
2. Name: `BP_WorldImporter`
3. Add Variable:
   | Name | Type | Default |
   |------|------|---------|
   | `GeneratedWorldActor` | Actor Reference | None |

---

## Step 2: Create Import Function

### Function: `Import_World_From_File`
- **Input**: `FilePath` (String)
- **Output**: `Success` (Boolean)

```
[Function: Import_World_From_File]
    │
    ├── [glTFRuntime: gltfLoadAssetFromFilename]
    │       Input: FilePath
    │       Config: (Default)
    │       Return: glTFRuntimeAsset
    │
    ├── [Branch: Is Valid?]
    │       │
    │       ├── TRUE:
    │       │   ├── [SpawnActor: glTFRuntimeAssetActor]
    │       │   │       Location: (0, 0, 0)
    │       │   │       Rotation: (0, 0, 0)
    │       │   │
    │       │   ├── [Set GeneratedWorldActor = Spawned Actor]
    │       │   │
    │       │   └── [Return: TRUE]
    │       │
    │       └── FALSE:
    │           └── [Print: "Failed to load GLTF"]
    │               [Return: FALSE]
```

---

## Step 3: Hook to Middleware

Add HTTP polling or expose via Remote Control:

### Option A: Poll Middleware Endpoint

```
[Event BeginPlay]
    │
    └── [Set Timer by Function Name]
            Function: "Check_For_New_World"
            Time: 30.0 seconds
            Looping: true

[Function: Check_For_New_World]
    │
    ├── [HTTP GET: http://localhost:5000/latest_world]
    │
    └── [On Response]
            │
            ├── [Parse JSON: file_path]
            │
            └── [If file_path != ""]
                    └── [Call: Import_World_From_File(file_path)]
```

### Option B: Remote Control (Simpler)

Expose `Import_World_From_File` to Remote Control API, then call from middleware:

```python
# In middleware.py after generation completes
def notify_ue5_import(file_path):
    payload = {
        "objectPath": "/Game/Maps/Main.Main:PersistentLevel.BP_WorldImporter",
        "functionName": "Import_World_From_File",
        "parameters": {"FilePath": file_path}
    }
    requests.put(UE5_REMOTE_CONTROL_URL, json=payload)
```

---

## Step 4: Test With Local File

1. Place a sample `.glb` file in `BloomPath/content/generated/test.glb`
2. In UE5, call `Import_World_From_File` with the full path
3. Verify the mesh spawns at origin

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Plugin not found" | Verify glTFRuntime folder in Plugins/ |
| Mesh invisible | Check material settings, add default material |
| Collision not working | Enable "Build Simple Collision" in import config |
