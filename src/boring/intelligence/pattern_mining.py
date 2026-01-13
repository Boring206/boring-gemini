# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Pattern Mining Module - Compatibility Layer for V10.26+

This module provides backward compatibility for the pattern mining interface
that was previously in boring/pattern_mining.py.

The actual pattern mining functionality is now handled by:
- intelligence/pattern_clustering.py (PatternClusterer)
- intelligence/brain_manager.py (BrainManager)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .pattern_clustering import get_pattern_clusterer


@dataclass
class Pattern:
    """Backward-compatible Pattern class."""

    description: str
    context: str
    solution: str
    success_count: int = 0
    pattern_type: str = "general"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "context": self.context,
            "solution": self.solution,
            "success_count": self.success_count,
            "pattern_type": self.pattern_type,
        }


class PatternMiner:
    """
    Backward-compatible PatternMiner class.

    Provides suggest_next and analyze_project_state methods
    that were used by assistant.py.
    """

    def __init__(self, project_root: Path):
        """
        Initialize pattern miner.

        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root)
        self.clusterer = get_pattern_clusterer()

    def suggest_next(self, project_root: Path, limit: int = 3) -> list[dict]:
        """
        Suggest next actions based on patterns.

        This is a simplified version that returns empty suggestions
        since the original module was deleted.

        Args:
            project_root: Project root path
            limit: Maximum suggestions

        Returns:
            List of suggestion dicts
        """
        # Return empty list - suggestions are now handled by
        # - BrainManager.get_relevant_patterns()
        # - _check_* functions in assistant.py
        return []

    def analyze_project_state(self, project_root: Path) -> dict:
        """
        Analyze project state.

        Returns basic project state info.

        Args:
            project_root: Project root path

        Returns:
            Dict with project state
        """
        project_root = Path(project_root)

        state = {
            "has_git": (project_root / ".git").exists(),
            "has_boring_memory": (project_root / ".boring_memory").exists(),
            "has_workflows": (project_root / ".agent" / "workflows").exists(),
            "has_brain": (project_root / ".boring" / "brain").exists(),
        }

        # Count patterns if brain exists
        brain_dir = project_root / ".boring" / "brain"
        if brain_dir.exists():
            patterns_file = brain_dir / "patterns.json"
            if patterns_file.exists():
                try:
                    import json

                    patterns = json.loads(patterns_file.read_text(encoding="utf-8"))
                    state["pattern_count"] = len(patterns)
                except Exception:
                    state["pattern_count"] = 0
            else:
                state["pattern_count"] = 0

        return state


# Singleton
_pattern_miner: Optional[PatternMiner] = None
_current_project_root: Optional[Path] = None


def get_pattern_miner(project_root: Any) -> PatternMiner:
    """
    Get or create pattern miner singleton.

    Args:
        project_root: Project root path

    Returns:
        PatternMiner instance
    """
    global _pattern_miner, _current_project_root

    project_root = Path(project_root) if project_root else None

    if _pattern_miner is None or project_root != _current_project_root:
        _pattern_miner = PatternMiner(project_root)
        _current_project_root = project_root

    return _pattern_miner


def clear_pattern_miner_cache():
    """
    Clear pattern miner cache.

    No-op for compatibility shim.
    """
    global _pattern_miner
    _pattern_miner = None
