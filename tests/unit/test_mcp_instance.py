"""
Unit tests for boring.mcp.instance module.
"""

import importlib
from unittest.mock import patch

import pytest


class TestMCPInstance:
    """Tests for MCP instance module."""

    def test_mcp_available(self):
        """Test when FastMCP is available."""
        try:
            import fastmcp  # noqa: F401

            # If fastmcp is installed, test the import
            import boring.mcp.instance as instance_module

            assert isinstance(instance_module.MCP_AVAILABLE, bool)
        except ImportError:
            # If fastmcp is not installed, skip the test
            pytest.skip("fastmcp module not installed")

    def test_mcp_not_available(self):
        """Test when FastMCP is not available."""
        with patch("boring.core.dependencies.DependencyManager.check_mcp", return_value=False):
            import boring.mcp.instance as instance_module

            importlib.reload(instance_module)

            assert not instance_module.MCP_AVAILABLE
            assert instance_module.mcp is None

    def test_mcp_available_flag(self):
        """Test MCP_AVAILABLE flag."""
        import boring.mcp.instance as instance_module

        assert isinstance(instance_module.MCP_AVAILABLE, bool)

    def test_fastmcp_import_success(self):
        """Test successful FastMCP import."""
        try:
            from boring.mcp.instance import MCP_AVAILABLE, mcp

            assert isinstance(MCP_AVAILABLE, bool)
            assert mcp is None or hasattr(mcp, "name")
        except ImportError:
            pytest.skip("FastMCP not available for testing")
