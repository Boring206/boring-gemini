import importlib
import json
import sys
from unittest.mock import MagicMock, patch

import pytest


# We need to ensure we can import the module with mcp available
@pytest.fixture(autouse=True)
def setup_mcp_env():
    # Patch the dependencies before import
    with (
        patch("boring.mcp.instance.MCP_AVAILABLE", True),
        patch("boring.mcp.instance.mcp") as mock_mcp,
    ):
        # Define the resource decorator mock to return the original function
        def resource_decorator(uri):
            def wrapper(func):
                func._mcp_uri = uri  # tag it for verification if needed
                return func

            return wrapper

        mock_mcp.resource = MagicMock(side_effect=resource_decorator)

        # Reload resources module to apply the patches
        if "boring.mcp.resources" in sys.modules:
            importlib.reload(sys.modules["boring.mcp.resources"])
        else:
            pass

        yield mock_mcp


def test_get_project_status(tmp_path):
    from boring.mcp.resources import get_project_status

    # Case 1: No project root
    with patch("boring.mcp.resources.detect_project_root", return_value=None):
        res = get_project_status()
        assert "No project detected" in res

    # Case 2: Valid project root
    with (
        patch("boring.mcp.resources.detect_project_root", return_value=tmp_path),
        patch("boring.intelligence.MemoryManager") as MockMM,
    ):
        mock_mm_instance = MockMM.return_value
        mock_mm_instance.get_project_state.return_value = {"state": "good"}

        res = get_project_status()
        assert "{'state': 'good'}" == res
        assert (tmp_path / "logs").exists()


def test_get_prompt(tmp_path):
    from boring.mcp.resources import get_prompt

    # Case 1: No project root
    with patch("boring.mcp.resources.detect_project_root", return_value=None):
        assert "No project detected" in get_prompt()

    # Case 2: No PROMPT.md
    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        assert "PROMPT.md not found" in get_prompt()

    # Case 3: Valid PROMPT.md
    prompt_file = tmp_path / "PROMPT.md"
    prompt_file.write_text("System Prompt", encoding="utf-8")

    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        assert "System Prompt" in get_prompt()


def test_get_workflows(tmp_path):
    from boring.mcp.resources import get_workflows

    # Case 1: No root
    with patch("boring.mcp.resources.detect_project_root", return_value=None):
        assert "[]" == get_workflows()

    # Case 2: No workflows dir
    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        assert "[]" == get_workflows()

    # Case 3: Workflows exist
    workflows_dir = tmp_path / ".agent" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "deploy.md").touch()
    (workflows_dir / "test.md").touch()

    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        res = get_workflows()
        assert "deploy" in res
        assert "test" in res


def test_get_project_config(tmp_path):
    from boring.mcp.resources import get_project_config

    # Case 1: No root
    with patch("boring.mcp.resources.detect_project_root", return_value=None):
        assert "No project detected" in get_project_config()

    # Case 2: Config exists
    boring_dir = tmp_path / ".boring"
    boring_dir.mkdir()
    config_file = boring_dir / "config.yaml"
    config_file.write_text("feature_flag: true", encoding="utf-8")

    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        res = get_project_config()
        data = json.loads(res)
        assert data["boring_config_exists"] is True
        assert data["boring_config"]["feature_flag"] is True

    # Case 3: Malformed config (Tab is illegal in YAML)
    config_file.write_text("\tkey: value", encoding="utf-8")
    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        res = get_project_config()
        data = json.loads(res)
        assert "boring_config" not in data


def test_get_project_tasks(tmp_path):
    from boring.mcp.resources import get_project_tasks

    # Case 1: No root
    with patch("boring.mcp.resources.detect_project_root", return_value=None):
        assert "No project detected" in get_project_tasks()

    # Case 2: No task.md
    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        res = json.loads(get_project_tasks())
        assert res["status"] == "not_found"

    # Case 3: Valid task.md
    task_file = tmp_path / "task.md"
    task_file.write_text(
        """
    - [x] Done task
    - [ ] Pending task 1
    - [ ] Pending task 2
    """,
        encoding="utf-8",
    )

    with patch("boring.mcp.resources.detect_project_root", return_value=tmp_path):
        res = json.loads(get_project_tasks())
        assert res["completed"] == 1
        assert res["pending"] == 2
        assert res["total"] == 3
