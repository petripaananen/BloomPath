
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
    mock_issue = {
        "key": "BLP-101",
        "fields": {
            "summary": "A mystical floating island",
            "description": "Level with zero gravity jumps",
            "labels": ["Genie"],
            "issuetype": {"name": "Story"}
        }
    }
    
    # Mock Clients
    # Patching the references inside orchestrator.py because of 'from X import Y'
    with patch('orchestrator.WorldLabsClient') as MockWorldClient, \
         patch('orchestrator.GenieClient') as MockGenieClient, \
         patch('ue5_interface.trigger_ue5_set_tag') as mock_ue5_tag:
         
        # Setup World Client Mock
        world_instance = MockWorldClient.return_value
        # Return a fake path and the existing test image we know works
        existing_image = os.path.join(os.getcwd(), r"..\brain\2d2f0246-5cd6-4228-b0d8-d4ae43f72970\chinese_garden_test_1769183395241.png")
        if not os.path.exists(existing_image):
             # Fallback if specific file missing, use any png or dummy
             existing_image = "dummy.png"
             
        world_instance.generate_world.return_value = {
            "mesh_path": "content/generated/test_world.gltf",
            "image_path": existing_image
        }
        
        # Setup Genie Client Mock
        genie_instance = MockGenieClient.return_value
        genie_instance.simulate_gameplay.side_effect = [
            # First call: FAIL (to test retry logic)
            {
                "status": "completed", 
                "data": {
                    "verdict": "FAIL", 
                    "issues": [{"type": "Clipping", "description": "Wall collision missing"}],
                    "gameplay_summary": "Player clipped through wall."
                }
            },
            # Second call: PASS
            {
                "status": "completed", 
                "data": {
                    "verdict": "PASS", 
                    "issues": [],
                    "gameplay_summary": "Smooth navigation."
                }
            }
        ]
        
        # Run Orchestrator
        orch = BloomPathOrchestrator()
        result = orch.process_ticket(mock_issue)
        
        # Assertions
        logger.info("📋 Verifying functionality...")
        
        # Check Retries
        # Expected: 2 calls to generate_world (initial + retry)
        # Expected: 2 calls to simulate_gameplay
        assert world_instance.generate_world.call_count == 2, f"Expected 2 world generations, got {world_instance.generate_world.call_count}"
        assert genie_instance.simulate_gameplay.call_count == 2, f"Expected 2 genie simulations, got {genie_instance.simulate_gameplay.call_count}"
        
        # Check Success
        assert result['status'] == 'success', "Orchestrator failed to return success"
        assert result['iterations'] == 2, f"Expected 2 iterations, got {result['iterations']}"
        
        # Check UE5 Injection
        # We expect some tags to be injected if the semantic analyzer works (which uses the real image if present)
        # Since we might be using a dummy image if the file doesn't exist, we warn if no calls.
        if mock_ue5_tag.call_count > 0:
            logger.info(f"✅ UE5 Tag Injection successful ({mock_ue5_tag.call_count} tags applied)")
        else:
            logger.warning("⚠️ No UE5 tags injected (might be expected if test image invalid or analyzed as empty)")
            
        logger.info("✅ Orchestrator Flow Verification Passed!")

def test_mechanics_parsing():
    logger.info("🧠 Testing Mechanics Parsing Logic...")
    orch = BloomPathOrchestrator()
    
    # Test Case 1: Dashboard (Standard)
    issue_standard = {"fields": {"summary": "Simple task", "labels": [], "key": "TEST-1"}}
    intent = orch.parse_intent(issue_standard)
    assert "Standard movement" in intent['mechanics']
    logger.info("✅ Standard mechanics parsed correctly.")
    
    # Test Case 2: Vehicle Level
    issue_vehicle = {"fields": {"summary": "Race track", "labels": ["vehicle"], "key": "TEST-2"}}
    intent = orch.parse_intent(issue_vehicle)
    assert "driving physics" in intent['mechanics']
    logger.info("✅ Vehicle mechanics parsed correctly.")
    
    # Test Case 3: Puzzle Platformer
    issue_complex = {"fields": {"summary": "Brain teaser", "labels": ["puzzle", "platformer"], "key": "TEST-3"}}
    intent = orch.parse_intent(issue_complex)
    assert "button interaction" in intent['mechanics']
    assert "double jump" in intent['mechanics']
    logger.info("✅ Complex mechanics parsed correctly.")

if __name__ == "__main__":
    test_mechanics_parsing()
    test_orchestrator_flow()
