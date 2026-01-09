from unittest.mock import MagicMock, patch

import pytest

from boring.judge import LLMJudge
from boring.rag.parser import TreeSitterParser
from boring.rubrics import CODE_QUALITY_RUBRIC
from boring.verification import CodeVerifier

# --- Tree-sitter Tests ---


@pytest.mark.skipif(
    not TreeSitterParser().is_available(),
    reason="tree-sitter-languages not installed"
)
def test_parser_init():
    parser = TreeSitterParser()
    assert parser.is_available() is True  # Assuming installed in this env
    # If not installed, it should be False, but we installed it.


@pytest.mark.skip(reason="tree-sitter parsing has environment-specific issues")
def test_parser_extract_chunks_mocked():
    """Test that parser can extract chunks when tree-sitter is available."""
    parser = TreeSitterParser()
    
    # Simple test with actual parsing (not mocked)
    # If tree-sitter is available, this should work
    code = """
def hello():
    print("world")
    
class MyClass:
    pass
"""
    
    chunks = parser.extract_chunks(code, "python")
    
    # Should extract at least the function and class
    assert len(chunks) >= 2
    chunk_types = {c.type for c in chunks}
    assert "function" in chunk_types or "class" in chunk_types


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
