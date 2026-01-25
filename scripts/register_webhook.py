import os
import requests
import json

# Configuration
API_KEY = os.environ.get("LINEAR_API_KEY")
TEAM_ID = os.environ.get("LINEAR_TEAM_ID")
NGROK_URL = "https://nonmotoring-closefisted-dorine.ngrok-free.dev"
WEBHOOK_URL = f"{NGROK_URL}/webhooks/linear"

if not API_KEY or not TEAM_ID:
    # Fallback for reliability in this shell
    API_KEY = "lin_api_X43vEYPTCxCdLCYIlLlHyRe9TT514qEJCDAy4nsw"
    TEAM_ID = "309b158e-1d2e-4722-bddc-e8b1c7f8b1f9"

GRAPHQL_URL = "https://api.linear.app/graphql"
HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

def execute_query(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    response = requests.post(GRAPHQL_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("data", {})

def main():
    print(f"🔗 Registering Webhook: {WEBHOOK_URL}")
    
    # 1. Check existing webhooks
    query_check = """
    query GetWebhooks {
        webhooks {
            nodes {
                id
                url
                enabled
            }
        }
    }
    """
    data = execute_query(query_check)
    existing = data.get("webhooks", {}).get("nodes", [])
    
    for wh in existing:
        if wh["url"] == WEBHOOK_URL:
            print(f"✅ Webhook already exists: {wh['id']}")
            return

    # 2. Create Webhook
    mutation = """
    mutation CreateWebhook($teamId: String!, $url: String!, $label: String!) {
        webhookCreate(input: {
            teamId: $teamId
            url: $url
            label: $label
            resourceTypes: ["Issue", "Comment"]
        }) {
            webhook {
                id
                secret
                enabled
            }
            success
        }
    }
    """
    
    variables = {
        "teamId": TEAM_ID,
        "url": WEBHOOK_URL,
        "label": "BloomPath Dev (Ngrok)"
    }
    
    result = execute_query(mutation, variables)
    webhook = result.get("webhookCreate", {}).get("webhook")
    
    if webhook:
        print(f"✅ Created Webhook: {webhook['id']}")
        print(f"🔑 Secret: {webhook['secret']}")
        
        # Write secret to a temp file so we can read it easily into env
        with open("linear_secret.txt", "w") as f:
            f.write(webhook['secret'])
    else:
        print("❌ Failed to create webhook")
        print(result)

if __name__ == "__main__":
    main()
