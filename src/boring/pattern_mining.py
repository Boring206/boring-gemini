"""
Backward compatibility stub for boring.pattern_mining

This module has been moved to boring.intelligence.pattern_mining
This stub file ensures existing imports continue to work.

Migration: Change `from boring.pattern_mining import X` to `from boring.intelligence.pattern_mining import X`
"""

from boring.intelligence.pattern_mining import *  # noqa: F401, F403
from boring.intelligence.pattern_mining import (
    Pattern,
    PatternMiner,
)

__all__ = ["PatternMiner", "Pattern"]
