"""Discover board types and find Scrum boards that support sprints."""
import requests
from dotenv import load_dotenv
import os

load_dotenv()

domain = os.getenv("JIRA_DOMAIN")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_API_TOKEN")

url = f"https://{domain}/rest/agile/1.0/board"
response = requests.get(url, auth=(email, token))

if response.status_code == 200:
    boards = response.json().get('values', [])
    print(f"\n{'='*60}")
    print("Jira Boards - Detailed View")
    print(f"{'='*60}")
    
    scrum_boards = []
    for b in boards:
        board_type = b.get('type', 'unknown')
        marker = "✅" if board_type == 'scrum' else "❌"
        print(f"  {marker} ID: {b['id']:>3}  |  Type: {board_type:>7}  |  Name: {b['name']}")
        if board_type == 'scrum':
            scrum_boards.append(b)
    
    print(f"{'='*60}")
    
    if scrum_boards:
        print(f"\n✅ Found {len(scrum_boards)} Scrum board(s) that support sprints!")
        print("   Use one of these Board IDs in your .env file.")
    else:
        print("\n⚠️ No Scrum boards found. Your boards are Kanban-style.")
        print("   Options:")
        print("   1. Create a new Scrum board for a project")
        print("   2. Use issue completion rate instead of sprint progress")
        print("   3. Convert the KAN board to Scrum (may require project changes)")
    print()
else:
    print(f"Error: {response.status_code} - {response.text}")
