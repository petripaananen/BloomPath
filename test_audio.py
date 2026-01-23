
import os
import sys
import logging
from unittest.mock import MagicMock, patch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test.Audio")

# Add current dir to path
sys.path.append(os.getcwd())

import middleware

def test_audio_trigger():
    logger.info("🔊 Testing Audio Feedback Trigger...")
    
    # Mock the UE5 interface function within middleware
    with patch('ue5_interface.trigger_ue5_play_sound_2d') as mock_sound:
        
        # Trigger an event that should produce sound
        logger.info("1. Simulating 'task_completed' event...")
        middleware.push_audio_event("task_completed", issue_key="TEST-123")
        
        # Verify call
        mock_sound.assert_called_with("Success_Chime")
        logger.info("✅ 'Success_Chime' triggered correctly.")
        
        # Trigger another event
        logger.info("2. Simulating 'blocker_added' event...")
        middleware.push_audio_event("blocker_added", issue_key="TEST-124")
        
        # Verify call
        mock_sound.assert_called_with("Error_Buzz")
        logger.info("✅ 'Error_Buzz' triggered correctly.")
        
        # Verify queue still populated (for polling/fallback)
        assert len(middleware.audio_event_queue) >= 2
        logger.info(f"✅ Audio event queue persisted ({len(middleware.audio_event_queue)} events).")

if __name__ == "__main__":
    test_audio_trigger()
