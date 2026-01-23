# Semantic Tagging Feature Analysis

## Concept Summary (Translated from Finnish)

The idea is to create a **Semantic Translation Pipeline** that transforms raw AI-generated 3D worlds into game-ready assets with proper physics, navigation, and interaction properties.

### The Problem
World models (like Marble/World Labs) create *visually* plausible spaces, but game engines need to know:
- What is navigable vs. blocked?
- What is destructible vs. solid?
- What physics properties apply (friction, mass)?

### The Solution: Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        JIRA (Intent)                        │
│          "Create a forest path that is difficult"           │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   WORLD LABS (Generation)                   │
│              Marble AI generates 3D geometry                │
│              + Bounding boxes / spatial data                │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  GEMINI AI (Analysis)                       │
│   "This brown blob is a rock with friction coefficient X"   │
│                Creates "World Manifest" JSON                │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    UE5 (Consumption)                        │
│         Tags injected: DifficultTerrain, Physics:Mud        │
│              Collision + Navigation auto-set                │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. World Manifest
A JSON document describing every object in the generated world:

```json
{
  "world_id": "abc123",
  "objects": [
    {
      "id": "obj_001",
      "bounding_box": {"min": [0,0,0], "max": [2,1,2]},
      "semantic_type": "rock",
      "tags": ["Obstacle", "Climbable"],
      "physics": {
        "friction": 0.8,
        "mass": 500,
        "destructible": false
      }
    },
    {
      "id": "obj_002", 
      "semantic_type": "mud_patch",
      "tags": ["DifficultTerrain", "SlowMovement"],
      "physics": {
        "friction": 0.2,
        "surface_type": "Mud"
      }
    }
  ]
}
```

### 2. Semantic Analysis (Gemini)
Use Gemini's vision capabilities to:
1. Take a screenshot/render of the generated world
2. Identify objects and their likely game properties
3. Output structured JSON manifest

### 3. UE5 Tag Injection
BloomPath middleware sends manifest to UE5, which:
1. Applies `Gameplay Tags` to actors
2. Sets physics materials
3. Configures navigation mesh (walkable/blocked)

### 4. Validation Loop (Future)
AI agents test the tagged world:
- Can they navigate the "difficult path"?
- If impossible → report back to Jira as bug

---

## Implementation Phases

### Phase 1: World Manifest Generation
- Extend `world_client.py` to capture bounding box data
- Create `semantic_analyzer.py` using Gemini API
- Output manifest JSON alongside `.glb` file

### Phase 2: UE5 Tag Injection
- Create Blueprint `BP_SemanticTagger`
- Read manifest JSON
- Apply tags + physics to spawned actors

### Phase 3: Validation Feedback
- Create agent navigation tests
- Report failures back to middleware
- Create Jira comments automatically

---

## Value Proposition (Thesis Angle)

> BloomPath becomes a **production process operating system**, not just a visualization tool.

| Metric | Without Semantic Tagging | With Semantic Tagging |
|--------|-------------------------|----------------------|
| Manual tagging time | Hours per asset | Zero |
| Complexity estimation | After UE5 import | Before import |
| Change propagation | Manual | Automatic |
