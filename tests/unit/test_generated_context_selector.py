# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.context_selector module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from boring.context_selector import ContextSelection, ContextSelector, FileScore


@pytest.fixture(autouse=True)
def mock_log_status():
    """Mock log_status for all tests."""
    with patch("boring.context_selector.log_status"):
        yield


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "tests").mkdir()
    return project


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestFileScore:
    """Tests for FileScore dataclass."""

    def test_file_score_creation(self):
        """Test FileScore creation."""
        score = FileScore(path=Path("test.py"), score=0.5, reasons=["keyword match"])
        assert score.path == Path("test.py")
        assert score.score == 0.5
        assert len(score.reasons) == 1


class TestContextSelection:
    """Tests for ContextSelection dataclass."""

    def test_context_selection_creation(self):
        """Test ContextSelection creation."""
        selection = ContextSelection(
            files=[Path("file1.py"), Path("file2.py")],
            total_tokens=1000,
            content="file content",
        )
        assert len(selection.files) == 2
        assert selection.total_tokens == 1000
        assert selection.content == "file content"


# =============================================================================
# CONTEXT SELECTOR TESTS
# =============================================================================


class TestContextSelector:
    """Tests for ContextSelector class."""

    def test_context_selector_init(self, temp_project):
        """Test ContextSelector initialization."""
        selector = ContextSelector(temp_project)
        assert selector.project_root == temp_project
        assert isinstance(selector.include_extensions, set)
        assert isinstance(selector.exclude_dirs, set)

    def test_context_selector_init_with_log_dir(self, temp_project):
        """Test ContextSelector with custom log directory."""
        log_dir = temp_project / "custom_logs"
        selector = ContextSelector(temp_project, log_dir=log_dir)
        assert selector.log_dir == log_dir

    def test_context_selector_init_with_max_file_size(self, temp_project):
        """Test ContextSelector with custom max file size."""
        selector = ContextSelector(temp_project, max_file_size=100000)
        assert selector.max_file_size == 100000

    def test_context_selector_extract_keywords(self, temp_project):
        """Test extract_keywords method."""
        selector = ContextSelector(temp_project)
        text = "This is a test about authentication and user management"
        keywords = selector.extract_keywords(text)
        assert isinstance(keywords, set)
        assert "authentication" in keywords or "user" in keywords or "management" in keywords

    def test_context_selector_extract_keywords_empty(self, temp_project):
        """Test extract_keywords with empty text."""
        selector = ContextSelector(temp_project)
        keywords = selector.extract_keywords("")
        assert keywords == set()

    def test_context_selector_extract_keywords_stop_words(self, temp_project):
        """Test extract_keywords filters stop words."""
        selector = ContextSelector(temp_project)
        text = "the a an is are"
        keywords = selector.extract_keywords(text)
        # Should filter out common stop words
        assert "the" not in keywords or len(keywords) == 0

    def test_context_selector_score_file(self, temp_project):
        """Test score_file method."""
        selector = ContextSelector(temp_project)
        test_file = temp_project / "test.py"
        test_file.write_text("def authenticate_user(): pass")

        keywords = {"authenticate", "user"}
        score = selector.score_file(test_file, keywords)
        assert isinstance(score, FileScore)
        assert score.path == test_file
        assert score.score >= 0

    def test_context_selector_score_file_nonexistent(self, temp_project):
        """Test score_file with nonexistent file."""
        selector = ContextSelector(temp_project)
        nonexistent = temp_project / "nonexistent.py"

        keywords = {"test"}
        score = selector.score_file(nonexistent, keywords)
        assert score.score == 0.0

    def test_context_selector_get_project_files(self, temp_project):
        """Test get_project_files method."""
        (temp_project / "src" / "file1.py").write_text("print('test')")
        (temp_project / "src" / "file2.js").write_text("console.log('test')")
        (temp_project / "tests" / "test_file.py").write_text("def test(): pass")

        selector = ContextSelector(temp_project)
        files = selector.get_project_files()
        assert len(files) >= 3
        assert all(f.suffix in selector.include_extensions for f in files)

    def test_context_selector_get_project_files_excludes(self, temp_project):
        """Test get_project_files excludes certain directories."""
        (temp_project / ".git").mkdir()
        (temp_project / ".git" / "config").write_text("git config")
        (temp_project / "__pycache__").mkdir()
        (temp_project / "__pycache__" / "file.pyc").write_bytes(b"binary")
        (temp_project / "src" / "file.py").write_text("print('test')")

        selector = ContextSelector(temp_project)
        files = selector.get_project_files()
        # Should exclude .git and __pycache__
        assert not any(".git" in str(f) for f in files)
        assert not any("__pycache__" in str(f) for f in files)

    def test_context_selector_select_files(self, temp_project):
        """Test select_files method."""
        (temp_project / "src" / "auth.py").write_text("def authenticate(): pass")
        (temp_project / "src" / "user.py").write_text("class User: pass")
        (temp_project / "src" / "other.py").write_text("def other(): pass")

        selector = ContextSelector(temp_project)
        files = selector.select_files("authenticate user", max_files=2)
        assert len(files) <= 2
        assert all(isinstance(f, FileScore) for f in files)
        assert all(isinstance(f.path, Path) for f in files)

    def test_context_selector_select_context(self, temp_project):
        """Test select_context method."""
        (temp_project / "src" / "auth.py").write_text("def authenticate(): pass")
        (temp_project / "PROMPT.md").write_text("Implement user authentication")

        selector = ContextSelector(temp_project)
        # We need to extract keywords that match the file content
        # auth.py has "authenticate"
        # Prompt has "Implement user authentication" -> "authentication"
        # "authentication" contains "auth"? No.
        # But score_file uses regex.
        # Let's verify what keywords context_selector extracts.
        # It expands camel/snake case.
        # Use "auth" to match filename "auth.py" which gives score 2.0 > 0.5
        context = selector.select_context("auth", max_tokens=1000)
        assert isinstance(context, ContextSelection)
        assert len(context.files) > 0
        assert context.total_tokens > 0
        assert len(context.content) > 0

    def test_context_selector_select_context_empty_prompt(self, temp_project):
        """Test select_context with empty prompt."""
        selector = ContextSelector(temp_project)
        context = selector.select_context("", max_tokens=1000)
        assert isinstance(context, ContextSelection)
        # May return empty or default files

    def test_context_selector_generate_context_injection(self, temp_project):
        """Test generate_context_injection method."""
        (temp_project / "src" / "file.py").write_text("def test(): pass")

        selector = ContextSelector(temp_project)
        injection = selector.generate_context_injection("test prompt")
        assert isinstance(injection, str)
        # Should contain context information
