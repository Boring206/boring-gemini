"""
Boring Loop State Machine V10.26

A refactored, state-pattern-based agent loop with clear separation of concerns.

Module Structure:
- base.py: LoopState ABC and utilities
- context.py: LoopContext shared state
- states/: Individual state implementations
- agent.py: StatefulAgentLoop context class

V10.26 Reorganization:
- shadow_mode: Human-in-the-loop protection (moved from root)
- workflow_manager: Workflow package management (moved from root)
- workflow_evolver: Dynamic workflow evolution (moved from root)
- background_agent: Async task execution (moved from root)
- transactions: Git-based snapshot/rollback (moved from root)
"""

from .agent import StatefulAgentLoop
from .background_agent import BackgroundTask, BackgroundTaskRunner
from .base import LoopState
from .context import LoopContext
from .legacy import AgentLoop

# V10.26 Reorganized Modules (moved from root)
from .shadow_mode import (
    OperationSeverity,
    PendingOperation,
    ShadowModeGuard,
    ShadowModeLevel,
    create_shadow_guard,
)
from .transactions import TransactionManager, TransactionState
from .workflow_evolver import ProjectContext, ProjectContextDetector, WorkflowEvolver
from .workflow_manager import WorkflowManager, WorkflowMetadata, WorkflowPackage

__all__ = [
    # Core Loop
    "StatefulAgentLoop",
    "LoopContext",
    "LoopState",
    "AgentLoop",
    # V10.26 Reorganized
    "ShadowModeGuard",
    "ShadowModeLevel",
    "OperationSeverity",
    "PendingOperation",
    "create_shadow_guard",
    "WorkflowManager",
    "WorkflowPackage",
    "WorkflowMetadata",
    "WorkflowEvolver",
    "ProjectContext",
    "ProjectContextDetector",
    "BackgroundTaskRunner",
    "BackgroundTask",
    "TransactionManager",
    "TransactionState",
]
