---
description: How to run the BloomPath test suite and verify code changes
---

# Run Tests

## Full Suite

// turbo-all

1. Run all pytest tests:
```powershell
cd c:\Users\petri\.gemini\antigravity\BloomPath
python -m pytest test_*.py -v
```

2. Run the orchestrator integration test:
```powershell
cd c:\Users\petri\.gemini\antigravity\BloomPath
python test_orchestrator.py
```

## Individual Test Files

| Test File | What it covers |
|-----------|---------------|
| `test_webhook_timeout.py` | Webhook response time + background processing |
| `test_orchestrator.py` | PWM pipeline flow + mechanics parsing |
| `test_audio.py` | Audio event system |
| `test_social.py` | Avatar/social presence |
| `test_sprint_health.py` | Sprint status + weather mapping |
| `test_world_gen.py` | World generation pipeline |

## Running a Specific Test

```powershell
cd c:\Users\petri\.gemini\antigravity\BloomPath
python -m pytest test_webhook_timeout.py::TestWebhookTimeout::test_linear_webhook_responds_fast -v
```

## If Tests Fail

1. Check dependencies: `python -m pip install -r requirements.txt`
2. Check `.env` is present: `Test-Path .env`
3. Check logs: `Get-Content middleware.log -Tail 50`
