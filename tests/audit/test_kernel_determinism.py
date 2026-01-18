import os
from unittest.mock import patch

import pytest

from boring.core.kernel import BoringKernel
from boring.flow.states import FlowStage


@pytest.fixture
def temp_home(tmp_path):
    # Mock user home to a temp dir to isolate "global" config lookups
    with patch("pathlib.Path.home", return_value=tmp_path):
        yield tmp_path


def test_kernel_cli_boot_simulation(temp_home):
    """Simulate CLI Boot (standard)."""
    # CLI typically runs in a subdir or passed root
    project_root = temp_home / "cli_project"
    project_root.mkdir()

    kernel = BoringKernel(project_root)
    # Check initial state
    assert kernel.state_manager.current.stage == FlowStage.SETUP
    # Check paths
    assert kernel.root == project_root
    assert kernel.state_manager.events.ledger_file == project_root / ".boring" / "events.jsonl"

    state = kernel.state_manager.current
    kernel.close()
    return state


def test_kernel_mcp_boot_simulation(temp_home):
    """Simulate MCP Boot (tool call)."""
    # MCP might be running from different cwd
    project_root = temp_home / "mcp_project"
    project_root.mkdir()

    # MCP "boot" is just the Kernel init in the tool function
    # environment vars might differ in real MCP, but Kernel should ignore them unless specified
    with patch.dict(os.environ, {"BORING_MCP_MODE": "1"}):
        kernel = BoringKernel(project_root)

    assert kernel.state_manager.current.stage == FlowStage.SETUP
    assert kernel.root == project_root

    state = kernel.state_manager.current
    kernel.close()
    return state


def test_boot_determinism(temp_home):
    """Verify CLI and MCP produce identical initial states."""
    state_cli = test_kernel_cli_boot_simulation(temp_home)
    state_mcp = test_kernel_mcp_boot_simulation(temp_home)

    # Deep equality check
    # Exclude session_id (which must be unique) and timestamps
    d_cli = state_cli.model_dump(exclude={"session_id", "last_updated"})
    d_mcp = state_mcp.model_dump(exclude={"session_id", "last_updated"})

    assert d_cli == d_mcp


def test_kernel_init_side_effects(temp_home):
    """Verify handlers are registered identically."""
    # Patch it where it's actually CALLED by BoringKernel.create_graph
    with patch("boring.core.kernel.register_auto_handlers") as mock_reg:
        kernel = BoringKernel(temp_home)
        kernel.create_graph({})  # Trigger registration
        mock_reg.assert_called_once()
        kernel.close()

    # Check that it happens EVERY time
    with patch("boring.core.kernel.register_auto_handlers") as mock_reg_2:
        kernel2 = BoringKernel(temp_home)
        kernel2.create_graph({})
        mock_reg_2.assert_called_once()
        kernel2.close()
