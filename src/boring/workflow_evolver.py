"""
Backward compatibility stub for boring.workflow_evolver

This module has been moved to boring.loop.workflow_evolver
This stub file ensures existing imports continue to work.

Migration: Change `from boring.workflow_evolver import X` to `from boring.loop.workflow_evolver import X`
"""

from boring.loop.workflow_evolver import *  # noqa: F401, F403
from boring.loop.workflow_evolver import (
    ProjectContext,
    ProjectContextDetector,
    WorkflowEvolution,
    WorkflowEvolver,
    WorkflowGap,
    WorkflowGapAnalyzer,
)

__all__ = [
    "WorkflowEvolver",
    "WorkflowEvolution",
    "ProjectContext",
    "ProjectContextDetector",
    "WorkflowGap",
    "WorkflowGapAnalyzer",
]
