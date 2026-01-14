# UE5 Watering Can Interaction Guide

This guide explains how to create a **watering can** interaction in Unreal Engine 5 that triggers Jira issue transitions, completing the bidirectional **Digital Twin of Organization** loop.

## Overview

```
Player waters flower → Animation plays → HTTP POST to middleware → Jira issue → DONE
```

---

## Step 1: Create BP_WateringCan Actor

### Create the Blueprint

1. Content Browser → Right-click → **Blueprint Class** → **Actor**
2. Name: `BP_WateringCan`
3. Add components:

| Component | Type | Purpose |
|-----------|------|---------|
| `CanMesh` | Static Mesh | Watering can body |
| `SpoutPoint` | Scene | Water spawn location |
| `WaterParticles` | Niagara System | Water effect (see Step 4) |

### Add Tag for Detection

1. Select the root component
2. In Details → **Tags** → Add: `WateringCan`

---

## Step 2: Modify BP_FlowerActor

Your existing flower actors need overlap detection to respond to watering.

### Add Collision Component

1. Open your flower Blueprint (or `BP_GrowerActor`)
2. Add **Box Collision** around the flower
3. Set collision preset to **OverlapAllDynamic**

### Create Variables

| Variable | Type | Description |
|----------|------|-------------|
| `JiraIssueKey` | String | The issue this flower represents (e.g., "KAN-32") |
| `IsWatered` | Boolean | Prevent duplicate waterings |

### Overlap Event

Add this logic to **OnComponentBeginOverlap**:

```
[On Component Begin Overlap]
    │
    ├── [Does Other Actor Have Tag "WateringCan"?]
    │       │
    │       ├── No → Return
    │       │
    │       └── Yes → [Is Watered == false?]
    │                       │
    │                       ├── No → Return (already watered)
    │                       │
    │                       └── Yes → [Set Is Watered = true]
    │                                       │
    │                                       ▼
    │                               [Play Water Animation on Can]
    │                                       │
    │                                       ▼
    │                               [Spawn Niagara Water Effect]
    │                                       │
    │                                       ▼
    │                               [Delay 2.0 seconds]
    │                                       │
    │                                       ▼
    │                               [Call: Send Complete Task]
```

---

## Step 3: Send HTTP Request to Middleware

### Create Custom Event: Send_Complete_Task

Add a function that sends the POST request:

```
[Custom Event: Send_Complete_Task]
    │
    ├── [Construct HTTP Request]
    │       │
    │       ├── URL: "http://localhost:5000/complete_task"
    │       ├── Verb: POST
    │       └── Content-Type: application/json
    │
    ├── [Set Request Content]
    │       │
    │       └── Body: {"issue_key": "[JiraIssueKey]"}
    │
    ├── [Bind Event: On Request Complete]
    │
    └── [Process Request]
```

### On Request Complete

```
[On Request Complete]
    │
    ├── [Was Successful?]
    │       │
    │       ├── No → [Print Warning: "Failed to complete task"]
    │       │
    │       └── Yes → [Call: Bloom Flower]
    │                       │
    │                       ├── [Set Dynamic Material: Bloom Color]
    │                       └── [Spawn Celebration Particles]
```

### Blueprint HTTP Request Setup

1. Enable plugin: **HTTP Blueprint**
2. Create a **HTTP Request** node
3. Configure:
   - **URL**: `http://localhost:5000/complete_task`
   - **Verb**: `POST`
   - **Headers**: Add `Content-Type: application/json`

---

## Step 4: Visual Effects (Niagara)

### Water Pouring Effect

Create a Niagara system for realistic water:

1. Content Browser → Right-click → **FX** → **Niagara System**
2. Choose template: **Simple Sprite Burst**
3. Modify:
   - **Spawn Rate**: 50/second
   - **Lifetime**: 1.5 seconds
   - **Velocity**: Downward arc from spout
   - **Color**: Light blue with transparency
   - **Size**: Start large, end small (droplet effect)

### Flower Bloom Effect

When watering succeeds, trigger a bloom:

1. Material: Lerp from current color → vibrant red/pink
2. Scale: Animate from 1.0 → 1.2 → 1.0 (bounce)
3. Particles: Sparkle/petal burst effect

---

## Step 5: Player Interaction

### Pickup System (Optional)

If players carry the watering can:

1. Add **Grab Component** (VR) or trace-based pickup
2. Attach can to player's hand socket
3. Use animation montage for pouring action

### Simple Overlap Approach

For quick testing, simply move the watering can actor near flowers - the overlap detection handles the rest.

---

## Testing

### Test HTTP Connection First

With middleware running (`python middleware.py`):

```powershell
$body = '{"issue_key": "KAN-32"}'
Invoke-RestMethod -Uri "http://localhost:5000/complete_task" -Method POST -Body $body -ContentType "application/json"
```

### Test in UE5

1. Place `BP_WateringCan` near a flower
2. Run Play-in-Editor
3. Move can into flower's collision box
4. Observe:
   - Water particles spawn
   - Flower blooms (material change)
   - Check Jira: issue should be DONE

---

## Middleware Endpoint Reference

**POST** `/complete_task`

```json
{
    "issue_key": "KAN-32"
}
```

**Response (Success)**:
```json
{
    "status": "success",
    "issue": "KAN-32"
}
```

**Response (Error)**:
```json
{
    "status": "error",
    "message": "No 'Done' transition available for KAN-32"
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| HTTP request fails | Check middleware is running on port 5000 |
| Overlap not detected | Verify collision settings and WateringCan tag |
| Jira transition fails | Check issue is in a status that can transition to Done |
| No water effect | Verify Niagara system is properly attached |
