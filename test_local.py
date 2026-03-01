import requests
import json
import uuid
import hmac
import hashlib
import os

secret = os.getenv("LINEAR_WEBHOOK_SECRET", "dummy_secret_for_tests")
url = "http://localhost:5005/webhooks/linear"

payload = {
    "action": "create",
    "type": "Issue",
    "data": {
        "id": str(uuid.uuid4()),
        "title": "Local Test Issue",
        "state": {"type": "started", "name": "In Progress"}
    }
}

payload_bytes = json.dumps(payload).encode('utf-8')
signature = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Linear-Signature": signature
}

print(f"POSTing to {url}...")
try:
    r = requests.post(url, data=payload_bytes, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
