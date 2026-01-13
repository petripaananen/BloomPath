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
    # Logic to parse Jira webhook and call UE5
    print(f"Received webhook: {data.get('issue_event_type_name')}")
    
    # Placeholder for status check and UE5 trigger
    # if data.get('issue', {}).get('fields', {}).get('status', {}).get('name') == "Done":
    #     trigger_ue5_growth("Branch_ID_Placeholder")
    
    return jsonify({"status": "success"}), 200

def trigger_ue5_growth(branch_id):
    payload = {
        "objectPath": "/Game/Maps/Main.Main:PersistentLevel.GrowerActor", # Update with actual path
        "functionName": "Grow_Leaves",
        "parameters": {
            "Target_Branch_ID": branch_id
        },
        "generateTransaction": True
    }
    try:
        response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error calling UE5: {e}")
        return None

if __name__ == '__main__':
    app.run(port=5000, debug=True)
