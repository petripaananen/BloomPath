import unittest
from unittest.mock import MagicMock, patch
import logging
import sys
import os

# Adjust path to import modules from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestrator import BloomPathOrchestrator

# Configure logging to show info
logging.basicConfig(level=logging.INFO, format='%(message)s')

class TestDreamingEngine(unittest.TestCase):
    @patch('orchestrator.WorldLabsClient')
    @patch('orchestrator.GenieClient')
    @patch('orchestrator.semantic_analyzer')
    @patch('ue5_interface.trigger_phantom_warning')
    @patch('ue5_interface.trigger_ue5_set_tag')
    def test_dreaming_consensus(self, mock_set_tag, mock_phantom, mock_semantic, mock_genie_cls, mock_world_cls):
        print("\n🧪 STARTING DREAMING ENGINE TEST 🧪")
        
        # 1. Setup Orchestrator with Mocks
        orchestrator = BloomPathOrchestrator()
        
        # Mock World Generation (Success)
        orchestrator.world_client.generate_world.return_value = {
            "mesh_path": "/tmp/test.gltf",
            "image_path": "/tmp/test.png"
        }
        
        # Mock Semantic Analysis
        mock_semantic.analyze_world.return_value = {"objects": [{"semantic_type": "wall", "tags": ["col_heavy"]}]}
        
        # 2. Mock Parallel Simulations (Crucial Step)
        # We want to simulate a "Risk Detected" scenario where Stress Test fails.
        
        def side_effect_simulate(image_path, mechanics, profile="baseline"):
            if profile == "stress_test":
                return {
                    "status": "completed",
                    "data": {
                        "verdict": "FAIL", 
                        "gameplay_summary": "Player clipped through floor at high velocity.",
                        "issues": [{"type": "Clipping", "severity": "High", "description": "Floor failure"}]
                    },
                    "profile": profile
                }
            else:
                # Baseline and Optimization PASS
                return {
                    "status": "completed",
                    "data": {
                        "verdict": "PASS", 
                        "gameplay_summary": "Smooth navigation.",
                        "issues": []
                    },
                    "profile": profile
                }
                
        orchestrator.genie_client.simulate_gameplay.side_effect = side_effect_simulate
        
        # 3. Run Process Ticket
        issue_data = {
            "key": "TEST-101",
            "fields": {
                "summary": "High-risk platforming level",
                "labels": ["platformer"]
            }
        }
        
        print(">> Processing Ticket...")
        result = orchestrator.process_ticket(issue_data)
        
        # 4. Assertions (The Proof)
        print("\n📊 VERIFICATION RESULTS:")
        
        # Check Confidence Score
        # 2 PASS, 1 FAIL => 66.6% Confidence
        self.assertAlmostEqual(result['confidence'], 66.6, delta=1.0)
        print(f"✅ Confidence Score verified: {result['confidence']:.1f}% (Expected ~66.7%)")
        
        # Check Phantom Warning Triggered
        mock_phantom.assert_called_once()
        call_args = mock_phantom.call_args
        # args is a tuple of positional arguments, kwargs is a dict
        _, kwargs = call_args 
        risk_calculated = kwargs.get('risk_level')
        print(f"✅ UE5 Ghost Object triggered. Risk Level sent: {risk_calculated:.2f}")
        
        # Check Report Generation
        expected_report = f"reports/PWM_Report_TEST-101_{int(result['duration'] + 0)}.md" # Timestamp tricky to match exactly, just check dir
        reports = os.listdir("reports")
        user_reports = [f for f in reports if "TEST-101" in f]
        self.assertTrue(len(user_reports) > 0)
        print(f"✅ Report generated: {user_reports[0]}")

if __name__ == '__main__':
    unittest.main()
