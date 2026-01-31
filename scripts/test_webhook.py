import requests
import json
import uuid

def get_ngrok_url():
    try:
        r = requests.get("http://localhost:4040/api/tunnels")
        data = r.json()
        return data["tunnels"][0]["public_url"]
    except:
        return None

ngrok_url = get_ngrok_url()
if not ngrok_url:
    print("Failed to get ngrok URL")
    exit(1)

url = f"{ngrok_url}/webhooks/linear"
print(f"Targeting: {url}")
payload = {
    "action": "update",
    "type": "Issue",
    "data": {
        "id": str(uuid.uuid4()),
        "identifier": "LIN-123",
        "title": "Test Issue",
        "state": {"type": "started", "name": "In Progress"}
    },
    "updatedFrom": {
        "stateId": "some-old-state-id"
    }
}

import hmac
import hashlib

import os
from dotenv import load_dotenv

load_dotenv()
secret = os.getenv("LINEAR_WEBHOOK_SECRET")
if not secret:
    print("❌ Error: LINEAR_WEBHOOK_SECRET not set in .env")
    exit(1)
payload_bytes = json.dumps(payload).encode('utf-8')
signature = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Linear-Signature": signature
}

try:
    print(f"POST {url}")
    # Note: requests.post(json=...) serializes automatically, but we need exact bytes for signature
    # So we pass data=bytes and correct header
    r = requests.post(url, data=payload_bytes, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
