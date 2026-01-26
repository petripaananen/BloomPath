
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock ue5_interface BEFORE importing middleware
mock_ue5 = MagicMock()
sys.modules["ue5_interface"] = mock_ue5

from middleware.models.ticket import UnifiedTicket, IssueType, IssueStatus
from middleware.core import process_ticket_event
from middleware.avatar_manager import avatar_manager

def test_audio_intensity():
    print("🧪 Starting Audio Intensity Verification...")
    
    # helper to simulate a user working
    def sim_user_activity(user_id, ticket_id):
        t = UnifiedTicket(
            id=ticket_id,
            provider="jira",
            title="Work",
            status=IssueStatus.IN_PROGRESS,
            issue_type=IssueType.TASK,
            priority=3,
            assignee_id=user_id,
            assignee_name=f"User {user_id}",
            assignee_avatar="url",
            raw_data={}
        )
        process_ticket_event(t, {"event_type": "updated"}, None)

    # 1. First User -> Intensity 0.2 (1/5)
    print("\n  > Adding User 1...")
    sim_user_activity("u1", "T-1")
    
    # Check trigger_ue5_ambience call
    if mock_ue5.trigger_ue5_ambience.called:
        args = mock_ue5.trigger_ue5_ambience.call_args[0][0] # first arg
        print(f"  ✅ Triggered Ambience: {args:.2f} (Expected 0.20)")
        if abs(args - 0.2) > 0.01:
             print("  ❌ Intensity mismatch!")
    else:
        print("  ❌ Ambience NOT triggered")

    # 2. Max out users -> Intensity 1.0 (5/5)
    print("\n  > Adding 4 more users (Total 5)...")
    sim_user_activity("u2", "T-2")
    sim_user_activity("u3", "T-3")
    sim_user_activity("u4", "T-4")
    sim_user_activity("u5", "T-5")
    
    # Get last call
    args = mock_ue5.trigger_ue5_ambience.call_args[0][0]
    print(f"  ✅ Triggered Ambience: {args:.2f} (Expected 1.00)")
    
    if args >= 1.0:
        print("  ✅ Saturation Logic Works")
    else:
         print(f"  ❌ Saturation Failed: {args}")

if __name__ == "__main__":
    test_audio_intensity()
