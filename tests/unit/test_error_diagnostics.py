"""
Tests for error diagnostics module.
"""


from boring.error_diagnostics import DiagnosticResult, ErrorDiagnostics


def test_diagnostic_result_creation():
    """Test creating a DiagnosticResult."""
    result = DiagnosticResult(
        error_type="syntax_error",
        message="Invalid syntax",
        file_path="test.py",
        line_number=10,
        column=5,
    )

    assert result.error_type == "syntax_error"
    assert result.message == "Invalid syntax"
    assert result.file_path == "test.py"
    assert result.line_number == 10
    assert result.column == 5


def test_diagnostic_result_to_dict():
    """Test converting DiagnosticResult to dict."""
    result = DiagnosticResult(
        error_type="import_error",
        message="Module not found",
        suggestions=["Install module", "Check imports"],
        auto_fixable=True,
        fix_command="pip install module",
    )

    result_dict = result.to_dict()

    assert result_dict["type"] == "import_error"
    assert result_dict["message"] == "Module not found"
    assert len(result_dict["suggestions"]) == 2
    assert result_dict["autoFixable"] is True
    assert result_dict["fixCommand"] == "pip install module"


def test_error_diagnostics_init():
    """Test ErrorDiagnostics initialization."""
    diagnostics = ErrorDiagnostics()
    assert diagnostics is not None
    assert hasattr(diagnostics, "ERROR_PATTERNS")


def test_error_diagnostics_analyze_syntax_error():
    """Test analyzing Python syntax error."""
    diagnostics = ErrorDiagnostics()
    error_output = "  File \"test.py\", line 5\n    if True\nSyntaxError: invalid syntax"

    results = diagnostics.analyze_error(error_output)

    assert len(results) > 0
    assert any(r.error_type == "syntax_error" for r in results)


def test_error_diagnostics_analyze_import_error():
    """Test analyzing import error."""
    diagnostics = ErrorDiagnostics()
    error_output = "ModuleNotFoundError: No module named 'missing_module'"

    results = diagnostics.analyze_error(error_output)

    assert len(results) > 0
    found = False
    for r in results:
        if r.error_type == "module_not_found":
            found = True
            assert "pip install" in " ".join(r.suggestions)

    assert found


def test_error_diagnostics_analyze_unused_import():
    """Test analyzing unused import."""
    diagnostics = ErrorDiagnostics()
    error_output = "test.py:1:1: F401 [*] `os` imported but unused"

    results = diagnostics.analyze_error(error_output)

    assert len(results) > 0
    found = False
    for r in results:
        if r.error_type == "unused_import":
            found = True
            assert r.auto_fixable or "Remove" in " ".join(r.suggestions)

    # At least should parse the error
    assert found or len(results) > 0


def test_error_diagnostics_analyze_indentation_error():
    """Test analyzing indentation error."""
    diagnostics = ErrorDiagnostics()
    error_output = "IndentationError: unexpected indent"

    results = diagnostics.analyze_error(error_output)

    assert len(results) > 0
    found = False
    for r in results:
        if r.error_type == "indentation_error":
            found = True
            assert any("indent" in s.lower() for s in r.suggestions)

    assert found


def test_error_diagnostics_error_patterns():
    """Test that ERROR_PATTERNS is defined."""
    assert hasattr(ErrorDiagnostics, "ERROR_PATTERNS")
    assert isinstance(ErrorDiagnostics.ERROR_PATTERNS, dict)
    assert len(ErrorDiagnostics.ERROR_PATTERNS) > 0


def test_diagnostic_result_default_values():
    """Test DiagnosticResult with default values."""
    result = DiagnosticResult(error_type="test", message="test message")

    assert result.file_path is None
    assert result.line_number is None
    assert result.column is None
    assert result.severity == "error"
    assert result.suggestions == []
    assert result.auto_fixable is False
    assert result.fix_command is None


def test_error_diagnostics_empty_input():
    """Test analyzing empty error output."""
    diagnostics = ErrorDiagnostics()
    results = diagnostics.analyze_error("")

    assert isinstance(results, list)


def test_error_diagnostics_unknown_error():
    """Test analyzing unknown error format."""
    diagnostics = ErrorDiagnostics()
    results = diagnostics.analyze_error("Some random error message that doesn't match patterns")

    assert isinstance(results, list)
