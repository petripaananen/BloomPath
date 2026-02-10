"""
Tests for the L3 Dreaming Engine (WFM-1).

Verifies scenario simulations, risk calculations, dream persistence,
and API endpoint behavior.
"""

import pytest
import json
import os
import shutil
from unittest.mock import patch, MagicMock
from dataclasses import asdict


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def sample_sprint_data():
    """Typical sprint data with 3 team members and 8 issues."""
    return {
        "issues": [
            {"id": "WFM-1", "status": "done", "assignee": "Alice", "priority": 1, "epic": "EPIC-1"},
            {"id": "WFM-2", "status": "in_progress", "assignee": "Alice", "priority": 2, "epic": "EPIC-1"},
            {"id": "WFM-3", "status": "in_progress", "assignee": "Bob", "priority": 3, "epic": "EPIC-2"},
            {"id": "WFM-4", "status": "open", "assignee": "Bob", "priority": 3, "epic": "EPIC-2"},
            {"id": "WFM-5", "status": "open", "assignee": "Charlie", "priority": 4, "epic": "EPIC-1"},
            {"id": "WFM-6", "status": "open", "assignee": "Charlie", "priority": 2, "epic": "EPIC-2"},
            {"id": "WFM-7", "status": "done", "assignee": "Alice", "priority": 3, "epic": "EPIC-1"},
            {"id": "WFM-8", "status": "open", "assignee": "Bob", "priority": 1, "epic": "EPIC-2"},
        ],
        "team_members": ["Alice", "Bob", "Charlie"],
        "velocity": 4.0,
        "days_remaining": 5
    }


@pytest.fixture
def engine(tmp_path):
    """Create a DreamingEngine with temp directories."""
    import dreaming_engine as de

    # Override dreams directory to temp
    original_dir = de.DREAMS_DIR
    de.DREAMS_DIR = str(tmp_path / "dreams")
    os.makedirs(de.DREAMS_DIR, exist_ok=True)

    engine = de.DreamingEngine()
    engine._dream_dir_override = de.DREAMS_DIR

    yield engine

    # Restore
    de.DREAMS_DIR = original_dir


@pytest.fixture
def app():
    os.environ.setdefault("LINEAR_API_KEY", "test-key")
    os.environ.setdefault("JIRA_API_TOKEN", "test")
    os.environ.setdefault("JIRA_DOMAIN", "test.atlassian.net")
    os.environ.setdefault("JIRA_EMAIL", "test@test.com")
    from middleware.app import create_app
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


# ── Unit Tests: Scenario Simulations ─────────────────────────────────

class TestResourceStress:
    """Tests for the resource_stress scenario."""

    @patch("dreaming_engine.GEMINI_API_KEY", None)  # Use fallback summary
    def test_removing_one_member_reduces_velocity(self, engine, sample_sprint_data):
        result = engine.dream("resource_stress", sample_sprint_data, {"remove_count": 1})

        assert result.scenario_type == "resource_stress"
        assert result.projected_velocity < result.original_velocity
        assert result.risk_score > 0.0
        assert len(result.affected_issues) > 0
        assert result.dream_id.startswith("dream_resource_stress_")

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_removing_all_members_max_risk(self, engine, sample_sprint_data):
        result = engine.dream("resource_stress", sample_sprint_data, {"remove_count": 3})

        assert result.projected_velocity == 0.0
        assert result.risk_score > 0.5

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_empty_team_no_crash(self, engine):
        empty_data = {"issues": [], "team_members": [], "velocity": 0, "days_remaining": 5}
        result = engine.dream("resource_stress", empty_data, {"remove_count": 1})

        assert result.risk_score == 0.0


class TestScopeCreep:
    """Tests for the scope_creep scenario."""

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_adding_issues_increases_risk(self, engine, sample_sprint_data):
        result = engine.dream("scope_creep", sample_sprint_data, {"additional_issues": 10})

        assert result.scenario_type == "scope_creep"
        assert result.risk_score > 0.0
        assert len(result.affected_issues) == 10  # synthetic DREAM-N IDs

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_high_priority_additions_cause_more_risk(self, engine, sample_sprint_data):
        low = engine.dream("scope_creep", sample_sprint_data, {"additional_issues": 5, "priority": 4})
        high = engine.dream("scope_creep", sample_sprint_data, {"additional_issues": 5, "priority": 1})

        assert high.risk_score >= low.risk_score


class TestPriorityShift:
    """Tests for the priority_shift scenario."""

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_shift_creates_starved_issues(self, engine, sample_sprint_data):
        result = engine.dream("priority_shift", sample_sprint_data, {
            "target_epic": "EPIC-1",
            "shift_percentage": 50
        })

        assert result.scenario_type == "priority_shift"
        assert len(result.affected_issues) > 0
        # Velocity stays the same (just redistributed)
        assert result.projected_velocity == result.original_velocity

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_auto_selects_target_epic(self, engine, sample_sprint_data):
        result = engine.dream("priority_shift", sample_sprint_data, {"shift_percentage": 30})
        assert result.scenario_type == "priority_shift"


# ── Unit Tests: Persistence ──────────────────────────────────────────

class TestDreamPersistence:

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_dream_is_saved(self, engine, sample_sprint_data):
        result = engine.dream("resource_stress", sample_sprint_data)

        dreams = engine.list_dreams()
        assert len(dreams) >= 1
        assert dreams[0]["dream_id"] == result.dream_id

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_dream_roundtrip(self, engine, sample_sprint_data):
        result = engine.dream("scope_creep", sample_sprint_data, {"additional_issues": 3})

        loaded = engine.load_dream(result.dream_id)
        assert loaded is not None
        assert loaded.dream_id == result.dream_id
        assert loaded.scenario_type == "scope_creep"
        assert loaded.risk_score == result.risk_score


# ── Integration Tests: API Endpoints ─────────────────────────────────

class TestDreamAPI:

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_dream_endpoint_missing_scenario(self, client):
        resp = client.post("/dream", json={})
        assert resp.status_code == 400
        assert "Missing" in resp.get_json()["message"]

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_dream_endpoint_invalid_scenario(self, client):
        resp = client.post("/dream", json={"scenario": "time_travel"})
        assert resp.status_code == 400
        assert "Invalid" in resp.get_json()["message"]

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    @patch("middleware.routes.api._build_sprint_data")
    def test_dream_endpoint_success(self, mock_build, client, sample_sprint_data):
        mock_build.return_value = sample_sprint_data

        resp = client.post("/dream", json={
            "scenario": "resource_stress",
            "params": {"remove_count": 1}
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "dream" in data
        assert data["dream"]["scenario_type"] == "resource_stress"
        assert data["dream"]["risk_score"] > 0.0

    @patch("dreaming_engine.GEMINI_API_KEY", None)
    def test_dreams_list_endpoint(self, client):
        resp = client.get("/dreams")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "dreams" in data
