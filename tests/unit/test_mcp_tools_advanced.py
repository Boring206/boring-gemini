"""
Unit tests for boring.mcp.tools.advanced module.
"""

from unittest.mock import MagicMock, patch

import pytest

from boring.mcp.tools import advanced


@pytest.fixture
def temp_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return project


class TestAdvancedTools:
    """Tests for advanced MCP tools."""

    def test_boring_security_scan_full(self, temp_project):
        """Test boring_security_scan with full scan."""
        mock_scanner = MagicMock()
        mock_report = MagicMock()
        mock_report.passed = True
        mock_report.total_issues = 0
        mock_report.secrets_found = []
        mock_report.vulnerabilities_found = []
        mock_report.dependency_issues = []
        mock_report.issues = []
        mock_scanner.report = mock_report

        with (
            patch("boring.security.SecurityScanner", return_value=mock_scanner),
            patch("boring.config.settings") as mock_settings,
        ):
            mock_settings.PROJECT_ROOT = temp_project

            result = advanced.boring_security_scan(project_path=str(temp_project), scan_type="full")

            assert result["passed"] is True
            assert result["total_issues"] == 0
            mock_scanner.full_scan.assert_called_once()

    def test_boring_security_scan_secrets(self, temp_project):
        """Test boring_security_scan with secrets scan."""
        mock_scanner = MagicMock()
        mock_report = MagicMock()
        mock_report.passed = True
        mock_report.total_issues = 0
        mock_report.secrets_found = []
        mock_report.issues = []
        mock_scanner.report = mock_report

        with (
            patch("boring.security.SecurityScanner", return_value=mock_scanner),
            patch("boring.config.settings") as mock_settings,
        ):
            mock_settings.PROJECT_ROOT = temp_project

            advanced.boring_security_scan(scan_type="secrets")

            mock_scanner.scan_secrets.assert_called_once()

    def test_boring_security_scan_vulnerabilities(self, temp_project):
        """Test boring_security_scan with vulnerabilities scan."""
        mock_scanner = MagicMock()
        mock_report = MagicMock()
        mock_report.passed = True
        mock_report.total_issues = 0
        mock_report.vulnerabilities_found = []
        mock_report.issues = []
        mock_scanner.report = mock_report

        with (
            patch("boring.security.SecurityScanner", return_value=mock_scanner),
            patch("boring.config.settings") as mock_settings,
        ):
            mock_settings.PROJECT_ROOT = temp_project

            advanced.boring_security_scan(scan_type="vulnerabilities")

            mock_scanner.scan_vulnerabilities.assert_called_once()

    def test_boring_security_scan_dependencies(self, temp_project):
        """Test boring_security_scan with dependencies scan."""
        mock_scanner = MagicMock()
        mock_report = MagicMock()
        mock_report.passed = True
        mock_report.total_issues = 0
        mock_report.dependency_issues = []
        mock_report.issues = []
        mock_scanner.report = mock_report

        with (
            patch("boring.security.SecurityScanner", return_value=mock_scanner),
            patch("boring.config.settings") as mock_settings,
        ):
            mock_settings.PROJECT_ROOT = temp_project

            advanced.boring_security_scan(scan_type="dependencies")

            mock_scanner.scan_dependencies.assert_called_once()

    def test_boring_transaction_start(self, temp_project):
        """Test boring_transaction start action."""
        with patch(
            "boring.transactions.start_transaction", return_value={"status": "started"}
        ) as mock_start:
            result = advanced.boring_transaction(action="start", description="Test transaction")

            assert result["status"] == "started"
            mock_start.assert_called_once()

    def test_boring_transaction_commit(self, temp_project):
        """Test boring_transaction commit action."""
        with patch(
            "boring.transactions.commit_transaction", return_value={"status": "committed"}
        ) as mock_commit:
            result = advanced.boring_transaction(action="commit")

            assert result["status"] == "committed"
            mock_commit.assert_called_once()

    def test_boring_transaction_rollback(self, temp_project):
        """Test boring_transaction rollback action."""
        with patch(
            "boring.transactions.rollback_transaction", return_value={"status": "rolled_back"}
        ) as mock_rollback:
            result = advanced.boring_transaction(action="rollback")

            assert result["status"] == "rolled_back"
            mock_rollback.assert_called_once()

    def test_boring_transaction_status(self, temp_project):
        """Test boring_transaction status action."""
        with patch(
            "boring.transactions.transaction_status", return_value={"status": "active"}
        ) as mock_status:
            result = advanced.boring_transaction(action="status")

            assert result["status"] == "active"
            mock_status.assert_called_once()

    def test_boring_transaction_unknown_action(self):
        """Test boring_transaction with unknown action."""
        result = advanced.boring_transaction(action="unknown")

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    def test_boring_task_submit(self, temp_project):
        """Test boring_task submit action."""
        with patch(
            "boring.background_agent.submit_background_task", return_value={"task_id": "123"}
        ) as mock_submit:
            result = advanced.boring_task(
                action="submit", task_type="verify", task_args={"level": "FULL"}
            )

            assert result["task_id"] == "123"
            mock_submit.assert_called_once_with("verify", {"level": "FULL"}, None)

    def test_boring_task_submit_no_type(self):
        """Test boring_task submit without task_type."""
        result = advanced.boring_task(action="submit")

        assert result["status"] == "error"
        assert "task_type is required" in result["message"]

    def test_boring_task_status(self):
        """Test boring_task status action."""
        with patch(
            "boring.background_agent.get_task_status", return_value={"status": "completed"}
        ) as mock_status:
            result = advanced.boring_task(action="status", task_id="123")

            assert result["status"] == "completed"
            mock_status.assert_called_once_with("123")

    def test_boring_task_status_no_id(self):
        """Test boring_task status without task_id."""
        result = advanced.boring_task(action="status")

        assert result["status"] == "error"
        assert "task_id is required" in result["message"]

    def test_boring_task_list(self):
        """Test boring_task list action."""
        with patch(
            "boring.background_agent.list_background_tasks", return_value={"tasks": []}
        ) as mock_list:
            result = advanced.boring_task(action="list")

            assert "tasks" in result
            mock_list.assert_called_once()

    def test_boring_task_unknown_action(self):
        """Test boring_task with unknown action."""
        result = advanced.boring_task(action="unknown")

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    def test_boring_context_save(self, temp_project):
        """Test boring_context save action."""
        with patch(
            "boring.context_sync.save_context", return_value={"status": "saved"}
        ) as mock_save:
            result = advanced.boring_context(
                action="save", context_id="ctx1", summary="Test context"
            )

            assert result["status"] == "saved"
            mock_save.assert_called_once_with("ctx1", "Test context", None)

    def test_boring_context_save_missing_params(self):
        """Test boring_context save without required params."""
        result = advanced.boring_context(action="save")

        assert result["status"] == "error"
        assert "context_id and summary are required" in result["message"]

    def test_boring_context_load(self, temp_project):
        """Test boring_context load action."""
        with patch(
            "boring.context_sync.load_context", return_value={"status": "loaded"}
        ) as mock_load:
            result = advanced.boring_context(action="load", context_id="ctx1")

            assert result["status"] == "loaded"
            mock_load.assert_called_once_with("ctx1", None)

    def test_boring_context_load_no_id(self):
        """Test boring_context load without context_id."""
        result = advanced.boring_context(action="load")

        assert result["status"] == "error"
        assert "context_id is required" in result["message"]

    def test_boring_context_list(self, temp_project):
        """Test boring_context list action."""
        with patch("boring.context_sync.list_contexts", return_value={"contexts": []}) as mock_list:
            result = advanced.boring_context(action="list")

            assert "contexts" in result
            mock_list.assert_called_once()

    def test_boring_context_unknown_action(self):
        """Test boring_context with unknown action."""
        result = advanced.boring_context(action="unknown")

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    def test_boring_profile_get(self):
        """Test boring_profile get action."""
        with patch(
            "boring.context_sync.get_user_profile", return_value={"name": "test"}
        ) as mock_get:
            result = advanced.boring_profile(action="get")

            assert result["name"] == "test"
            mock_get.assert_called_once()

    def test_boring_profile_learn(self):
        """Test boring_profile learn action."""
        with patch(
            "boring.context_sync.learn_fix", return_value={"status": "learned"}
        ) as mock_learn:
            result = advanced.boring_profile(
                action="learn",
                error_pattern="Error pattern",
                fix_pattern="Fix pattern",
                context="Context",
            )

            assert result["status"] == "learned"
            mock_learn.assert_called_once_with("Error pattern", "Fix pattern", "Context")

    def test_boring_profile_learn_missing_params(self):
        """Test boring_profile learn without required params."""
        result = advanced.boring_profile(action="learn")

        assert result["status"] == "error"
        assert "error_pattern and fix_pattern required" in result["message"]

    def test_boring_profile_unknown_action(self):
        """Test boring_profile with unknown action."""
        result = advanced.boring_profile(action="unknown")

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    def test_register_advanced_tools(self):
        """Test registering advanced tools."""
        mock_mcp = MagicMock()

        advanced.register_advanced_tools(mock_mcp)

        # Should register 5 tools
        assert mock_mcp.tool.call_count == 5

        # Check tool descriptions
        [str(call) for call in mock_mcp.tool.call_args_list]
        assert any("security scan" in str(call).lower() for call in mock_mcp.tool.call_args_list)
        assert any("transaction" in str(call).lower() for call in mock_mcp.tool.call_args_list)
        assert any("background task" in str(call).lower() for call in mock_mcp.tool.call_args_list)
        assert any(
            "conversation context" in str(call).lower() for call in mock_mcp.tool.call_args_list
        )
        assert any("user profile" in str(call).lower() for call in mock_mcp.tool.call_args_list)
