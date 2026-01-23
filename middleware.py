import os
import re
import json
import logging
import time
from datetime import datetime
from typing import Optional, Any

import requests
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from functools import wraps

load_dotenv()

from world_client import WorldLabsClient
from semantic_analyzer import analyze_world, save_manifest
from validation_agent import run_validation

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("BloomPath")

app = Flask(__name__)

# ============================================================================
# Configuration
# ============================================================================
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

UE5_REMOTE_CONTROL_URL = os.getenv("UE5_REMOTE_CONTROL_URL", "http://localhost:8080/remote/object/call")
UE5_ACTOR_PATH = os.getenv("UE5_ACTOR_PATH", "/Game/Maps/Main.Main:PersistentLevel.GrowerActor")
UE5_GROW_FUNCTION = os.getenv("UE5_GROW_FUNCTION", "Grow_Leaves")
UE5_SHRINK_FUNCTION = os.getenv("UE5_SHRINK_FUNCTION", "Shrink_Leaves")
UE5_THORNS_FUNCTION = os.getenv("UE5_THORNS_FUNCTION", "Add_Thorns")
UE5_REMOVE_THORNS_FUNCTION = os.getenv("UE5_REMOVE_THORNS_FUNCTION", "Remove_Thorns")
UE5_WEATHER_FUNCTION = os.getenv("UE5_WEATHER_FUNCTION", "Set_Weather")
UE5_TIME_FUNCTION = os.getenv("UE5_TIME_FUNCTION", "Set_Time_Of_Day")

# Sprint Health Configuration
JIRA_BOARD_ID = os.getenv("JIRA_BOARD_ID")
JIRA_STORY_POINTS_FIELD = os.getenv("JIRA_STORY_POINTS_FIELD", "customfield_10016")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Blocker status detection
BLOCKER_STATUSES = ["Blocked", "Impediment", "On Hold", "Waiting"]

# Issue type to growth type mapping
ISSUE_TYPE_GROWTH = {
    "Bug": "flower",      # Bugs bloom into flowers when fixed
    "Story": "branch",    # Stories grow new branches
    "Task": "leaf",       # Tasks grow leaves
    "Epic": "trunk",      # Epics grow the trunk
    "Sub-task": "bud",    # Sub-tasks create buds
}

# Priority to growth modifier mapping
PRIORITY_MODIFIER = {
    "Highest": 2.0,   # Double growth
    "High": 1.5,      # 50% more growth
    "Medium": 1.0,    # Normal growth
    "Low": 0.75,      # Smaller growth
    "Lowest": 0.5,    # Half growth
}

# Priority to color mapping (RGB values for UE5)
PRIORITY_COLORS = {
    "Highest": {"R": 1.0, "G": 0.2, "B": 0.2},  # Red - urgent
    "High": {"R": 1.0, "G": 0.6, "B": 0.1},     # Gold - important
    "Medium": {"R": 0.3, "G": 0.8, "B": 0.3},   # Green - normal
    "Low": {"R": 0.4, "G": 0.6, "B": 0.4},      # Moss - low priority
    "Lowest": {"R": 0.5, "G": 0.5, "B": 0.5},   # Gray - minimal
}

# Issue key validation pattern (e.g., KAN-123, PROJ-1)
ISSUE_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9]+-\d+$')

# ============================================================================
# Audio Event Queue (Phase 5)
# ============================================================================
# Thread-safe event queue for UE5 audio feedback
audio_event_queue: list[dict[str, Any]] = []

def push_audio_event(event_type: str, issue_key: Optional[str] = None, 
                     user: Optional[str] = None, extra: Optional[dict] = None) -> None:
    """Push an audio event to the queue for UE5 to consume."""
    event = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
    }
    if issue_key:
        event["issue_key"] = issue_key
    if user:
        event["user"] = user
    if extra:
        event.update(extra)
    
    audio_event_queue.append(event)
    logger.info(f"🔔 Audio event queued: {event_type} (queue size: {len(audio_event_queue)})")


# ============================================================================
# Jira Authentication Helper
# ============================================================================
def get_jira_auth() -> HTTPBasicAuth:
    """Get centralized Jira authentication."""
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)


def validate_issue_key(issue_key: str) -> bool:
    """Validate Jira issue key format."""
    return bool(ISSUE_KEY_PATTERN.match(issue_key))


# ============================================================================
# Retry Decorator
# ============================================================================
def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator to retry a function on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception: Optional[Exception] = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
            logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator


# ============================================================================
# UE5 Remote Control Functions
# ============================================================================
@retry_on_failure()
def trigger_ue5_growth(
    branch_id: str,
    growth_type: str = "leaf",
    growth_modifier: float = 1.0,
    color: Optional[dict[str, float]] = None,
    epic_key: Optional[str] = None
) -> dict[str, Any]:
    """Calls the UE5 Remote Control API to trigger the Grow_Leaves function.
    
    Args:
        branch_id: The Jira issue key (e.g., KAN-28)
        growth_type: Type of growth based on issue type (leaf, branch, flower, etc.)
        growth_modifier: Size modifier based on priority
        color: RGB color dict based on priority
        epic_key: Parent Epic key for tree mapping
    """
    if color is None:
        color = PRIORITY_COLORS.get("Medium")
    
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_GROW_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id,
            "Growth_Type": growth_type,
            "Growth_Modifier": growth_modifier,
            "Color_R": color.get("R", 0.3),
            "Color_G": color.get("G", 0.8),
            "Color_B": color.get("B", 0.3),
            "Epic_ID": epic_key or ""
        },
        "generateTransaction": True
    }
    
    logger.info(f"Triggering UE5 growth: {branch_id} (type={growth_type}, modifier={growth_modifier}, epic={epic_key})")
    response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


@retry_on_failure()
def trigger_ue5_shrink(branch_id: str) -> dict[str, Any]:
    """Calls the UE5 Remote Control API to trigger the Shrink_Leaves function."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_SHRINK_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id
        },
        "generateTransaction": True
    }
    
    logger.info(f"Triggering UE5 shrink: {branch_id}")
    response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


@retry_on_failure()
def trigger_ue5_thorns(branch_id: str, epic_key: Optional[str] = None) -> dict[str, Any]:
    """Calls the UE5 Remote Control API to add thorns for blocked issues."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_THORNS_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id,
            "Epic_ID": epic_key or ""
        },
        "generateTransaction": True
    }
    
    logger.info(f"Triggering UE5 thorns (blocker): {branch_id}")
    response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


@retry_on_failure()
def trigger_ue5_remove_thorns(branch_id: str) -> dict[str, Any]:
    """Calls the UE5 Remote Control API to remove thorns when blocker is resolved."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_REMOVE_THORNS_FUNCTION,
        "parameters": {
            "Target_Branch_ID": branch_id
        },
        "generateTransaction": True
    }
    
    logger.info(f"Triggering UE5 remove thorns: {branch_id}")
    response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


# ============================================================================
# Jira Transition (UE5 → Jira)
# ============================================================================
@retry_on_failure()
def transition_issue_to_done(issue_key: str) -> dict[str, str]:
    """Transition a Jira issue to 'Done' status.
    
    This enables bidirectional flow: player waters flower in UE5 → issue moves to Done.
    Dynamically finds the 'Done' transition ID since it varies by workflow.
    """
    if not all([JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise ValueError("Missing Jira configuration")
    
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/transitions"
    auth = get_jira_auth()
    
    # Get available transitions
    response = requests.get(url, auth=auth, timeout=10)
    response.raise_for_status()
    transitions = response.json().get('transitions', [])
    
    # Find the "Done" transition (case-insensitive)
    done_transition: Optional[str] = None
    for t in transitions:
        if t['name'].lower() == 'done':
            done_transition = t['id']
            break
    
    if not done_transition:
        available = [t['name'] for t in transitions]
        raise ValueError(f"No 'Done' transition available for {issue_key}. Available: {available}")
    
    # Execute the transition
    payload = {"transition": {"id": done_transition}}
    response = requests.post(url, json=payload, auth=auth, timeout=10)
    response.raise_for_status()
    
    logger.info(f"🌊 Successfully transitioned {issue_key} to Done (watered in UE5)")
    return {"status": "success", "issue": issue_key}


# ============================================================================
# Sprint Health (Environmental Dynamics)
# ============================================================================
@retry_on_failure()
def get_active_sprint() -> Optional[dict[str, Any]]:
    """Get the active sprint from Jira board.
    
    Returns:
        dict with sprint info including id, name, startDate, endDate
        None if no active sprint
    """
    if not JIRA_BOARD_ID:
        logger.warning("JIRA_BOARD_ID not configured")
        return None
    
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/board/{JIRA_BOARD_ID}/sprint"
    auth = get_jira_auth()
    
    response = requests.get(url, params={"state": "active"}, auth=auth, timeout=10)
    response.raise_for_status()
    
    sprints = response.json().get('values', [])
    if sprints:
        return sprints[0]  # Return first active sprint
    return None


@retry_on_failure()
def get_sprint_issues(sprint_id: int) -> list[dict[str, Any]]:
    """Get all issues in a sprint with their status and story points.
    
    Returns:
        list of issues with key, status, and storyPoints
    """
    url = f"https://{JIRA_DOMAIN}/rest/agile/1.0/sprint/{sprint_id}/issue"
    auth = get_jira_auth()
    
    response = requests.get(
        url, 
        params={"fields": f"status,{JIRA_STORY_POINTS_FIELD},issuetype"},
        auth=auth, 
        timeout=10
    )
    response.raise_for_status()
    
    return response.json().get('issues', [])


def calculate_sprint_health(issues: list[dict[str, Any]]) -> str:
    """Calculate weather based on sprint issue status.
    
    Returns: 'sunny' | 'cloudy' | 'storm'
    - sunny: >= 70% done or on track
    - cloudy: 40-70% done, some blockers
    - storm: < 40% done or many blockers
    """
    if not issues:
        return "sunny"  # No issues = calm
    
    total = len(issues)
    done = 0
    blocked = 0
    
    for issue in issues:
        status = issue.get('fields', {}).get('status', {}).get('name', '')
        if status.lower() == 'done':
            done += 1
        elif status.lower() in [s.lower() for s in BLOCKER_STATUSES]:
            blocked += 1
    
    done_ratio = done / total
    blocked_ratio = blocked / total
    
    # Storm if many blockers or very behind
    if blocked_ratio > 0.2 or done_ratio < 0.3:
        return "storm"
    # Cloudy if moderate blockers or somewhat behind
    elif blocked_ratio > 0.1 or done_ratio < 0.6:
        return "cloudy"
    # Sunny if on track
    else:
        return "sunny"


def calculate_sprint_progress(sprint: Optional[dict[str, Any]]) -> float:
    """Calculate sprint progress as percentage based on dates.
    
    Returns: float 0.0 to 1.0 (maps to dawn → sunset in UE5)
    """
    if not sprint:
        return 0.5  # Default to midday
    
    start_str = sprint.get('startDate')
    end_str = sprint.get('endDate')
    
    if not start_str or not end_str:
        return 0.5
    
    try:
        # Parse ISO format dates
        start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        now = datetime.now(start.tzinfo)
        
        total_duration = (end - start).total_seconds()
        elapsed = (now - start).total_seconds()
        
        if total_duration <= 0:
            return 0.5
        
        progress = max(0.0, min(1.0, elapsed / total_duration))
        return progress
    except Exception as e:
        logger.warning(f"Error calculating sprint progress: {e}")
        return 0.5


@retry_on_failure()
def trigger_ue5_weather(weather: str) -> dict[str, Any]:
    """Send weather state to UE5."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_WEATHER_FUNCTION,
        "parameters": {
            "Weather_State": weather  # "sunny", "cloudy", or "storm"
        },
        "generateTransaction": True
    }
    
    logger.info(f"🌤️ Setting UE5 weather: {weather}")
    response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


@retry_on_failure()
def trigger_ue5_time(progress: float) -> dict[str, Any]:
    """Send time-of-day to UE5 based on sprint progress."""
    payload = {
        "objectPath": UE5_ACTOR_PATH,
        "functionName": UE5_TIME_FUNCTION,
        "parameters": {
            "Time_Progress": progress  # 0.0 (dawn) to 1.0 (dusk)
        },
        "generateTransaction": True
    }
    
    logger.info(f"🌅 Setting UE5 time: {progress:.2%}")
    response = requests.put(UE5_REMOTE_CONTROL_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


# ============================================================================
# Jira Integration
# ============================================================================
def get_epic_key(issue: dict[str, Any]) -> Optional[str]:
    """Extract Epic key from Jira issue.
    
    Jira Cloud uses 'parent' field for Epic links in next-gen projects,
    or custom fields in classic projects.
    """
    fields = issue.get('fields', {})
    
    # Next-gen projects: Check parent field
    parent = fields.get('parent', {})
    parent_type = parent.get('fields', {}).get('issuetype', {}).get('name', '')
    if parent_type == 'Epic':
        return parent.get('key')
    
    # Classic projects: Check epic link custom field (commonly customfield_10014)
    epic_link = fields.get('customfield_10014')  # May vary by instance
    if epic_link:
        return epic_link
    
    return None


def get_growth_params(issue: dict[str, Any]) -> tuple[str, float, dict[str, float], Optional[str]]:
    """Extract all growth parameters from Jira issue data.
    
    Returns:
        tuple: (growth_type, growth_modifier, color, epic_key)
    """
    fields = issue.get('fields', {})
    
    # Get issue type
    issue_type = fields.get('issuetype', {}).get('name', 'Task')
    growth_type = ISSUE_TYPE_GROWTH.get(issue_type, 'leaf')
    
    # Get priority
    priority = fields.get('priority', {}).get('name', 'Medium')
    growth_modifier = PRIORITY_MODIFIER.get(priority, 1.0)
    color = PRIORITY_COLORS.get(priority, PRIORITY_COLORS['Medium'])
    
    # Get Epic key
    epic_key = get_epic_key(issue)
    
    return growth_type, growth_modifier, color, epic_key


def construct_sprint_prompt(issues: list[dict[str, Any]]) -> str:
    """Analyze sprint issues to create a World Labs prompt."""
    if not issues:
        return "A peaceful serene garden, sunny day"
        
    bug_count = sum(1 for i in issues if i.get('fields', {}).get('issuetype', {}).get('name') == 'Bug')
    story_count = len(issues) - bug_count
    
    # Base theme
    prompt = "A 3D garden environment"
    
    if bug_count > story_count:
        prompt += ", dark atmospheric, swampy, mysterious fog, overgrown ruins"
    else:
        prompt += ", futuristic sci-fi city park, neon lights, clean structures, sunny"
        
    return prompt


def sync_initial_state() -> None:
    """Queries Jira for all 'Done' issues and triggers growth in UE5."""
    logger.info("Starting initial state synchronization...")
    
    if not all([JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
        logger.warning("Missing Jira configuration. Skipping synchronization.")
        return

    jql = f"project = '{JIRA_PROJECT_KEY}' AND status = 'Done'"
    url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
    auth = get_jira_auth()
    
    try:
        response = requests.get(
            url, 
            params={"jql": jql, "maxResults": 100, "fields": "key,issuetype,priority,parent,customfield_10014"}, 
            auth=auth,
            timeout=30
        )
        response.raise_for_status()
        issues = response.json().get("issues", [])
        
        logger.info(f"Found {len(issues)} issues in 'Done' status")
        
        for issue in issues:
            issue_key = issue.get("key")
            growth_type, growth_modifier, color, epic_key = get_growth_params(issue)
            
            logger.info(f"Syncing {issue_key} (type={growth_type}, modifier={growth_modifier}, epic={epic_key})")
            try:
                trigger_ue5_growth(issue_key, growth_type, growth_modifier, color, epic_key)
            except Exception as e:
                logger.error(f"Failed to sync {issue_key}: {e}")
            
        logger.info("Initial state synchronization complete")
    except Exception as e:
        logger.error(f"Error during Jira synchronization: {e}")


def was_reopened(data: dict[str, Any]) -> bool:
    """Check if the issue was reopened (status changed FROM Done)."""
    changelog = data.get('changelog', {})
    for item in changelog.get('items', []):
        if item.get('field') == 'status' and item.get('fromString') == 'Done':
            return True
    return False


def was_blocked(data: dict[str, Any]) -> bool:
    """Check if the issue was just blocked (status changed TO a blocker status)."""
    changelog = data.get('changelog', {})
    for item in changelog.get('items', []):
        if item.get('field') == 'status' and item.get('toString') in BLOCKER_STATUSES:
            return True
    return False


def was_unblocked(data: dict[str, Any]) -> bool:
    """Check if the issue was unblocked (status changed FROM a blocker status)."""
    changelog = data.get('changelog', {})
    for item in changelog.get('items', []):
        if item.get('field') == 'status' and item.get('fromString') in BLOCKER_STATUSES:
            return True
    return False


# ============================================================================
# Team Members (Phase 4: Social Layer)
# ============================================================================
@retry_on_failure()
def get_team_members() -> list[dict[str, Any]]:
    """Get team members from Jira project with their assigned tasks.
    
    Returns list of team members with:
    - account_id, display_name, avatar_url
    - active_tasks (list of issue keys)
    - completed_today (count)
    - position (x, y, z for UE5 avatar spawning)
    """
    if not all([JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
        logger.warning("Missing Jira configuration for team members")
        return []
    
    auth = get_jira_auth()
    
    # Get all active issues with assignees
    jql = f"project = '{JIRA_PROJECT_KEY}' AND assignee IS NOT EMPTY AND status != Done"
    url = f"https://{JIRA_DOMAIN}/rest/api/3/search"
    
    response = requests.get(
        url,
        params={"jql": jql, "maxResults": 100, "fields": "assignee,status,key"},
        auth=auth,
        timeout=30
    )
    response.raise_for_status()
    issues = response.json().get("issues", [])
    
    # Also get issues completed today
    today = datetime.now().strftime("%Y-%m-%d")
    jql_done = f"project = '{JIRA_PROJECT_KEY}' AND status = Done AND statusCategoryChangedDate >= '{today}'"
    
    response_done = requests.get(
        url,
        params={"jql": jql_done, "maxResults": 100, "fields": "assignee,key"},
        auth=auth,
        timeout=30
    )
    response_done.raise_for_status()
    done_issues = response_done.json().get("issues", [])
    
    # Group by assignee
    members_dict: dict[str, dict[str, Any]] = {}
    
    for issue in issues:
        assignee = issue.get("fields", {}).get("assignee")
        if not assignee:
            continue
        
        account_id = assignee.get("accountId")
        if account_id not in members_dict:
            members_dict[account_id] = {
                "account_id": account_id,
                "display_name": assignee.get("displayName", "Unknown"),
                "avatar_url": assignee.get("avatarUrls", {}).get("48x48", ""),
                "active_tasks": [],
                "completed_today": 0
            }
        
        members_dict[account_id]["active_tasks"].append(issue.get("key"))
    
    # Count completed today
    for issue in done_issues:
        assignee = issue.get("fields", {}).get("assignee")
        if not assignee:
            continue
        
        account_id = assignee.get("accountId")
        if account_id in members_dict:
            members_dict[account_id]["completed_today"] += 1
        else:
            # Member only has completed tasks
            members_dict[account_id] = {
                "account_id": account_id,
                "display_name": assignee.get("displayName", "Unknown"),
                "avatar_url": assignee.get("avatarUrls", {}).get("48x48", ""),
                "active_tasks": [],
                "completed_today": 1
            }
    
    # Calculate positions (spread members in a circle around origin)
    members = list(members_dict.values())
    for i, member in enumerate(members):
        angle = (2 * 3.14159 * i) / max(len(members), 1)
        radius = 500  # 500 units from center
        member["position"] = {
            "x": round(radius * (1 if i % 2 == 0 else -1) * ((i + 1) / 2) * 200, 1),
            "y": round(radius * (0.5 if i % 3 == 0 else 0), 1),
            "z": 0
        }
    
    logger.info(f"👥 Found {len(members)} team members with active tasks")
    return members


# ============================================================================
# Flask Routes
# ============================================================================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "BloomPath",
        "jira_configured": all([JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN]),
        "ue5_endpoint": UE5_REMOTE_CONTROL_URL
    }), 200


@app.route('/webhook', methods=['POST'])
def jira_webhook():
    """Handle Jira webhook events."""
    data = request.json
    if not data:
        logger.warning("Received webhook with no JSON payload")
        return jsonify({"status": "error", "message": "No JSON payload"}), 400

    # Optional: Verify webhook secret
    if WEBHOOK_SECRET:
        received_secret = request.headers.get('X-Atlassian-Webhook-Identifier')
        # Note: Jira Cloud uses different header, adjust as needed
    
    # Extract event data
    event_type = data.get('issue_event_type_name', data.get('webhookEvent', 'unknown'))
    issue = data.get('issue', {})
    issue_key = issue.get('key')
    fields = issue.get('fields', {})
    status = fields.get('status', {}).get('name')
    
    logger.info(f"Webhook received: [{event_type}] {issue_key} → {status}")
    
    # Get all growth parameters
    growth_type, growth_modifier, color, epic_key = get_growth_params(issue)

    # Check if issue was blocked (add thorns)
    if was_blocked(data):
        logger.info(f"Issue {issue_key} was blocked, triggering thorns")
        push_audio_event("blocker_added", issue_key=issue_key)
        try:
            trigger_ue5_thorns(issue_key, epic_key)
            return jsonify({"status": "thorns_triggered", "issue": issue_key}), 200
        except Exception as e:
            logger.error(f"Failed to trigger thorns for {issue_key}: {e}")
            return jsonify({"status": "ue5_error", "issue": issue_key, "error": str(e)}), 500
    
    # Check if issue was unblocked (remove thorns)
    if was_unblocked(data):
        logger.info(f"Issue {issue_key} was unblocked, removing thorns")
        push_audio_event("blocker_resolved", issue_key=issue_key)
        try:
            trigger_ue5_remove_thorns(issue_key)
        except Exception as e:
            logger.warning(f"Failed to remove thorns for {issue_key}: {e}")
        # Continue processing - might also be going to Done

    # Check if issue was reopened (status changed FROM Done)
    if was_reopened(data):
        logger.info(f"Issue {issue_key} was reopened, triggering shrink")
        push_audio_event("task_reopened", issue_key=issue_key)
        try:
            trigger_ue5_shrink(issue_key)
            return jsonify({"status": "shrink_triggered", "issue": issue_key}), 200
        except Exception as e:
            logger.error(f"Failed to trigger shrink for {issue_key}: {e}")
            return jsonify({"status": "ue5_error", "issue": issue_key, "error": str(e)}), 500

    # Trigger growth when status changes to 'Done'
    if status == "Done":
        # Get assignee name for audio event
        assignee = fields.get('assignee', {})
        assignee_name = assignee.get('displayName', 'Someone') if assignee else 'Someone'
        
        logger.info(f"Issue {issue_key} completed (type={growth_type}, modifier={growth_modifier}, epic={epic_key})")
        push_audio_event("task_completed", issue_key=issue_key, user=assignee_name)
        
        try:
            result = trigger_ue5_growth(issue_key, growth_type, growth_modifier, color, epic_key)
            logger.info(f"Successfully triggered growth for {issue_key}")
            return jsonify({"status": "growth_triggered", "issue": issue_key, "epic": epic_key}), 200
        except Exception as e:
            logger.error(f"Failed to trigger growth for {issue_key}: {e}")
            return jsonify({"status": "ue5_error", "issue": issue_key, "error": str(e)}), 500

    return jsonify({"status": "received", "issue": issue_key}), 200


@app.route('/complete_task', methods=['POST'])
def complete_task() -> tuple[Response, int]:
    """Handle task completion from UE5 (watering a flower).
    
    This endpoint enables bidirectional flow:
    Player waters flower in UE5 → POST here → Jira issue transitions to Done
    """
    data = request.json
    if not data:
        logger.warning("Received /complete_task with no JSON payload")
        return jsonify({"status": "error", "message": "No JSON payload"}), 400
    
    issue_key = data.get('issue_key')
    if not issue_key:
        logger.warning("Received /complete_task without issue_key")
        return jsonify({"status": "error", "message": "Missing issue_key"}), 400
    
    # Validate issue key format (e.g., KAN-123)
    if not validate_issue_key(issue_key):
        logger.warning(f"Received /complete_task with invalid issue_key: {issue_key}")
        return jsonify({"status": "error", "message": f"Invalid issue_key format: {issue_key}"}), 400
    
    logger.info(f"🌊 Watering received from UE5 for {issue_key}")
    
    try:
        result = transition_issue_to_done(issue_key)
        return jsonify(result), 200
    except ValueError as e:
        logger.error(f"Transition error for {issue_key}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to transition {issue_key}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/sprint_status', methods=['GET'])
def sprint_status():
    """Return current sprint health for UE5 environmental dynamics.
    
    UE5 polls this endpoint to update weather and time-of-day.
    """
    try:
        sprint = get_active_sprint()
        
        if not sprint:
            return jsonify({
                "status": "no_sprint",
                "weather": "sunny",
                "progress": 0.5,
                "message": "No active sprint found"
            }), 200
        
        issues = get_sprint_issues(sprint['id'])
        weather = calculate_sprint_health(issues)
        progress = calculate_sprint_progress(sprint)
        
        return jsonify({
            "status": "ok",
            "sprint_name": sprint.get('name'),
            "weather": weather,
            "progress": progress,
            "issues_total": len(issues),
            "issues_done": sum(1 for i in issues if i.get('fields', {}).get('status', {}).get('name') == 'Done')
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sprint status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/generate_sprint_world', methods=['POST'])
def generate_sprint_world():
    """Trigger World Labs generation based on current sprint."""
    sprint = get_active_sprint()
    if not sprint:
        return jsonify({"status": "error", "message": "No active sprint"}), 404
        
    issues = get_sprint_issues(sprint['id'])
    prompt = construct_sprint_prompt(issues)
    
    # Generate
    client = WorldLabsClient()
    filename = f"sprint_{sprint['id']}_world.gltf"
    output_path = os.path.join(os.getcwd(), "content", "generated", filename)
    
    # Run in background (simplification for now - blocking call)
    # Ideally should be a true background task
    result_path = client.generate_world(prompt, output_path)
    
    if result_path:
        global _latest_world_path
        _latest_world_path = result_path
        logger.info(f"🌍 World generated: {result_path}")
        return jsonify({
            "status": "success", 
            "prompt": prompt,
            "file": result_path
        }), 200
    else:
        return jsonify({
            "status": "failed",
            "prompt": prompt
        }), 500


# Global to track latest generated world path
_latest_world_path: Optional[str] = None


@app.route('/latest_world', methods=['GET'])
def latest_world() -> tuple[Response, int]:
    """Return the path to the most recently generated world file.
    
    UE5 polls this endpoint to check for new world imports.
    """
    global _latest_world_path
    
    if _latest_world_path and os.path.exists(_latest_world_path):
        return jsonify({
            "status": "ok",
            "file_path": _latest_world_path
        }), 200
    else:
        return jsonify({
            "status": "no_world",
            "file_path": ""
        }), 200


# Global to track latest manifest path
_latest_manifest_path: Optional[str] = None


@app.route('/analyze_world', methods=['POST'])
def analyze_world_endpoint() -> tuple[Response, int]:
    """Analyze a World Labs render using Gemini vision.
    
    Request body: {"image_path": "/path/to/thumbnail.png"}
    Or uses latest world's thumbnail if no path provided.
    """
    global _latest_manifest_path
    
    data = request.json or {}
    image_path = data.get('image_path')
    
    # If no image provided, try to use latest world thumbnail
    if not image_path:
        # World Labs returns thumbnail_url in assets
        return jsonify({
            "status": "error",
            "message": "image_path required"
        }), 400
    
    # Run analysis
    manifest = analyze_world(image_path)
    
    if not manifest:
        return jsonify({
            "status": "failed",
            "message": "Analysis failed"
        }), 500
    
    # Save manifest alongside the image
    manifest_path = image_path.rsplit('.', 1)[0] + '_manifest.json'
    save_manifest(manifest, manifest_path)
    _latest_manifest_path = manifest_path
    
    return jsonify({
        "status": "success",
        "manifest_path": manifest_path,
        "object_count": len(manifest.get('objects', [])),
        "scene_description": manifest.get('scene_description', '')
    }), 200


@app.route('/latest_manifest', methods=['GET'])
def latest_manifest() -> tuple[Response, int]:
    """Return the latest world manifest for UE5."""
    global _latest_manifest_path
    
    if _latest_manifest_path and os.path.exists(_latest_manifest_path):
        with open(_latest_manifest_path, 'r') as f:
            manifest = json.load(f)
        return jsonify({
            "status": "ok",
            "manifest": manifest
        }), 200
    else:
        return jsonify({
            "status": "no_manifest",
            "manifest": None
        }), 200


@app.route('/validate_world', methods=['POST'])
def validate_world_endpoint() -> tuple[Response, int]:
    """Run validation on the latest manifest and optionally report to Jira.
    
    Request body: {"jira_issue_key": "BLP-123"} (optional)
    """
    global _latest_manifest_path
    
    if not _latest_manifest_path or not os.path.exists(_latest_manifest_path):
        return jsonify({
            "status": "error",
            "message": "No manifest available - run /analyze_world first"
        }), 404
    
    data = request.json or {}
    jira_key = data.get('jira_issue_key')
    
    result = run_validation(_latest_manifest_path, jira_key)
    
    return jsonify(result), 200


@app.route('/team_members', methods=['GET'])
def team_members() -> tuple[Response, int]:
    """Return team members with their assigned tasks for avatar spawning.
    
    UE5 polls this endpoint to spawn/update gardener NPCs.
    """
    try:
        members = get_team_members()
        return jsonify({
            "status": "ok",
            "count": len(members),
            "members": members
        }), 200
    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "members": []
        }), 500


@app.route('/audio_events', methods=['GET'])
def audio_events() -> tuple[Response, int]:
    """Return queued audio events for UE5 to play.
    
    UE5 polls this endpoint for sound triggers, then events are cleared.
    """
    global audio_event_queue
    
    # Copy and clear the queue
    events = audio_event_queue.copy()
    audio_event_queue = []
    
    if events:
        logger.info(f"🔊 Returning {len(events)} audio events to UE5")
    
    return jsonify({
        "status": "ok",
        "count": len(events),
        "events": events
    }), 200


# ============================================================================
# Main Entry Point
# ============================================================================
if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🌱 BloomPath Middleware Starting")
    logger.info("=" * 50)
    logger.info(f"Jira Project: {JIRA_PROJECT_KEY}")
    logger.info(f"UE5 Endpoint: {UE5_REMOTE_CONTROL_URL}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    
    # Run initial sync
    sync_initial_state()
    
    logger.info("Starting webhook server on port 5000...")
    app.run(port=5000, debug=(LOG_LEVEL == "DEBUG"))
