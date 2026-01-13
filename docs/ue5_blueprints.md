# UE5 Blueprint Implementation Guide

This guide explains how to set up the Unreal Engine 5 Blueprints required for BloomPath's "Garden of Productivity" visualization.

## Overview

BloomPath triggers growth animations in UE5 when Jira issues are completed. The middleware calls UE5's Remote Control API, which executes Blueprint functions.

```
Jira Issue → "Done" → Middleware → UE5 Remote Control API → Grow_Leaves()
```

## Prerequisites

- Unreal Engine 5.3+ installed
- A UE5 project with a level (e.g., `Main`)

---

## Step 1: Enable Remote Control Plugin

1. Open your UE5 project
2. Go to **Edit** → **Plugins**
3. Search for **"Remote Control API"**
4. Enable the plugin and restart UE5

### Configure Remote Control

1. Go to **Edit** → **Project Settings**
2. Search for **"Remote Control"**
3. Ensure these settings:
   | Setting | Value |
   |---------|-------|
   | Enable Remote Control | ✅ Enabled |
   | HTTP Server Port | `8080` |
   | Enable HTTP Server | ✅ Enabled |

---

## Step 2: Create the GrowerActor Blueprint

1. In Content Browser, right-click → **Blueprint Class** → **Actor**
2. Name it: `BP_GrowerActor`
3. Open the Blueprint

### Add Components

Add the following components to the Blueprint:

| Component | Type | Purpose |
|-----------|------|---------|
| `RootScene` | Scene Component | Root for organization |
| `TreeMesh` | Static Mesh | Base tree/plant mesh |
| `LeavesMesh` | Static Mesh | Leaves that will grow |

### Create Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GrowthProgress` | Float | 0.0 | Current growth (0-1) |
| `GrowthSpeed` | Float | 1.0 | Animation speed |
| `CompletedIssues` | Map<String, Bool> | Empty | Tracks grown issues |

---

## Step 3: Implement Grow_Leaves Function

1. In the Blueprint, go to **Functions** → **Add Function**
2. Name it: `Grow_Leaves`
3. Add an input parameter:
   | Name | Type |
   |------|------|
   | `Target_Branch_ID` | String |

### Blueprint Logic

```
[Event Grow_Leaves (Target_Branch_ID: String)]
    │
    ├──► [Branch: Is Valid?]
    │         │
    │         ├── No  → [Print: "Invalid Branch ID"] → Return
    │         │
    │         └── Yes → [Check: Already in CompletedIssues?]
    │                         │
    │                         ├── Yes → Return (already grown)
    │                         │
    │                         └── No  → [Add to CompletedIssues]
    │                                         │
    │                                         ▼
    │                                   [Play Growth Animation]
    │                                         │
    │                                         ▼
    │                                   [Timeline: 0→1 over 2 sec]
    │                                         │
    │                                         ▼
    │                                   [Set LeavesMesh Scale]
    │                                   [Spawn Particle Effect]
    │                                         │
    │                                         ▼
    │                                   [Print: "🌱 Growth complete"]
    ▼
[Return]
```

### Expose to Remote Control

1. Select the `Grow_Leaves` function
2. In Details panel, enable: **☑️ Call In Editor**
3. Right-click the function → **Expose to Remote Control**

---

## Step 4: Implement Shrink_Leaves Function (Optional)

For handling reopened issues:

1. Create function: `Shrink_Leaves`
2. Input: `Target_Branch_ID` (String)
3. Logic: Reverse the growth animation and remove from `CompletedIssues`

---

## Step 5: Place Actor in Level

1. Drag `BP_GrowerActor` into your level
2. Position as desired
3. Note the actor path for `.env` configuration:
   ```
   /Game/Maps/Main.Main:PersistentLevel.BP_GrowerActor_C_0
   ```

### Find Actor Path

1. Select the actor in the level
2. Right-click → **Copy Reference**
3. The path format: `/Game/Maps/LEVELNAME.LEVELNAME:PersistentLevel.ACTORNAME`

---

## Step 6: Test Remote Control

### In UE5
1. Start **Play in Editor** (PIE) or run the game
2. Open a browser to: `http://localhost:8080/remote/info`
3. You should see the Remote Control API info

### Test API Call
Use PowerShell to test:

```powershell
$body = @{
    objectPath = "/Game/Maps/Main.Main:PersistentLevel.BP_GrowerActor_C_0"
    functionName = "Grow_Leaves"
    parameters = @{
        Target_Branch_ID = "TEST-001"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/remote/object/call" -Method PUT -Body $body -ContentType "application/json"
```

---

## Visual Reference

### Component Hierarchy
```
BP_GrowerActor
├── RootScene (Scene)
│   ├── TreeMesh (Static Mesh)
│   │   └── Material: M_TreeBark
│   └── LeavesMesh (Static Mesh)
│       └── Material: M_Leaves (with growth parameter)
└── GrowthTimeline (Timeline)
```

### Growth Animation

| Time | Scale | Effect |
|------|-------|--------|
| 0.0s | 0.0 | Invisible |
| 0.5s | 0.3 | Budding |
| 1.0s | 0.7 | Growing |
| 2.0s | 1.0 | Full bloom + particles |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Function not found | Ensure "Expose to Remote Control" is enabled |
| Connection refused | Check Remote Control plugin is enabled and PIE is running |
| Wrong actor path | Use "Copy Reference" from level to get exact path |
| No animation | Verify Timeline is connected and playing |
