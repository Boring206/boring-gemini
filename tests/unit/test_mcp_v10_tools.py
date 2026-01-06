"""
Unit tests for boring.mcp.v10_tools module.
"""

import pytest
from unittest.mock import MagicMock, patch

from boring.mcp import v10_tools


class TestV10Tools:
    """Tests for V10 tools registration."""

    def test_register_v10_tools_success(self):
        """Test registering V10 tools successfully."""
        mock_mcp = MagicMock()
        mock_audited = MagicMock()
        helpers = {}
        
        with patch("boring.mcp.v10_tools.register_rag_tools") as mock_rag, \
             patch("boring.mcp.v10_tools.register_agent_tools") as mock_agent, \
             patch("boring.mcp.v10_tools.register_shadow_tools") as mock_shadow:
            count = v10_tools.register_v10_tools(mock_mcp, mock_audited, helpers)
            
            assert count == 12  # 4 + 3 + 5
            mock_rag.assert_called_once()
            mock_agent.assert_called_once()
            mock_shadow.assert_called_once()

    def test_register_v10_tools_rag_import_error(self):
        """Test registering when RAG tools import fails."""
        mock_mcp = MagicMock()
        mock_audited = MagicMock()
        helpers = {}
        
        with patch("boring.mcp.v10_tools.register_rag_tools", side_effect=ImportError("Error")), \
             patch("boring.mcp.v10_tools.register_agent_tools") as mock_agent, \
             patch("boring.mcp.v10_tools.register_shadow_tools") as mock_shadow, \
             patch("sys.stderr.write"):
            count = v10_tools.register_v10_tools(mock_mcp, mock_audited, helpers)
            
            # Should continue and register other tools
            assert count == 8  # 0 + 3 + 5
            mock_agent.assert_called_once()
            mock_shadow.assert_called_once()

    def test_register_v10_tools_agent_import_error(self):
        """Test registering when agent tools import fails."""
        mock_mcp = MagicMock()
        mock_audited = MagicMock()
        helpers = {}
        
        with patch("boring.mcp.v10_tools.register_rag_tools") as mock_rag, \
             patch("boring.mcp.v10_tools.register_agent_tools", side_effect=ImportError("Error")), \
             patch("boring.mcp.v10_tools.register_shadow_tools") as mock_shadow, \
             patch("sys.stderr.write"):
            count = v10_tools.register_v10_tools(mock_mcp, mock_audited, helpers)
            
            assert count == 9  # 4 + 0 + 5
            mock_rag.assert_called_once()
            mock_shadow.assert_called_once()

    def test_register_v10_tools_shadow_import_error(self):
        """Test registering when shadow tools import fails."""
        mock_mcp = MagicMock()
        mock_audited = MagicMock()
        helpers = {}
        
        with patch("boring.mcp.v10_tools.register_rag_tools") as mock_rag, \
             patch("boring.mcp.v10_tools.register_agent_tools") as mock_agent, \
             patch("boring.mcp.v10_tools.register_shadow_tools", side_effect=ImportError("Error")), \
             patch("sys.stderr.write"):
            count = v10_tools.register_v10_tools(mock_mcp, mock_audited, helpers)
            
            assert count == 7  # 4 + 3 + 0
            mock_rag.assert_called_once()
            mock_agent.assert_called_once()

    def test_register_v10_tools_rag_exception(self):
        """Test registering when RAG tools raise exception."""
        mock_mcp = MagicMock()
        mock_audited = MagicMock()
        helpers = {}
        
        with patch("boring.mcp.v10_tools.register_rag_tools", side_effect=Exception("Error")), \
             patch("boring.mcp.v10_tools.register_agent_tools") as mock_agent, \
             patch("boring.mcp.v10_tools.register_shadow_tools") as mock_shadow, \
             patch("sys.stderr.write"):
            count = v10_tools.register_v10_tools(mock_mcp, mock_audited, helpers)
            
            assert count == 8  # 0 + 3 + 5

