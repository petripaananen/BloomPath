"""
API routes for BloomPath middleware.

These endpoints are consumed by UE5 and other clients to query
project state and trigger actions.
"""

import logging
from flask import Blueprint, request, jsonify

from middleware.providers.jira import JiraProvider
from middleware.providers.linear import LinearProvider
from middleware.models.ticket import IssueStatus

logger = logging.getLogger("BloomPath.Routes.API")

api_bp = Blueprint('api', __name__)


def _get_provider(provider_name: str = None):
    """Get the appropriate provider based on name or config."""
    if provider_name == 'linear':
        return LinearProvider()
    return JiraProvider()  # Default to Jira


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    jira = JiraProvider()
    linear = LinearProvider()
    
    return jsonify({
        "status": "healthy",
        "service": "BloomPath",
        "providers": {
            "jira": {
                "configured": bool(jira.domain and jira.email and jira.api_token)
            },
            "linear": {
                "configured": bool(linear.api_key)
            }
        }
    }), 200


@api_bp.route('/sprint_status', methods=['GET'])
def sprint_status():
    """
    Return current sprint/cycle health for UE5 environmental dynamics.
    
    Query params:
    - provider: 'jira' or 'linear' (default: jira)
    """
    provider_name = request.args.get('provider', 'jira')
    provider = _get_provider(provider_name)
    
    try:
        sprint = provider.get_active_sprint_or_cycle()
        
        if not sprint:
            return jsonify({
                "status": "no_sprint",
                "provider": provider.name,
                "weather": "sunny",
                "progress": 0.5,
                "message": f"No active {'cycle' if provider.name == 'linear' else 'sprint'} found"
            }), 200
        
        sprint_id = sprint.get('id')
        issues = provider.get_sprint_issues(sprint_id)
        
        # Calculate health metrics
        total = len(issues)
        done = sum(1 for t in issues if t.status == IssueStatus.DONE)
        blocked = sum(1 for t in issues if t.is_blocked)
        
        done_ratio = done / total if total > 0 else 0
        blocked_ratio = blocked / total if total > 0 else 0
        
        # Determine weather based on health
        if blocked_ratio > 0.2 or done_ratio < 0.3:
            weather = "storm"
        elif blocked_ratio > 0.1 or done_ratio < 0.6:
            weather = "cloudy"
        else:
            weather = "sunny"
        
        # Calculate progress (for time-of-day)
        progress = sprint.get('progress', done_ratio)
        
        return jsonify({
            "status": "ok",
            "provider": provider.name,
            "sprint_name": sprint.get('name'),
            "weather": weather,
            "progress": progress,
            "issues_total": total,
            "issues_done": done,
            "issues_blocked": blocked
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sprint status: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/complete_task', methods=['POST'])
def complete_task():
    """
    Handle task completion from UE5 (watering a flower).
    
    This enables bidirectional flow:
    Player waters flower in UE5 → POST here → Issue transitions to Done
    
    Request body:
    - issue_id: The issue identifier (e.g., "KAN-123" or "LIN-abc")
    - provider: Optional, 'jira' or 'linear' (auto-detected from ID format)
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload"}), 400
    
    issue_id = data.get('issue_id') or data.get('issue_key')
    if not issue_id:
        return jsonify({"status": "error", "message": "Missing issue_id"}), 400
    
    # Auto-detect provider from issue ID format
    provider_name = data.get('provider')
    if not provider_name:
        # Jira IDs are like "KAN-123", Linear are like "LIN-abc" or UUIDs
        if '-' in issue_id and issue_id.split('-')[0].isupper():
            provider_name = 'jira'
        else:
            provider_name = 'linear'
    
    provider = _get_provider(provider_name)
    
    logger.info(f"🌊 Watering received for {issue_id} ({provider.name})")
    
    try:
        success = provider.transition_to_done(issue_id)
        if success:
            return jsonify({
                "status": "success",
                "issue": issue_id,
                "provider": provider.name
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to transition {issue_id}"
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to complete task {issue_id}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/team_members', methods=['GET'])
def team_members():
    """
    Get team members with their active tasks.
    
    Query params:
    - provider: 'jira' or 'linear' (default: jira)
    """
    provider_name = request.args.get('provider', 'jira')
    provider = _get_provider(provider_name)
    
    try:
        sprint = provider.get_active_sprint_or_cycle()
        if not sprint:
            return jsonify({"status": "ok", "members": []}), 200
        
        issues = provider.get_sprint_issues(sprint.get('id'))
        
        # Group by assignee
        members_dict = {}
        for ticket in issues:
            if not ticket.assignee_id:
                continue
            
            if ticket.assignee_id not in members_dict:
                members_dict[ticket.assignee_id] = {
                    "account_id": ticket.assignee_id,
                    "display_name": ticket.assignee_name,
                    "avatar_url": ticket.assignee_avatar,
                    "active_tasks": [],
                    "completed": 0
                }
            
            if ticket.status == IssueStatus.DONE:
                members_dict[ticket.assignee_id]["completed"] += 1
            else:
                members_dict[ticket.assignee_id]["active_tasks"].append(ticket.id)
        
        return jsonify({
            "status": "ok",
            "provider": provider.name,
            "members": list(members_dict.values())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting team members: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/dependencies/<issue_id>', methods=['GET'])
def get_dependencies(issue_id: str):
    """
    Get dependencies for a specific issue.
    
    Used by UE5 to draw vines between plants.
    """
    provider_name = request.args.get('provider', 'jira')
    provider = _get_provider(provider_name)
    
    try:
        deps = provider.get_issue_dependencies(issue_id)
        return jsonify({
            "status": "ok",
            "issue_id": issue_id,
            "provider": provider.name,
            "dependencies": deps
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dependencies for {issue_id}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
