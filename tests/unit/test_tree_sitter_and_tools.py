from unittest.mock import MagicMock, patch

from boring.judge import LLMJudge
from boring.rag.parser import TreeSitterParser
from boring.rubrics import CODE_QUALITY_RUBRIC
from boring.verification import CodeVerifier

# --- Tree-sitter Tests ---


def test_parser_init():
    parser = TreeSitterParser()
    assert parser.is_available() is True  # Assuming installed in this env
    # If not installed, it should be False, but we installed it.


@patch("boring.rag.parser.get_language")
@patch("boring.rag.parser.get_parser")
def test_parser_extract_chunks_mocked(mock_get_parser, mock_get_curr_lang):
    """Test chunk extraction logic with mocked tree-sitter bindings."""
    parser = TreeSitterParser()

    # Mock Parser Object
    mock_parser_instance = MagicMock()
    mock_tree = MagicMock()
    mock_parser_instance.parse.return_value = mock_tree
    mock_get_parser.return_value = mock_parser_instance

    # Mock Language Object & Query
    mock_lang_instance = MagicMock()
    mock_query = MagicMock()
    mock_lang_instance.query.return_value = mock_query
    mock_get_curr_lang.return_value = mock_lang_instance

    # Mock Query Captures
    # Return a mocked node for a function
    mock_node = MagicMock()
    mock_node.start_point = (10, 0)
    mock_node.end_point = (20, 0)
    mock_node.text = b"function foo() {}"
    mock_node.id = 123

    # Isolate parent to prevent infinite recursion
    mock_node.parent = None

    # We simulate a "function" capture and a "name" capture
    # In reality, tree-sitter returns complex recursive structures,
    # but our logic simplifies to iterating captures.
    mock_query.captures.return_value = [
        (mock_node, "function"),
        (mock_node, "name"),  # Simplified: In real AST, Name is usually a child node
    ]

    chunks = parser.extract_chunks("fake code", "javascript")

    assert len(chunks) == 1
    assert chunks[0].type == "function"
    assert (
        chunks[0].name == "anonymous"
    )  # Name logic in our parser requires parent/child relations we didn't fully mock
    assert chunks[0].start_line == 11
    assert chunks[0].end_line == 21


# --- Verifier Dispatcher Tests ---


def test_verifier_generic_dispatch(tmp_path):
    verifier = CodeVerifier(project_root=tmp_path)
    verifier.tools["golangci-lint"] = True
    verifier.cli_tool_map = {".go": ("golangci-lint", ["golangci-lint", "run"])}

    file_path = tmp_path / "main.go"
    file_path.write_text("package main")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="DONE")

        # Manually call generic dispatcher to test it
        result = verifier._verify_lint_generic(file_path)

        assert result.passed is True
        assert "golangci-lint" in str(mock_run.call_args)
        # Verify arguments: generic map provided ["golangci-lint", "run"] + [filepath]
        call_args = mock_run.call_args[0][0]
        assert call_args[-1] == str(file_path)


# --- Judge Language-Aware Prompt Tests ---


def test_judge_prompt_language_awareness():
    mock_cli = MagicMock()
    judge = LLMJudge(mock_cli)

    # Python
    prompt_py = judge._build_grade_prompt("test.py", "def foo(): pass", CODE_QUALITY_RUBRIC)
    assert "Follow PEP 8" in prompt_py
    assert "highly idiomatic Python" in prompt_py

    # Go
    prompt_go = judge._build_grade_prompt("main.go", "func main() {}", CODE_QUALITY_RUBRIC)
    assert "Effective Go" in prompt_go
    assert "if err != nil" in prompt_go

    # Rust
    prompt_rs = judge._build_grade_prompt("lib.rs", "fn main() {}", CODE_QUALITY_RUBRIC)
    assert "Idiomatic Rust" in prompt_rs
    assert "Option/Result handling" in prompt_rs
