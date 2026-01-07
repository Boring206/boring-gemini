# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.quality_tracker module.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from boring.quality_tracker import QualityEntry, QualityTracker

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


# =============================================================================
# QUALITY ENTRY TESTS
# =============================================================================


class TestQualityEntry:
    """Tests for QualityEntry dataclass."""

    def test_quality_entry_creation(self):
        """Test QualityEntry creation."""
        entry = QualityEntry(
            timestamp=1000.0,
            date="2024-01-01 00:00:00",
            score=4.5,
            issues_count=2,
            commit_hash="abc123",
            context="manual",
        )
        assert entry.timestamp == 1000.0
        assert entry.score == 4.5
        assert entry.issues_count == 2

    def test_quality_entry_defaults(self):
        """Test QualityEntry with default values."""
        entry = QualityEntry(
            timestamp=1000.0,
            date="2024-01-01 00:00:00",
            score=3.0,
            issues_count=0,
        )
        assert entry.commit_hash is None
        assert entry.context == ""


# =============================================================================
# QUALITY TRACKER TESTS
# =============================================================================


class TestQualityTracker:
    """Tests for QualityTracker class."""

    def test_quality_tracker_init(self, temp_project):
        """Test QualityTracker initialization."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)
            assert tracker.project_root == temp_project
            assert tracker.history_file.exists() or tracker.brain_dir.exists()

    def test_quality_tracker_init_default_root(self, tmp_path):
        """Test QualityTracker with default project root."""
        default_root = tmp_path / "default"
        default_root.mkdir()
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = default_root
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker()
            assert tracker.project_root == default_root

    def test_quality_tracker_record(self, temp_project):
        """Test recording a quality entry."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)
            tracker.record(score=4.5, issues_count=2, context="test")

            assert tracker.history_file.exists()
            history = json.loads(tracker.history_file.read_text())
            assert len(history) == 1
            assert history[0]["score"] == 4.5

    def test_quality_tracker_record_multiple(self, temp_project):
        """Test recording multiple entries."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)

            for i in range(5):
                tracker.record(score=float(i), issues_count=i)

            history = json.loads(tracker.history_file.read_text())
            assert len(history) == 5

    def test_quality_tracker_record_limit(self, temp_project):
        """Test that history is limited to 100 entries."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)

            # Record more than 100 entries
            for _i in range(105):
                tracker.record(score=3.0, issues_count=0)

            history = json.loads(tracker.history_file.read_text())
            assert len(history) == 100

    def test_quality_tracker_get_trend(self, temp_project):
        """Test get_trend method."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)

            for i in range(10):
                tracker.record(score=float(i), issues_count=0)

            trend = tracker.get_trend(limit=5)
            assert len(trend) == 5

    def test_quality_tracker_get_trend_empty(self, temp_project):
        """Test get_trend with no history."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)

            trend = tracker.get_trend()
            assert trend == []

    def test_quality_tracker_render_ascii_chart(self, temp_project):
        """Test render_ascii_chart."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)

            for i in range(10):
                tracker.record(score=float(i % 5), issues_count=0)

            chart = tracker.render_ascii_chart()
            assert isinstance(chart, str)
            assert "Quality Trend" in chart

    def test_quality_tracker_render_ascii_chart_empty(self, temp_project):
        """Test render_ascii_chart with no history."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)

            chart = tracker.render_ascii_chart()
            assert "No quality history" in chart

    def test_quality_tracker_render_ascii_chart_custom_size(self, temp_project):
        """Test render_ascii_chart with custom dimensions."""
        with patch("boring.quality_tracker.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = ".boring_brain"
            tracker = QualityTracker(temp_project)

            tracker.record(score=3.0, issues_count=0)
            chart = tracker.render_ascii_chart(width=40, height=5)
            assert isinstance(chart, str)
