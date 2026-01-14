"""Test the /sprint_status endpoint to verify Environmental Dynamics configuration."""
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# The middleware needs to be running for this to work
# This script tests directly against Jira to verify our configuration

domain = os.getenv("JIRA_DOMAIN")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_API_TOKEN")
board_id = os.getenv("JIRA_BOARD_ID")

print(f"\n{'='*60}")
print("Testing Sprint Health Configuration")
print(f"{'='*60}")
print(f"Board ID: {board_id}")

# Get active sprint
url = f"https://{domain}/rest/agile/1.0/board/{board_id}/sprint"
response = requests.get(url, params={"state": "active"}, auth=(email, token))

if response.status_code == 200:
    sprints = response.json().get('values', [])
    if sprints:
        sprint = sprints[0]
        print(f"\n✅ Active Sprint Found: {sprint.get('name')}")
        print(f"   Start: {sprint.get('startDate', 'N/A')}")
        print(f"   End: {sprint.get('endDate', 'N/A')}")
        
        # Get issues in sprint
        issues_url = f"https://{domain}/rest/agile/1.0/sprint/{sprint['id']}/issue"
        issues_resp = requests.get(issues_url, params={"fields": "status"}, auth=(email, token))
        
        if issues_resp.status_code == 200:
            issues = issues_resp.json().get('issues', [])
            done_count = sum(1 for i in issues if i.get('fields', {}).get('status', {}).get('name', '').lower() == 'done')
            print(f"   Issues: {len(issues)} total, {done_count} done")
            
            # Calculate weather
            if issues:
                ratio = done_count / len(issues)
                if ratio >= 0.6:
                    weather = "☀️ sunny"
                elif ratio >= 0.3:
                    weather = "☁️ cloudy"
                else:
                    weather = "⛈️ storm"
                print(f"\n🌤️ Predicted Weather: {weather} ({ratio:.0%} complete)")
    else:
        print("\n⚠️ No active sprint found. Start a sprint to test weather features.")
else:
    print(f"\n❌ Error: {response.status_code} - {response.text}")

print(f"\n{'='*60}\n")
