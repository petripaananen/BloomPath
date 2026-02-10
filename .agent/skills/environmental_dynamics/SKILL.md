---
name: Environmental Dynamics
description: Standardized workflow for adding weather effects and environmental visualizations driven by sprint/cycle health data.
---

# Environmental Dynamics Skill

Use this skill when adding new environmental effects (weather, lighting, ambience) that reflect project health metrics.

## Architecture

```
/sprint_status API → health metrics → UE5 environmental controls
```

The middleware calculates health from sprint data, then drives UE5 Niagara systems and lighting.

## 1. Health Metric Source (`middleware/routes/api.py`)

The `/sprint_status` endpoint calculates:
- `done_ratio`: % of issues completed
- `blocked_ratio`: % of issues blocked
- `weather`: derived state (`sunny`, `cloudy`, `storm`)
- `progress`: sprint progress (maps to time-of-day)

- [ ] If adding a new metric, compute it in the `sprint_status()` route.
- [ ] Return the new metric in the JSON response for UE5 consumption.

## 2. UE5 Interface Function (`ue5_interface.py`)

Follow the standard pattern:

```python
# 1. Define the function name constant
UE5_NEW_EFFECT = os.getenv("UE5_NEW_EFFECT", "Set_Effect_Name")

# 2. Implement with retry decorator
@retry_on_failure()
def trigger_ue5_new_effect(param: float) -> dict:
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_NEW_EFFECT,
        "parameters": {"Intensity": param},
        "generateTransaction": True
    }
    return _send_request(payload)
```

## 3. Core Integration (`middleware/core.py`)

- [ ] Add the trigger to the appropriate event type in `process_ticket_event()`.
- [ ] Or create a periodic polling mechanism if the effect is time-based.

## 4. UE5 Blueprint Requirements

Document the required Blueprint function signature:
- **Actor**: The BloomPath controller actor (path in `UE5_ACTOR_PATH`)
- **Function name**: Must match the `UE5_NEW_EFFECT` constant
- **Parameters**: Document each parameter type and valid ranges

## 5. Verification

- [ ] Mock UE5 and verify the correct payload structure is sent.
- [ ] Test with real UE5 instance to validate visual result.
- [ ] Update `ARCHITECTURE.md` environmental dynamics diagram.
