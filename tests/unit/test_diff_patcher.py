"""
Tests for diff_patcher module (V4.0 Diff/Patch functionality)
"""

from boring.diff_patcher import (
    apply_search_replace,
    apply_search_replace_blocks,
    extract_search_replace_blocks,
)


class TestExtractSearchReplaceBlocks:
    """Tests for parsing SEARCH_REPLACE blocks from output."""

    def test_extract_simple_block(self):
        """Test extracting a simple search/replace block."""
        output = """Some text before

<<<<<<< SEARCH
def old_function():
    print("old")
=======
def old_function():
    print("new")
>>>>>>> REPLACE

Some text after"""

        blocks = extract_search_replace_blocks(output)

        assert len(blocks) == 1
        assert "def old_function():" in blocks[0]["search"]
        assert 'print("old")' in blocks[0]["search"]
        assert 'print("new")' in blocks[0]["replace"]

    def test_extract_block_with_file_path(self):
        """Test extracting block with file path header."""
        output = """FILE: src/main.py
<<<<<<< SEARCH
old_code
=======
new_code
>>>>>>> REPLACE"""

        blocks = extract_search_replace_blocks(output)

        assert len(blocks) == 1
        assert blocks[0]["file_path"] == "src/main.py"
        assert blocks[0]["search"] == "old_code"
        assert blocks[0]["replace"] == "new_code"

    def test_extract_multiple_blocks(self):
        """Test extracting multiple search/replace blocks."""
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

        assert len(blocks) == 2
        assert blocks[0]["file_path"] == "file1.py"
        assert blocks[1]["file_path"] == "file2.py"

    def test_extract_no_blocks(self):
        """Test when no search/replace blocks are present."""
        output = "Just regular text without any blocks"

        blocks = extract_search_replace_blocks(output)

        assert len(blocks) == 0


class TestApplySearchReplace:
    """Tests for applying search/replace to files."""

    def test_apply_simple_replace(self, tmp_path):
        """Test applying a simple search/replace."""
        test_file = tmp_path / "test.py"
        test_file.write_text('def hello():\n    print("old")\n')

        success, error = apply_search_replace(test_file, 'print("old")', 'print("new")')

        assert success is True
        assert error is None
        assert 'print("new")' in test_file.read_text()

    def test_apply_replace_not_found(self, tmp_path):
        """Test when search text is not found."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    pass\n")

        success, error = apply_search_replace(test_file, "nonexistent_text", "replacement")

        assert success is False
        assert "not found" in error.lower()

    def test_apply_replace_file_not_found(self, tmp_path):
        """Test when file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.py"

        success, error = apply_search_replace(nonexistent, "search", "replace")

        assert success is False
        assert "not found" in error.lower()

    def test_apply_replace_only_first_occurrence(self, tmp_path):
        """Test that only the first occurrence is replaced."""
        test_file = tmp_path / "test.py"
        test_file.write_text("hello world hello world")

        success, error = apply_search_replace(test_file, "hello", "hi")

        assert success is True
        content = test_file.read_text()
        assert content == "hi world hello world"


class TestApplySearchReplaceBlocks:
    """Tests for applying multiple search/replace operations."""

    def test_apply_multiple_blocks(self, tmp_path):
        """Test applying multiple search/replace blocks."""
        file1 = tmp_path / "file1.py"
        file1.write_text("old content 1")

        file2 = tmp_path / "file2.py"
        file2.write_text("old content 2")

        blocks = [
            {"file_path": "file1.py", "search": "old content 1", "replace": "new content 1"},
            {"file_path": "file2.py", "search": "old content 2", "replace": "new content 2"},
        ]

        results = apply_search_replace_blocks(blocks, tmp_path)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert "new content 1" in file1.read_text()
        assert "new content 2" in file2.read_text()
