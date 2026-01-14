# UE5 Environmental Dynamics Guide

This guide explains how to implement weather and time-of-day systems in Unreal Engine 5 that reflect sprint health from Jira.

## Overview

```
Middleware /sprint_status → UE5 polls → Weather changes + Time-of-Day shifts
```

---

## Step 1: Create Weather Manager Actor

### Create the Blueprint

1. Content Browser → Right-click → **Blueprint Class** → **Actor**
2. Name: `BP_WeatherManager`
3. Add components:

| Component | Type | Purpose |
|-----------|------|---------|
| `DirectionalLight` | Light | Sun position/color |
| `SkyAtmosphere` | Sky Atmosphere | Sky appearance |
| `ExponentialHeightFog` | Fog | Atmosphere density |
| `PS_Rain` | Niagara System | Rain particles |
| `PS_Storm` | Niagara System | Storm effects |

---

## Step 2: Weather State Machine

### Create Variables

| Variable | Type | Default |
|----------|------|---------|
| `CurrentWeather` | String | "sunny" |
| `TargetWeather` | String | "sunny" |
| `TransitionAlpha` | Float | 1.0 |

### Weather States

| State | Sky Color | Fog Density | Light Intensity | Effects |
|-------|-----------|-------------|-----------------|---------|
| sunny | Clear blue | 0.01 | 10.0 | None |
| cloudy | Gray | 0.03 | 5.0 | Light fog |
| storm | Dark gray | 0.08 | 2.0 | Rain, lightning |

### Set_Weather Function

1. Create function: `Set_Weather`
2. Input: `Weather_State` (String)
3. Expose to Remote Control

```
[Event Set_Weather (Weather_State: String)]
    │
    ├── [Set TargetWeather = Weather_State]
    │
    ├── [Start Timeline: WeatherTransition]
    │       │
    │       └── Over 3 seconds, lerp:
    │           - Sky color
    │           - Fog density
    │           - Light intensity
    │
    └── [Activate/Deactivate Niagara systems]
```

---

## Step 3: Time-of-Day System

### Set_Time_Of_Day Function

1. Create function: `Set_Time_Of_Day`
2. Input: `Time_Progress` (Float, 0.0-1.0)
3. Expose to Remote Control

```
[Event Set_Time_Of_Day (Time_Progress: Float)]
    │
    ├── [Calculate Sun Rotation]
    │       │
    │       └── Pitch = Lerp(-10°, 170°, Time_Progress)
    │           (0.0 = sunrise, 0.5 = noon, 1.0 = sunset)
    │
    ├── [Set DirectionalLight Rotation]
    │
    └── [Adjust Light Color]
            │
            └── 0.0 = warm orange
                0.5 = white
                1.0 = warm orange/red
```

---

## Step 4: Polling Middleware

UE5 needs to periodically fetch sprint status. Use a Timer in Blueprint:

```
[Event BeginPlay]
    │
    └── [Set Timer by Function Name]
            Function: "Poll_Sprint_Status"
            Time: 60.0 seconds (once per minute)
            Looping: true

[Function Poll_Sprint_Status]
    │
    ├── [Construct HTTP Request]
    │       URL: "http://localhost:5000/sprint_status"
    │       Verb: GET
    │
    ├── [Process Request]
    │
    └── [On Response]
            │
            ├── [Parse JSON: weather, progress]
            │
            ├── [Call Set_Weather(weather)]
            │
            └── [Call Set_Time_Of_Day(progress)]
```

---

## Step 5: Niagara Weather Effects

### Rain System

1. Create Niagara System → Template: **Fountain**
2. Modify:
   - Spawn Rate: 500/second
   - Velocity: Strong downward (-Z)
   - Lifetime: 2 seconds
   - Sprite: Rain streak texture

### Storm Effects

1. Lightning flashes (random light pulses)
2. Thunder audio cues
3. Heavier rain particles
4. Wind particles (leaves, debris)

---

## Middleware Endpoint

**GET** `/sprint_status`

**Response:**
```json
{
    "status": "ok",
    "sprint_name": "Sprint 5",
    "weather": "sunny",
    "progress": 0.65,
    "issues_total": 12,
    "issues_done": 8
}
```

---

## Testing

### Test Middleware

```powershell
# Ensure JIRA_BOARD_ID is set in .env
curl http://localhost:5000/sprint_status
```

### Test UE5 Remote Control

```powershell
# Test weather
$body = @{
    objectPath = "/Game/Maps/Main.Main:PersistentLevel.BP_WeatherManager"
    functionName = "Set_Weather"
    parameters = @{ Weather_State = "storm" }
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/remote/object/call" -Method PUT -Body $body -ContentType "application/json"

# Test time
$body = @{
    objectPath = "/Game/Maps/Main.Main:PersistentLevel.BP_WeatherManager"
    functionName = "Set_Time_Of_Day"
    parameters = @{ Time_Progress = 0.8 }
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/remote/object/call" -Method PUT -Body $body -ContentType "application/json"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No weather change | Verify WeatherManager is in level |
| /sprint_status fails | Check JIRA_BOARD_ID in .env |
| Time not changing | Ensure DirectionalLight Mobility = Movable |
