# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.pattern_mining module.
"""

import json
from datetime import datetime

import pytest

from boring.pattern_mining import Pattern, PatternMiner, get_pattern_miner

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_brain_dir(tmp_path):
    """Create a temporary brain directory."""
    brain_dir = tmp_path / ".boring_brain"
    brain_dir.mkdir()
    return brain_dir


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


# =============================================================================
# PATTERN DATACLASS TESTS
# =============================================================================


class TestPattern:
    """Tests for Pattern dataclass."""

    def test_pattern_creation(self):
        """Test Pattern creation."""
        pattern = Pattern(
            id="test_pattern",
            name="Test Pattern",
            description="Test description",
            trigger_conditions=["condition1"],
            suggested_actions=["action1"],
            success_rate=0.9,
            usage_count=5,
            last_used=datetime.now(),
        )
        assert pattern.id == "test_pattern"
        assert pattern.success_rate == 0.9
        assert pattern.usage_count == 5

    def test_pattern_defaults(self):
        """Test Pattern with default last_used."""
        pattern = Pattern(
            id="test",
            name="Test",
            description="Test",
            trigger_conditions=[],
            suggested_actions=[],
            success_rate=0.0,
            usage_count=0,
        )
        assert pattern.last_used is None


# =============================================================================
# PATTERN MINER TESTS
# =============================================================================


class TestPatternMiner:
    """Tests for PatternMiner class."""

    def test_pattern_miner_init(self, temp_brain_dir):
        """Test PatternMiner initialization."""
        miner = PatternMiner(temp_brain_dir)
        assert miner.brain_dir == temp_brain_dir
        assert len(miner.patterns) > 0  # Should have default patterns

    def test_pattern_miner_load_patterns_default(self, temp_brain_dir):
        """Test PatternMiner loads default patterns when no file exists."""
        miner = PatternMiner(temp_brain_dir)
        assert len(miner.patterns) > 0
        assert any(p.id == "new_project" for p in miner.patterns)

    def test_pattern_miner_load_patterns_from_file(self, temp_brain_dir):
        """Test PatternMiner loads patterns from file."""
        patterns_file = temp_brain_dir / "patterns.json"
        pattern_data = {
            "patterns": [
                {
                    "id": "custom_pattern",
                    "name": "Custom Pattern",
                    "description": "Custom",
                    "trigger_conditions": ["condition1"],
                    "suggested_actions": ["action1"],
                    "success_rate": 0.8,
                    "usage_count": 10,
                    "last_used": None,
                }
            ]
        }
        patterns_file.write_text(json.dumps(pattern_data))

        miner = PatternMiner(temp_brain_dir)
        assert len(miner.patterns) > 0

    def test_pattern_miner_analyze_project_state(self, temp_project):
        """Test PatternMiner.analyze_project_state method."""
        brain_dir = temp_project / ".boring_brain"
        brain_dir.mkdir()
        miner = PatternMiner(brain_dir)

        state = miner.analyze_project_state(temp_project)
        assert isinstance(state, dict)

    def test_pattern_miner_match_patterns(self, temp_project):
        """Test PatternMiner.match_patterns method."""
        brain_dir = temp_project / ".boring_brain"
        brain_dir.mkdir()
        miner = PatternMiner(brain_dir)

        state = miner.analyze_project_state(temp_project)
        matches = miner.match_patterns(state)
        assert isinstance(matches, list)

    def test_pattern_miner_suggest_next(self, temp_project):
        """Test PatternMiner.suggest_next method."""
        brain_dir = temp_project / ".boring_brain"
        brain_dir.mkdir()
        miner = PatternMiner(brain_dir)

        suggestions = miner.suggest_next(temp_project, limit=3)
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3

    def test_pattern_miner_suggest_next_limit(self, temp_project):
        """Test PatternMiner.suggest_next with different limits."""
        brain_dir = temp_project / ".boring_brain"
        brain_dir.mkdir()
        miner = PatternMiner(brain_dir)

        suggestions = miner.suggest_next(temp_project, limit=5)
        assert len(suggestions) <= 5


# =============================================================================
# MODULE FUNCTIONS TESTS
# =============================================================================


class TestGetPatternMiner:
    """Tests for get_pattern_miner function."""

    def test_get_pattern_miner(self, temp_project):
        """Test get_pattern_miner function."""
        miner = get_pattern_miner(temp_project)
        assert isinstance(miner, PatternMiner)
        assert miner.brain_dir == temp_project / ".boring_brain"
