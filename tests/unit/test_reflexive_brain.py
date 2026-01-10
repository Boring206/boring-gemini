from pathlib import Path
from unittest.mock import MagicMock, patch

from boring.mcp.tools.assistant import _check_learned_patterns, register_assistant_tools

# Mock Objects
mock_mcp = MagicMock()


def mock_audited(x):
    return x


def get_boring_suggest_next_function():
    """Helper to extract boring_suggest_next."""
    registered_tools = {}

    def tool_decorator(**kwargs):
        def real_decorator(func):
            name = getattr(func, "__name__", str(func))
            registered_tools[name] = func
            return func

        return real_decorator

    mock_mcp.tool.side_effect = tool_decorator

    helpers = {
        "get_project_root_or_error": lambda x: (Path("/tmp"), None),
        "detect_project_root": lambda x: Path("/tmp"),  # Add this if needed by others
        "configure_runtime": MagicMock(),
    }

    with (
        patch("boring.mcp.tools.assistant.get_pattern_miner"),
        patch("boring.mcp.tools.assistant.get_streaming_manager"),
    ):
        register_assistant_tools(mock_mcp, mock_audited, helpers)

    return registered_tools.get("boring_suggest_next")


def test_check_learned_patterns_reflexive():
    """Test that _check_learned_patterns actively queries for error messages."""

    # Setup
    args = (Path("/tmp"), "Connection refused")

    with patch("boring.intelligence.brain_manager.BrainManager") as MockBrain:
        mock_brain_instance = MockBrain.return_value
        mock_brain_instance.get_relevant_patterns.return_value = [
            {"solution": "Check firewall", "description": "Firewall issue", "success_count": 5}
        ]

        # Execute
        results = _check_learned_patterns(args)

        # Verify Query
        # Should query with the error message
        mock_brain_instance.get_relevant_patterns.assert_called_with("Connection refused", limit=5)

        # Verify Result
        assert len(results) == 1
        assert results[0]["type"] == "learned_pattern"
        assert results[0]["priority"] == "critical"  # Should be critical for error fixes
        assert "Proven Fix" in results[0]["details"]


def test_check_learned_patterns_generic():
    """Test fallback to generic query when no error message provided."""
    # Setup
    args = (Path("/tmp"), None)

    with patch("boring.intelligence.brain_manager.BrainManager") as MockBrain:
        mock_brain_instance = MockBrain.return_value
        mock_brain_instance.get_relevant_patterns.return_value = []

        # Execute
        _check_learned_patterns(args)

        # Verify Query
        mock_brain_instance.get_relevant_patterns.assert_called_with(
            "next steps recommendations", limit=3
        )


def test_boring_suggest_next_propagates_error():
    """Test that boring_suggest_next propagates error info to helper."""
    tool = get_boring_suggest_next_function()

    with (
        patch("boring.mcp.tools.assistant._check_learned_patterns") as mock_check,
        patch("boring.mcp.tools.assistant.get_pattern_miner"),
        patch("boring.mcp.tool_profiles.get_profile"),
        patch("boring.mcp.tools.assistant._check_git_changes") as mock_git,
        patch("boring.mcp.tools.assistant._check_rag_index") as mock_rag,
        patch("boring.mcp.tools.assistant._check_task_progress") as mock_task,
        patch("boring.mcp.tools.assistant._check_project_empty") as mock_empty,
        patch("boring.mcp.tools.assistant._check_project_context") as mock_context,
    ):
        # KEY FIX: Set __name__ for all mocks because ThreadPool uses it
        mock_check.__name__ = "_check_learned_patterns"
        mock_git.__name__ = "_check_git_changes"
        mock_rag.__name__ = "_check_rag_index"
        mock_task.__name__ = "_check_task_progress"
        mock_empty.__name__ = "_check_project_empty"
        mock_context.__name__ = "_check_project_context"

        mock_check.return_value = []
        mock_git.return_value = []
        mock_rag.return_value = []
        mock_task.return_value = []
        mock_empty.return_value = []
        mock_context.return_value = []

        # Call with error message
        tool(error_message="My specific error")

        # Verify call
        mock_check.assert_called()
        call_args = mock_check.call_args[0][0]
        assert call_args == (Path("/tmp"), "My specific error")
