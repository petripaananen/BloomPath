"""
UnifiedTicket: The universal data model for project management issues.

This is the "Rosetta Stone" that normalizes data from Jira, Linear, and
potentially other providers into a single consistent format.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class IssueType(str, Enum):
    """Unified issue types across all providers."""
    EPIC = "epic"           # Jira: Epic, Linear: Label or Project
    FEATURE = "feature"     # Jira: Story, Linear: default
    BUG = "bug"             # Jira: Bug, Linear: Label
    TASK = "task"           # Jira: Task, Linear: no label
    CHORE = "chore"         # Jira: Sub-task, Linear: Label


class IssueStatus(str, Enum):
    """Unified status across all providers."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class RelationType(str, Enum):
    """Unified relation/dependency types."""
    BLOCKS = "blocks"           # This issue blocks another
    BLOCKED_BY = "blocked_by"   # This issue is blocked by another
    PARENT = "parent"           # Epic or parent issue
    CHILD = "child"             # Sub-task or child issue
    RELATES_TO = "relates_to"   # General relation
    DUPLICATES = "duplicates"   # Duplicate issue


@dataclass
class Relation:
    """Represents a relationship between two issues."""
    target_id: str
    relation_type: RelationType
    target_provider: Optional[str] = None  # For cross-provider relations


@dataclass
class UnifiedTicket:
    """
    Universal representation of a project management issue.
    
    This model normalizes data from multiple providers (Jira, Linear)
    into a single consistent format for BloomPath processing.
    """
    # Core identifiers
    id: str                             # e.g., "KAN-123" or "LIN-abc123"
    provider: str                       # "jira" or "linear"
    
    # Content
    title: str
    description: Optional[str] = None
    
    # Classification
    status: IssueStatus = IssueStatus.TODO
    issue_type: IssueType = IssueType.TASK
    priority: int = 3                   # 1 (lowest) to 5 (highest)
    
    # Assignment
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_avatar: Optional[str] = None
    
    # Hierarchy
    parent_id: Optional[str] = None     # Epic or parent issue ID
    
    # Relations/Dependencies
    relations: List[Relation] = field(default_factory=list)
    
    # Categorization
    labels: List[str] = field(default_factory=list)
    
    # Attachments (URLs to downloadable files)
    attachments: List[dict] = field(default_factory=list)
    
    # Sprint/Cycle
    sprint_id: Optional[str] = None
    sprint_name: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Raw data for debugging
    raw_data: Optional[dict] = field(default=None, repr=False)
    
    @property
    def blocked_by(self) -> List[str]:
        """Get list of issue IDs that block this issue."""
        return [r.target_id for r in self.relations 
                if r.relation_type == RelationType.BLOCKED_BY]
    
    @property
    def blocking(self) -> List[str]:
        """Get list of issue IDs that this issue blocks."""
        return [r.target_id for r in self.relations 
                if r.relation_type == RelationType.BLOCKS]
    
    @property
    def is_blocked(self) -> bool:
        """Check if this issue is blocked by any other issue."""
        return len(self.blocked_by) > 0 or self.status == IssueStatus.BLOCKED
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "provider": self.provider,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "issue_type": self.issue_type.value,
            "priority": self.priority,
            "assignee": {
                "id": self.assignee_id,
                "name": self.assignee_name,
                "avatar": self.assignee_avatar
            } if self.assignee_id else None,
            "parent_id": self.parent_id,
            "relations": [
                {"target_id": r.target_id, "type": r.relation_type.value}
                for r in self.relations
            ],
            "labels": self.labels,
            "attachments": self.attachments,
            "sprint": {
                "id": self.sprint_id,
                "name": self.sprint_name
            } if self.sprint_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
