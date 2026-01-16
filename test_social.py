"""Test the Phase 4 & 5 endpoints: /team_members and /audio_events."""
import requests

MIDDLEWARE_URL = "http://localhost:5000"

print("\n" + "="*60)
print("Testing Phase 4 & 5: Social Layer + Audio Feedback")
print("="*60)

# Test 1: Health check
print("\n[1/3] Testing middleware health...")
try:
    resp = requests.get(f"{MIDDLEWARE_URL}/health", timeout=5)
    if resp.status_code == 200:
        print("  ✅ Middleware is running")
    else:
        print(f"  ❌ Health check failed: {resp.status_code}")
        exit(1)
except Exception as e:
    print(f"  ❌ Middleware not responding: {e}")
    print("     Start the middleware with: python middleware.py")
    exit(1)

# Test 2: Team Members (Phase 4)
print("\n[2/3] Testing /team_members (Social Layer)...")
try:
    resp = requests.get(f"{MIDDLEWARE_URL}/team_members", timeout=30)
    data = resp.json()
    print(f"  ✅ Response: {data['status']}")
    print(f"     Found {data['count']} team members")
    for member in data.get('members', []):
        tasks = len(member.get('active_tasks', []))
        done = member.get('completed_today', 0)
        pos = member.get('position', {})
        print(f"     - {member['display_name']}: {tasks} active, {done} done today")
        print(f"       Position: ({pos.get('x', 0)}, {pos.get('y', 0)}, {pos.get('z', 0)})")
except Exception as e:
    print(f"  ⚠️ Error: {e}")

# Test 3: Audio Events (Phase 5)
print("\n[3/3] Testing /audio_events (Audio Feedback)...")
try:
    resp = requests.get(f"{MIDDLEWARE_URL}/audio_events", timeout=5)
    data = resp.json()
    print(f"  ✅ Response: {data['status']}")
    print(f"     Found {data['count']} queued events")
    for event in data.get('events', []):
        print(f"     - {event['type']}: {event.get('issue_key', 'N/A')}")
except Exception as e:
    print(f"  ⚠️ Error: {e}")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
print("\nUE5 Usage:")
print("  • Poll /team_members every 30s for avatar spawning")
print("  • Poll /audio_events every 1s for sound triggers")
print("")
