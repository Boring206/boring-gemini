"""
Backward compatibility stub for boring.background_agent

This module has been moved to boring.loop.background_agent
This stub file ensures existing imports continue to work.

Migration: Change `from boring.background_agent import X` to `from boring.loop.background_agent import X`
"""

from boring.loop.background_agent import *  # noqa: F401, F403
from boring.loop.background_agent import (
    BackgroundTask,
    BackgroundTaskRunner,
)

__all__ = ["BackgroundTaskRunner", "BackgroundTask"]
