from unittest.mock import MagicMock, patch

from boring.mcp.tools.git import boring_checkpoint, boring_commit, boring_hooks_status


class TestGitTools:
    """Tests for Git MCP Tools."""

    def test_boring_hooks_status(self, tmp_path):
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(tmp_path, None)):
            with patch("boring.mcp.tools.git.HooksManager") as mock_manager:
                mock_inst = mock_manager.return_value
                mock_inst.status.return_value = {"is_git_repo": True, "hooks": {}}

                result = boring_hooks_status(project_path=str(tmp_path))
                assert result["is_git_repo"] is True

    def test_boring_commit_no_tasks(self, tmp_path):
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(tmp_path, None)):
            # Task file exists but empty
            task_file = tmp_path / "task.md"
            task_file.write_text("# Tasks\n- [ ] Todo", encoding="utf-8")

            result = boring_commit(project_path=str(tmp_path))
            assert result["status"] == "NO_COMPLETED_TASKS"

    def test_boring_commit_success(self, tmp_path):
        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(tmp_path, None)):
            task_file = tmp_path / "task.md"
            task_file.write_text("- [x] Add login feature\n- [x] Fix auth bug", encoding="utf-8")

            result = boring_commit(project_path=str(tmp_path))
            assert result["status"] == "SUCCESS"
            assert "feat" in result["message"]
            assert "add login feature" in result["message"]
            assert 'git commit -m "' in result["command"]

    @patch("subprocess.run")
    def test_boring_checkpoint_list(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            stdout="checkpoint/v1\ncheckpoint/v2", stderr="", returncode=0
        )

        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(tmp_path, None)):
            result = boring_checkpoint(action="list", project_path=str(tmp_path))
            assert result["status"] == "SUCCESS"
            assert "v1" in result["checkpoints"]
            assert "v2" in result["checkpoints"]

    @patch("subprocess.run")
    def test_boring_checkpoint_create(self, mock_run, tmp_path):
        import subprocess

        # 1. rev-parse check (fail = not exist)
        # 2. tag command (success)
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git", stderr="not found"),
            MagicMock(stdout="", stderr="", returncode=0),
        ]

        with patch("boring.mcp.tools.git.get_project_root_or_error", return_value=(tmp_path, None)):
            result = boring_checkpoint(action="create", name="save1", project_path=str(tmp_path))
            assert result["status"] == "SUCCESS"
            assert "created" in result["message"]
