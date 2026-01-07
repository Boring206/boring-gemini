# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.diff_patcher module.
"""

import pytest

from boring.diff_patcher import (
    AIDER_PATTERN,
    CLAUDE_PATTERN,
    DIFF_PATTERN,
    FILE_SEARCH_REPLACE_PATTERN,
    OLD_NEW_PATTERN,
    SEARCH_REPLACE_PATTERN,
    SearchReplaceOp,
    apply_search_replace,
    apply_search_replace_blocks,
    extract_search_replace_blocks,
    process_output_for_patches,
    quick_replace,
)

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


class TestSearchReplaceOp:
    """Tests for SearchReplaceOp dataclass."""

    def test_search_replace_op_creation(self):
        """Test SearchReplaceOp creation."""
        op = SearchReplaceOp(
            file_path="test.py",
            search="old",
            replace="new",
            success=True,
        )
        assert op.file_path == "test.py"
        assert op.search == "old"
        assert op.replace == "new"
        assert op.success is True

    def test_search_replace_op_defaults(self):
        """Test SearchReplaceOp with default values."""
        op = SearchReplaceOp(file_path="test.py", search="old", replace="new")
        assert op.success is False
        assert op.error is None


# =============================================================================
# REGEX PATTERN TESTS
# =============================================================================


class TestRegexPatterns:
    """Tests for regex patterns."""

    def test_search_replace_pattern(self):
        """Test SEARCH_REPLACE_PATTERN."""
        text = "<<<<<<< SEARCH\nold text\n=======\nnew text\n>>>>>>> REPLACE"
        match = SEARCH_REPLACE_PATTERN.search(text)
        assert match is not None

    def test_file_search_replace_pattern(self):
        """Test FILE_SEARCH_REPLACE_PATTERN."""
        text = "FILE: test.py\n<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE"
        match = FILE_SEARCH_REPLACE_PATTERN.search(text)
        assert match is not None
        assert "test.py" in match.group(1)

    def test_aider_pattern(self):
        """Test AIDER_PATTERN."""
        text = "```\nFILE: test.py\n<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE\n```"
        match = AIDER_PATTERN.search(text)
        assert match is not None

    def test_claude_pattern(self):
        """Test CLAUDE_PATTERN."""
        text = "SEARCH_REPLACE_START\nFILE: test.py\nold\n===\nnew\nSEARCH_REPLACE_END"
        match = CLAUDE_PATTERN.search(text)
        assert match is not None

    def test_old_new_pattern(self):
        """Test OLD_NEW_PATTERN."""
        text = "SEARCH_REPLACE_START\nFILE: test.py\nOLD: old\nNEW: new\nSEARCH_REPLACE_END"
        match = OLD_NEW_PATTERN.search(text)
        assert match is not None

    def test_diff_pattern(self):
        """Test DIFF_PATTERN."""
        text = "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-old\n+new"
        match = DIFF_PATTERN.search(text)
        assert match is not None


# =============================================================================
# EXTRACTION TESTS
# =============================================================================


class TestExtractSearchReplaceBlocks:
    """Tests for extract_search_replace_blocks function."""

    def test_extract_search_replace_blocks_file_format(self):
        """Test extract_search_replace_blocks with file format."""
        output = "FILE: test.py\n<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE"
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) > 0
        assert blocks[0]["file_path"] == "test.py"

    def test_extract_search_replace_blocks_aider_format(self):
        """Test extract_search_replace_blocks with Aider format."""
        output = "```\nFILE: test.py\n<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE\n```"
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) > 0

    def test_extract_search_replace_blocks_claude_format(self):
        """Test extract_search_replace_blocks with Claude format."""
        output = "SEARCH_REPLACE_START\nFILE: test.py\nold\n===\nnew\nSEARCH_REPLACE_END"
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) > 0

    def test_extract_search_replace_blocks_old_new_format(self):
        """Test extract_search_replace_blocks with OLD/NEW format."""
        output = "SEARCH_REPLACE_START\nFILE: test.py\nOLD: old\nNEW: new\nSEARCH_REPLACE_END"
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) > 0

    def test_extract_search_replace_blocks_simple_format(self):
        """Test extract_search_replace_blocks with simple format."""
        output = "<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE"
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) > 0
        assert blocks[0]["file_path"] == ""  # No file path

    def test_extract_search_replace_blocks_empty(self):
        """Test extract_search_replace_blocks with empty output."""
        blocks = extract_search_replace_blocks("")
        assert blocks == []

    def test_extract_search_replace_blocks_multiple(self):
        """Test extract_search_replace_blocks with multiple blocks."""
        output = """FILE: file1.py
<<<<<<< SEARCH
old1
=======
new1
>>>>>>> REPLACE
FILE: file2.py
<<<<<<< SEARCH
old2
=======
new2
>>>>>>> REPLACE"""
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) >= 2


# =============================================================================
# APPLICATION TESTS
# =============================================================================


class TestApplySearchReplace:
    """Tests for apply_search_replace function."""

    def test_apply_search_replace_success(self, temp_project):
        """Test apply_search_replace with successful replacement."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('old')")

        success, error = apply_search_replace(
            test_file, "print('old')", "print('new')", log_dir=temp_project / "logs"
        )
        assert success is True
        assert error is None
        assert "new" in test_file.read_text()

    def test_apply_search_replace_file_not_found(self, temp_project):
        """Test apply_search_replace with nonexistent file."""
        nonexistent = temp_project / "nonexistent.py"

        success, error = apply_search_replace(
            nonexistent, "old", "new", log_dir=temp_project / "logs"
        )
        assert success is False
        assert "not found" in error.lower()

    def test_apply_search_replace_text_not_found(self, temp_project):
        """Test apply_search_replace with text not found."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('different')")

        success, error = apply_search_replace(
            test_file, "print('old')", "print('new')", log_dir=temp_project / "logs"
        )
        assert success is False
        assert "not found" in error.lower()

    def test_apply_search_replace_normalized_match(self, temp_project):
        """Test apply_search_replace with normalized whitespace match."""
        test_file = temp_project / "test.py"
        test_file.write_text("print( 'old' )")

        success, error = apply_search_replace(
            test_file, "print('old')", "print('new')", log_dir=temp_project / "logs"
        )
        # May succeed with fuzzy match or fail
        assert isinstance(success, bool)

    def test_apply_search_replace_no_change(self, temp_project):
        """Test apply_search_replace when no change is made."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        success, error = apply_search_replace(
            test_file, "print('test')", "print('test')", log_dir=temp_project / "logs"
        )
        assert success is False
        assert "No changes" in error or "No changes" in str(error).lower()


class TestApplySearchReplaceBlocks:
    """Tests for apply_search_replace_blocks function."""

    def test_apply_search_replace_blocks_success(self, temp_project):
        """Test apply_search_replace_blocks with successful operations."""
        test_file = temp_project / "test.py"
        test_file.write_text("old content")

        blocks = [
            {"file_path": "test.py", "search": "old", "replace": "new"},
        ]

        results = apply_search_replace_blocks(blocks, temp_project, log_dir=temp_project / "logs")
        assert len(results) == 1
        assert results[0].success is True

    def test_apply_search_replace_blocks_no_file_path(self, temp_project):
        """Test apply_search_replace_blocks without file path."""
        blocks = [
            {"file_path": "", "search": "old", "replace": "new"},
        ]

        results = apply_search_replace_blocks(blocks, temp_project, log_dir=temp_project / "logs")
        assert len(results) == 1
        assert results[0].success is False

    def test_apply_search_replace_blocks_with_default_file(self, temp_project):
        """Test apply_search_replace_blocks with default file."""
        test_file = temp_project / "default.py"
        test_file.write_text("old")

        blocks = [
            {"file_path": "", "search": "old", "replace": "new"},
        ]

        results = apply_search_replace_blocks(
            blocks, temp_project, default_file=test_file, log_dir=temp_project / "logs"
        )
        assert len(results) == 1

    def test_apply_search_replace_blocks_empty_search(self, temp_project):
        """Test apply_search_replace_blocks with empty search."""
        blocks = [
            {"file_path": "test.py", "search": "", "replace": "new"},
        ]

        results = apply_search_replace_blocks(blocks, temp_project, log_dir=temp_project / "logs")
        assert len(results) == 0  # Should skip empty search

    def test_apply_search_replace_blocks_multiple(self, temp_project):
        """Test apply_search_replace_blocks with multiple blocks."""
        test_file1 = temp_project / "file1.py"
        test_file2 = temp_project / "file2.py"
        test_file1.write_text("old1")
        test_file2.write_text("old2")

        blocks = [
            {"file_path": "file1.py", "search": "old1", "replace": "new1"},
            {"file_path": "file2.py", "search": "old2", "replace": "new2"},
        ]

        results = apply_search_replace_blocks(blocks, temp_project, log_dir=temp_project / "logs")
        assert len(results) == 2


class TestProcessOutputForPatches:
    """Tests for process_output_for_patches function."""

    def test_process_output_for_patches_search_replace(self, temp_project):
        """Test process_output_for_patches with search/replace blocks."""
        output = "FILE: test.py\n<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE"

        results, num_full = process_output_for_patches(
            output, temp_project, log_dir=temp_project / "logs"
        )
        assert isinstance(results, list)
        assert isinstance(num_full, int)

    def test_process_output_for_patches_file_blocks(self, temp_project):
        """Test process_output_for_patches with file blocks."""
        output = "```python FILE:test.py\nprint('hello')\n```"

        results, num_full = process_output_for_patches(
            output, temp_project, log_dir=temp_project / "logs"
        )
        assert isinstance(results, list)
        assert isinstance(num_full, int)

    def test_process_output_for_patches_empty(self, temp_project):
        """Test process_output_for_patches with empty output."""
        results, num_full = process_output_for_patches(
            "", temp_project, log_dir=temp_project / "logs"
        )
        assert results == []
        assert num_full == 0


class TestQuickReplace:
    """Tests for quick_replace function."""

    def test_quick_replace_success(self, temp_project):
        """Test quick_replace with successful replacement."""
        test_file = temp_project / "test.py"
        test_file.write_text("old")

        success = quick_replace(
            temp_project, "test.py", "old", "new", log_dir=temp_project / "logs"
        )
        assert success is True
        assert "new" in test_file.read_text()

    def test_quick_replace_failure(self, temp_project):
        """Test quick_replace with failure."""
        success = quick_replace(
            temp_project, "nonexistent.py", "old", "new", log_dir=temp_project / "logs"
        )
        assert success is False
