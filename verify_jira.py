import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

def test_connection(domain):
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    
    url = f"https://{domain}/rest/api/3/myself"
    auth = HTTPBasicAuth(email, token)
    
    print(f"Testing connection to: {url}")
    try:
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            print(f"✅ Success! Connected to {domain}")
            return True
        else:
            print(f"❌ Failed! Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Try domain from .env
domain_env = os.getenv("JIRA_DOMAIN")
if not test_connection(domain_env):
    if "atlassia.net" in domain_env:
        alternative = domain_env.replace("atlassia.net", "atlassian.net")
        print(f"\nRetrying with likely correct domain: {alternative}")
        test_connection(alternative)
