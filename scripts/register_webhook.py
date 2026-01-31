import os
import requests
import json

# Configuration
API_KEY = os.environ.get("LINEAR_API_KEY")
TEAM_ID = os.environ.get("LINEAR_TEAM_ID")
NGROK_URL = "https://nonmotoring-closefisted-dorine.ngrok-free.dev"
WEBHOOK_URL = f"{NGROK_URL}/webhooks/linear"

if not API_KEY or not TEAM_ID:
    print("❌ Error: Missing LINEAR_API_KEY or LINEAR_TEAM_ID environment variables.")
    print("Please set these in your .env file or environment.")
    exit(1)

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

def get_ngrok_url():
    try:
        r = requests.get("http://localhost:4040/api/tunnels")
        data = r.json()
        return data["tunnels"][0]["public_url"]
    except Exception as e:
        print(f"❌ Failed to get ngrok URL: {e}")
        return None

def main():
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        return
        
    webhook_url = f"{ngrok_url}/webhooks/linear"
    print(f"🔗 Registering Webhook: {webhook_url}")
    
    # 1. Check existing webhooks and DELETE if found (to rotate secret)
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
    mutation_delete = """
    mutation DeleteWebhook($id: String!) {
        webhookDelete(id: $id) {
            success
        }
    }
    """
    data = execute_query(query_check)
    existing = data.get("webhooks", {}).get("nodes", [])
    
    for wh in existing:
        if wh["url"] == webhook_url:
            print(f"⚠️  Found existing webhook {wh['id']}, deleting to rotate secret...")
            execute_query(mutation_delete, {"id": wh["id"]})

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
        "url": webhook_url,
        "label": "BloomPath Dev (Ngrok)"
    }
    
    result = execute_query(mutation, variables)
    webhook = result.get("webhookCreate", {}).get("webhook")
    
    if webhook:
        print(f"✅ Created Webhook: {webhook['id']}")
        print(f"KEY_START{webhook['secret']}KEY_END")
        
        # Write secret to a temp file so we can read it easily into env
        with open("linear_secret.txt", "w") as f:
            f.write(webhook['secret'])
    else:
        print("❌ Failed to create webhook")
        print(result)

if __name__ == "__main__":
    main()
