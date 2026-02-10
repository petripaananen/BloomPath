"""
Background task queue for webhook processing.

Webhook handlers must respond quickly (< 1s) to avoid timeouts,
especially from Linear. This module provides a thread-safe queue
that processes ticket events in the background.
"""

import logging
import queue
import threading
from typing import Any, Dict

from middleware.models.ticket import UnifiedTicket
from middleware.providers.base import IssueProvider

logger = logging.getLogger("BloomPath.TaskQueue")

# Thread-safe queue for background processing
_task_queue: queue.Queue = queue.Queue()
_worker_thread: threading.Thread = None
_worker_started = False


def _worker():
    """Background worker that drains the queue and processes events."""
    logger.info("🔄 Background task worker started")
    while True:
        try:
            item = _task_queue.get(block=True)
            if item is None:
                break  # Shutdown signal

            ticket, event_info, provider = item
            logger.info(f"⚙️ Processing {ticket.id} ({event_info.get('event_type', '?')}) in background")

            try:
                from middleware.core import process_ticket_event
                process_ticket_event(ticket, event_info, provider)
            except Exception as e:
                logger.error(f"❌ Background processing failed for {ticket.id}: {e}", exc_info=True)
            finally:
                _task_queue.task_done()

        except Exception as e:
            logger.error(f"❌ Task worker error: {e}", exc_info=True)


def _ensure_worker():
    """Start the background worker if not already running."""
    global _worker_thread, _worker_started
    if _worker_started and _worker_thread and _worker_thread.is_alive():
        return

    _worker_thread = threading.Thread(target=_worker, name="BloomPath-TaskWorker", daemon=True)
    _worker_thread.start()
    _worker_started = True


def enqueue_ticket_event(
    ticket: UnifiedTicket,
    event_info: Dict[str, Any],
    provider: IssueProvider
) -> None:
    """
    Enqueue a ticket event for background processing.

    This returns immediately, allowing the webhook handler to respond fast.
    """
    _ensure_worker()
    _task_queue.put((ticket, event_info, provider))
    logger.info(f"📥 Enqueued {ticket.id} (queue depth: {_task_queue.qsize()})")


def get_queue_status() -> Dict[str, Any]:
    """Get current queue status for health monitoring."""
    return {
        "pending": _task_queue.qsize(),
        "worker_alive": _worker_thread.is_alive() if _worker_thread else False,
    }
