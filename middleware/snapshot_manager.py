"""
SnapshotManager: Handles persistence of the Garden state (Time Machine).

Saves current tickets and avatars to JSON snapshots, and coordinates
restoration via UE5 commands.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from middleware.models.ticket import UnifiedTicket, IssueStatus, IssueType
# Avoid circular imports by importing managers inside methods or passing them in

logger = logging.getLogger("BloomPath.SnapshotManager")

SNAPSHOT_DIR = os.path.join(os.getcwd(), "data", "snapshots")

class SnapshotManager:
    def __init__(self):
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    def take_snapshot(self, 
                      tickets: List[UnifiedTicket], 
                      avatars: Dict[str, Any], 
                      label: str = "manual") -> str:
        """
        Serialize current state to a JSON snapshot file.
        
        Args:
            tickets: List of active UnifiedTicket objects
            avatars: Dict of UnifiedUser objects (from AvatarManager)
            label: Descriptive label for the snapshot
        
        Returns:
            The filename of the saved snapshot.
        """
        timestamp = int(time.time())
        snapshot_id = f"{timestamp}_{label.replace(' ', '_')}"
        filename = f"{snapshot_id}.json"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        
        # Serialize Tickets
        # UnifiedTicket is a dataclass, so asdict works (but need to handle datetime)
        serialized_tickets = []
        for t in tickets:
            t_dict = asdict(t)
            # DateTime objects are not JSON serializable by default
            if t_dict.get('created_at'): t_dict['created_at'] = t_dict['created_at'].isoformat()
            if t_dict.get('updated_at'): t_dict['updated_at'] = t_dict['updated_at'].isoformat()
            serialized_tickets.append(t_dict)
            
        # Serialize Avatars
        serialized_avatars = []
        for uid, user in avatars.items():
            serialized_avatars.append(asdict(user))
            
        data = {
            "version": "1.0",
            "timestamp": timestamp,
            "label": label,
            "tickets": serialized_tickets,
            "avatars": serialized_avatars
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"📸 Snapshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return ""

    def list_snapshots(self) -> List[str]:
        """Return list of available snapshot filenames."""
        try:
            return sorted([f for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".json")])
        except Exception:
            return []

    def load_snapshot(self, filename: str) -> Dict[str, Any]:
        """
        Load a snapshot from disk and Return the data.
        Does NOT trigger restoration logic (separation of concerns).
        """
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        if not os.path.exists(filepath):
            logger.error(f"Snapshot not found: {filename}")
            return {}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"📂 Snapshot loaded: {filename}")
            return data
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return {}

# Global instance
snapshot_manager = SnapshotManager()
