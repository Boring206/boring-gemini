import pytest
from unittest.mock import MagicMock, patch
from boring.mcp.tools.integration import boring_setup_extensions, boring_notebooklm_guide

class TestIntegrationTools:

    @patch("boring.mcp.tools.integration.get_project_root_or_error")
    @patch("boring.extensions.ExtensionsManager")
    def test_boring_setup_extensions_success(self, mock_extensions_cls, mock_get_root):
        """Test successful extension setup."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.is_gemini_available.return_value = True
        mock_manager.install_recommended_extensions.return_value = {
            "ext1": (True, "Installed")
        }
        mock_extensions_cls.return_value = mock_manager
        
        res = boring_setup_extensions()
        
        assert res["status"] == "SUCCESS"
        assert "ext1" in res["installed"]
        mock_manager.install_recommended_extensions.assert_called_once()

    @patch("boring.mcp.tools.integration.get_project_root_or_error")
    @patch("boring.extensions.ExtensionsManager")
    def test_boring_setup_extensions_no_gemini(self, mock_extensions_cls, mock_get_root):
        """Test setup gracefully handles missing Gemini CLI."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_manager = MagicMock()
        mock_manager.is_gemini_available.return_value = False
        mock_extensions_cls.return_value = mock_manager
        
        res = boring_setup_extensions()
        
        assert res["status"] == "SKIPPED"
        mock_manager.install_recommended_extensions.assert_not_called()

    def test_boring_notebooklm_guide(self):
        """Test guide retrieval."""
        res = boring_notebooklm_guide()
        assert "NotebookLM Integration Guide" in res
