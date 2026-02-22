import os
import sys
import logging
from unittest.mock import MagicMock, patch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test.Audio")

# Add current dir to path
sys.path.append(os.getcwd())

import middleware.core as core
from middleware.models.ticket import UnifiedTicket, IssueStatus
from middleware.providers.base import IssueProvider

def test_audio_trigger():
    logger.info("🔊 Testing Audio Feedback Trigger...")
    
    # Mock the UE5 interface function directly
    with patch('ue5_interface.trigger_ue5_play_sound_2d') as mock_sound:
        
        # Trigger an event that should produce sound
        logger.info("1. Simulating 'task_completed' event...")
        core._push_audio_event("task_completed", issue_key="TEST-123")
        
        # Verify call
        mock_sound.assert_called_with("Success_Chime")
        logger.info("✅ 'Success_Chime' triggered correctly.")
        
        # Trigger another event
        logger.info("2. Simulating 'blocker_added' event...")
        core._push_audio_event("blocker_added", issue_key="TEST-124")
        
        # Verify call
        mock_sound.assert_called_with("Error_Buzz")
        logger.info("✅ 'Error_Buzz' triggered correctly.")

def test_sprint_audio_intensity():
    logger.info("🔊 Testing Sprint Audio Intensity calculation...")
    
    mock_provider = MagicMock(spec=IssueProvider)
    
    # Simulate 10 total issues: 4 done => intensity should be 0.4
    issues = [
        UnifiedTicket(id="1", provider="mock", project_id="test", title="T1", description="1", status=IssueStatus.DONE),
        UnifiedTicket(id="2", provider="mock", project_id="test", title="T2", description="2", status=IssueStatus.DONE),
        UnifiedTicket(id="3", provider="mock", project_id="test", title="T3", description="3", status=IssueStatus.DONE),
        UnifiedTicket(id="4", provider="mock", project_id="test", title="T4", description="4", status=IssueStatus.DONE),
        UnifiedTicket(id="5", provider="mock", project_id="test", title="T5", description="5", status=IssueStatus.IN_PROGRESS),
        UnifiedTicket(id="6", provider="mock", project_id="test", title="T6", description="6", status=IssueStatus.IN_PROGRESS),
        UnifiedTicket(id="7", provider="mock", project_id="test", title="T7", description="7", status=IssueStatus.TODO),
        UnifiedTicket(id="8", provider="mock", project_id="test", title="T8", description="8", status=IssueStatus.TODO),
        UnifiedTicket(id="9", provider="mock", project_id="test", title="T9", description="9", status=IssueStatus.TODO),
        UnifiedTicket(id="10", provider="mock", project_id="test", title="T10", description="10", status=IssueStatus.TODO)
    ]
    mock_provider.get_sprint_issues.return_value = issues
    
    mock_ue5 = MagicMock()
    sys.modules['ue5_interface'] = mock_ue5
    
    core.update_sprint_audio_intensity(mock_provider, "mock-sprint-id")
    
    # 4 done issues / 10 max cap = 0.4
    mock_ue5.trigger_ue5_ambient_audio.assert_called_with(0.4)
    logger.info("✅ Calculated 0.4 / 1.0 ambient intensity correctly.")
    
    # Simulate high performance: 15 done issues => intensity should cap at 1.0
    issues = [UnifiedTicket(id=str(i), provider="mock", project_id="test", title=f"T{i}", description="", status=IssueStatus.DONE) for i in range(15)]
    mock_provider.get_sprint_issues.return_value = issues
    
    mock_ue5.reset_mock()
    core.update_sprint_audio_intensity(mock_provider, "mock-sprint-id")
    
    # Intensity max clamp is 1.0
    mock_ue5.trigger_ue5_ambient_audio.assert_called_with(1.0)
    logger.info("✅ Clamped intensity at max 1.0 correctly.")

if __name__ == "__main__":
    test_audio_trigger()
    test_sprint_audio_intensity()
