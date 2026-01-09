"""
Unit tests for boring.mcp.instance module.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestMCPInstance:
    """Tests for MCP instance module."""

    def test_mcp_available(self):
        """Test when FastMCP is available."""
        with patch("boring.core.dependencies.DependencyManager.check_mcp", return_value=True):
            import importlib
            import boring.mcp.instance as instance_module
            
            # Use create=True to ensure we can patch it even if not imported
            with patch("boring.mcp.instance.FastMCP", create=True) as mock_fastmcp:
                importlib.reload(instance_module)
                assert instance_module.MCP_AVAILABLE
                assert instance_module.mcp is not None

    def test_mcp_not_available(self):
        """Test when FastMCP is not available."""
        with patch("boring.core.dependencies.DependencyManager.check_mcp", return_value=False):
            import importlib
            import boring.mcp.instance as instance_module
            importlib.reload(instance_module)

            # When FastMCP is not available, mcp should be None
            assert not instance_module.MCP_AVAILABLE
            assert instance_module.mcp is None

    def test_mcp_available_flag(self):
        """Test MCP_AVAILABLE flag."""
        import boring.mcp.instance as instance_module

        # MCP_AVAILABLE should be a boolean
        assert isinstance(instance_module.MCP_AVAILABLE, bool)

    def test_fastmcp_import_success(self):
        """Test successful FastMCP import."""
        # This test verifies the import logic
        try:
            from boring.mcp.instance import MCP_AVAILABLE, mcp

            assert isinstance(MCP_AVAILABLE, bool)
            # mcp should be either None or a FastMCP instance
            assert mcp is None or hasattr(mcp, "name")
        except ImportError:
            pytest.skip("FastMCP not available for testing")
