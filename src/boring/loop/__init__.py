"""
Boring Loop State Machine

A refactored, state-pattern-based agent loop with clear separation of concerns.

Module Structure:
- base.py: LoopState ABC and utilities
- context.py: LoopContext shared state
- states/: Individual state implementations
- agent.py: StatefulAgentLoop context class
"""

from .agent import StatefulAgentLoop
from .context import LoopContext
from .base import LoopState
from .legacy import AgentLoop

__all__ = ["StatefulAgentLoop", "LoopContext", "LoopState", "AgentLoop"]
