"""
Unit tests for MCP Vibe Tools (extra coverage).
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from boring.mcp.vibe_tools import register_vibe_tools

@pytest.fixture
def mcp_mock():
    mcp = MagicMock()
    return mcp

@pytest.fixture
def helpers_mock():
    return {
        "get_project_root_or_error": MagicMock(return_value=(Path("/tmp"), None)),
        "configure_runtime": MagicMock(),
    }

def get_registered_funcs(mcp_mock, helpers_mock):
    funcs = {}
    def capture_tool(description=None, annotations=None):
        def wrapper(func):
            funcs[func.__name__] = func
            return func
        return wrapper
    mcp_mock.tool = capture_tool
    register_vibe_tools(mcp_mock, lambda x: x, helpers_mock)
    return funcs

def test_boring_vibe_check_basic(mcp_mock, helpers_mock):
    with patch("boring.mcp.vibe_tools.vibe_engine") as mock_engine:
        with patch("boring.mcp.vibe_tools.SecurityScanner") as mock_scanner:
            # Mock engine results
            mock_engine.perform_code_review.return_value.issues = []
            mock_engine.extract_documentation.return_value.items = []
            
            # Mock scanner
            mock_scanner.return_value.scan_for_secrets.return_value.issues = []
            
            funcs = get_registered_funcs(mcp_mock, helpers_mock)
            
            # Test with a fake file
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.read_text", return_value="print('hello')"):
                        result = funcs["boring_vibe_check"](target_path="test.py")
                        
                        assert result["status"] == "SUCCESS"
                        assert result["score"] == 100
                        assert "S-Tier" in result["tier"]

def test_boring_vibe_check_with_issues(mcp_mock, helpers_mock):
    with patch("boring.mcp.vibe_tools.vibe_engine") as mock_engine:
        with patch("boring.mcp.vibe_tools.SecurityScanner") as mock_scanner:
            # Mock issue
            mock_issue = MagicMock()
            mock_issue.severity = "high"
            mock_issue.message = "Bad code"
            mock_issue.line = 10
            mock_engine.perform_code_review.return_value.issues = [mock_issue]
            mock_engine.extract_documentation.return_value.items = []
            
            # Mock scanner
            mock_scanner.return_value.scan_for_secrets.return_value.issues = []
            
            funcs = get_registered_funcs(mcp_mock, helpers_mock)
            
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.read_text", return_value="print('bad')"):
                        result = funcs["boring_vibe_check"](target_path="bad.py")
                        
                        assert result["status"] == "SUCCESS"
                        assert result["score"] < 100
                        assert "A-Tier" in result["tier"] or "B-Tier" in result["tier"]

def test_boring_vibe_check_storage_integration(mcp_mock, helpers_mock):
    with patch("boring.mcp.vibe_tools._get_storage") as mock_get_storage:
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        # Mock history with previous score
        mock_storage.get_metrics.return_value = [{"metric_value": 80.0}, {"metric_value": 70.0}]
        
        with patch("boring.mcp.vibe_tools.vibe_engine") as mock_engine:
            mock_engine.perform_code_review.return_value.issues = []
            mock_engine.extract_documentation.return_value.items = []
            
            funcs = get_registered_funcs(mcp_mock, helpers_mock)
            
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("pathlib.Path.read_text", return_value="test"):
                        result = funcs["boring_vibe_check"](target_path="test.py")
                        
                        assert result["status"] == "SUCCESS"
                        mock_storage.record_metric.assert_called()
                        # Should show trend
                        assert "📈" in result["score_trend"] or "➡️" in result["score_trend"]
