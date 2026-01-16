"""
Boring Flow Event System V14.0

Implements an event bus mechanism to decouple flow stages from
automated actions (like auto-fixing, notifications, and analytics).
"""

import logging
import threading
from collections.abc import Callable
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class FlowEvent(Enum):
    """Events triggered during the One Dragon Flow."""

    # Lifecycle Events
    PRE_SETUP = auto()
    POST_SETUP = auto()
    PRE_DESIGN = auto()
    POST_DESIGN = auto()
    PRE_BUILD = auto()
    POST_BUILD = auto()
    PRE_POLISH = auto()
    POST_POLISH = auto()

    # Trigger Events
    ON_ERROR = auto()
    ON_LINT_FAIL = auto()
    ON_TEST_FAIL = auto()
    ON_SECURITY_ISSUE = auto()
    ON_TASK_COMPLETE = auto()

    # Agent Events
    AGENT_START = auto()
    AGENT_COMPLETE = auto()
    AGENT_FAILURE = auto()


class FlowEventBus:
    """
    Central event bus for the flow engine.
    Thread-safe implementation for potential parallel agent usage.
    """

    _handlers: dict[FlowEvent, list[Callable]] = {}
    _lock = threading.Lock()
    _history: list[dict[str, Any]] = []

    @classmethod
    def subscribe(cls, event: FlowEvent, handler: Callable):
        """Subscribe a handler to an event."""
        with cls._lock:
            if event not in cls._handlers:
                cls._handlers[event] = []
            cls._handlers[event].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to {event.name}")

    @classmethod
    def emit(cls, event: FlowEvent, **kwargs):
        """Emit an event with payload."""
        payload = kwargs
        # Add basic metadata

        with cls._lock:
            # Record history
            cls._history.append({"event": event.name, "payload": payload})

            handlers = cls._handlers.get(event, [])

        # Execute handlers outside lock to prevent blocking/deadlocks
        if handlers:
            logger.debug(f"Emitting {event.name} to {len(handlers)} handlers")
            for handler in handlers:
                try:
                    handler(**payload)
                except Exception as e:
                    logger.error(f"Handler {handler.__name__} failed for {event.name}: {e}")

    @classmethod
    def get_history(cls) -> list[dict[str, Any]]:
        """Get event history."""
        return cls._history.copy()

    @classmethod
    def clear(cls):
        """Clear all handlers (useful for testing)."""
        with cls._lock:
            cls._handlers.clear()
            cls._history.clear()
