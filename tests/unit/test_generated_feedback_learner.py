# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.feedback_learner module.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from boring.feedback_learner import FeedbackEntry, FeedbackLearner

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
# DATACLASS TESTS
# =============================================================================


class TestFeedbackEntry:
    """Tests for FeedbackEntry dataclass."""

    def test_feedback_entry_creation(self):
        """Test FeedbackEntry creation."""
        entry = FeedbackEntry(
            timestamp=1234567890.0,
            date="2024-01-01 12:00:00",
            review_id="review_123",
            verdict="NEEDS_WORK",
            issues=["issue1", "issue2"],
            fix_applied=True,
            fix_successful=True,
            code_hash="abc123",
            pattern_type="security",
            context="test context",
        )
        assert entry.review_id == "review_123"
        assert entry.verdict == "NEEDS_WORK"
        assert len(entry.issues) == 2
        assert entry.fix_applied is True

    def test_feedback_entry_defaults(self):
        """Test FeedbackEntry with default context."""
        entry = FeedbackEntry(
            timestamp=1234567890.0,
            date="2024-01-01 12:00:00",
            review_id="review_123",
            verdict="PASS",
            issues=[],
            fix_applied=False,
            fix_successful=False,
            code_hash="",
            pattern_type="general",
        )
        assert entry.context == ""


# =============================================================================
# FEEDBACK LEARNER TESTS
# =============================================================================


class TestFeedbackLearner:
    """Tests for FeedbackLearner class."""

    def test_feedback_learner_init(self, temp_project):
        """Test FeedbackLearner initialization."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)
            assert learner.project_root == temp_project

    def test_feedback_learner_init_default_root(self):
        """Test FeedbackLearner with default project root."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner()
            assert learner.project_root == Path("/default")

    def test_feedback_learner_record_review(self, temp_project):
        """Test FeedbackLearner.record_review method."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review(
                review_id="review_1",
                verdict="NEEDS_WORK",
                issues=["issue1"],
            )

            feedback_file = temp_project / ".boring" / "review_feedback.json"
            assert feedback_file.exists()
            data = json.loads(feedback_file.read_text())
            assert len(data) == 1
            assert data[0]["review_id"] == "review_1"

    def test_feedback_learner_record_review_with_all_params(self, temp_project):
        """Test FeedbackLearner.record_review with all parameters."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review(
                review_id="review_2",
                verdict="REJECT",
                issues=["issue1", "issue2"],
                code_hash="hash123",
                pattern_type="security",
                context="test context",
            )

            feedback_file = temp_project / ".boring" / "review_feedback.json"
            data = json.loads(feedback_file.read_text())
            assert data[0]["pattern_type"] == "security"
            assert data[0]["code_hash"] == "hash123"

    def test_feedback_learner_record_fix(self, temp_project):
        """Test FeedbackLearner.record_fix method."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review("review_1", "NEEDS_WORK", ["issue1"])
            learner.record_fix("review_1", success=True)

            feedback_file = temp_project / ".boring" / "review_feedback.json"
            data = json.loads(feedback_file.read_text())
            assert data[0]["fix_applied"] is True
            assert data[0]["fix_successful"] is True

    def test_feedback_learner_record_fix_failure(self, temp_project):
        """Test FeedbackLearner.record_fix with failure."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review("review_1", "NEEDS_WORK", ["issue1"])
            learner.record_fix("review_1", success=False)

            feedback_file = temp_project / ".boring" / "review_feedback.json"
            data = json.loads(feedback_file.read_text())
            assert data[0]["fix_successful"] is False

    def test_feedback_learner_get_suggestions(self, temp_project):
        """Test FeedbackLearner.get_suggestions method."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review("review_1", "NEEDS_WORK", ["issue1", "issue2"])
            learner.record_review("review_2", "NEEDS_WORK", ["issue1"])

            suggestions = learner.get_suggestions("test.py", limit=5)
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0

    def test_feedback_learner_get_suggestions_limit(self, temp_project):
        """Test FeedbackLearner.get_suggestions with limit."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            for i in range(10):
                learner.record_review(f"review_{i}", "NEEDS_WORK", [f"issue{i}"])

            suggestions = learner.get_suggestions("test.py", limit=3)
            assert len(suggestions) <= 3

    def test_feedback_learner_get_fix_success_rate(self, temp_project):
        """Test FeedbackLearner.get_fix_success_rate method."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review("review_1", "NEEDS_WORK", ["issue1"], pattern_type="security")
            learner.record_fix("review_1", success=True)

            rates = learner.get_fix_success_rate()
            assert isinstance(rates, dict)
            assert "security" in rates or "general" in rates

    def test_feedback_learner_get_fix_success_rate_by_pattern(self, temp_project):
        """Test FeedbackLearner.get_fix_success_rate with pattern filter."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review("review_1", "NEEDS_WORK", ["issue1"], pattern_type="security")
            learner.record_fix("review_1", success=True)

            rates = learner.get_fix_success_rate(pattern_type="security")
            assert isinstance(rates, dict)

    def test_feedback_learner_get_recurring_issues(self, temp_project):
        """Test FeedbackLearner.get_recurring_issues method."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            # Create recurring issue
            for i in range(5):
                learner.record_review(f"review_{i}", "NEEDS_WORK", ["same issue"])

            recurring = learner.get_recurring_issues(min_occurrences=3)
            assert isinstance(recurring, list)
            assert len(recurring) > 0

    def test_feedback_learner_get_recurring_issues_min_occurrences(self, temp_project):
        """Test FeedbackLearner.get_recurring_issues with min_occurrences."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            learner.record_review("review_1", "NEEDS_WORK", ["issue1"])

            recurring = learner.get_recurring_issues(min_occurrences=3)
            assert len(recurring) == 0  # Only 1 occurrence, need 3

    def test_feedback_learner_load_history_empty(self, temp_project):
        """Test FeedbackLearner._load_history with no file."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            history = learner._load_history()
            assert history == []

    def test_feedback_learner_load_history_corrupted(self, temp_project):
        """Test FeedbackLearner._load_history with corrupted file."""
        with patch("boring.feedback_learner.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BRAIN_DIR = Path(".boring")
            learner = FeedbackLearner(temp_project)

            feedback_file = temp_project / ".boring" / "review_feedback.json"
            feedback_file.write_text("invalid json")

            history = learner._load_history()
            assert history == []
