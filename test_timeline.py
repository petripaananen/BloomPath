import os
import sys
import time
import logging
from unittest.mock import patch, MagicMock

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test.Timeline")

# Add current dir to path
sys.path.append(os.getcwd())

from middleware.models.ticket import UnifiedTicket, IssueStatus, IssueType
# Use an in-memory db for testing so we don't pollute the actual cache
from middleware.timeline_cache import TimelineCache


def test_timeline_caching():
    logger.info("🕒 Testing Timeline Scrubbing...")
    
    # Init floating in-memory cache
    cache = TimelineCache(db_path=":memory:")
    
    # 1. T1 Created
    t1 = UnifiedTicket(
        id="TEST-1", provider="mock", project_id="zoneA", title="Test 1", description="",
        status=IssueStatus.TODO, issue_type=IssueType.TASK, priority=3
    )
    cache.log_event("created", t1)
    
    time.sleep(0.1) # artificial wait for distinct timestamps
    t_after_create = time.time()
    logger.info(f"Marker A: {t_after_create}")
    
    # 2. T1 Blocked
    time.sleep(0.1)
    t1.status = IssueStatus.IN_PROGRESS
    cache.log_event("blocked", t1)
    
    time.sleep(0.1)
    t_after_blocked = time.time()
    logger.info(f"Marker B: {t_after_blocked}")
    
    # 3. T1 Unblocked and Done
    time.sleep(0.1)
    t1.status = IssueStatus.DONE
    cache.log_event("completed", t1)
    
    time.sleep(0.1)
    t_after_done = time.time()
    logger.info(f"Marker C: {t_after_done}")
    
    # ── Assertions ──
    
    logger.info("Checking state at Marker A (Created)")
    state_a = cache.get_state_at_timestamp(t_after_create)
    assert len(state_a) == 1
    assert getattr(state_a[0], '_last_historical_event') == "created"
    assert state_a[0].status == IssueStatus.TODO
    
    logger.info("Checking state at Marker B (Blocked)")
    state_b = cache.get_state_at_timestamp(t_after_blocked)
    assert len(state_b) == 1
    assert getattr(state_b[0], '_last_historical_event') == "blocked"
    assert state_b[0].status == IssueStatus.IN_PROGRESS
    
    logger.info("Checking state at Marker C (Done)")
    state_c = cache.get_state_at_timestamp(t_after_done)
    assert len(state_c) == 1
    assert getattr(state_c[0], '_last_historical_event') == "completed"
    assert state_c[0].status == IssueStatus.DONE
    
    logger.info("✅ Timeline reconstruction accurately reproduces state isolation without bleeding forwards.")


def test_timeline_scrub_ue5_batcher():
    logger.info("🌲 Testing UE5 Replay Script Generation...")
    
    from ue5_interface import BATCHER, trigger_ue5_scrub_timeline
    
    # Construct a dummy state
    t1 = UnifiedTicket(
        id="TEST-1", provider="mock", project_id="zoneA", title="Test 1", description="",
        status=IssueStatus.IN_PROGRESS, issue_type=IssueType.TASK, priority=3
    )
    t1._last_historical_event = "blocked"
    
    t2 = UnifiedTicket(
        id="TEST-2", provider="mock", project_id="zoneB", title="Test 2", description="",
        status=IssueStatus.DONE, issue_type=IssueType.FEATURE, priority=5
    )
    t2._last_historical_event = "completed"
    
    historical_state = [t1, t2]
    
    # Execute batch formulation
    # We must patch trigger_ue5_reset_garden and AGENT.execute_python to avoid actual connections
    with patch('ue5_interface.trigger_ue5_reset_garden') as mock_reset:
        with patch('ue5_interface.AGENT.execute_python', return_value="success") as mock_exec:
            res = trigger_ue5_scrub_timeline(historical_state)
            
            mock_reset.assert_called_once()
            mock_exec.assert_called_once()
            
            # Extract the generated script block
            generated_script = mock_exec.call_args[0][0]
            
            # Check assertions in raw text since this is what hits UE5
            assert "actor.Trigger_Growth('TEST-1', 'leaf', 1.0, 'zoneA', false)" in generated_script, "Missing expected Growth call for TEST-1"
            assert "actor.Add_Thorns('TEST-1', '')" in generated_script, "Missing requested thorns on TEST-1"
            
            assert "actor.Trigger_Growth('TEST-2', 'branch', 2.0, 'zoneB', true)" in generated_script, "Missing expected Growth+Bloom call for priority 5 feature TEST-2"
            
            logger.info("✅ Batcher synthesizes correctly injected growth properties and respects historical thorn modifiers.")

if __name__ == "__main__":
    test_timeline_caching()
    test_timeline_scrub_ue5_batcher()
