import os
import requests
import json

from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("LINEAR_API_KEY")
if not api_key:
    print("❌ Error: LINEAR_API_KEY not found in environment")
    exit(1)

print(f"Using API Key: {api_key[:10]}...")

url = "https://api.linear.app/graphql"
headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}

query = """
query {
  viewer {
    id
    name
    email
  }
  teams {
    nodes {
      id
      name
      key
    }
  }
}
"""

try:
    response = requests.post(url, json={"query": query}, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    if "errors" in data:
        print("Errors:", data["errors"])
    else:
        viewer = data["data"]["viewer"]
        print(f"\nUser: {viewer['name']} ({viewer['email']})")
        
        teams = data["data"]["teams"]["nodes"]
        print(f"\nFound {len(teams)} Teams:")
        for team in teams:
            print(f"- Name: {team['name']}")
            print(f"  ID: {team['id']}")
            print(f"  Key: {team['key']}")
            print("-" * 20)

except Exception as e:
    print(f"Error: {e}")
