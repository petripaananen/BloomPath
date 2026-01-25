"""
LinearProvider: Adapter for Linear.

Maps Linear's data model (Issues with labels, priorities, states) and
relations (blockedBy/blocking) to the UnifiedTicket format.
"""

import os
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests

from middleware.providers.base import IssueProvider
from middleware.models.ticket import (
    UnifiedTicket, IssueType, IssueStatus, Relation, RelationType
)

logger = logging.getLogger("BloomPath.Provider.Linear")


# Mapping from Linear labels to unified issue types
# Linear uses labels to categorize issues, not built-in types
LINEAR_LABEL_TYPE_MAP: Dict[str, IssueType] = {
    "epic": IssueType.EPIC,
    "feature": IssueType.FEATURE,
    "bug": IssueType.BUG,
    "task": IssueType.TASK,
    "chore": IssueType.CHORE,
    "improvement": IssueType.FEATURE,
    "refactor": IssueType.CHORE,
}

# Mapping from Linear priority (0-4) to unified priority (1-5)
# Linear: 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
LINEAR_PRIORITY_MAP: Dict[int, int] = {
    0: 3,  # No priority -> Medium
    1: 5,  # Urgent -> Highest
    2: 4,  # High -> High
    3: 3,  # Medium -> Medium
    4: 2,  # Low -> Low
}

# Mapping from Linear state types to unified status
LINEAR_STATE_MAP: Dict[str, IssueStatus] = {
    "backlog": IssueStatus.TODO,
    "unstarted": IssueStatus.TODO,
    "started": IssueStatus.IN_PROGRESS,
    "completed": IssueStatus.DONE,
    "canceled": IssueStatus.DONE,
}


class LinearProvider(IssueProvider):
    """Linear implementation of IssueProvider."""
    
    GRAPHQL_URL = "https://api.linear.app/graphql"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        team_id: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        self.webhook_secret = webhook_secret or os.getenv("LINEAR_WEBHOOK_SECRET")
        self.team_id = team_id or os.getenv("LINEAR_TEAM_ID")
        
        if not self.api_key:
            logger.warning("Linear API key not configured")
    
    @property
    def name(self) -> str:
        return "linear"
    
    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query against Linear API."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.GRAPHQL_URL,
                json=payload,
                headers=self._headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                return {}
            
            return result.get("data", {})
        except requests.RequestException as e:
            logger.error(f"Linear API request failed: {e}")
            return {}
    
    def _normalize_type(self, labels: List[Dict]) -> IssueType:
        """Determine issue type from Linear labels."""
        for label in labels:
            label_name = label.get("name", "").lower()
            if label_name in LINEAR_LABEL_TYPE_MAP:
                return LINEAR_LABEL_TYPE_MAP[label_name]
        return IssueType.FEATURE  # Default for Linear issues
    
    def _normalize_priority(self, linear_priority: int) -> int:
        """Convert Linear priority (0-4) to unified priority (1-5)."""
        return LINEAR_PRIORITY_MAP.get(linear_priority, 3)
    
    def _normalize_status(self, state: Dict) -> IssueStatus:
        """Convert Linear state to unified status."""
        state_type = state.get("type", "").lower()
        return LINEAR_STATE_MAP.get(state_type, IssueStatus.TODO)
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Linear datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _extract_relations(self, issue_data: Dict) -> List[Relation]:
        """Extract relations from Linear issue data."""
        relations: List[Relation] = []
        
        # Blocked by relations
        blocked_by = issue_data.get("blockedBy", {}).get("nodes", [])
        for blocker in blocked_by:
            relations.append(Relation(
                target_id=blocker.get("identifier", blocker.get("id")),
                relation_type=RelationType.BLOCKED_BY,
                target_provider="linear"
            ))
        
        # Blocking relations
        blocking = issue_data.get("blocking", {}).get("nodes", [])
        for blocked in blocking:
            relations.append(Relation(
                target_id=blocked.get("identifier", blocked.get("id")),
                relation_type=RelationType.BLOCKS,
                target_provider="linear"
            ))
        
        # Related issues
        related = issue_data.get("relations", {}).get("nodes", [])
        for rel in related:
            related_issue = rel.get("relatedIssue", {})
            relations.append(Relation(
                target_id=related_issue.get("identifier", related_issue.get("id")),
                relation_type=RelationType.RELATES_TO,
                target_provider="linear"
            ))
        
        # Children (sub-issues)
        children = issue_data.get("children", {}).get("nodes", [])
        for child in children:
            relations.append(Relation(
                target_id=child.get("identifier", child.get("id")),
                relation_type=RelationType.CHILD,
                target_provider="linear"
            ))
        
        return relations
    
    def _issue_to_ticket(self, issue: Dict[str, Any]) -> UnifiedTicket:
        """Convert a Linear issue to UnifiedTicket."""
        labels = issue.get("labels", {}).get("nodes", [])
        state = issue.get("state", {})
        assignee = issue.get("assignee") or {}
        cycle = issue.get("cycle") or {}
        parent = issue.get("parent") or {}
        project = issue.get("project") or {}
        
        return UnifiedTicket(
            id=issue.get("identifier", issue.get("id", "")),
            provider=self.name,
            title=issue.get("title", ""),
            description=issue.get("description"),
            status=self._normalize_status(state),
            issue_type=self._normalize_type(labels),
            priority=self._normalize_priority(issue.get("priority", 0)),
            assignee_id=assignee.get("id"),
            assignee_name=assignee.get("name"),
            assignee_avatar=assignee.get("avatarUrl"),
            parent_id=parent.get("identifier") or project.get("id"),
            relations=self._extract_relations(issue),
            labels=[l.get("name", "") for l in labels],
            sprint_id=cycle.get("id"),
            sprint_name=cycle.get("name"),
            created_at=self._parse_datetime(issue.get("createdAt")),
            updated_at=self._parse_datetime(issue.get("updatedAt")),
            raw_data=issue
        )
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Linear webhook signature (HMAC-SHA256)."""
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping verification")
            return True
        
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    def parse_webhook(self, payload: Dict[str, Any]) -> UnifiedTicket:
        """Parse Linear webhook payload into UnifiedTicket."""
        # Linear webhooks have different structures based on action
        data = payload.get("data", {})
        
        # The issue data may be nested under different keys
        issue_data = data
        if "issue" in data:
            issue_data = data["issue"]
        
        return self._issue_to_ticket(issue_data)
    
    def get_issue(self, issue_id: str) -> Optional[UnifiedTicket]:
        """Fetch a single issue from Linear by identifier."""
        query = """
        query GetIssue($identifier: String!) {
            issue(identifier: $identifier) {
                id
                identifier
                title
                description
                priority
                state { id name type }
                assignee { id name avatarUrl }
                parent { id identifier }
                project { id name }
                cycle { id name }
                labels { nodes { id name } }
                blockedBy { nodes { id identifier } }
                blocking { nodes { id identifier } }
                relations { nodes { relatedIssue { id identifier } } }
                children { nodes { id identifier } }
                createdAt
                updatedAt
            }
        }
        """
        
        result = self._execute_query(query, {"identifier": issue_id})
        issue = result.get("issue")
        
        if not issue:
            logger.warning(f"Linear issue {issue_id} not found")
            return None
        
        return self._issue_to_ticket(issue)
    
    def get_active_sprint_or_cycle(self) -> Optional[Dict[str, Any]]:
        """Get the currently active cycle from Linear."""
        query = """
        query GetActiveCycle($teamId: String!) {
            team(id: $teamId) {
                activeCycle {
                    id
                    name
                    startsAt
                    endsAt
                    progress
                }
            }
        }
        """
        
        if not self.team_id:
            logger.warning("LINEAR_TEAM_ID not configured")
            return None
        
        result = self._execute_query(query, {"teamId": self.team_id})
        return result.get("team", {}).get("activeCycle")
    
    def get_sprint_issues(self, sprint_id: str) -> List[UnifiedTicket]:
        """Get all issues in a cycle."""
        query = """
        query GetCycleIssues($cycleId: String!) {
            cycle(id: $cycleId) {
                issues {
                    nodes {
                        id
                        identifier
                        title
                        description
                        priority
                        state { id name type }
                        assignee { id name avatarUrl }
                        parent { id identifier }
                        project { id name }
                        labels { nodes { id name } }
                        blockedBy { nodes { id identifier } }
                        blocking { nodes { id identifier } }
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
        
        result = self._execute_query(query, {"cycleId": sprint_id})
        issues = result.get("cycle", {}).get("issues", {}).get("nodes", [])
        return [self._issue_to_ticket(issue) for issue in issues]
    
    def transition_to_done(self, issue_id: str) -> bool:
        """Transition a Linear issue to completed state."""
        # First, get the completed state ID for the team
        state_query = """
        query GetCompletedState($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                    }
                }
            }
        }
        """
        
        if not self.team_id:
            logger.error("LINEAR_TEAM_ID required for transitions")
            return False
        
        result = self._execute_query(state_query, {"teamId": self.team_id})
        states = result.get("team", {}).get("states", {}).get("nodes", [])
        
        # Find completed state
        done_state_id = None
        for state in states:
            if state.get("type") == "completed":
                done_state_id = state.get("id")
                break
        
        if not done_state_id:
            logger.error("No completed state found for team")
            return False
        
        # Update issue state
        mutation = """
        mutation UpdateIssueState($issueId: String!, $stateId: String!) {
            issueUpdate(id: $issueId, input: { stateId: $stateId }) {
                success
            }
        }
        """
        
        # Need to get the issue UUID from identifier
        issue = self.get_issue(issue_id)
        if not issue or not issue.raw_data:
            return False
        
        issue_uuid = issue.raw_data.get("id")
        result = self._execute_query(mutation, {
            "issueId": issue_uuid,
            "stateId": done_state_id
        })
        
        success = result.get("issueUpdate", {}).get("success", False)
        if success:
            logger.info(f"✅ Transitioned Linear {issue_id} to Done")
        return success
    
    def get_issue_dependencies(self, issue_id: str) -> Dict[str, List[str]]:
        """Get all dependencies for a Linear issue."""
        ticket = self.get_issue(issue_id)
        if not ticket:
            return {"blocks": [], "blocked_by": [], "relates_to": []}
        
        result: Dict[str, List[str]] = {
            "blocks": [],
            "blocked_by": [],
            "relates_to": []
        }
        
        for rel in ticket.relations:
            if rel.relation_type == RelationType.BLOCKS:
                result["blocks"].append(rel.target_id)
            elif rel.relation_type == RelationType.BLOCKED_BY:
                result["blocked_by"].append(rel.target_id)
            elif rel.relation_type == RelationType.RELATES_TO:
                result["relates_to"].append(rel.target_id)
        
        return result
