"""
IssueProvider: Abstract base class for project management tool adapters.

Each provider (Jira, Linear, etc.) implements this interface to normalize
their data into the UnifiedTicket format.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from middleware.models.ticket import UnifiedTicket


class IssueProvider(ABC):
    """
    Abstract base class for issue provider adapters.
    
    Implementations handle the specifics of each project management tool
    (Jira, Linear, etc.) and normalize data into UnifiedTicket format.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name (e.g., 'jira', 'linear')."""
        pass
    
    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> UnifiedTicket:
        """
        Parse a webhook payload into a UnifiedTicket.
        
        Args:
            payload: Raw webhook JSON from the provider
            
        Returns:
            UnifiedTicket with normalized data
        """
        pass
    
    @abstractmethod
    def get_issue(self, issue_id: str) -> Optional[UnifiedTicket]:
        """
        Fetch a single issue by ID from the provider API.
        
        Args:
            issue_id: The issue identifier (e.g., "KAN-123")
            
        Returns:
            UnifiedTicket if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_active_sprint_or_cycle(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active sprint (Jira) or cycle (Linear).
        
        Returns:
            Dict with sprint/cycle info including id, name, dates
            None if no active sprint/cycle
        """
        pass
    
    @abstractmethod
    def get_sprint_issues(self, sprint_id: str) -> List[UnifiedTicket]:
        """
        Get all issues in a sprint/cycle.
        
        Args:
            sprint_id: The sprint or cycle identifier
            
        Returns:
            List of UnifiedTickets in the sprint
        """
        pass
    
    @abstractmethod
    def transition_to_done(self, issue_id: str) -> bool:
        """
        Transition an issue to the 'Done' status.
        
        This enables bidirectional sync (UE5 watering -> issue completion).
        
        Args:
            issue_id: The issue identifier
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_issue_dependencies(self, issue_id: str) -> Dict[str, List[str]]:
        """
        Get all dependencies for an issue.
        
        Args:
            issue_id: The issue identifier
            
        Returns:
            Dict with 'blocks', 'blocked_by', 'relates_to' keys,
            each containing a list of issue IDs
        """
        pass
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security.
        
        Override in subclasses that support signed webhooks.
        
        Args:
            payload: Raw request body
            signature: Signature from request headers
            
        Returns:
            True if valid, False otherwise
        """
        return True  # Default: no verification
