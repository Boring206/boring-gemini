import pytest
from unittest.mock import MagicMock, patch

# Check if MCP is available
try:
    from boring.mcp.resources import get_project_status, get_prompt, get_workflows
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    get_project_status = None
    get_prompt = None
    get_workflows = None


@pytest.mark.skipif(not MCP_AVAILABLE, reason="FastMCP not available")
class TestResources:

    @patch("boring.mcp.resources.detect_project_root")
    @patch("boring.memory.MemoryManager")
    def test_get_project_status(self, mock_mem_cls, mock_detect):
        """Test status resource."""
        mock_detect.return_value = MagicMock()
        
        mock_mem = MagicMock()
        mock_mem.get_project_state.return_value = {"status": "ok"}
        mock_mem_cls.return_value = mock_mem
        
        res = get_project_status.fn()
        assert "status" in res
        assert "ok" in res

    @patch("boring.mcp.resources.detect_project_root")
    def test_get_prompt(self, mock_detect):
        """Test prompt resource."""
        mock_root = MagicMock()
        
        # Mock / operator (root / "PROMPT.md")
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "# Spec"
        mock_root.__truediv__.return_value = mock_file
        
        mock_detect.return_value = mock_root
        
        res = get_prompt.fn()
        assert res == "# Spec"

