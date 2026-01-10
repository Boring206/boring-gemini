import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock expensive modules
sys.modules["boring.git_utils"] = MagicMock()
sys.modules["boring.mcp.chroma_handler"] = MagicMock()

# Import the registration function
from boring.mcp.tool_profiles import ProfileConfig
from boring.mcp.tools.assistant import register_assistant_tools

# Mock Objects
mock_mcp = MagicMock()
mock_audited = lambda x: x


def get_boring_suggest_next_function():
    """Helper to extract boring_suggest_next from the closure."""

    # Capture the decorated functions
    registered_tools = {}

    def tool_decorator(**kwargs):
        def real_decorator(func):
            name = getattr(func, "__name__", str(func))
            registered_tools[name] = func
            return func

        return real_decorator

    mock_mcp.tool.side_effect = tool_decorator

    # Helper mocks
    helpers = {
        "get_project_root_or_error": lambda x: (Path("/tmp"), None),
        "detect_project_root": lambda x: Path("/tmp"),
        "configure_runtime": MagicMock(),
    }

    # Call registration to define the inner functions
    register_assistant_tools(mock_mcp, mock_audited, helpers)

    return registered_tools.get("boring_suggest_next")


def test_suggest_next_filtering_in_lite_profile():
    # 1. Extract the function
    boring_suggest_next = get_boring_suggest_next_function()
    assert boring_suggest_next is not None

    # 2. Mock Profile to be LITE
    lite_profile = ProfileConfig(
        name="lite", description="Lite", tools=["boring_suggest_next"], prompts=[]
    )

    # 3. Running the function requires patching internal calls
    # Note: Patch paths updated to boring.mcp.tools.assistant
    with (
        patch("boring.mcp.tools.assistant.get_pattern_miner") as mock_get_miner,
        patch("boring.mcp.tool_profiles.get_profile") as mock_get_profile,
        patch("boring.mcp.tool_profiles.should_register_tool") as mock_should_tool,
        patch("boring.mcp.tools.assistant._check_rag_index") as mock_rag_check,
    ):
        mock_get_profile.return_value = lite_profile

        mock_miner = MagicMock()
        mock_miner.suggest_next.return_value = [{"action": "Basic Task"}]
        mock_miner.analyze_project_state.return_value = "Active"
        mock_get_miner.return_value = mock_miner

        # Simulate LITE restriction
        mock_should_tool.side_effect = lambda tool, prof: tool != "boring_rag_index"

        # Mock RAG check check - needs __name__ for ThreadPoolExecutor
        mock_rag_check.return_value = [
            {"type": "rag_not_indexed", "action": "Run `boring_rag_index` now", "priority": "high"}
        ]
        mock_rag_check.__name__ = "_check_rag_index"

        # Mock others and ensure they have __name__ attributes
        with (
            patch("boring.mcp.tools.assistant._check_git_changes", return_value=[]) as m1,
            patch("boring.mcp.tools.assistant._check_learned_patterns", return_value=[]) as m2,
            patch("boring.mcp.tools.assistant._check_task_progress", return_value=[]) as m3,
            patch("boring.mcp.tools.assistant._check_project_empty", return_value=[]) as m4,
        ):
            m1.__name__ = "_check_git_changes"
            m2.__name__ = "_check_learned_patterns"
            m3.__name__ = "_check_task_progress"
            m4.__name__ = "_check_project_empty"

            result = boring_suggest_next(limit=5)

            # Verify
            assert result["status"] == "SUCCESS"
            enhancements = result["context_enhancements"]
            rag_suggestion = next(
                item for item in enhancements if item["type"] == "rag_not_indexed"
            )

            assert "Switch to STANDARD profile" in rag_suggestion["action"]
            assert "boring_rag_index" not in rag_suggestion["action"]


def test_suggest_next_allowed_in_full_profile():
    boring_suggest_next = get_boring_suggest_next_function()
    full_profile = ProfileConfig(name="full", description="Full", tools=None)

    with (
        patch("boring.mcp.tools.assistant.get_pattern_miner") as mock_get_miner,
        patch("boring.mcp.tool_profiles.get_profile", return_value=full_profile),
        patch("boring.mcp.tool_profiles.should_register_tool", return_value=True),
        patch("boring.mcp.tools.assistant._check_rag_index") as mock_rag_check,
    ):
        mock_get_miner.return_value.suggest_next.return_value = []
        mock_get_miner.return_value.analyze_project_state.return_value = ""
        mock_rag_check.return_value = [
            {"type": "rag_not_indexed", "action": "Run `boring_rag_index`"}
        ]
        mock_rag_check.__name__ = "_check_rag_index"

        with (
            patch("boring.mcp.tools.assistant._check_git_changes", return_value=[]) as m1,
            patch("boring.mcp.tools.assistant._check_learned_patterns", return_value=[]) as m2,
            patch("boring.mcp.tools.assistant._check_task_progress", return_value=[]) as m3,
            patch("boring.mcp.tools.assistant._check_project_empty", return_value=[]) as m4,
        ):
            m1.__name__ = "_check_git_changes"
            m2.__name__ = "_check_learned_patterns"
            m3.__name__ = "_check_task_progress"
            m4.__name__ = "_check_project_empty"

            result = boring_suggest_next()
            assert "Run `boring_rag_index`" in result["context_enhancements"][0]["action"]
