"""
Backward compatibility stub for boring.vector_memory

This module has been moved to boring.intelligence.vector_memory
This stub file ensures existing imports continue to work.

Migration: Change `from boring.vector_memory import X` to `from boring.intelligence.vector_memory import X`
"""

from boring.intelligence.vector_memory import *  # noqa: F401, F403
from boring.intelligence.vector_memory import (
    Experience,
    VectorMemory,
)

__all__ = ["VectorMemory", "Experience"]
