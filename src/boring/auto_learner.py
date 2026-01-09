"""
Backward compatibility stub for boring.auto_learner

This module has been moved to boring.intelligence.auto_learner
This stub file ensures existing imports continue to work.

Migration: Change `from boring.auto_learner import X` to `from boring.intelligence.auto_learner import X`
"""

from boring.intelligence.auto_learner import *  # noqa: F401, F403
from boring.intelligence.auto_learner import (
    AutoLearner,
    ErrorSolutionPair,
)

__all__ = ["AutoLearner", "ErrorSolutionPair"]
