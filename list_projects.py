import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

domain = os.getenv("JIRA_DOMAIN")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_API_TOKEN")

url = f"https://{domain}/rest/api/3/project"
auth = HTTPBasicAuth(email, token)

print(f"Listing projects for: {domain}")
try:
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    projects = response.json()
    for p in projects:
        print(f" - {p.get('key')}: {p.get('name')}")
except Exception as e:
    print(f"❌ Error: {e}")
