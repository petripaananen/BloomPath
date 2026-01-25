# BloomPath User Test Guide

## End-to-End Testing: Jira → Middleware → UE5

This guide provides step-by-step instructions to test the complete BloomPath workflow.

---

## Prerequisites

Before testing, ensure:
- [ ] `.env` file is configured with valid Jira credentials and API keys
- [ ] UE5 project is open with Remote Control Plugin enabled
- [ ] ngrok is running (or webhook URL is accessible)
- [ ] Python virtual environment is activated

---

## Test Case 1: Basic Garden Growth (Done Transition)

**Goal**: Verify that completing a Jira issue triggers growth in UE5.

### Steps

1. **Start the Middleware**
   ```bash
   cd C:\Users\petri\.gemini\antigravity\BloomPath
   python middleware.py
   ```
   *Expected*: Console shows "Flask running on http://0.0.0.0:5000"

2. **Start ngrok** (separate terminal)
   ```bash
   .\start_ngrok.ps1
   ```
   *Expected*: ngrok shows a public URL (e.g., `https://xxxx.ngrok.io`)

3. **Configure Jira Webhook** (if not done)
   - Go to: Jira Settings → System → Webhooks
   - Create webhook pointing to: `https://xxxx.ngrok.io/webhook`
   - Events: `issue_updated`

4. **Create a Test Issue in Jira**
   - Project: BloomPath (or your test project)
   - Type: Task
   - Summary: `Test Growth - [Your Name] [Timestamp]`
   - Labels: (none for basic test)

5. **Transition Issue to "Done"**
   - Open the issue in Jira
   - Click "Done" or drag to Done column

6. **Verify Middleware Console**
   *Expected Output*:
   ```
   [INFO] Received webhook: issue_updated
   [INFO] Issue TEST-123 moved to Done
   [INFO] Triggering UE5 growth: TEST-123
   ```

7. **Verify UE5 Viewport**
   - Look at the Garden Actor
   - *Expected*: A new leaf/branch mesh appears

---

## Test Case 2: Blocker Thorns (Flagged Issues)

**Goal**: Verify that flagged/blocked issues show thorns in UE5.

### Steps

1. **Ensure middleware and ngrok are running** (as above)

2. **Create a Test Issue**
   - Summary: `Test Blocker - [Timestamp]`

3. **Add Flag/Impediment**
   - Open issue → Click flag icon (🚩) or add label `blocker`

4. **Verify Middleware Console**
   ```
   [INFO] Issue TEST-124 flagged as blocker
   [INFO] Triggering UE5 thorns: TEST-124
   ```

5. **Verify UE5 Viewport**
   - *Expected*: Thorns appear on the corresponding branch

6. **Remove Flag**
   - Click flag icon again to remove

7. **Verify Thorns Removed**
   - *Expected*: Thorns disappear from UE5

---

## Test Case 3: Sprint Weather System

**Goal**: Verify sprint health affects garden weather.

### Steps

1. **Start an Active Sprint**
   - Go to Backlog → Create Sprint → Start Sprint

2. **Add Issues to Sprint**
   - Move 5-10 issues into the active sprint

3. **Check Initial Weather**
   - Middleware console should show sprint sync
   - UE5 weather should reflect sprint progress

4. **Complete 50% of Issues**
   - Transition half the issues to Done

5. **Verify Weather Change**
   - *Expected*: Weather transitions (e.g., Cloudy → Sunny)
   - Time-of-day should shift toward "afternoon"

---

## Test Case 4: PWM Dreaming Engine (L3 Features)

**Goal**: Test the parallel simulation and risk prediction.

### Steps

1. **Create Issue with Special Label**
   - Summary: `Complex Platformer Level`
   - Labels: `platformer`

2. **Trigger Orchestrator**
   - The orchestrator should auto-trigger on new issues
   - Or manually run:
   ```python
   from orchestrator import BloomPathOrchestrator
   orch = BloomPathOrchestrator()
   orch.process_ticket({"key": "TEST-125", "fields": {"summary": "Test Level", "labels": ["platformer"]}})
   ```

3. **Verify Parallel Simulations**
   *Expected Console*:
   ```
   🎹 Orchestrator (Agentic Mode) for TEST-125
   > Dispatching 3 Parallel Simulation Agents (The Dreaming)...
     > Agent 'BASELINE' finished with PASS
     > Agent 'STRESS_TEST' finished with FAIL
     > Agent 'OPTIMIZATION' finished with PASS
   > Dreaming Complete. Confidence Score: 66.7%
   ```

4. **Check Report Generation**
   - Navigate to: `BloomPath/reports/`
   - *Expected*: `PWM_Report_TEST-125_[timestamp].md` exists

5. **Verify Ghost Object (if confidence < 100%)**
   - Check UE5 for semi-transparent red mesh
   - *Expected*: Phantom hazard spawned at center location

---

## Test Case 5: Watering Interaction (UE5 → Jira)

**Goal**: Test bidirectional sync - watering plants completes Jira issues.

### Steps

1. **Create an Open Issue**
   - Status: To Do or In Progress

2. **Play UE5 in PIE Mode**
   - Enter Play mode in Unreal

3. **Locate the Plant for Your Issue**
   - Find the plant corresponding to your issue

4. **Use Watering Interaction**
   - Approach plant → Press interaction key
   - Water effects should play

5. **Verify Jira Update**
   - Check the issue in Jira
   - *Expected*: Status changed to "Done"

6. **Verify Middleware Logs**
   ```
   [INFO] UE5 watering event for: TEST-126
   [INFO] Transitioning Jira issue to Done
   ```

---

## Troubleshooting

| Symptom | Check |
| :--- | :--- |
| Webhook not received | Is ngrok running? Is URL correct in Jira? |
| UE5 not responding | Is Remote Control Plugin enabled? Check port 8080 |
| Growth not visible | Check if actor path in `.env` matches your level |
| No simulation results | Is `GEMINI_API_KEY` set in `.env`? |

---

## Quick Smoke Test Checklist

- [ ] Middleware starts without errors
- [ ] ngrok tunnel is active
- [ ] Create issue in Jira
- [ ] Move issue to Done
- [ ] Growth visible in UE5
- [ ] Blocker flag shows thorns
- [ ] Sprint weather reflects progress
