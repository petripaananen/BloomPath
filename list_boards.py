"""Script to list all Jira boards for finding the Board ID."""
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
    print(f"\n{'='*50}")
    print("Available Jira Boards")
    print(f"{'='*50}")
    for b in boards:
        print(f"  ID: {b['id']:>3}  |  Name: {b['name']}")
    print(f"{'='*50}\n")
else:
    print(f"Error: {response.status_code} - {response.text}")
