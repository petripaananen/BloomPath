# UE5 Semantic Tag Injection Guide

This guide explains how to read the World Manifest JSON and apply Gameplay Tags to imported actors.

## Prerequisites

1. **glTFRuntime** plugin installed (from previous guide)
2. **Gameplay Tag** system enabled in project
3. Middleware running with `/latest_manifest` endpoint

---

## Step 1: Create Gameplay Tags

1. Edit > Project Settings > Gameplay Tags
2. Add tags (or import from file):

```
Environment.Walkable
Environment.Obstacle
Environment.Climbable
Environment.Water
Physics.HighFriction
Physics.LowFriction
Physics.Destructible
Interaction.Interactable
Sound.Footstep.Stone
Sound.Footstep.Mud
```

---

## Step 2: Create BP_SemanticTagger Actor

### Variables

| Name | Type | Purpose |
|------|------|---------|
| `ManifestData` | String | Raw JSON from endpoint |
| `ParsedObjects` | Array of Struct | Parsed object list |

### Create Struct: `S_SemanticObject`

| Field | Type |
|-------|------|
| `ObjectID` | String |
| `SemanticType` | String |
| `Tags` | Array<String> |
| `Friction` | Float |
| `Destructible` | Boolean |

---

## Step 3: Fetch Manifest Function

```
[Function: Fetch_Manifest]
    │
    ├── [HTTP GET: http://localhost:5000/latest_manifest]
    │
    └── [On Response]
            │
            ├── [Branch: status == "ok"]
            │       │
            │       └── [Parse JSON "manifest.objects" -> ParsedObjects]
            │
            └── [For Each: ParsedObjects]
                    │
                    └── [Call: Apply_Tags_To_Actor(Object)]
```

---

## Step 4: Apply Tags to Actor

```
[Function: Apply_Tags_To_Actor]
    Input: SemanticObject (S_SemanticObject struct)
    │
    ├── [Find Actor by Location/Name matching Object.ObjectID]
    │       (Match bounding box center to spawned actor location)
    │
    ├── [For Each: Object.Tags]
    │       │
    │       └── [Add Gameplay Tag to Actor]
    │               Tag: "Environment." + TagName
    │
    ├── [Set Physics Material]
    │       │
    │       └── [If Object.Friction < 0.3]
    │               → Apply "PM_Slippery"
    │           [Else If Object.Friction > 0.7]  
    │               → Apply "PM_Rough"
    │
    └── [If Object.Destructible]
            │
            └── [Enable Destructible Component]
```

---

## Step 5: Integration with World Import

Call `Fetch_Manifest` after importing the world:

```
[Event: On_World_Imported]
    │
    ├── [Delay: 1.0 seconds]
    │       (Allow actors to initialize)
    │
    └── [Call: Fetch_Manifest]
```

---

## Testing

1. Generate a world and run `/analyze_world`
2. Import world into UE5
3. Verify actors have Gameplay Tags applied
4. Check physics materials on different surfaces

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tags not appearing | Verify actor has "Gameplay Tag" component |
| Wrong actors tagged | Check bounding box matching logic |
| HTTP timeout | Ensure middleware is running |
