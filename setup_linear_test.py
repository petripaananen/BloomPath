import os
import requests
import random
import time

# Configuration
API_KEY = os.environ.get("LINEAR_API_KEY")
TEAM_ID = os.environ.get("LINEAR_TEAM_ID")
PROJECT_NAME = "Garden Protocol"
GRAPHQL_URL = "https://api.linear.app/graphql"

if not API_KEY or not TEAM_ID:
    print("Error: Missing LINEAR_API_KEY or LINEAR_TEAM_ID")
    exit(1)

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
    result = response.json()
    
    if "errors" in result:
        print(f"GraphQL Errors: {result['errors']}")
        return None
    
    return result.get("data", {})

def create_project(team_id, name):
    print(f"Creating project '{name}'...")
    mutation = """
    mutation CreateProject($teamId: String!, $name: String!) {
        projectCreate(input: { teamIds: [$teamId], name: $name }) {
            project {
                id
                name
                slugId
            }
            success
        }
    }
    """
    
    result = execute_query(mutation, {"teamId": team_id, "name": name})
    if result:
        project = result.get("projectCreate", {}).get("project")
        if project:
            print(f"✅ Created project: {project['name']} (ID: {project['id']})")
            return project['id']
    return None

def create_issue(team_id, project_id, title, description, priority, label_name=None):
    mutation = """
    mutation CreateIssue($teamId: String!, $projectId: String, $title: String!, $description: String, $priority: Int) {
        issueCreate(input: { 
            teamId: $teamId, 
            projectId: $projectId, 
            title: $title, 
            description: $description,
            priority: $priority
        }) {
            issue {
                id
                identifier
                title
                url
            }
            success
        }
    }
    """
    
    # Simple mapping for labels: In a real script we'd need to fetch label IDs first.
    # We'll skip label assignment in creation for simplicity unless we fetch them first.
    
    variables = {
        "teamId": team_id,
        "projectId": project_id,
        "title": title,
        "description": description,
        "priority": priority
    }
    
    result = execute_query(mutation, variables)
    if result:
        issue = result.get("issueCreate", {}).get("issue")
        if issue:
            print(f"  - Created {issue['identifier']}: {issue['title']}")
            return issue
    return None

def main():
    print(f"🌿 Setting up '{PROJECT_NAME}' in Linear...")
    
    # 1. Create Project
    project_id = create_project(TEAM_ID, PROJECT_NAME)
    if not project_id:
        # Try to find existing project if creation failed (maybe it already exists)
        query = """
        query GetProjects($teamId: String!) {
            team(id: $teamId) {
                projects {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        result = execute_query(query, {"teamId": TEAM_ID})
        projects = result.get("team", {}).get("projects", {}).get("nodes", [])
        for p in projects:
            if p["name"] == PROJECT_NAME:
                project_id = p["id"]
                print(f"ℹ️  Found existing project: {p['name']} (ID: {project_id})")
                break
    
    if not project_id:
        print("❌ Failed to get Project ID. Aborting.")
        return

    # 2. Create Test Issues
    issues_data = [
        ("Implement L3 Dreaming Engine", "Core logic for the dreaming engine.", 1),
        ("Visualize Latent Risks", "Show risks as red vines in the garden.", 2),
        ("Optimize Rendering Performance", "Ensure 60fps in UE5.", 3),
        ("Fix Webhook Timeout", "Linear webhooks depend on fast response.", 1),
        ("Add Weather Effects", "Map sprint health to rain/sun.", 4),
        ("Refactor Provider Class", " Abstract Jira/Linear logic.", 3),
        ("Update Documentation", "Add new architecture diagrams.", 4),
    ]
    
    print("\nCreating test issues...")
    for title, desc, prio in issues_data:
        create_issue(TEAM_ID, project_id, title, desc, prio)
        time.sleep(0.5) # Rate limiting politeness

    print("\n✅ Setup Complete! Check your Linear workspace.")

if __name__ == "__main__":
    main()
