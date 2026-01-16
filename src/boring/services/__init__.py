"""
Services Module
Contains background services and daemons.
"""

from .notifier import configure as configure_notifications
from .notifier import done, notify

__all__ = ["notify", "done", "configure_notifications"]
