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

    # Social Layer: Manage Avatars
    try:
        from middleware.avatar_manager import avatar_manager
        
        if ticket.assignee_id and ticket.assignee_name:
            avatar_manager.register_user(
                user_id=ticket.assignee_id,
                name=ticket.assignee_name,
                avatar_url=ticket.assignee_avatar,
                provider=ticket.provider
            )
            # Move avatar to this ticket if they are the assignee and interacting with it
            avatar_manager.update_user_location(ticket.assignee_id, ticket.id)

            # Phase 5: Audio Intensity
            # Calculate intensity based on active avatars (users working on an issue)
            try:
                from ue5_interface import trigger_ue5_ambience
                active_users = sum(1 for u in avatar_manager.users.values() if u.current_issue_id)
                # Map 0-5 users to 0.0-1.0 intensity
                intensity = min(1.0, active_users / 5.0)
                trigger_ue5_ambience(intensity)
            except ImportError:
                pass
            
    except Exception as e:
        logger.warning(f"Avatar/Audio update failed: {e}")
    
    # Import UE5 interface here to avoid circular imports
    try:
        from ue5_interface import (
            trigger_ue5_growth,
            trigger_ue5_shrink,
            trigger_ue5_thorns,
            trigger_ue5_remove_thorns
        )
    except ImportError as e:
        logger.warning(f"UE5 interface not available: {e}")
        return {"status": "ok", "action": "logged_only", "issue": ticket.id}
    
    growth_type = GROWTH_TYPE_MAP.get(ticket.issue_type, "leaf")
    growth_modifier = PRIORITY_MODIFIER_MAP.get(ticket.priority, 1.0)
    
    try:
        if event_type == 'completed':
            # Issue completed -> Grow plant
            trigger_ue5_growth(
                branch_id=ticket.id,
                growth_type=growth_type,
                growth_modifier=growth_modifier,
                epic_key=ticket.parent_id
            )
            
            # Trigger audio event
            _push_audio_event("task_completed", ticket.id, ticket.assignee_name)
            
            # Social Layer: Celebration animation
            if ticket.assignee_id:
                avatar_manager.play_animation(ticket.assignee_id, "celebrate")
            
            return {
                "status": "growth_triggered",
                "issue": ticket.id,
                "growth_type": growth_type
            }
        
        elif event_type == 'reopened':
            # Issue reopened -> Shrink plant
            trigger_ue5_shrink(ticket.id)
            _push_audio_event("task_reopened", ticket.id)
            
            # Social Layer: Confused animation
            if ticket.assignee_id:
                avatar_manager.play_animation(ticket.assignee_id, "confused")
            
            return {"status": "shrink_triggered", "issue": ticket.id}
        
        elif event_type == 'blocked':
            # Issue blocked -> Add thorns
            trigger_ue5_thorns(ticket.id, ticket.parent_id)
            _push_audio_event("blocker_added", ticket.id)
            
            # Social Layer: Frustrated animation
            if ticket.assignee_id:
                avatar_manager.play_animation(ticket.assignee_id, "frustrated")
            
            return {"status": "thorns_triggered", "issue": ticket.id}
        
        elif event_type == 'unblocked':
            # Issue unblocked -> Remove thorns
            trigger_ue5_remove_thorns(ticket.id)
            _push_audio_event("blocker_resolved", ticket.id)
            
            # Social Layer: Relieved animation
            if ticket.assignee_id:
                avatar_manager.play_animation(ticket.assignee_id, "relieved")
            
            return {"status": "thorns_removed", "issue": ticket.id}
        
        elif event_type == 'created' or (event_type == 'updated' and growth_type in ['branch', 'trunk']):
            # New issue -> Check for WorldGen trigger to launch PWM Pipeline
            if "WorldGen" in (ticket.labels or []):
                logger.info(f"✨ Triggering PWM Pipeline for {ticket.id}...")
                try:
                    from orchestrator import BloomPathOrchestrator
                    orchestrator = BloomPathOrchestrator()
                    orchestrator.process_ticket(ticket)
                except Exception as ex:
                    logger.error(f"PWM Pipeline failed: {ex}")

            return {"status": "received", "action": "processed", "issue": ticket.id}
        
        elif event_type == 'queued_for_build':
            # Issue moved to "To Do"
            return {"status": "received", "action": "queued", "issue": ticket.id}
        
        elif event_type == 'started':
            # Social Layer: Working animation
            if ticket.assignee_id:
                avatar_manager.play_animation(ticket.assignee_id, "working")
            
            # Issue moved to "In Progress" - trigger PWM Pipeline only if labeled
            if any(label in (ticket.labels or []) for label in ["WorldGen", "World Lab"]):
                logger.info(f"🏗️ PWM Pipeline triggered for {ticket.id} (Started)")
                try:
                    from orchestrator import BloomPathOrchestrator
                    orchestrator = BloomPathOrchestrator()
                    orchestrator.process_ticket(ticket)
                    return {"status": "pwm_triggered", "issue": ticket.id}
                except Exception as ex:
                    logger.error(f"PWM Pipeline error: {ex}")
                    return {"status": "pwm_error", "issue": ticket.id, "error": str(ex)}
            else:
                logger.info(f"⏭️ Skipping PWM Pipeline for {ticket.id} (Missing WorldGen label)")
                return {"status": "pwm_skipped", "issue": ticket.id}
        
        else:
            # General update
            return {"status": "received", "issue": ticket.id}
    
    except Exception as e:
        logger.error(f"UE5 action failed for {ticket.id}: {e}")
        return {"status": "ue5_error", "issue": ticket.id, "error": str(e)}
    finally:
        # Always update environmental dynamics after a ticket event
        _update_environmental_dynamics(provider)


def _update_environmental_dynamics(provider: IssueProvider) -> None:
    """Calculates sprint health and pushes weather/time updates to UE5."""
    try:
        from ue5_interface import trigger_ue5_weather, trigger_ue5_time
        sprint = provider.get_active_sprint_or_cycle()
        if not sprint:
            return
            
        sprint_id = sprint.get('id')
        issues = provider.get_sprint_issues(sprint_id)
        total = len(issues)
        if total == 0:
            return
            
        done = sum(1 for t in issues if t.status == IssueStatus.DONE)
        blocked = sum(1 for t in issues if t.is_blocked)
        
        done_ratio = done / total
        blocked_ratio = blocked / total
        
        if blocked_ratio > 0.2 or done_ratio < 0.3:
            weather = "storm"
        elif blocked_ratio > 0.1 or done_ratio < 0.6:
            weather = "cloudy"
        else:
            weather = "sunny"
            
        progress = sprint.get('progress', done_ratio)
        
        trigger_ue5_weather(weather)
        trigger_ue5_time(progress)
        logger.info(f"⛅ Env Update: {weather}, time: {progress:.2f}")
    except Exception as e:
        logger.warning(f"Failed to update environmental dynamics: {e}")


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
        from ue5_interface import trigger_ue5_sync_all_vines
        from middleware.routes.api import _get_provider
        
        provider_name = ticket.provider
        # We need a provider instance to fetch dependencies
        # This is a bit of a circular dependency if we import specific provider classes here
        # Ideally, the caller should have passed the dependencies or the provider
        # For now, let's just use the provider attached to the ticket if available, or fetch fresh
        
        # Simplified: We just fetch dependencies for THIS ticket and sync them
        # In a real batch scenario, we'd sync the whole graph
        
        provider = _get_provider(provider_name)
        
        deps = provider.get_issue_dependencies(ticket.id)
        if deps:
            # Transform to the format expected by sync_all_vines
            formatted_deps = []
            for d in deps:
                formatted_deps.append({
                    "from": ticket.id,
                    "to": d['id'],
                    "type": d['relation_type']
                })
            
            trigger_ue5_sync_all_vines(formatted_deps)
            
    except ImportError:
        logger.debug("Dependency vine visualization not available")
    except Exception as e:
        logger.warning(f"Failed to visualize dependencies: {e}")
