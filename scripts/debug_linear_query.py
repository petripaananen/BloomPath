# ... (imports and config same)
import os
import requests
import json

# Configuration
API_KEY = os.environ.get("LINEAR_API_KEY")
if not API_KEY:
    API_KEY = "lin_api_X43vEYPTCxCdLCYIlLlHyRe9TT514qEJCDAy4nsw"

GRAPHQL_URL = "https://api.linear.app/graphql"
HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

QUERY = """
query GetIssue($identifier: String!) {
    issue(id: $identifier) {
        id
        identifier
        title
        description
        # Removing blockedBy / blocking
        relations { 
            nodes { 
                type
                relatedIssue { id identifier } 
            } 
        }
    }
}
"""

VARIABLES = {"identifier": "WFM-1"}

def main():
    print("🔍 Testing Simplified Query...")
    payload = {"query": QUERY, "variables": VARIABLES}
    response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        print("✅ Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed: {response.text}")

if __name__ == "__main__":
    main()
