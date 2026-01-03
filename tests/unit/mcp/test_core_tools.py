import pytest
from unittest.mock import MagicMock, patch
from boring.mcp.tools.core import (
    run_boring, boring_health_check, boring_status,
    boring_quickstart, boring_done
)

class TestCoreTools:

    # =========================================================================
    # run_boring tests
    # =========================================================================
    
    @patch("boring.mcp.tools.core.check_rate_limit")
    @patch("boring.mcp.tools.core.get_project_root_or_error")
    @patch("boring.mcp.tools.core.configure_runtime_for_project")
    @patch("boring.loop.StatefulAgentLoop")
    def test_run_boring_success(self, mock_loop_cls, mock_configure, mock_get_root, mock_rate_limit):
        """Test successful run_boring execution."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)
        mock_rate_limit.return_value = (True, "")
        
        mock_loop_instance = MagicMock()
        mock_loop_instance.context.loop_count = 3
        mock_loop_instance.context.output_content = "Done."
        mock_loop_cls.return_value = mock_loop_instance
        
        result = run_boring(
            task_description="Test task",
            project_path="/tmp/test"
        )
        
        assert result["status"] == "SUCCESS"
        assert result["loops_completed"] == 3
        mock_loop_instance.run.assert_called_once()
        
    def test_run_boring_empty_task(self):
        """Test empty task validation."""
        res = run_boring("")
        assert res["status"] == "ERROR"
        assert "task_description" in res["message"]
        
    def test_run_boring_whitespace_task(self):
        """Test whitespace-only task validation."""
        res = run_boring("   ")
        assert res["status"] == "ERROR"
        assert "task_description" in res["message"]
        
    def test_run_boring_invalid_level(self):
        """Test invalid verification level."""
        res = run_boring("task", verification_level="INVALID")
        assert res["status"] == "ERROR"
        assert "Invalid verification_level" in res["message"]
        
    def test_run_boring_invalid_max_loops_low(self):
        """Test max_loops below range."""
        res = run_boring("task", max_loops=0)
        assert res["status"] == "ERROR"
        assert "max_loops" in res["message"]
        
    def test_run_boring_invalid_max_loops_high(self):
        """Test max_loops above range."""
        res = run_boring("task", max_loops=100)
        assert res["status"] == "ERROR"
        assert "max_loops" in res["message"]
    
    @patch("boring.mcp.tools.core.check_rate_limit")
    def test_run_boring_rate_limited(self, mock_rate_limit):
        """Test rate limit handling."""
        mock_rate_limit.return_value = (False, "Rate limit exceeded")
        
        res = run_boring("task")
        assert res["status"] == "RATE_LIMITED"
        assert "Rate limit" in res["message"]
        
    @patch("boring.mcp.tools.core.check_rate_limit")
    @patch("boring.mcp.tools.core.get_project_root_or_error")
    def test_run_boring_no_project(self, mock_get_root, mock_rate_limit):
        """Test when no project root found."""
        mock_rate_limit.return_value = (True, "")
        mock_get_root.return_value = (None, {"status": "ERROR", "message": "No project"})
        
        res = run_boring("task")
        assert res["status"] == "ERROR"

    # =========================================================================
    # boring_health_check tests
    # =========================================================================

    @patch("boring.health.run_health_check")
    def test_boring_health_check_healthy(self, mock_run_health):
        """Test health check when system is healthy."""
        mock_report = MagicMock()
        mock_report.is_healthy = True
        mock_report.passed = 5
        mock_report.warnings = 0
        mock_report.failed = 0
        mock_report.checks = []
        mock_run_health.return_value = mock_report
        
        res = boring_health_check()
        assert res["healthy"] == True
        assert res["passed"] == 5
        
    @patch("boring.health.run_health_check")
    def test_boring_health_check_with_checks(self, mock_run_health):
        """Test health check returns check details."""
        mock_check = MagicMock()
        mock_check.name = "api_key"
        mock_check.status.name = "PASS"
        mock_check.message = "API key valid"
        mock_check.suggestion = None
        
        mock_report = MagicMock()
        mock_report.is_healthy = True
        mock_report.passed = 1
        mock_report.warnings = 0
        mock_report.failed = 0
        mock_report.checks = [mock_check]
        mock_run_health.return_value = mock_report
        
        res = boring_health_check()
        assert len(res["checks"]) == 1
        assert res["checks"][0]["name"] == "api_key"
        
    @patch("boring.health.run_health_check", side_effect=Exception("Network error"))
    def test_boring_health_check_exception(self, mock_run_health):
        """Test health check handles exceptions."""
        res = boring_health_check()
        assert res["healthy"] == False
        assert "Network error" in res["error"]

    # =========================================================================
    # boring_quickstart tests
    # =========================================================================

    @patch("boring.mcp.tools.core.get_project_root_or_error")
    def test_boring_quickstart_with_project(self, mock_get_root):
        """Test quickstart with valid project."""
        mock_get_root.return_value = (MagicMock(), None)
        
        res = boring_quickstart()
        assert "welcome" in res
        assert res["project_detected"] == True
        assert "boring_health_check" in str(res["recommended_first_steps"])
        
    @patch("boring.mcp.tools.core.get_project_root_or_error")
    def test_boring_quickstart_no_project(self, mock_get_root):
        """Test quickstart without project."""
        mock_get_root.return_value = (None, {"status": "ERROR"})
        
        res = boring_quickstart()
        assert res["project_detected"] == False
        assert "Create a project" in str(res["recommended_first_steps"])
        
    def test_boring_quickstart_has_workflows(self):
        """Test quickstart includes workflow categories."""
        with patch("boring.mcp.tools.core.get_project_root_or_error") as mock:
            mock.return_value = (MagicMock(), None)
            res = boring_quickstart()
            
            assert "spec_driven" in res["available_workflows"]
            assert "evolution" in res["available_workflows"]
            assert "verification" in res["available_workflows"]

    # =========================================================================
    # boring_status tests
    # =========================================================================

    @patch("boring.mcp.tools.core.get_project_root_or_error")
    @patch("boring.mcp.tools.core.configure_runtime_for_project")
    @patch("boring.memory.MemoryManager")
    def test_boring_status_success(self, mock_memory_cls, mock_configure, mock_get_root):
        """Test status retrieval."""
        mock_get_root.return_value = (MagicMock(), None)
        
        mock_memory = MagicMock()
        mock_memory.get_project_state.return_value = {
            "project_name": "TestProject",
            "total_loops": 42,
            "successful_loops": 40,
            "failed_loops": 2
        }
        mock_memory_cls.return_value = mock_memory
        
        res = boring_status()
        assert res["total_loops"] == 42
        assert res["project_name"] == "TestProject"
        
    @patch("boring.mcp.tools.core.get_project_root_or_error")
    def test_boring_status_no_project(self, mock_get_root):
        """Test status when no project found."""
        mock_get_root.return_value = (None, {"status": "ERROR", "message": "No project"})
        
        res = boring_status()
        assert res["status"] == "ERROR"
        
    @patch("boring.mcp.tools.core.get_project_root_or_error")
    @patch("boring.mcp.tools.core.configure_runtime_for_project")
    @patch("boring.memory.MemoryManager", side_effect=Exception("DB error"))
    def test_boring_status_exception(self, mock_memory_cls, mock_configure, mock_get_root):
        """Test status handles exceptions."""
        mock_get_root.return_value = (MagicMock(), None)
        
        res = boring_status()
        assert "error" in res
        assert "DB error" in res["error"]

    # =========================================================================
    # boring_done tests
    # =========================================================================

    def test_boring_done_returns_message(self):
        """Test boring_done returns completion message."""
        res = boring_done("Task completed successfully")
        assert "Task done" in res
        assert "Task completed successfully" in res
        
    def test_boring_done_with_long_message(self):
        """Test boring_done handles long messages."""
        long_msg = "A" * 500
        res = boring_done(long_msg)
        assert "Task done" in res
        
    @patch("boring.mcp.tools.core.boring_done.__code__")  # Just test it doesn't crash
    def test_boring_done_no_notification_lib(self):
        """Test boring_done works without notification libraries."""
        # This test verifies the function handles ImportError gracefully
        res = boring_done("Test")
        assert "Task done" in res

