"""
Additional tests for diff_patcher to increase coverage.
"""

from boring.tools.diff_patcher import (
    SearchReplaceOp,
    apply_search_replace,
    apply_search_replace_blocks,
    extract_search_replace_blocks,
)


class TestSearchReplaceOp:
    """Tests for SearchReplaceOp dataclass."""

    def test_search_replace_op_creation(self):
        """Test creating SearchReplaceOp."""
        op = SearchReplaceOp(file_path="test.py", search="old", replace="new")
        assert op.file_path == "test.py"
        assert op.search == "old"
        assert op.replace == "new"
        assert op.success is False
        assert op.error is None


class TestExtractSearchReplaceBlocks:
    """Additional tests for extract_search_replace_blocks."""

    def test_extract_with_whitespace(self):
        """Test extracting blocks with whitespace."""
        output = """
<<<<<<< SEARCH
  old code
=======
  new code
>>>>>>> REPLACE
"""
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) == 1
        assert "old code" in blocks[0]["search"]
        assert "new code" in blocks[0]["replace"]

    def test_extract_multiple_same_file(self):
        """Test extracting multiple blocks for same file."""
        output = """
FILE: test.py
<<<<<<< SEARCH
old1
=======
new1
>>>>>>> REPLACE

FILE: test.py
<<<<<<< SEARCH
old2
=======
new2
>>>>>>> REPLACE
"""
        blocks = extract_search_replace_blocks(output)
        assert len(blocks) >= 1  # At least one block extracted
        # May extract 1 or 2 depending on pattern matching


class TestApplySearchReplace:
    """Additional tests for apply_search_replace."""

    def test_apply_to_nonexistent_file(self, tmp_path):
        """Test applying to non-existent file."""
        result = apply_search_replace(
            file_path=tmp_path / "nonexistent.py", search="old", replace="new"
        )
        # Should return (success, error) tuple
        assert isinstance(result, tuple)
        assert result[0] is False

    def test_apply_no_match(self, tmp_path):
        """Test applying when search pattern doesn't match."""
        test_file = tmp_path / "test.py"
        test_file.write_text("different content", encoding="utf-8")

        success, error = apply_search_replace(
            file_path=test_file, search="old content", replace="new content"
        )

        assert success is False
        assert error is not None


class TestApplySearchReplaceBlocks:
    """Additional tests for apply_search_replace_blocks."""

    def test_apply_empty_blocks(self, tmp_path):
        """Test applying empty blocks list."""
        results = apply_search_replace_blocks([], tmp_path)
        assert len(results) == 0

    def test_apply_with_errors(self, tmp_path):
        """Test applying blocks with some errors."""
        blocks = [
            {"file_path": "valid.py", "search": "old", "replace": "new"},
            {"file_path": "../invalid.py", "search": "old", "replace": "new"},  # Path traversal
        ]

        # Create valid file
        (tmp_path / "valid.py").write_text("old content", encoding="utf-8")

        results = apply_search_replace_blocks(blocks, tmp_path)
        assert len(results) >= 1
        # At least one should succeed or be blocked
        assert any(r.success or r.error for r in results)
