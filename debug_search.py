import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

domain = os.getenv("JIRA_DOMAIN", "petri-paananen.atlassian.net")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_API_TOKEN")

url = f"https://{domain}/rest/api/3/search"
auth = HTTPBasicAuth(email, token)
params = {"jql": "project = 'KAN'", "maxResults": 1}

print(f"Testing Search API: {url}")
try:
    response = requests.get(url, params=params, auth=auth)
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}")
    else:
        print(f"Total Issues: {response.json().get('total')}")
except Exception as e:
    print(f"❌ Error: {e}")
