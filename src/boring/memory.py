"""
Backward compatibility stub for boring.memory

This module has been moved to boring.intelligence.memory
This stub file ensures existing imports continue to work.

Migration: Change `from boring.memory import X` to `from boring.intelligence.memory import X`
"""

from boring.intelligence.memory import *  # noqa: F401, F403
from boring.intelligence.memory import (
    LoopMemory,
    MemoryManager,
    ProjectMemory,
)

__all__ = ["MemoryManager", "LoopMemory", "ProjectMemory"]
