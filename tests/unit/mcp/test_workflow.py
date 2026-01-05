from unittest.mock import MagicMock, patch

from boring.mcp.tools.workflow import (
    boring_install_workflow,
    boring_list_workflows,
    speckit_evolve_workflow,
    speckit_reset_workflow,
)


class TestWorkflowTools:
    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.workflow_evolver.WorkflowEvolver")
    def test_speckit_evolve_workflow(self, mock_evolver_cls, mock_get_root):
        """Test workflow evolution."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_evolver = MagicMock()
        mock_evolver.evolve_workflow.return_value = {"status": "SUCCESS"}
        mock_evolver_cls.return_value = mock_evolver

        res = speckit_evolve_workflow("speckit-plan", "content", "reason")

        assert res["status"] == "SUCCESS"
        mock_evolver.evolve_workflow.assert_called_once()

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    @patch("boring.workflow_evolver.WorkflowEvolver")
    def test_speckit_reset_workflow(self, mock_evolver_cls, mock_get_root):
        """Test workflow reset."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_evolver = MagicMock()
        mock_evolver.reset_workflow.return_value = {"status": "SUCCESS"}
        mock_evolver_cls.return_value = mock_evolver

        res = speckit_reset_workflow("speckit-plan")

        assert res["status"] == "SUCCESS"
        mock_evolver.reset_workflow.assert_called_once()

    @patch("boring.mcp.tools.workflow.detect_project_root")
    @patch("boring.workflow_manager.WorkflowManager")
    def test_boring_install_workflow(self, mock_manager_cls, mock_detect_root):
        """Test workflow installation."""
        mock_detect_root.return_value = MagicMock()

        mock_manager = MagicMock()
        mock_manager.install_workflow.return_value = (True, "Installed")
        mock_manager_cls.return_value = mock_manager

        res = boring_install_workflow("source.json")

        assert "✅" in res
        mock_manager.install_workflow.assert_called_once()

    @patch("boring.mcp.tools.workflow.get_project_root_or_error")
    def test_boring_list_workflows(self, mock_get_root):
        """Test listing workflows."""
        mock_root = MagicMock()
        mock_get_root.return_value = (mock_root, None)

        # Mock glob
        mock_file = MagicMock()
        mock_file.stem = "test"
        mock_file.name = "test.md"
        mock_file.read_text.return_value = "---\ndescription: Test\n---"
        mock_root.__truediv__.return_value.__truediv__.return_value.glob.return_value = [mock_file]
        mock_root.__truediv__.return_value.__truediv__.return_value.exists.return_value = True

        res = boring_list_workflows()

        assert res["status"] == "SUCCESS"
        assert len(res["workflows"]) == 1
        assert res["workflows"][0]["description"] == "Test"
