"""
Tests for healer node.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.flow.nodes.base import NodeResult
from boring.flow.nodes.healer import HealerNode


class TestHealerNode:
    """Tests for HealerNode."""

    @pytest.fixture
    def healer(self):
        return HealerNode()

    @pytest.fixture
    def mock_context(self, tmp_path):
        context = MagicMock()
        context.project_root = tmp_path
        context.last_error = None
        return context

    def test_healer_node_initialization(self, healer):
        """Test healer node initialization."""
        assert healer.name == "Healer"

    def test_execute_no_error(self, healer, mock_context):
        """Test process when there's no error."""
        mock_context.errors = []
        result = healer.process(mock_context)
        assert isinstance(result, NodeResult)

    def test_execute_with_module_error(self, healer, mock_context):
        """Test process with module import error."""
        mock_context.errors = ["ModuleNotFoundError: No module named 'test_module'"]

        with (
            patch("boring.loop.shadow_mode.create_shadow_guard") as mock_guard,
            patch("boring.mcp.tools.git.boring_checkpoint") as _mock_checkpoint,
            patch("subprocess.check_call") as mock_subprocess,
        ):
            mock_guard_instance = MagicMock()
            mock_guard_instance.mode.value = "NORMAL"
            mock_guard.return_value = mock_guard_instance

            mock_subprocess.return_value = None  # check_call returns None on success

            result = healer.process(mock_context)
            # Should attempt to install module or return success/failure
            assert isinstance(result, NodeResult)

    def test_extract_module_name(self, healer):
        """Test extracting module name from error."""
        error1 = "ModuleNotFoundError: No module named 'requests'"
        module1 = healer._extract_module(error1)
        assert module1 == "requests"

        error2 = "ImportError: cannot import name 'foo' from 'bar'"
        module2 = healer._extract_module(error2)
        # Implementation only handles "No module named" pattern
        assert module2 == ""  # Empty string for non-matching patterns

        error3 = "Some other error"
        module3 = healer._extract_module(error3)
        assert module3 == ""
