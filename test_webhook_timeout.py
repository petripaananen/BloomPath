"""
Tests for WFM-4: Webhook Timeout Fix.

Verifies that webhook handlers respond instantly (< 500ms)
and that processing happens in the background.
"""

import time
import json
import logging
from unittest.mock import patch, MagicMock

import pytest

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Create a Flask test app."""
    import os
    os.environ.setdefault("LINEAR_API_KEY", "test-key")
    os.environ.setdefault("LINEAR_WEBHOOK_SECRET", "test-secret")
    os.environ.setdefault("DEFAULT_PROVIDER", "linear")

    from middleware.app import create_app
    app = create_app({"TESTING": True})
    return app


@pytest.fixture
def client(app):
    return app.test_client()


LINEAR_PAYLOAD = {
    "action": "update",
    "type": "Issue",
    "data": {
        "id": "abc-123",
        "identifier": "WFM-99",
        "title": "Test Timeout Issue",
        "state": {"type": "started", "name": "In Progress"},
    },
    "updatedFrom": {"stateId": "old-state-id"},
}

JIRA_PAYLOAD = {
    "webhookEvent": "jira:issue_updated",
    "issue": {
        "key": "KAN-42",
        "fields": {
            "summary": "Jira timeout test",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Task"},
            "priority": {"name": "Medium"},
        },
    },
    "changelog": {"items": []},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWebhookTimeout:
    """Verify that webhook endpoints respond within the timeout budget."""

    def test_linear_webhook_responds_fast(self, client):
        """Linear webhook must return 200 in < 500ms."""
        start = time.monotonic()
        resp = client.post(
            "/webhooks/linear",
            data=json.dumps(LINEAR_PAYLOAD),
            content_type="application/json",
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "accepted"
        assert "issue" in body
        assert elapsed_ms < 500, f"Response took {elapsed_ms:.0f}ms (budget: 500ms)"

    def test_jira_webhook_responds_fast(self, client):
        """Jira webhook must return 200 in < 500ms."""
        start = time.monotonic()
        resp = client.post(
            "/webhooks/jira",
            data=json.dumps(JIRA_PAYLOAD),
            content_type="application/json",
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "accepted"
        assert elapsed_ms < 500, f"Response took {elapsed_ms:.0f}ms (budget: 500ms)"

    @patch("middleware.core.process_ticket_event")
    def test_background_processing_called(self, mock_process, client):
        """After the fast response, the event is processed in the background."""
        resp = client.post(
            "/webhooks/linear",
            data=json.dumps(LINEAR_PAYLOAD),
            content_type="application/json",
        )
        assert resp.status_code == 200

        # Give the background worker a moment to pick up the job
        time.sleep(0.5)

        assert mock_process.call_count >= 1, "process_ticket_event was not called in the background"

    def test_health_includes_queue_status(self, client):
        """The /health endpoint should report task queue status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert "task_queue" in body
        assert "pending" in body["task_queue"]
        assert "worker_alive" in body["task_queue"]
