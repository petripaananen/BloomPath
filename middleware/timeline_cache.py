import sqlite3
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, List

from middleware.models.ticket import UnifiedTicket, IssueStatus, IssueType

logger = logging.getLogger("BloomPath.Timeline")

# Default DB location in data directory
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "timeline.db")


class TimelineCache:
    """
    Manages a persistent SQLite timeline of ticket states.
    Allows for time-scrubbing reconstructs of the garden.
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                issue_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                project_id TEXT,
                parent_id TEXT,
                issue_type TEXT,
                status TEXT,
                priority INTEGER,
                assignee_id TEXT
            )
        ''')
        
        # Simple index for faster scrubbing queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_issue_id ON events(issue_id)')
        self.conn.commit()

    def log_event(self, event_type: str, ticket: UnifiedTicket):
        """Append an event snapshot to the timeline."""
        timestamp = datetime.now().timestamp()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO events (
                timestamp, issue_id, event_type, project_id, 
                parent_id, issue_type, status, priority, assignee_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            ticket.id,
            event_type,
            str(ticket.project_id) if ticket.project_id else None,
            ticket.parent_id,
            ticket.issue_type.name,
            ticket.status.name,
            ticket.priority,
            ticket.assignee_id
        ))
        self.conn.commit()
        logger.info(f"⏱️ Timeline logged: {event_type} for {ticket.id} at {timestamp}")

    def get_state_at_timestamp(self, target_timestamp: float) -> List[UnifiedTicket]:
        """
        Reconstruct the state of all tickets exactly as they were at target_timestamp.
        Returns a mock UnifiedTicket list representing that snapshot.
        """
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Since we want the latest state for *each* issue up to the target_timestamp,
        # we group by issue_id and grab the one with the max timestamp <= target.
        cursor.execute('''
            SELECT e.*
            FROM events e
            INNER JOIN (
                SELECT issue_id, MAX(timestamp) as max_ts
                FROM events
                WHERE timestamp <= ?
                GROUP BY issue_id
            ) latest ON e.issue_id = latest.issue_id AND e.timestamp = latest.max_ts
        ''', (target_timestamp,))
        
        rows = cursor.fetchall()
            
        reconstructed_tickets = []
        for row in rows:
            # We don't reconstruct dependencies here since the UE5 interface
            # handles dependency vines dynamically on standard updates, but we need
            # sufficient fields to replay `trigger_ue5_growth` / `shrink` etc.
            
            try:
                # Need to safely parse string enums back to their objects
                status_enum = IssueStatus[row['status']]
                type_enum = IssueType[row['issue_type']]
            except KeyError:
                status_enum = IssueStatus.BACKLOG
                type_enum = IssueType.TASK
                
            ticket = UnifiedTicket(
                id=row['issue_id'],
                provider="timeline", # mock provider
                project_id=row['project_id'],
                title="Historical Fragment", # title isn't needed for UE5 viz
                description="",
                status=status_enum,
                issue_type=type_enum,
                priority=row['priority'],
                parent_id=row['parent_id'],
                assignee_id=row['assignee_id'],
            )
            # Tag along the last associated event_type (created, completed, blocked, reopened)
            # so the replayer knows what visualization phase it was sitting in (bloom vs generic)
            ticket._last_historical_event = row['event_type']
            reconstructed_tickets.append(ticket)
            
        return reconstructed_tickets


# Global singleton cache
timeline_cache = TimelineCache()
