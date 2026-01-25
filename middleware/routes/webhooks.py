"""
Webhook routes for receiving events from project management tools.

Each provider has its own endpoint to handle tool-specific payloads,
which are then normalized to UnifiedTicket and processed uniformly.
"""

import logging
from flask import Blueprint, request, jsonify

from middleware.providers.jira import JiraProvider
from middleware.providers.linear import LinearProvider
from middleware.core import process_ticket_event

logger = logging.getLogger("BloomPath.Routes.Webhooks")

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')


@webhooks_bp.route('/jira', methods=['POST'])
def jira_webhook():
    """
    Handle Jira webhook events.
    
    Parses the Jira-specific payload and processes it through the
    unified ticket pipeline.
    """
    data = request.json
    if not data:
        logger.warning("Received Jira webhook with no JSON payload")
        return jsonify({"status": "error", "message": "No JSON payload"}), 400
    
    event_type = data.get('webhookEvent', data.get('issue_event_type_name', 'unknown'))
    logger.info(f"📨 Jira webhook received: {event_type}")
    
    try:
        provider = JiraProvider()
        ticket = provider.parse_webhook(data)
        
        # Detect event type from changelog
        event_info = _detect_jira_event(data)
        
        result = process_ticket_event(ticket, event_info, provider)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing Jira webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@webhooks_bp.route('/linear', methods=['POST'])
def linear_webhook():
    """
    Handle Linear webhook events.
    
    Verifies the webhook signature, parses the Linear-specific payload,
    and processes it through the unified ticket pipeline.
    """
    data = request.json
    if not data:
        logger.warning("Received Linear webhook with no JSON payload")
        return jsonify({"status": "error", "message": "No JSON payload"}), 400
    
    # Verify signature
    signature = request.headers.get('X-Linear-Signature', '')
    provider = LinearProvider()
    
    if signature and not provider.verify_webhook_signature(request.get_data(), signature):
        logger.warning("Invalid Linear webhook signature")
        return jsonify({"status": "error", "message": "Invalid signature"}), 401
    
    action = data.get('action', 'unknown')
    logger.info(f"📨 Linear webhook received: {action}")
    
    try:
        ticket = provider.parse_webhook(data)
        
        # Map Linear actions to event types
        event_info = _detect_linear_event(data)
        
        result = process_ticket_event(ticket, event_info, provider)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing Linear webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


def _detect_jira_event(data: dict) -> dict:
    """
    Detect the type of Jira event from webhook data.
    
    Returns a dict with event classification:
    - event_type: 'completed', 'reopened', 'blocked', 'unblocked', 'updated'
    - from_status: Previous status (if status change)
    - to_status: New status (if status change)
    """
    changelog = data.get('changelog', {})
    items = changelog.get('items', [])
    
    for item in items:
        if item.get('field') == 'status':
            from_status = item.get('fromString', '')
            to_status = item.get('toString', '')
            
            if to_status.lower() == 'done':
                return {
                    'event_type': 'completed',
                    'from_status': from_status,
                    'to_status': to_status
                }
            elif from_status.lower() == 'done':
                return {
                    'event_type': 'reopened',
                    'from_status': from_status,
                    'to_status': to_status
                }
            elif to_status.lower() in ['blocked', 'impediment', 'on hold']:
                return {
                    'event_type': 'blocked',
                    'from_status': from_status,
                    'to_status': to_status
                }
            elif from_status.lower() in ['blocked', 'impediment', 'on hold']:
                return {
                    'event_type': 'unblocked',
                    'from_status': from_status,
                    'to_status': to_status
                }
    
    return {'event_type': 'updated'}


def _detect_linear_event(data: dict) -> dict:
    """
    Detect the type of Linear event from webhook data.
    
    Linear uses 'action' field: 'create', 'update', 'remove'
    and 'type' field: 'Issue', 'Comment', etc.
    """
    action = data.get('action', '')
    webhook_type = data.get('type', '')
    
    if webhook_type != 'Issue':
        return {'event_type': 'other', 'action': action}
    
    # Check for state changes in updated data
    updated_from = data.get('updatedFrom', {})
    issue_data = data.get('data', {})
    
    if 'stateId' in updated_from:
        # State changed
        new_state = issue_data.get('state', {})
        state_type = new_state.get('type', '').lower()
        
        if state_type == 'completed':
            return {'event_type': 'completed'}
        elif state_type == 'canceled':
            return {'event_type': 'completed'}  # Treat as done
    
    # Check for blocking changes
    if 'blockedBy' in updated_from or 'blocking' in updated_from:
        blocked_by = issue_data.get('blockedBy', {}).get('nodes', [])
        if blocked_by:
            return {'event_type': 'blocked'}
        else:
            return {'event_type': 'unblocked'}
    
    if action == 'create':
        return {'event_type': 'created'}
    
    return {'event_type': 'updated'}
