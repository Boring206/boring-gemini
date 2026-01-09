"""
Backward compatibility stub for boring.brain_manager

This module has been moved to boring.intelligence.brain_manager
This stub file ensures existing imports continue to work.

Migration: Change `from boring.brain_manager import X` to `from boring.intelligence.brain_manager import X`
"""

from boring.intelligence.brain_manager import *  # noqa: F401, F403
from boring.intelligence.brain_manager import (
    BrainManager,
    GlobalKnowledgeStore,
    LearnedPattern,
    Rubric,
)

__all__ = ["BrainManager", "LearnedPattern", "Rubric", "GlobalKnowledgeStore"]
