---
name: UE5 Integration
description: Standardized workflow for adding new Unreal Engine 5 interactions to BloomPath.
---

# UE5 Integration Skill

Use this skill when adding new visual features, mechanics, or bidirectional sync with Unreal Engine 5.

## 1. Interface Definition (`ue5_interface.py`)
- [ ] Define the function constant defaults at the top:
  ```python
  UE5_NEW_FUNC = os.getenv("UE5_NEW_FUNC", "My_Blueprint_Function")
  ```
- [ ] Implement the trigger function using `@retry_on_failure()`:
  ```python
  @retry_on_failure()
  def trigger_ue5_new_feature(arg1: str, ...) -> dict:
      payload = {
          "objectPath": UE5_ACTOR_PATH,
          "functionName": UE5_NEW_FUNC,
          "parameters": { ... },
          "generateTransaction": True
      }
      return _send_request(payload)
  ```

## 2. Core Logic Integration (`middleware/core.py`)
- [ ] Import the new trigger function (inside the function to avoid circular imports if needed).
- [ ] Add the logic to `process_ticket_event` or relevant handler.
- [ ] Ensure proper event logging and error handling.

## 3. API/Route Exposure (Optional)
- [ ] If this is triggered externally (not by webhook), add a route in `middleware/routes/api.py`.
- [ ] Ensure the route allows specifying the `provider` (Jira/Linear).

## 4. Documentation
- [ ] Update `TEST_GUIDE.md` with a test case for the new interaction.
- [ ] Explicitly list the function signature required in the UE5 Blueprint (Actor).

## 5. Verification
- [ ] Use `python -c` to dry-run the function (mocking the request if UE5 isn't running).
- [ ] Verify logs show the correct payload structure.
