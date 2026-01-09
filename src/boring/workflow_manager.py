"""
Backward compatibility stub for boring.workflow_manager

This module has been moved to boring.loop.workflow_manager
This stub file ensures existing imports continue to work.

Migration: Change `from boring.workflow_manager import X` to `from boring.loop.workflow_manager import X`
"""

from boring.loop.workflow_manager import *  # noqa: F401, F403
from boring.loop.workflow_manager import (
    WorkflowManager,
    WorkflowMetadata,
    WorkflowPackage,
)

__all__ = ["WorkflowManager", "WorkflowMetadata", "WorkflowPackage"]
