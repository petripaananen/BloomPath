
import os
import sys
import logging
import time
from unittest.mock import MagicMock, patch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test.Orchestrator")

# Add current dir to path
sys.path.append(os.getcwd())

from orchestrator import BloomPathOrchestrator

def test_orchestrator_flow():
    logger.info("🚀 Starting BloomPath Orchestrator Verification")
    
    # Mock data
    class MockIssue:
        def __init__(self, id, title, labels):
            self.id = id
            self.title = title
            self.labels = labels

    mock_issue = MockIssue("BLP-101", "A mystical floating island", ["puzzle"])
    
    # Mock Clients
    with patch('orchestrator.WorldLabsClient') as MockWorldClient, \
         patch('orchestrator.semantic_analyzer.analyze_world') as mock_analyze, \
         patch('ue5_interface.trigger_ue5_load_level') as mock_load, \
         patch('ue5_interface.trigger_ue5_set_tag') as mock_tag, \
         patch('os.path.exists') as mock_exists:
         
        mock_exists.return_value = True
        
        # Setup World Client Mock
        world_instance = MockWorldClient.return_value
        world_instance.generate_world.return_value = {
            "mesh_path": "content/generated/test_world.gltf",
            "image_path": "test_image.png"
        }
        
        # Setup Semantic Analyzer Mock
        mock_analyze.return_value = {
            "objects": [
                {"name": "Island", "semantic_type": "StaticMesh", "tags": ["Floating"]}
            ]
        }
        
        # Run Orchestrator
        orch = BloomPathOrchestrator()
        result = orch.process_ticket(mock_issue)
        
        # Assertions
        logger.info("📋 Verifying functionality...")
        
        assert world_instance.generate_world.call_count == 1
        assert mock_analyze.call_count == 1
        assert mock_load.call_count == 1
        assert result['status'] == 'success'
        
        logger.info("✅ Orchestrator Flow Verification Passed!")

def test_mechanics_parsing():
    logger.info("🧠 Testing Mechanics Parsing Logic...")
    orch = BloomPathOrchestrator()
    
    class MockIssue:
        def __init__(self, id, title, labels):
            self.id = id
            self.title = title
            self.labels = labels

    # Test Case 1: Standard
    issue_standard = MockIssue("TEST-1", "Simple task", [])
    intent = orch.parse_intent(issue_standard)
    assert "Standard movement" in intent['mechanics']
    logger.info("✅ Standard mechanics parsed correctly.")
    
    # Test Case 2: Vehicle Level
    issue_vehicle = MockIssue("TEST-2", "Race track", ["vehicle"])
    intent = orch.parse_intent(issue_vehicle)
    # Note: This depends on mechanics.json content
    # For now we just verify it runs without error if config is missing
    logger.info(f"Mechanics found: {intent['mechanics']}")
    
if __name__ == "__main__":
    test_mechanics_parsing()
    test_orchestrator_flow()
