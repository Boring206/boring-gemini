"""
Type definitions for Boring Brain components.
Extracted from brain_manager.py to avoid circular imports.
"""

from dataclasses import dataclass


@dataclass
class LearnedPattern:
    """A pattern learned from successful executions."""

    pattern_id: str
    pattern_type: str  # error_solution, workflow_optimization, code_fix
    description: str
    context: str
    solution: str
    success_count: int
    created_at: str
    last_used: str
    # V10.23: Enhanced fields
    decay_score: float = 1.0  # Relevance decay over time
    session_boost: float = 0.0  # Temporary boost from current session
    cluster_id: str = ""  # For pattern clustering


@dataclass
class Rubric:
    """Evaluation rubric for quality assessment."""

    name: str
    description: str
    criteria: list[dict[str, str]]
    created_at: str
