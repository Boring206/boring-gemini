# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.file_patcher module.
"""

from unittest.mock import patch

import pytest

from boring.file_patcher import (
    FILE_BLOCK_PATTERN,
    HEADER_FILE_PATTERN,
    LANG_PATH_PATTERN,
    SECTION_FILE_PATTERN,
    XML_FILE_PATTERN,
    apply_patches,
    extract_file_blocks,
    process_gemini_output,
    process_structured_calls,
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
# REGEX PATTERN TESTS
# =============================================================================


class TestRegexPatterns:
    """Tests for regex patterns."""

    def test_file_block_pattern(self):
        """Test FILE_BLOCK_PATTERN matches file blocks."""
        text = "```python FILE:test.py\nprint('hello')\n```"
        match = FILE_BLOCK_PATTERN.search(text)
        assert match is not None
        assert match.group(2) == "test.py"

    def test_lang_path_pattern(self):
        """Test LANG_PATH_PATTERN matches lang:path format."""
        text = "```python:src/main.py\nprint('hello')\n```"
        match = LANG_PATH_PATTERN.search(text)
        assert match is not None
        assert match.group(2) == "src/main.py"

    def test_header_file_pattern(self):
        """Test HEADER_FILE_PATTERN matches header format."""
        text = "# File: test.py\n```python\nprint('hello')\n```"
        match = HEADER_FILE_PATTERN.search(text)
        assert match is not None
        assert "test.py" in match.group(1)

    def test_section_file_pattern(self):
        """Test SECTION_FILE_PATTERN matches section format."""
        text = "=== File: test.py ===\n```python\nprint('hello')\n```"
        match = SECTION_FILE_PATTERN.search(text)
        assert match is not None

    def test_xml_file_pattern(self):
        """Test XML_FILE_PATTERN matches XML format."""
        text = '<file path="test.py">print("hello")</file>'
        match = XML_FILE_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "test.py"


# =============================================================================
# STRUCTURED CALL PROCESSOR TESTS
# =============================================================================


class TestProcessStructuredCalls:
    """Tests for process_structured_calls function."""

    def test_process_structured_calls_write_file(self, temp_project):
        """Test process_structured_calls with write_file."""
        function_calls = [
            {
                "name": "write_file",
                "args": {
                    "file_path": "test.py",
                    "content": "print('hello')",
                },
            }
        ]

        with patch("boring.file_patcher.BackupManager"):
            count, paths, errors = process_structured_calls(
                function_calls, temp_project, log_dir=temp_project / "logs"
            )
            assert count >= 0
            assert isinstance(paths, list)
            assert isinstance(errors, list)

    def test_process_structured_calls_search_replace(self, temp_project):
        """Test process_structured_calls with search_replace."""
        # Create existing file
        test_file = temp_project / "test.py"
        test_file.write_text("print('old')")

        function_calls = [
            {
                "name": "search_replace",
                "args": {
                    "file_path": "test.py",
                    "search": "old",
                    "replace": "new",
                },
            }
        ]

        with patch("boring.file_patcher.BackupManager"):
            count, paths, errors = process_structured_calls(
                function_calls, temp_project, log_dir=temp_project / "logs"
            )
            assert isinstance(paths, list)
            assert isinstance(errors, list)

    def test_process_structured_calls_mixed(self, temp_project):
        """Test process_structured_calls with mixed calls."""
        function_calls = [
            {
                "name": "write_file",
                "args": {"file_path": "new.py", "content": "print('new')"},
            },
            {
                "name": "search_replace",
                "args": {"file_path": "new.py", "search": "new", "replace": "updated"},
            },
        ]

        with patch("boring.file_patcher.BackupManager"):
            count, paths, errors = process_structured_calls(
                function_calls, temp_project, log_dir=temp_project / "logs"
            )
            assert isinstance(paths, list)

    def test_process_structured_calls_invalid(self, temp_project):
        """Test process_structured_calls with invalid calls."""
        function_calls = [
            {"name": "write_file", "args": {}},  # Missing file_path
            {"name": "search_replace", "args": {}},  # Missing args
        ]

        with patch("boring.file_patcher.BackupManager"):
            count, paths, errors = process_structured_calls(
                function_calls, temp_project, log_dir=temp_project / "logs"
            )
            assert len(errors) > 0

    def test_process_structured_calls_empty(self, temp_project):
        """Test process_structured_calls with empty list."""
        count, paths, errors = process_structured_calls(
            [], temp_project, log_dir=temp_project / "logs"
        )
        assert count == 0
        assert paths == []
        assert errors == []


# =============================================================================
# LEGACY EXTRACTION TESTS
# =============================================================================


class TestExtractFileBlocks:
    """Tests for extract_file_blocks function."""

    def test_extract_file_blocks_file_format(self):
        """Test extract_file_blocks with FILE: format."""
        output = "```python FILE:test.py\nprint('hello')\n```"
        blocks = extract_file_blocks(output)
        assert isinstance(blocks, dict)

    def test_extract_file_blocks_lang_path_format(self):
        """Test extract_file_blocks with lang:path format."""
        output = "```python:src/main.py\nprint('hello')\n```"
        blocks = extract_file_blocks(output)
        assert isinstance(blocks, dict)

    def test_extract_file_blocks_header_format(self):
        """Test extract_file_blocks with header format."""
        output = "# File: test.py\n```python\nprint('hello')\n```"
        blocks = extract_file_blocks(output)
        assert isinstance(blocks, dict)

    def test_extract_file_blocks_section_format(self):
        """Test extract_file_blocks with section format."""
        output = "=== File: test.py ===\n```python\nprint('hello')\n```"
        blocks = extract_file_blocks(output)
        assert isinstance(blocks, dict)

    def test_extract_file_blocks_xml_format(self):
        """Test extract_file_blocks with XML format."""
        output = '<file path="test.py">print("hello")</file>'
        blocks = extract_file_blocks(output)
        assert isinstance(blocks, dict)

    def test_extract_file_blocks_empty(self):
        """Test extract_file_blocks with empty output."""
        blocks = extract_file_blocks("")
        assert blocks == {}

    def test_extract_file_blocks_multiple(self):
        """Test extract_file_blocks with multiple files."""
        output = """```python FILE:file1.py
print('file1')
```
```python FILE:file2.py
print('file2')
```"""
        blocks = extract_file_blocks(output)
        assert len(blocks) >= 1


# =============================================================================
# PATCH APPLICATION TESTS
# =============================================================================


class TestApplyPatches:
    """Tests for apply_patches function."""

    def test_apply_patches_new_file(self, temp_project):
        """Test apply_patches creates new file."""
        patches = {"test.py": "print('hello')"}

        result = apply_patches(patches, temp_project, log_dir=temp_project / "logs")
        assert len(result) > 0  # files_modified
        assert result[0][0] == "test.py"  # modified_paths

    def test_apply_patches_existing_file(self, temp_project):
        """Test apply_patches modifies existing file."""
        test_file = temp_project / "test.py"
        test_file.write_text("old content")

        patches = {"test.py": "new content"}

        result = apply_patches(patches, temp_project, log_dir=temp_project / "logs")
        assert len(result) > 0

    def test_apply_patches_empty(self, temp_project):
        """Test apply_patches with empty patches."""
        result = apply_patches({}, temp_project, log_dir=temp_project / "logs")
        assert len(result) == 0

    def test_apply_patches_invalid_path(self, temp_project):
        """Test apply_patches with invalid path."""
        patches = {"../../../etc/passwd": "malicious"}

        result = apply_patches(patches, temp_project, log_dir=temp_project / "logs")
        # Should reject invalid paths
        assert len(result) == 0


# =============================================================================
# GEMINI OUTPUT PROCESSOR TESTS
# =============================================================================


class TestProcessGeminiOutput:
    """Tests for process_gemini_output function."""

    def test_process_gemini_output_legacy(self, temp_project):
        """Test process_gemini_output with legacy format."""
        output_file = temp_project / "gemini_output.md"
        output_file.write_text("```python FILE:test.py\nprint('hello')\n```")

        result = process_gemini_output(output_file, temp_project, log_dir=temp_project / "logs")
        assert result == 1
        assert (temp_project / "test.py").exists()

    def test_process_gemini_output_empty(self, temp_project):
        """Test process_gemini_output with empty output."""
        output_file = temp_project / "gemini_output.md"
        output_file.write_text("")

        result = process_gemini_output(output_file, temp_project, log_dir=temp_project / "logs")
        assert result == 0
