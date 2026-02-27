
import os
import sys
import logging
import pytest
from unittest.mock import MagicMock, patch, call

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test.SpawnInteractive")

sys.path.append(os.getcwd())


# ── Shared Fixtures ─────────────────────────────────────────────────

class MockIssue:
    """Lightweight stand-in for a UnifiedTicket."""
    def __init__(self, id, title, labels, attachments=None):
        self.id = id
        self.title = title
        self.labels = labels
        self.attachments = attachments or []


# ── UE5 Interface: trigger_ue5_spawn_interactive ────────────────────

class TestSpawnInteractiveFunction:
    """Tests for ue5_interface.trigger_ue5_spawn_interactive."""

    @patch("ue5_interface.AGENT")
    def test_spawn_sends_correct_python_script(self, mock_agent):
        """Verify the generated Python snippet references the right BP method."""
        mock_agent.execute_python.return_value = "Success"

        from ue5_interface import trigger_ue5_spawn_interactive
        result = trigger_ue5_spawn_interactive("BP_Microwave_C", "CounterTop")

        mock_agent.execute_python.assert_called_once()
        script = mock_agent.execute_python.call_args[0][0]

        assert "Spawn_Interactive_Item" in script
        assert "BP_Microwave_C" in script
        assert "CounterTop" in script
        assert result == {"output": "Success"}
        logger.info("✅ spawn_interactive sends correct Python script")

    @patch("ue5_interface.AGENT")
    def test_spawn_with_different_items(self, mock_agent):
        """Verify the function works for different item/surface combos."""
        mock_agent.execute_python.return_value = "Success"

        from ue5_interface import trigger_ue5_spawn_interactive

        combos = [
            ("BP_Mug_C", "DeskTop"),
            ("BP_Lamp_C", "TableTop"),
            ("BP_Chair_C", "Floor"),
        ]
        for item, surface in combos:
            mock_agent.reset_mock()
            trigger_ue5_spawn_interactive(item, surface)

            script = mock_agent.execute_python.call_args[0][0]
            assert item in script
            assert surface in script

        logger.info("✅ spawn_interactive parameterises items correctly")


# ── Orchestrator: UE5 Label Routing ─────────────────────────────────

class TestOrchestratorUE5Routing:
    """Tests that UE5-labeled issues route to spawn_interactive, not World Labs."""

    def test_parse_intent_detects_ue5_label(self):
        """parse_intent sets is_ue5_interactive when 'UE5' label present."""
        from orchestrator import BloomPathOrchestrator

        orch = BloomPathOrchestrator()
        issue = MockIssue("WFM-99", "Add a Microwave", ["UE5"])
        intent = orch.parse_intent(issue)

        assert intent["is_ue5_interactive"] is True
        logger.info("✅ parse_intent detects UE5 label")

    def test_parse_intent_case_insensitive(self):
        """UE5 label detection is case-insensitive."""
        from orchestrator import BloomPathOrchestrator

        orch = BloomPathOrchestrator()
        for label in ["ue5", "Ue5", "UE5", "uE5"]:
            issue = MockIssue("WFM-99", "Add item", [label])
            intent = orch.parse_intent(issue)
            assert intent["is_ue5_interactive"] is True

        logger.info("✅ UE5 label detection is case-insensitive")

    def test_non_ue5_issue_is_false(self):
        """Issues without UE5 label do not trigger interactive spawn."""
        from orchestrator import BloomPathOrchestrator

        orch = BloomPathOrchestrator()
        issue = MockIssue("WFM-100", "A forest scene", ["puzzle", "Feature"])
        intent = orch.parse_intent(issue)

        assert intent["is_ue5_interactive"] is False
        logger.info("✅ Non-UE5 issue is correctly excluded")

    @patch("orchestrator.WorldLabsClient")
    @patch("ue5_interface.AGENT")
    def test_ue5_issue_calls_spawn_not_world_labs(self, mock_agent, MockWorldClient):
        """UE5 issue routes to spawn_interactive and never calls World Labs."""
        mock_agent.execute_python.return_value = "Success"
        world_instance = MockWorldClient.return_value

        from orchestrator import BloomPathOrchestrator

        orch = BloomPathOrchestrator()
        issue = MockIssue("WFM-99", "Add a Microwave", ["UE5"])
        result = orch.process_ticket(issue)

        # World Labs should NOT have been called
        world_instance.generate_world.assert_not_called()

        # The spawn interactive script should have been sent to UE5
        mock_agent.execute_python.assert_called_once()
        script = mock_agent.execute_python.call_args[0][0]
        assert "Spawn_Interactive_Item" in script
        assert "Add a Microwave" in script
        assert "CounterTop" in script

        assert result["status"] == "success"
        logger.info("✅ UE5 issue routes to spawn_interactive, skips World Labs")

    @patch("orchestrator.WorldLabsClient")
    @patch("orchestrator.semantic_analyzer.analyze_world")
    @patch("ue5_interface.AGENT")
    @patch("os.path.exists", return_value=True)
    def test_non_ue5_issue_calls_world_labs(
        self, mock_exists, mock_agent, mock_analyze, MockWorldClient
    ):
        """Non-UE5 issues follow the standard World Labs pipeline."""
        world_instance = MockWorldClient.return_value
        world_instance.generate_world.return_value = {
            "mesh_path": "content/generated/test.gltf",
            "image_path": "test.png",
        }
        mock_analyze.return_value = {"objects": []}

        from orchestrator import BloomPathOrchestrator

        orch = BloomPathOrchestrator()
        issue = MockIssue("WFM-100", "Forest clearing", ["puzzle"])
        result = orch.process_ticket(issue)

        world_instance.generate_world.assert_called_once()
        assert result["status"] == "success"
        logger.info("✅ Non-UE5 issue routes to standard World Labs pipeline")


# ── Semantic Analyzer: Surface Detection ────────────────────────────

class TestSemanticSurfaceDetection:
    """Tests that the semantic analyzer prompt includes surface detection."""

    def test_prompt_includes_surface_keywords(self):
        """ANALYSIS_PROMPT contains the critical flat-surface identification."""
        from semantic_analyzer import ANALYSIS_PROMPT

        for keyword in ["CounterTop", "DeskTop", "TableTop", "Floor"]:
            assert keyword in ANALYSIS_PROMPT, f"Missing surface keyword: {keyword}"

        logger.info("✅ Semantic analyzer prompt includes surface detection")

    def test_prompt_includes_object_spawner_tag(self):
        """ANALYSIS_PROMPT lists ObjectSpawner as a valid tag."""
        from semantic_analyzer import ANALYSIS_PROMPT

        assert "ObjectSpawner" in ANALYSIS_PROMPT
        logger.info("✅ Semantic analyzer prompt includes ObjectSpawner tag")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
