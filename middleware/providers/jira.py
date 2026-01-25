"""
JiraProvider: Adapter for Atlassian Jira.

Maps Jira's data model (Epic, Story, Task, Bug, Sub-task) and issue links
to the UnifiedTicket format.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests
from requests.auth import HTTPBasicAuth

from middleware.providers.base import IssueProvider
from middleware.models.ticket import (
    UnifiedTicket, IssueType, IssueStatus, Relation, RelationType
)

logger = logging.getLogger("BloomPath.Provider.Jira")


# Mapping from Jira issue types to unified types
JIRA_TYPE_MAP: Dict[str, IssueType] = {
    "Epic": IssueType.EPIC,
    "Story": IssueType.FEATURE,
    "Bug": IssueType.BUG,
    "Task": IssueType.TASK,
    "Sub-task": IssueType.CHORE,
    # Common custom types
    "Feature": IssueType.FEATURE,
    "Improvement": IssueType.FEATURE,
    "Spike": IssueType.TASK,
    "Technical Debt": IssueType.CHORE,
}

# Mapping from Jira priority to unified priority (1-5)
JIRA_PRIORITY_MAP: Dict[str, int] = {
    "Highest": 5,
    "High": 4,
    "Medium": 3,
    "Low": 2,
    "Lowest": 1,
}

# Mapping from Jira status to unified status
JIRA_STATUS_MAP: Dict[str, IssueStatus] = {
    "To Do": IssueStatus.TODO,
    "Open": IssueStatus.TODO,
    "Backlog": IssueStatus.TODO,
    "In Progress": IssueStatus.IN_PROGRESS,
    "In Review": IssueStatus.IN_PROGRESS,
    "Blocked": IssueStatus.BLOCKED,
    "Impediment": IssueStatus.BLOCKED,
    "On Hold": IssueStatus.BLOCKED,
    "Waiting": IssueStatus.BLOCKED,
    "Done": IssueStatus.DONE,
    "Closed": IssueStatus.DONE,
    "Resolved": IssueStatus.DONE,
}

# Mapping from Jira issue link types to unified relation types
JIRA_LINK_MAP: Dict[str, RelationType] = {
    "Blocks": RelationType.BLOCKS,
    "blocks": RelationType.BLOCKS,
    "is blocked by": RelationType.BLOCKED_BY,
    "Duplicate": RelationType.DUPLICATES,
    "duplicates": RelationType.DUPLICATES,
    "is duplicated by": RelationType.DUPLICATES,
    "Relates": RelationType.RELATES_TO,
    "relates to": RelationType.RELATES_TO,
}


class JiraProvider(IssueProvider):
    """Jira implementation of IssueProvider."""
    
    def __init__(
        self,
        domain: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        board_id: Optional[str] = None
    ):
        self.domain = domain or os.getenv("JIRA_DOMAIN")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        self.board_id = board_id or os.getenv("JIRA_BOARD_ID")
        
        if not all([self.domain, self.email, self.api_token]):
            logger.warning("Jira credentials not fully configured")
    
    @property
    def name(self) -> str:
        return "jira"
    
    @property
    def _auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.email, self.api_token)
    
    @property
    def _base_url(self) -> str:
        return f"https://{self.domain}/rest/api/3"
    
    @property
    def _agile_url(self) -> str:
        return f"https://{self.domain}/rest/agile/1.0"
    
    def _normalize_type(self, jira_type: str) -> IssueType:
        """Convert Jira issue type to unified type."""
        return JIRA_TYPE_MAP.get(jira_type, IssueType.TASK)
    
    def _normalize_priority(self, jira_priority: Optional[str]) -> int:
        """Convert Jira priority to unified priority (1-5)."""
        if not jira_priority:
            return 3
        return JIRA_PRIORITY_MAP.get(jira_priority, 3)
    
    def _normalize_status(self, jira_status: str) -> IssueStatus:
        """Convert Jira status to unified status."""
        return JIRA_STATUS_MAP.get(jira_status, IssueStatus.TODO)
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _extract_parent_id(self, fields: Dict[str, Any]) -> Optional[str]:
        """Extract Epic or parent issue ID from Jira fields."""
        # Next-gen projects use 'parent' field
        parent = fields.get('parent', {})
        if parent:
            return parent.get('key')
        
        # Classic projects use custom field for Epic link
        epic_link = fields.get('customfield_10014')  # Common field ID
        if epic_link:
            return epic_link
        
        return None
    
    def _extract_relations(self, fields: Dict[str, Any]) -> List[Relation]:
        """Extract issue links and convert to unified relations."""
        relations: List[Relation] = []
        issue_links = fields.get('issuelinks', [])
        
        for link in issue_links:
            link_type = link.get('type', {})
            
            # Outward links (this issue -> target)
            if 'outwardIssue' in link:
                outward_type = link_type.get('outward', '')
                target_key = link['outwardIssue'].get('key')
                if target_key:
                    rel_type = JIRA_LINK_MAP.get(outward_type, RelationType.RELATES_TO)
                    relations.append(Relation(
                        target_id=target_key,
                        relation_type=rel_type,
                        target_provider="jira"
                    ))
            
            # Inward links (target -> this issue)
            if 'inwardIssue' in link:
                inward_type = link_type.get('inward', '')
                target_key = link['inwardIssue'].get('key')
                if target_key:
                    rel_type = JIRA_LINK_MAP.get(inward_type, RelationType.RELATES_TO)
                    relations.append(Relation(
                        target_id=target_key,
                        relation_type=rel_type,
                        target_provider="jira"
                    ))
        
        # Add sub-task relations
        subtasks = fields.get('subtasks', [])
        for subtask in subtasks:
            relations.append(Relation(
                target_id=subtask.get('key'),
                relation_type=RelationType.CHILD,
                target_provider="jira"
            ))
        
        return relations
    
    def _issue_to_ticket(self, issue: Dict[str, Any]) -> UnifiedTicket:
        """Convert a Jira issue to UnifiedTicket."""
        fields = issue.get('fields', {})
        
        # Extract assignee info
        assignee = fields.get('assignee') or {}
        
        # Extract sprint info (if available)
        sprint_data = None
        sprint_field = fields.get('customfield_10020', [])  # Common sprint field
        if sprint_field and isinstance(sprint_field, list) and len(sprint_field) > 0:
            sprint_data = sprint_field[-1]  # Get most recent sprint
        
        return UnifiedTicket(
            id=issue.get('key', ''),
            provider=self.name,
            title=fields.get('summary', ''),
            description=fields.get('description'),
            status=self._normalize_status(
                fields.get('status', {}).get('name', 'To Do')
            ),
            issue_type=self._normalize_type(
                fields.get('issuetype', {}).get('name', 'Task')
            ),
            priority=self._normalize_priority(
                fields.get('priority', {}).get('name')
            ),
            assignee_id=assignee.get('accountId'),
            assignee_name=assignee.get('displayName'),
            assignee_avatar=assignee.get('avatarUrls', {}).get('48x48'),
            parent_id=self._extract_parent_id(fields),
            relations=self._extract_relations(fields),
            labels=fields.get('labels', []),
            sprint_id=sprint_data.get('id') if sprint_data else None,
            sprint_name=sprint_data.get('name') if sprint_data else None,
            created_at=self._parse_datetime(fields.get('created')),
            updated_at=self._parse_datetime(fields.get('updated')),
            raw_data=issue
        )
    
    def parse_webhook(self, payload: Dict[str, Any]) -> UnifiedTicket:
        """Parse Jira webhook payload into UnifiedTicket."""
        issue = payload.get('issue', {})
        return self._issue_to_ticket(issue)
    
    def get_issue(self, issue_id: str) -> Optional[UnifiedTicket]:
        """Fetch a single issue from Jira."""
        url = f"{self._base_url}/issue/{issue_id}"
        params = {
            "fields": "summary,description,status,issuetype,priority,assignee,"
                      "parent,labels,issuelinks,subtasks,created,updated,"
                      "customfield_10014,customfield_10020"  # Epic link, Sprint
        }
        
        try:
            response = requests.get(url, params=params, auth=self._auth, timeout=10)
            response.raise_for_status()
            return self._issue_to_ticket(response.json())
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Jira issue {issue_id}: {e}")
            return None
    
    def get_active_sprint_or_cycle(self) -> Optional[Dict[str, Any]]:
        """Get the active sprint from Jira board."""
        if not self.board_id:
            logger.warning("JIRA_BOARD_ID not configured")
            return None
        
        url = f"{self._agile_url}/board/{self.board_id}/sprint"
        
        try:
            response = requests.get(
                url, params={"state": "active"}, auth=self._auth, timeout=10
            )
            response.raise_for_status()
            sprints = response.json().get('values', [])
            return sprints[0] if sprints else None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch active sprint: {e}")
            return None
    
    def get_sprint_issues(self, sprint_id: str) -> List[UnifiedTicket]:
        """Get all issues in a sprint."""
        url = f"{self._agile_url}/sprint/{sprint_id}/issue"
        params = {
            "fields": "summary,description,status,issuetype,priority,assignee,"
                      "parent,labels,issuelinks,subtasks,created,updated"
        }
        
        try:
            response = requests.get(url, params=params, auth=self._auth, timeout=30)
            response.raise_for_status()
            issues = response.json().get('issues', [])
            return [self._issue_to_ticket(issue) for issue in issues]
        except requests.RequestException as e:
            logger.error(f"Failed to fetch sprint {sprint_id} issues: {e}")
            return []
    
    def transition_to_done(self, issue_id: str) -> bool:
        """Transition a Jira issue to Done status."""
        url = f"{self._base_url}/issue/{issue_id}/transitions"
        
        try:
            # First, get available transitions
            response = requests.get(url, auth=self._auth, timeout=10)
            response.raise_for_status()
            transitions = response.json().get('transitions', [])
            
            # Find "Done" transition
            done_id = None
            for t in transitions:
                if t['name'].lower() == 'done':
                    done_id = t['id']
                    break
            
            if not done_id:
                logger.error(f"No 'Done' transition for {issue_id}")
                return False
            
            # Execute transition
            payload = {"transition": {"id": done_id}}
            response = requests.post(url, json=payload, auth=self._auth, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✅ Transitioned {issue_id} to Done")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to transition {issue_id}: {e}")
            return False
    
    def get_issue_dependencies(self, issue_id: str) -> Dict[str, List[str]]:
        """Get all dependencies for a Jira issue."""
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
