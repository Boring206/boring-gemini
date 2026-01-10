# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Tests for boring.paths module - Unified path management.
"""

import warnings
from pathlib import Path

import pytest

from boring.paths import (
    BORING_ROOT,
    BoringPaths,
    check_needs_migration,
    get_boring_path,
    get_boring_root,
    get_migration_plan,
    get_state_file,
)


class TestGetBoringRoot:
    """Tests for get_boring_root function."""

    def test_returns_boring_directory(self, tmp_path: Path):
        """Should return .boring directory path."""
        result = get_boring_root(tmp_path)
        assert result == tmp_path / BORING_ROOT
        assert result.name == ".boring"


class TestGetBoringPath:
    """Tests for get_boring_path function."""

    def test_creates_new_path_when_nothing_exists(self, tmp_path: Path):
        """Should create new .boring/memory when neither exists."""
        result = get_boring_path(tmp_path, "memory", create=True, warn_legacy=False)
        assert result == tmp_path / ".boring" / "memory"
        assert result.exists()

    def test_uses_new_path_when_exists(self, tmp_path: Path):
        """Should use new path when it exists."""
        new_path = tmp_path / ".boring" / "brain"
        new_path.mkdir(parents=True)

        result = get_boring_path(tmp_path, "brain", create=False, warn_legacy=True)
        assert result == new_path

    def test_falls_back_to_legacy_path(self, tmp_path: Path):
        """Should fallback to legacy path when new doesn't exist."""
        legacy_path = tmp_path / ".boring_memory"
        legacy_path.mkdir()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = get_boring_path(tmp_path, "memory", create=False, warn_legacy=True)

        assert result == legacy_path
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

    def test_prefers_new_over_legacy(self, tmp_path: Path):
        """Should prefer new path when both exist."""
        new_path = tmp_path / ".boring" / "cache"
        new_path.mkdir(parents=True)
        legacy_path = tmp_path / ".boring_cache"
        legacy_path.mkdir()

        result = get_boring_path(tmp_path, "cache", create=False, warn_legacy=True)
        assert result == new_path

    def test_raises_for_unknown_subdir(self, tmp_path: Path):
        """Should raise ValueError for unknown subdirectory."""
        with pytest.raises(ValueError, match="Unknown subdir"):
            get_boring_path(tmp_path, "invalid_subdir")

    def test_no_warning_when_disabled(self, tmp_path: Path):
        """Should not warn when warn_legacy=False."""
        legacy_path = tmp_path / ".boring_brain"
        legacy_path.mkdir()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_boring_path(tmp_path, "brain", create=False, warn_legacy=False)

        assert len(w) == 0


class TestGetStateFile:
    """Tests for get_state_file function."""

    def test_returns_new_location_for_new_projects(self, tmp_path: Path):
        """Should return state dir path for new projects."""
        result = get_state_file(tmp_path, "call_count", create_dir=True)
        assert result == tmp_path / ".boring" / "state" / "call_count"

    def test_finds_legacy_state_file(self, tmp_path: Path):
        """Should find legacy state file in project root."""
        legacy_file = tmp_path / ".call_count"
        legacy_file.write_text("5")

        result = get_state_file(tmp_path, "call_count", create_dir=False)
        assert result == legacy_file

    def test_strips_leading_dot(self, tmp_path: Path):
        """Should handle filenames with or without leading dot."""
        result1 = get_state_file(tmp_path, ".call_count", create_dir=True)
        result2 = get_state_file(tmp_path, "call_count", create_dir=True)
        assert result1 == result2


class TestBoringPaths:
    """Tests for BoringPaths class."""

    def test_all_properties(self, tmp_path: Path):
        """Should provide all path properties."""
        paths = BoringPaths(tmp_path, create=True)

        assert paths.root == tmp_path / ".boring"
        assert paths.memory == tmp_path / ".boring" / "memory"
        assert paths.brain == tmp_path / ".boring" / "brain"
        assert paths.cache == tmp_path / ".boring" / "cache"
        assert paths.backups == tmp_path / ".boring" / "backups"
        assert paths.state == tmp_path / ".boring" / "state"

    def test_convenience_methods(self, tmp_path: Path):
        """Should provide convenience methods."""
        paths = BoringPaths(tmp_path, create=True)

        assert paths.get_rag_db() == tmp_path / ".boring" / "memory" / "rag_db"
        assert paths.get_sessions_dir() == tmp_path / ".boring" / "memory" / "sessions"
        assert (
            paths.get_patterns_file()
            == tmp_path / ".boring" / "brain" / "learned_patterns" / "patterns.json"
        )
        assert paths.get_rubrics_dir() == tmp_path / ".boring" / "brain" / "rubrics"


class TestMigrationUtilities:
    """Tests for migration helper functions."""

    def test_check_needs_migration_empty(self, tmp_path: Path):
        """Should return all False for empty project."""
        result = check_needs_migration(tmp_path)
        assert all(not v for v in result.values())

    def test_check_needs_migration_with_legacy(self, tmp_path: Path):
        """Should detect legacy directories needing migration."""
        (tmp_path / ".boring_memory").mkdir()
        (tmp_path / ".boring_brain").mkdir()

        result = check_needs_migration(tmp_path)
        assert result["memory"] is True
        assert result["brain"] is True
        assert result["cache"] is False

    def test_get_migration_plan(self, tmp_path: Path):
        """Should generate migration plan for legacy directories."""
        (tmp_path / ".boring_memory").mkdir()
        (tmp_path / ".call_count").write_text("10")

        plan = get_migration_plan(tmp_path)
        assert len(plan) == 2

        sources = [str(p[0]) for p in plan]
        assert any(".boring_memory" in s for s in sources)
        assert any(".call_count" in s for s in sources)
