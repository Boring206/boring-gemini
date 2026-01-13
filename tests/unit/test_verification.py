"""
Tests for verification module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from boring.verification import CodeVerifier, VerificationResult
from boring.verification.handlers import (
    verify_imports_python,
    verify_lint_python,
    verify_syntax_python,
)


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_result_creation(self):
        """Test creating a verification result."""
        result = VerificationResult(
            passed=True, check_type="syntax", message="OK", details=[], suggestions=[]
        )
        assert result.passed is True
        assert result.check_type == "syntax"

    def test_failed_result_with_details(self):
        """Test failed result with details and suggestions."""
        result = VerificationResult(
            passed=False,
            check_type="lint",
            message="Lint failed",
            details=["Error 1", "Error 2"],
            suggestions=["Fix it"],
        )
        assert result.passed is False
        assert len(result.details) == 2
        assert len(result.suggestions) == 1


class TestCodeVerifierSyntax:
    """Tests for syntax verification."""

    def test_verify_syntax_valid(self, tmp_path):
        """Test syntax check on valid Python."""
        test_file = tmp_path / "valid.py"
        test_file.write_text("def hello():\n    return 'world'\n")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_syntax(test_file)

        assert result.passed is True
        assert result.check_type == "syntax"
        assert "OK" in result.message

    def test_verify_syntax_invalid(self, tmp_path):
        """Test syntax check on invalid Python."""
        test_file = tmp_path / "invalid.py"
        test_file.write_text("def broken(\n")  # Missing closing paren

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_syntax(test_file)

        assert result.passed is False
        assert result.check_type == "syntax"
        assert "Error" in result.message
        assert len(result.details) > 0

    def test_verify_syntax_empty_file(self, tmp_path):
        """Test syntax check on empty file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_syntax(test_file)

        assert result.passed is True


class TestCodeVerifierLint:
    """Tests for linting verification."""

    def test_verify_lint_no_ruff(self, tmp_path):
        """Test lint check when ruff is not available."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x=1")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["ruff"] = False  # Simulate ruff not available

        result = verifier.verify_lint(test_file)

        assert result.passed is True  # Skipped, so passes
        assert "skipped" in result.message.lower()

    def test_verify_lint_with_ruff_mock_success(self, tmp_path):
        """Test lint check with mocked ruff success."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["ruff"] = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = verifier.verify_lint(test_file)

        assert result.passed is True
        assert result.check_type == "lint"

    def test_verify_lint_with_ruff_mock_failure(self, tmp_path):
        """Test lint check with mocked ruff failure."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x=1")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["ruff"] = True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="test.py:1:1: E225 missing whitespace", stderr=""
            )
            result = verifier.verify_lint(test_file)

        assert result.passed is False


class TestCodeVerifierImports:
    """Tests for import verification."""

    def test_verify_imports_standard_lib(self, tmp_path):
        """Test import check with standard library imports."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\nimport sys\n")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_imports(test_file)

        assert result.passed is True
        assert result.check_type == "import"

    def test_verify_imports_relative(self, tmp_path):
        """Test import check with relative imports (should be skipped)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from .utils import helper\n")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        result = verifier.verify_imports(test_file)

        assert result.passed is True  # Relative imports are skipped


class TestCodeVerifierTests:
    """Tests for test runner."""

    def test_run_tests_no_pytest(self, tmp_path):
        """Test running tests when pytest is not available."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["pytest"] = False

        result = verifier.run_tests()

        assert result.passed is True  # Skipped
        assert "skipped" in result.message.lower()

    def test_run_tests_no_tests_dir(self, tmp_path):
        """Test running tests when tests directory doesn't exist."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["pytest"] = True

        result = verifier.run_tests()

        assert result.passed is True
        assert "No tests" in result.message


class TestCodeVerifierProject:
    """Tests for project-level verification."""

    def test_verify_project_no_src(self, tmp_path):
        """Test project verification when src doesn't exist."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)

        passed, message = verifier.verify_project()

        # When no src/ directory exists, it scans root and finds 0 Python files
        assert passed is True
        assert "checks passed" in message or "not found" in message

    def test_verify_project_with_valid_files(self, tmp_path):
        """Test project verification with valid Python files."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        (src_dir / "module.py").write_text("def hello(): pass\n")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        verifier.tools["ruff"] = False  # Skip ruff

        passed, message = verifier.verify_project(level="BASIC")

        assert passed is True

    def test_verify_file_non_python(self, tmp_path):
        """Test that non-Python files are skipped."""
        test_file = tmp_path / "readme.md"
        test_file.write_text("# README")

        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        results = verifier.verify_file(test_file)

        assert len(results) == 0


class TestGenerateFeedbackPrompt:
    """Tests for feedback prompt generation."""

    def test_generate_feedback_no_failures(self, tmp_path):
        """Test feedback generation when all passed."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        results = [VerificationResult(True, "syntax", "OK", [], [])]

        feedback = verifier.generate_feedback_prompt(results)

        assert feedback == ""

    def test_generate_feedback_with_failures(self, tmp_path):
        """Test feedback generation with failures."""
        verifier = CodeVerifier(project_root=tmp_path, log_dir=tmp_path)
        results = [
            VerificationResult(False, "syntax", "Syntax Error", ["Line 5: invalid"], ["Fix line 5"])
        ]

        feedback = verifier.generate_feedback_prompt(results)

        assert "CRITICAL" in feedback
        assert "SYNTAX" in feedback
        assert "Line 5" in feedback


# --- Submodule Tests (Refactored in V10.15) ---


class TestVerificationSubmodules:
    """Test the individual components of the verification package."""

    def test_tool_manager_init(self, mocker):
        # Mock subprocess to avoid real tool checks
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(returncode=0)

        from boring.verification.tools import ToolManager

        manager = ToolManager()
        assert "ruff" in manager.available_tools

    def test_load_custom_rules_mock(self, tmp_path):
        from boring.verification.config import load_custom_rules

        # Mock .boring.toml
        config_path = tmp_path / ".boring.toml"
        config_path.write_text("""
[boring.verification]
custom_rules = ["Rule 1", "Rule 2"]
""")

        rules = load_custom_rules(tmp_path)
        assert len(rules["custom_commands"]) == 2
        assert "Rule 1" in rules["custom_commands"]

    def test_verify_syntax_python_compile(self, tmp_path):
        file_path = tmp_path / "test.py"
        file_path.write_text("def foo(): pass")

        tools_mock = MagicMock()
        result = verify_syntax_python(file_path, tmp_path, tools_mock)

        assert result.passed is True
        assert "Syntax OK" in result.message

    def test_verify_lint_python_mock(self, tmp_path, mocker):
        file_path = tmp_path / "test.py"
        file_path.write_text("import os")

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        tools_mock = MagicMock()
        tools_mock.is_available.return_value = True

        result = verify_lint_python(file_path, tmp_path, tools_mock, auto_fix=True)
        assert result.passed is True
        assert mock_run.call_count >= 2

    def test_verify_imports_python_logic(self, tmp_path):
        file_path = tmp_path / "test.py"
        file_path.write_text("from non_existent_pkg import something")

        result = verify_imports_python(file_path, tmp_path)
        assert result.passed is False
        assert "non_existent_pkg" in result.details


class TestJudgeSubmodules:
    """Test the individual components of the judge package."""

    def test_extract_json_logic(self):
        from boring.judge.parsers import extract_json

        text = 'Result: {"score": 5}'
        res = extract_json(text)
        assert res["score"] == 5

    def test_build_grade_prompt_logic(self):
        from boring.judge.prompts import build_grade_prompt
        from boring.rubrics import CODE_QUALITY_RUBRIC

        prompt = build_grade_prompt("test.py", "pass", CODE_QUALITY_RUBRIC, "Mock")
        assert "test.py" in prompt

    def test_create_judge_provider_logic(self):
        from boring.judge.factory import create_judge_provider

        with patch("boring.judge.factory.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "ollama"
            mock_settings.LLM_MODEL = "mistral"
            mock_settings.LLM_BASE_URL = "http://localhost:11434"
            mock_settings.LOG_DIR = Path("logs")

            provider = create_judge_provider()
            from boring.llm.ollama import OllamaProvider

            assert isinstance(provider, OllamaProvider)
            assert provider.model_name == "mistral"





class TestCoreModule:
    """Additional tests for core module to increase coverage."""

    def test_circuit_state_import(self):
        from boring.core import CircuitState

        assert CircuitState.CLOSED is not None
        assert CircuitState.OPEN is not None

    def test_should_halt_execution_import(self):
        from boring.core import should_halt_execution

        assert callable(should_halt_execution)

    def test_log_status_import(self):
        from boring.core import log_status

        assert callable(log_status)

    def test_can_make_call_import(self):
        from boring.core import can_make_call

        assert callable(can_make_call)

    def test_constants_import(self):
        from boring.core import MAX_CONSECUTIVE_DONE_SIGNALS, MAX_CONSECUTIVE_TEST_LOOPS

        assert MAX_CONSECUTIVE_TEST_LOOPS > 0
        assert MAX_CONSECUTIVE_DONE_SIGNALS > 0

    def test_circuit_functions_import(self):
        from boring.core import get_circuit_state, init_circuit_breaker, reset_circuit_breaker

        assert callable(init_circuit_breaker)
        assert callable(reset_circuit_breaker)
        assert callable(get_circuit_state)

    def test_limiter_functions_import(self):
        from boring.core import get_calls_made, increment_call_counter, init_call_tracking

        assert callable(init_call_tracking)
        assert callable(get_calls_made)
        assert callable(increment_call_counter)


class TestModelsModule:
    """Tests for boring.models dataclasses."""

    def test_verification_result_dataclass(self):
        from boring.models import VerificationResult

        result = VerificationResult(
            passed=True,
            check_type="test",
            message="Test passed",
            details=["detail1"],
            suggestions=["suggestion1"],
        )
        assert result.passed is True
        assert result.check_type == "test"
        assert len(result.details) == 1

    def test_loop_info_model(self):
        from boring.models import LoopInfo

        info = LoopInfo(loop=1, files_changed=5, has_errors=False, output_length=1000)
        assert info.loop == 1
        assert info.files_changed == 5

    def test_exit_signals_model(self):
        from boring.models import ExitSignals

        signals = ExitSignals(
            test_only_loops=[1, 2], done_signals=[3], completion_indicators=["Done!"]
        )
        assert len(signals.test_only_loops) == 2
        assert len(signals.done_signals) == 1

    def test_workflow_step_model(self):
        from boring.models import WorkflowStep

        step = WorkflowStep(index=1, content="Do something")
        assert step.index == 1
        assert step.content == "Do something"
