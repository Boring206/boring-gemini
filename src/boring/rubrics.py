"""
Backward compatibility stub for boring.rubrics

This module has been moved to boring.judge.rubrics
This stub file ensures existing imports continue to work.

Migration: Change `from boring.rubrics import X` to `from boring.judge.rubrics import X`
"""

from boring.judge.rubrics import *  # noqa: F401, F403
from boring.judge.rubrics import (
    API_DESIGN_RUBRIC,
    ARCHITECTURE_RUBRIC,
    CODE_QUALITY_RUBRIC,
    DOCUMENTATION_RUBRIC,
    IMPLEMENTATION_PLAN_RUBRIC,
    PERFORMANCE_RUBRIC,
    PRODUCTION_RUBRIC,
    RUBRIC_REGISTRY,
    SECURITY_RUBRIC,
    TESTING_RUBRIC,
    Criterion,
    Rubric,
    get_rubric,
    list_rubrics,
)

__all__ = [
    "Rubric",
    "Criterion",
    "CODE_QUALITY_RUBRIC",
    "SECURITY_RUBRIC",
    "PERFORMANCE_RUBRIC",
    "ARCHITECTURE_RUBRIC",
    "IMPLEMENTATION_PLAN_RUBRIC",
    "TESTING_RUBRIC",
    "DOCUMENTATION_RUBRIC",
    "API_DESIGN_RUBRIC",
    "PRODUCTION_RUBRIC",
    "RUBRIC_REGISTRY",
    "get_rubric",
    "list_rubrics",
]
