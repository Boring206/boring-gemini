from unittest.mock import MagicMock, patch

from boring.mcp.tools.knowledge import boring_brain_summary, boring_create_rubrics, boring_learn


class TestKnowledgeTools:
    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.brain_manager.BrainManager")
    @patch("boring.storage.SQLiteStorage")
    def test_boring_learn_success(self, mock_storage_cls, mock_brain_cls, mock_get_root):
        """Test learning trigger."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_brain = MagicMock()
        mock_brain.learn_from_memory.return_value = {"patterns": 5}
        mock_brain_cls.return_value = mock_brain

        res = boring_learn()

        assert res["patterns"] == 5
        mock_brain.learn_from_memory.assert_called_once()
        mock_storage_cls.assert_called_once()

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.brain_manager.BrainManager")
    def test_boring_create_rubrics(self, mock_brain_cls, mock_get_root):
        """Test rubric creation."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_brain = MagicMock()
        mock_brain.create_default_rubrics.return_value = ["rubric1", "rubric2"]
        mock_brain_cls.return_value = mock_brain

        res = boring_create_rubrics()

        assert len(res) == 2
        mock_brain.create_default_rubrics.assert_called_once()

    @patch("boring.mcp.tools.knowledge.get_project_root_or_error")
    @patch("boring.brain_manager.BrainManager")
    def test_boring_brain_summary(self, mock_brain_cls, mock_get_root):
        """Test brain summary."""
        mock_get_root.return_value = (MagicMock(), None)

        mock_brain = MagicMock()
        mock_brain.get_brain_summary.return_value = {"patterns": 10}
        mock_brain_cls.return_value = mock_brain

        res = boring_brain_summary()

        assert res["patterns"] == 10
        mock_brain.get_brain_summary.assert_called_once()
