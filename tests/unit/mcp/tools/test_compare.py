from unittest.mock import patch

import pytest

from boring.mcp.tools.compare import boring_compare_files
from boring.rag.parser import ParsedChunk


@pytest.fixture
def mock_project_root(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    return root


def test_boring_compare_files_text_diff(mock_project_root):
    file_a = mock_project_root / "a.txt"
    file_b = mock_project_root / "b.txt"
    file_a.write_text("Hello\nWorld\n", encoding="utf-8")
    file_b.write_text("Hello\nPython\n", encoding="utf-8")

    result = boring_compare_files(
        file_a=str(file_a), file_b=str(file_b), mode="text", project_path=str(mock_project_root)
    )

    assert result["status"] == "success"
    diff = result["data"]["diff"]
    assert "--- a.txt" in diff
    assert "+++ b.txt" in diff
    assert "-World" in diff
    assert "+Python" in diff


def test_boring_compare_files_identical(mock_project_root):
    file_a = mock_project_root / "a.txt"
    file_a.write_text("Identify\n", encoding="utf-8")

    result = boring_compare_files(
        file_a=str(file_a), file_b=str(file_a), mode="text", project_path=str(mock_project_root)
    )

    assert result["status"] == "success"
    assert result["message"] == "Files are identical."


def test_boring_compare_files_semantic_mock(mock_project_root):
    # Mocking TreeSitterParser to avoid dependency on actual tree-sitter lib for unit test
    with patch("boring.mcp.tools.compare.TreeSitterParser") as MockParser:
        instance = MockParser.return_value
        instance.is_available.return_value = True
        instance.get_language_for_file.return_value = "python"

        # Scenario: Function 'foo' modified, Class 'Bar' removed
        chunk_a_foo = ParsedChunk(
            type="function", name="foo", start_line=1, end_line=5, content="def foo(): pass"
        )
        chunk_a_bar = ParsedChunk(
            type="class", name="Bar", start_line=10, end_line=20, content="class Bar: pass"
        )

        chunk_b_foo = ParsedChunk(
            type="function", name="foo", start_line=1, end_line=5, content="def foo(): return 1"
        )

        instance.extract_chunks.side_effect = [
            [chunk_a_foo, chunk_a_bar],  # chunks_a
            [chunk_b_foo],  # chunks_b
        ]

        file_a = mock_project_root / "a.py"
        file_b = mock_project_root / "b.py"
        file_a.touch()
        file_b.touch()

        result = boring_compare_files(
            file_a=str(file_a),
            file_b=str(file_b),
            mode="semantic",
            project_path=str(mock_project_root),
        )

        assert result["status"] == "success"
        data = result["data"]
        assert "function:foo" in data["modified"]
        assert "class:Bar" in data["removed"]
        assert len(data["added"]) == 0


def test_boring_compare_files_missing_file_error(mock_project_root):
    result = boring_compare_files(
        file_a="non_existent_a.txt",
        file_b="non_existent_b.txt",
        project_path=str(mock_project_root),
    )
    assert result["status"] == "error"
    assert result["message"] == "Neither file exists."


def test_boring_compare_files_fallback(mock_project_root):
    with patch("boring.mcp.tools.compare.TreeSitterParser") as MockParser:
        instance = MockParser.return_value
        instance.is_available.return_value = False

        file_a = mock_project_root / "a.py"
        file_b = mock_project_root / "b.py"
        file_a.write_text("a", encoding="utf-8")
        file_b.write_text("b", encoding="utf-8")

        result = boring_compare_files(
            file_a=str(file_a),
            file_b=str(file_b),
            mode="semantic",
            project_path=str(mock_project_root),
        )

        # Should fallback to text diff logic
        assert result["status"] == "success"
        assert result["data"]["mode"] == "fallback_text"
        assert "-a" in result["data"]["diff"]
