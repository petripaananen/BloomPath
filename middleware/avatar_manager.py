"""
AvatarManager: Manages user avatars in the BloomPath garden.

This module tracks active users, their assigned issues, and orchestrates
avatar spawning and movement in UE5.
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("BloomPath.AvatarManager")

@dataclass
class UnifiedUser:
    """Represents a human user in the system."""
    id: str
    name: str
    avatar_url: Optional[str] = None
    current_issue_id: Optional[str] = None
    provider: str = "unknown"

class AvatarManager:
    """
    Singleton-style manager for tracking user presence.
    """
    
    def __init__(self):
        self.users: Dict[str, UnifiedUser] = {}
        
    def register_user(self, user_id: str, name: str, avatar_url: Optional[str], provider: str) -> UnifiedUser:
        """Register or update a user in the cache."""
        if not user_id:
            return None
            
        if user_id not in self.users:
            self.users[user_id] = UnifiedUser(
                id=user_id,
                name=name,
                avatar_url=avatar_url,
                provider=provider
            )
        else:
            # Update existing user info if changed
            user = self.users[user_id]
            user.name = name
            user.avatar_url = avatar_url or user.avatar_url
            
        return self.users[user_id]
        
    def update_user_location(self, user_id: str, issue_id: str) -> None:
        """
        Update a user's focus (assigned issue).
        Triggers UE5 commands to move/spawn avatar.
        """
        if user_id not in self.users:
            logger.warning(f"Attempted to move unknown user {user_id}")
            return
            
        user = self.users[user_id]
        
        # If location hasn't changed, do nothing
        if user.current_issue_id == issue_id:
            return
            
        logger.info(f"👤 Moving Avatar {user.name} ({user_id}) to {issue_id}")
        
        try:
            from ue5_interface import trigger_ue5_spawn_avatar, trigger_ue5_move_avatar
            
            # If they had a previous location, we 'move' them
            # If not, we 'spawn' them
            if user.current_issue_id:
                trigger_ue5_move_avatar(user_id, issue_id)
            else:
                trigger_ue5_spawn_avatar(user_id, issue_id, user.name)
                
            user.current_issue_id = issue_id
            
        except ImportError:
            logger.warning("UE5 interface not available for avatar movement")
        except Exception as e:
            logger.error(f"Failed to move avatar for {user_id}: {e}")

    def remove_avatar(self, user_id: str) -> None:
        """Despawn an avatar."""
        if user_id not in self.users:
            return

        user = self.users[user_id]
        logger.info(f"👤 Removing Avatar {user.name}")
        
        try:
            from ue5_interface import trigger_ue5_remove_avatar
            trigger_ue5_remove_avatar(user_id)
            user.current_issue_id = None
        except Exception as e:
            logger.error(f"Failed to remove avatar: {e}")

# Global instance
avatar_manager = AvatarManager()
