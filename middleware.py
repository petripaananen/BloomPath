import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
UE5_REMOTE_CONTROL_URL = os.getenv("UE5_REMOTE_CONTROL_URL", "http://localhost:8080/remote/object/call")

@app.route('/webhook', methods=['POST'])
def jira_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload"}), 400

    # Jira Webhook Event Type
    event_type = data.get('issue_event_type_name')
    issue = data.get('issue', {})
    issue_key = issue.get('key')
    fields = issue.get('fields', {})
    status = fields.get('status', {}).get('name')

    print(f"[{event_type}] Issue: {issue_key}, Status: {status}")

    # Trigger growth in UE5 when status changes to 'Done'
    if status == "Done":
        branch_id = issue_key # Using Jira issue key as branch ID
        result = trigger_ue5_growth(branch_id)
        if result:
            print(f"✅ Triggered growth for {branch_id} in UE5")
            return jsonify({"status": "triggered", "issue": issue_key}), 200
        else:
            print(f"❌ Failed to trigger growth for {branch_id}")
            return jsonify({"status": "ue5_error", "issue": issue_key}), 500

    return jsonify({"status": "received", "issue": issue_key}), 200

def trigger_ue5_growth(branch_id):
    # Remote Control API Payload
    payload = {
        "objectPath": "/Game/Maps/Main.Main:PersistentLevel.GrowerActor", # Placeholder actor path
        "functionName": "Grow_Leaves",
        "parameters": {
            "Target_Branch_ID": branch_id
        },
        "generateTransaction": True
    }
    try:
        # Note: UE5 Remote Control uses PUT for function calls
        response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling UE5 Remote Control: {e}")
        return None

if __name__ == '__main__':
    app.run(port=5000, debug=True)
