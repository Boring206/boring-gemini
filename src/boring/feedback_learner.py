"""
Backward compatibility stub for boring.feedback_learner

This module has been moved to boring.intelligence.feedback_learner
This stub file ensures existing imports continue to work.

Migration: Change `from boring.feedback_learner import X` to `from boring.intelligence.feedback_learner import X`
"""

from boring.intelligence.feedback_learner import *  # noqa: F401, F403
from boring.intelligence.feedback_learner import (
    FeedbackEntry,
    FeedbackLearner,
)

__all__ = ["FeedbackLearner", "FeedbackEntry"]
