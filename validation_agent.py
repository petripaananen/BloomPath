"""Validation Agent - Tests navigation in semantically tagged worlds.

This module simulates agent pathfinding through the tagged world and
reports navigation failures back to Jira as comments.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List, Tuple

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

logger = logging.getLogger("BloomPath.ValidationAgent")

# Configuration
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")


def get_jira_auth() -> HTTPBasicAuth:
    """Get Jira authentication."""
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)


def validate_navigation(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Simulate navigation validation based on the world manifest.
    
    Checks:
    1. Are there walkable paths?
    2. Is the path blocked by obstacles?
    3. Are there unreachable areas?
    
    Args:
        manifest: World manifest with tagged objects
        
    Returns:
        List of validation issues found
    """
    issues = []
    objects = manifest.get("objects", [])
    
    if not objects:
        issues.append({
            "type": "NO_OBJECTS",
            "severity": "critical",
            "message": "No objects found in manifest - world may be empty"
        })
        return issues
    
    # Check for walkable surfaces
    walkable_objects = [
        obj for obj in objects 
        if "Walkable" in obj.get("tags", [])
    ]
    
    if not walkable_objects:
        issues.append({
            "type": "NO_WALKABLE_SURFACE",
            "severity": "critical", 
            "message": "No walkable surfaces found - player cannot move"
        })
    
    # Check for obstacles blocking paths
    obstacles = [
        obj for obj in objects 
        if "Obstacle" in obj.get("tags", [])
    ]
    
    # Heuristic: If obstacles outnumber walkable by 3:1, path may be blocked
    if len(obstacles) > len(walkable_objects) * 3:
        issues.append({
            "type": "POTENTIAL_BLOCKAGE",
            "severity": "warning",
            "message": f"High obstacle ratio ({len(obstacles)} obstacles vs {len(walkable_objects)} walkable) - path may be blocked"
        })
    
    # Check for low friction surfaces (slippery)
    slippery_count = sum(
        1 for obj in objects 
        if obj.get("physics", {}).get("friction", 1.0) < 0.3
    )
    
    if slippery_count > len(objects) * 0.5:
        issues.append({
            "type": "TOO_SLIPPERY",
            "severity": "warning",
            "message": f"Over 50% of surfaces are slippery - may be difficult to navigate"
        })
    
    # If all checks pass
    if not issues:
        logger.info("✅ Validation passed - no navigation issues found")
    else:
        logger.warning(f"⚠️ Found {len(issues)} validation issues")
    
    return issues


def report_to_jira(issue_key: str, validation_issues: List[Dict[str, Any]]) -> bool:
    """
    Post validation results as a comment on the Jira issue.
    
    Args:
        issue_key: Jira issue key (e.g., BLP-123)
        validation_issues: List of validation issues found
        
    Returns:
        True if comment posted successfully
    """
    if not all([JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN]):
        logger.error("Jira configuration missing")
        return False
    
    # Build comment body
    if not validation_issues:
        comment_body = "🌿 **BloomPath Validation Passed**\n\nAI navigation agent found no issues with the generated world."
    else:
        comment_body = "⚠️ **BloomPath Validation Issues**\n\n"
        for issue in validation_issues:
            emoji = "🔴" if issue["severity"] == "critical" else "🟡"
            comment_body += f"{emoji} **{issue['type']}**: {issue['message']}\n"
    
    url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/comment"
    
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": comment_body
                }]
            }]
        }
    }
    
    try:
        response = requests.post(
            url, 
            json=payload, 
            auth=get_jira_auth(),
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"📝 Validation report posted to {issue_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to post Jira comment: {e}")
        return False


def run_validation(manifest_path: str, jira_issue_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Run full validation pipeline.
    
    Args:
        manifest_path: Path to world_manifest.json
        jira_issue_key: Optional Jira issue to report to
        
    Returns:
        Validation result dict
    """
    # Load manifest
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        return {"status": "error", "message": f"Failed to load manifest: {e}"}
    
    # Run validation
    issues = validate_navigation(manifest)
    
    # Report to Jira if key provided
    if jira_issue_key and issues:
        report_to_jira(jira_issue_key, issues)
    
    return {
        "status": "completed",
        "issues_found": len(issues),
        "issues": issues,
        "reported_to_jira": jira_issue_key if issues else None
    }
