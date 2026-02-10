---
name: Testing and Debugging
description: Standardized patterns for writing tests, running the test suite, and debugging BloomPath issues.
---

# Testing & Debugging Skill

Use this skill when writing new tests, running the test suite, or debugging issues in BloomPath.

## Test File Conventions

| Convention | Pattern |
|-----------|---------|
| File naming | `test_<module>.py` in project root |
| Framework | `pytest` with class-based grouping |
| Fixtures | Use `@pytest.fixture` for Flask app/client |
| Mocking | `unittest.mock.patch` for external services |

## 1. Writing Tests

### Flask Route Tests (Webhook/API)

```python
import pytest
from unittest.mock import patch

@pytest.fixture
def app():
    import os
    os.environ.setdefault("LINEAR_API_KEY", "test-key")
    from middleware.app import create_app
    return create_app({"TESTING": True})

@pytest.fixture
def client(app):
    return app.test_client()

class TestMyFeature:
    def test_endpoint(self, client):
        resp = client.post("/webhooks/linear", json={...})
        assert resp.status_code == 200
```

### UE5 Interface Tests

Always mock the `_send_request` function to avoid needing a running UE5:

```python
with patch('ue5_interface._send_request') as mock_send:
    mock_send.return_value = {"status": "ok"}
    trigger_ue5_growth("ISSUE-1", "Bug", "tree")
    mock_send.assert_called_once()
```

### Orchestrator / Pipeline Tests

Mock all external clients:

```python
with patch('orchestrator.WorldLabsClient') as MockWorld, \
     patch('orchestrator.semantic_analyzer.analyze_world') as mock_analyze, \
     patch('ue5_interface.trigger_ue5_load_level') as mock_load:
    # Setup mocks, run orchestrator, assert calls
```

## 2. Running Tests

```powershell
# Run all tests
python -m pytest test_*.py -v

# Run a specific test file
python -m pytest test_webhook_timeout.py -v

# Run a specific test class or method
python -m pytest test_webhook_timeout.py::TestWebhookTimeout::test_linear_webhook_responds_fast -v

# Run with output visible
python -m pytest test_*.py -v -s
```

## 3. Debugging

### Log Files

Middleware logs are written to `middleware_v*.log` (versioned). Check the latest:

```powershell
Get-Content middleware.log -Tail 50
```

### Common Issues

| Symptom | Check |
|---------|-------|
| `ModuleNotFoundError` | Run `python -m pip install -r requirements.txt` |
| UE5 connection refused | Ensure UE5 is running with Remote Control API |
| Webhook signature invalid | Verify `LINEAR_WEBHOOK_SECRET` in `.env` |
| World generation fails | Check `WORLD_LABS_API_KEY` quota |
| Tests hang | Check for unmocked network calls |

### Environment Verification

```powershell
python verify_env.py
```
