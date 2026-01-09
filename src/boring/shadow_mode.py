"""
Backward compatibility stub for boring.shadow_mode

This module has been moved to boring.loop.shadow_mode
This stub file ensures existing imports continue to work.

Migration: Change `from boring.shadow_mode import X` to `from boring.loop.shadow_mode import X`
"""

from boring.loop.shadow_mode import *  # noqa: F401, F403
from boring.loop.shadow_mode import (
    OperationSeverity,
    PendingOperation,
    ShadowModeGuard,
    ShadowModeLevel,
)

__all__ = ["ShadowModeLevel", "ShadowModeGuard", "OperationSeverity", "PendingOperation"]
