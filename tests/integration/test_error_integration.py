import pytest

from boring.services.audit import audited


# Mock tool that returns error dict
@audited
def mock_tool_error_dict():
    return {"status": "ERROR", "message": "ModuleNotFoundError: No module named 'numpy'"}


# Mock tool that raises exception
@audited
def mock_tool_exception():
    raise ModuleNotFoundError("No module named 'scipy'")


# Mock tool success
@audited
def mock_tool_success():
    return {"status": "SUCCESS", "message": "All good"}


def test_error_dict_translation():
    result = mock_tool_error_dict()
    assert result["status"] == "ERROR"
    assert "vibe_explanation" in result
    assert "工具箱" in result["vibe_explanation"]
    assert "boring_run_plugin" in result.get("vibe_fix", "")


def test_exception_logging(caplog):
    # Exception handling in audited just logs and re-raises
    # We can't check return value, but we can check if it didn't crash the logger
    # In a real MCP server, the framework catches the exception.
    # Here we just verify the audited wrapper lets it through.
    with pytest.raises(ModuleNotFoundError):
        mock_tool_exception()


def test_success_pass_through():
    result = mock_tool_success()
    assert result["status"] == "SUCCESS"
    assert "vibe_explanation" not in result
