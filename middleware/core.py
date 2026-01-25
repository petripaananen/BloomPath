"""
Core processing logic for BloomPath middleware.

This module contains the provider-agnostic ticket processing logic
that triggers UE5 visualizations based on issue events.
"""

import logging
from typing import Dict, Any, Optional

from middleware.models.ticket import UnifiedTicket, IssueStatus, IssueType
from middleware.providers.base import IssueProvider

logger = logging.getLogger("BloomPath.Core")

# Issue type to UE5 growth mapping
GROWTH_TYPE_MAP = {
    IssueType.EPIC: "trunk",
    IssueType.FEATURE: "branch",
    IssueType.BUG: "flower",
    IssueType.TASK: "leaf",
    IssueType.CHORE: "bud",
}

# Priority to growth modifier
PRIORITY_MODIFIER_MAP = {
    5: 2.0,   # Highest: Double growth
    4: 1.5,   # High: 50% more
    3: 1.0,   # Medium: Normal
    2: 0.75,  # Low: Smaller
    1: 0.5,   # Lowest: Half
}


def process_ticket_event(
    ticket: UnifiedTicket,
    event_info: Dict[str, Any],
    provider: IssueProvider
) -> Dict[str, Any]:
    """
    Process a ticket event and trigger appropriate UE5 visualizations.
    
    Args:
        ticket: The normalized ticket data
        event_info: Event classification (completed, blocked, etc.)
        provider: The provider that parsed this ticket
        
    Returns:
        Result dict with status and action taken
    """
    event_type = event_info.get('event_type', 'updated')
    
    logger.info(f"🎫 Processing {ticket.id} ({ticket.provider}): {event_type}")
    
    # Import UE5 interface here to avoid circular imports
    try:
        from ue5_interface import (
            trigger_ue5_growth,
            trigger_ue5_shrink,
            trigger_ue5_thorns,
            trigger_ue5_remove_thorns
        )
    except ImportError:
        logger.warning("UE5 interface not available")
        return {"status": "ok", "action": "logged_only", "issue": ticket.id}
    
    growth_type = GROWTH_TYPE_MAP.get(ticket.issue_type, "leaf")
    growth_modifier = PRIORITY_MODIFIER_MAP.get(ticket.priority, 1.0)
    
    try:
        if event_type == 'completed':
            # Issue completed -> Grow plant
            trigger_ue5_growth(
                issue_key=ticket.id,
                growth_type=growth_type,
                growth_modifier=growth_modifier,
                epic_key=ticket.parent_id
            )
            
            # Trigger audio event
            _push_audio_event("task_completed", ticket.id, ticket.assignee_name)
            
            return {
                "status": "growth_triggered",
                "issue": ticket.id,
                "growth_type": growth_type
            }
        
        elif event_type == 'reopened':
            # Issue reopened -> Shrink plant
            trigger_ue5_shrink(ticket.id)
            _push_audio_event("task_reopened", ticket.id)
            
            return {"status": "shrink_triggered", "issue": ticket.id}
        
        elif event_type == 'blocked':
            # Issue blocked -> Add thorns
            trigger_ue5_thorns(ticket.id, ticket.parent_id)
            _push_audio_event("blocker_added", ticket.id)
            
            return {"status": "thorns_triggered", "issue": ticket.id}
        
        elif event_type == 'unblocked':
            # Issue unblocked -> Remove thorns
            trigger_ue5_remove_thorns(ticket.id)
            _push_audio_event("blocker_resolved", ticket.id)
            
            return {"status": "thorns_removed", "issue": ticket.id}
        
        elif event_type == 'created' or (event_type == 'updated' and growth_type == 'feature'):
            # New issue -> Could spawn seed/bud AND trigger Dreaming Engine
            
            # Initialize Dreaming Engine for new Features/Epics
            if ticket.issue_type in [IssueType.FEATURE, IssueType.EPIC]:
                logger.info(f"✨ Triggering L3 Dreaming Engine for {ticket.id}...")
                try:
                    from orchestrator import BloomPathOrchestrator
                    orchestrator = BloomPathOrchestrator()
                    orchestrator.process_ticket(ticket)
                except Exception as ex:
                    logger.error(f"Dreaming Engine failed: {ex}")

            return {"status": "received", "action": "dreaming_triggered", "issue": ticket.id}
        
        else:
            # General update
            return {"status": "received", "issue": ticket.id}
    
    except Exception as e:
        logger.error(f"UE5 action failed for {ticket.id}: {e}")
        return {"status": "ue5_error", "issue": ticket.id, "error": str(e)}


def _push_audio_event(
    event_type: str,
    issue_key: str,
    user: Optional[str] = None
) -> None:
    """Push an audio event to the queue for UE5 to consume."""
    try:
        from ue5_interface import trigger_ue5_play_sound_2d
        
        sound_map = {
            "task_completed": "Success_Chime",
            "blocker_added": "Error_Buzz",
            "task_reopened": "Shrink_Wraow",
            "blocker_resolved": "Relief_Sigh"
        }
        sound_name = sound_map.get(event_type, "Default_Beep")
        trigger_ue5_play_sound_2d(sound_name)
    except Exception as e:
        logger.warning(f"Failed to trigger audio for {event_type}: {e}")


def process_dependencies_visualization(ticket: UnifiedTicket) -> None:
    """
    Trigger UE5 visualization of dependencies as vines.
    
    Called after a ticket is processed to draw connections.
    """
    try:
        from ue5_interface import trigger_ue5_dependency_vine
        
        for blocked_id in ticket.blocked_by:
            trigger_ue5_dependency_vine(
                from_id=ticket.id,
                to_id=blocked_id,
                relation_type="blocked_by"
            )
        
        for blocking_id in ticket.blocking:
            trigger_ue5_dependency_vine(
                from_id=ticket.id,
                to_id=blocking_id,
                relation_type="blocks"
            )
    except ImportError:
        logger.debug("Dependency vine visualization not available")
    except Exception as e:
        logger.warning(f"Failed to visualize dependencies: {e}")
