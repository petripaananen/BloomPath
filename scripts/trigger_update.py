import os
import requests
import time

API_KEY = os.environ.get("LINEAR_API_KEY") or "lin_api_X43vEYPTCxCdLCYIlLlHyRe9TT514qEJCDAy4nsw"
GRAPHQL_URL = "https://api.linear.app/graphql"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}

def main():
    print("🔄 Triggering update on WFM-1...")
    
    # Update title slightly to trigger webhook
    mutation = """
    mutation UpdateIssue($identifier: String!, $title: String!) {
        issueUpdate(id: $identifier, input: { title: $title }) {
            issue {
                id
                title
            }
            success
        }
    }
    """
    
    new_title = f"Implement L3 Dreaming Engine (Updated {int(time.time())})"
    
    # Need UUID for update, let's fetch it first or use identifier if supported (Linear API often needs UUID for mutations)
    # Actually issueUpdate takes 'id' which can be the UUID.
    # We found WFM-1 UUID earlier or we can query it again to be safe.
    
    # Quick Fetch WFM-1
    q_id = """query { issue(id: "WFM-1") { id } }"""
    r_id = requests.post(GRAPHQL_URL, json={"query": q_id}, headers=HEADERS).json()
    issue_uuid = r_id["data"]["issue"]["id"]
    
    payload = {
        "query": mutation,
        "variables": {
            "identifier": issue_uuid,
            "title": new_title
        }
    }
    
    response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    main()
