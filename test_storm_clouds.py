import os
import sys
import logging
from unittest.mock import patch, MagicMock

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test.StormClouds")

# Add current dir to path
sys.path.append(os.getcwd())

from dreaming_engine import dreaming_engine


def test_evaluate_dependency_risks():
    logger.info("🌩️ Testing Localized Dependency Storm Clouds...")
    
    # Construct mock sprint data
    sprint_data = {
        "issues": [
            # Zone A: Highly Blocked, High Priority (Severe Storm Expected)
            {"id": "A1", "epic": "Zone-A", "status": "blocked", "priority": 1},
            {"id": "A2", "epic": "Zone-A", "status": "blocked", "priority": 2},
            {"id": "A3", "epic": "Zone-A", "status": "in_progress", "priority": 1}, # Treated as blocked due to priority
            {"id": "A4", "epic": "Zone-A", "status": "done", "priority": 3},
            
            # Zone B: All Done (Clear Skies Expected)
            {"id": "B1", "epic": "Zone-B", "status": "done", "priority": 3},
            {"id": "B2", "epic": "Zone-B", "status": "done", "priority": 5},
            
            # Zone C: Marginal Risk (In progress low priority, not blocked)
            {"id": "C1", "epic": "Zone-C", "status": "in_progress", "priority": 4},
            {"id": "C2", "epic": "Zone-C", "status": "todo", "priority": 5},
            {"id": "C3", "epic": "Zone-C", "status": "done", "priority": 3},
        ]
    }
    
    with patch('ue5_interface.trigger_ue5_storm_cloud') as mock_storm:
        intensities = dreaming_engine.evaluate_dependency_risks(sprint_data)
        
        logger.info(f"Storm Intensities output: {intensities}")
        
        # Zone A assertions
        assert "Zone-A" in intensities, "Zone A should be evaluated"
        assert intensities["Zone-A"] > 0.6, "Zone A should have a severe storm intensity"
        
        # Zone B assertions
        assert "Zone-B" in intensities, "Zone B should be evaluated"
        assert intensities["Zone-B"] == 0.0, "Zone B should have 0.0 intensity (Clear Skies)"
        
        # Zone C assertions
        assert "Zone-C" in intensities, "Zone C should be evaluated"
        assert intensities["Zone-C"] < 0.6, "Zone C has no blocked but low completion, giving it a moderate risk score. Should be below 0.6"
        
        # Verify trigger counts. mock_storm is called for EVERY zone, even 0.0 intensity (to clear them)
        assert mock_storm.call_count == 3
        
        # Check specific call arguments
        # Call list evaluates mock arguments
        calls = mock_storm.call_args_list
        for call in calls:
            args, kwargs = call
            zone_id, int_val = args
            assert int_val == intensities[zone_id]
            logger.info(f"Verified call: Spawn_Storm_Cloud('{zone_id}', {int_val:.2f})")
            
        logger.info("✅ Dependency risks effectively segment localized spatial zones and output correct intensities.")

if __name__ == "__main__":
    test_evaluate_dependency_risks()
