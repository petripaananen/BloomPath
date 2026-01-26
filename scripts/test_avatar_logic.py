
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock ue5_interface BEFORE importing middleware modules
mock_ue5 = MagicMock()
sys.modules["ue5_interface"] = mock_ue5

from middleware.models.ticket import UnifiedTicket, IssueType, IssueStatus
from middleware.core import process_ticket_event
from middleware.avatar_manager import avatar_manager

def test_avatar_integration():
    print("🧪 Starting Social Layer Integration Test...")

    # 1. Simulate a Ticket with an Assignee
    ticket = UnifiedTicket(
        id="PROJ-123",
        provider="jira",
        title="Planting New Features",
        status=IssueStatus.IN_PROGRESS,
        issue_type=IssueType.TASK,
        priority=3,
        assignee_id="user_alice",
        assignee_name="Alice Gardener",
        assignee_avatar="http://example.com/alice.jpg",
        raw_data={}
    )

    # 2. Process an 'updated' event
    print(f"  > Processing event for ticket assigned to {ticket.assignee_name}...")
    process_ticket_event(ticket, {"event_type": "updated"}, None)

    # 3. Verify User Registration in AvatarManager
    user = avatar_manager.users.get("user_alice")
    if user:
        print(f"  ✅ User registered correctly: {user.name} ({user.id})")
        if user.current_issue_id == "PROJ-123":
             print(f"  ✅ User location tracked at: {user.current_issue_id}")
        else:
             print(f"  ❌ User location mismatch: Expected PROJ-123, got {user.current_issue_id}")
    else:
        print("  ❌ User registration failed")

    # 4. Verify UE5 Interface Calls
    # Since it's the first time, it should SPIAWN
    if mock_ue5.trigger_ue5_spawn_avatar.called:
        args = mock_ue5.trigger_ue5_spawn_avatar.call_args
        print(f"  ✅ trigger_ue5_spawn_avatar called with: {args}")
    else:
        print("  ❌ trigger_ue5_spawn_avatar was NOT called (Expected for new user)")

    # 5. Move user to a new ticket
    print("\n  > Moving user to a new ticket (PROJ-456)...")
    ticket.id = "PROJ-456"
    process_ticket_event(ticket, {"event_type": "updated"}, None)

    if mock_ue5.trigger_ue5_move_avatar.called:
        args = mock_ue5.trigger_ue5_move_avatar.call_args
        print(f"  ✅ trigger_ue5_move_avatar called with: {args}")
    else:
        print("  ❌ trigger_ue5_move_avatar was NOT called")

if __name__ == "__main__":
    test_avatar_integration()
