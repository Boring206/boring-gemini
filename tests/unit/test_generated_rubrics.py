# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.rubrics module.
"""

from unittest.mock import patch

from boring.rubrics import Criterion, Rubric, get_rubric, list_rubrics

# =============================================================================
# CRITERION TESTS
# =============================================================================


class TestCriterion:
    """Tests for Criterion class."""

    def test_criterion_creation(self):
        """Test Criterion creation."""
        criterion = Criterion(
            name="test_criterion",
            description="Test description",
            weight=1.0,
        )
        assert criterion.name == "test_criterion"
        assert criterion.description == "Test description"
        assert criterion.weight == 1.0


# =============================================================================
# RUBRIC TESTS
# =============================================================================


class TestRubric:
    """Tests for Rubric class."""

    def test_rubric_creation(self):
        """Test Rubric creation."""
        rubric = Rubric(
            name="test_rubric",
            description="Test rubric",
            criteria=[],
        )
        assert rubric.name == "test_rubric"
        assert rubric.description == "Test rubric"
        assert rubric.criteria == []

    def test_rubric_with_criteria(self):
        """Test Rubric with criteria."""
        criteria = [
            Criterion(name="criterion1", description="Desc1", weight=1.0),
            Criterion(name="criterion2", description="Desc2", weight=2.0),
        ]
        rubric = Rubric(
            name="test",
            description="Test",
            criteria=criteria,
        )
        assert len(rubric.criteria) == 2


# =============================================================================
# RUBRIC FUNCTIONS TESTS
# =============================================================================


class TestRubricFunctions:
    """Tests for rubric functions."""

    def test_get_rubric(self):
        """Test get_rubric function."""
        with patch(
            "boring.judge.rubrics.RUBRIC_REGISTRY",
            {"test": Rubric(name="test", description="Test", criteria=[])},
        ):
            rubric = get_rubric("test")
            assert rubric is not None
            assert rubric.name == "test"

    def test_get_rubric_not_found(self):
        """Test get_rubric with nonexistent rubric."""
        with patch("boring.judge.rubrics.RUBRIC_REGISTRY", {}):
            rubric = get_rubric("nonexistent")
            assert rubric is None

    def test_list_rubrics(self):
        """Test list_rubrics function."""
        with patch("boring.judge.rubrics.RUBRIC_REGISTRY", {"rubric1": None, "rubric2": None}):
            rubrics = list_rubrics()
            assert len(rubrics) == 2
            assert "rubric1" in rubrics
            assert "rubric2" in rubrics

    def test_list_rubrics_empty(self):
        """Test list_rubrics with no rubrics."""
        with patch("boring.judge.rubrics.RUBRIC_REGISTRY", {}):
            rubrics = list_rubrics()
            assert rubrics == []
