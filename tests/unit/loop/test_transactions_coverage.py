from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from boring.loop.transactions import TransactionManager, TransactionState


class TestTransactionManager:
    @pytest.fixture
    def temp_project(self, tmp_path):
        project_root = tmp_path / "project"
        project_root.mkdir()
        return project_root

    @pytest.fixture
    def manager(self, temp_project):
        return TransactionManager(temp_project)

    def test_init(self, manager, temp_project):
        assert manager.project_root == temp_project
        assert manager.state_file == temp_project / ".boring_transaction"
        assert manager.current_transaction is None

    @patch("subprocess.run")
    def test_run_git_success(self, mock_run, manager):
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        success, output = manager._run_git(["status"])
        assert success is True
        assert output == "output"
        mock_run.assert_called_once()
        # Verify env has GIT_TERMINAL_PROMPT=0
        args, kwargs = mock_run.call_args
        assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"

    @patch("subprocess.run")
    def test_run_git_failure(self, mock_run, manager):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        success, output = manager._run_git(["status"])
        assert success is False
        assert output == "error"

    @patch("subprocess.run")
    def test_run_git_exception(self, mock_run, manager):
        mock_run.side_effect = Exception("crash")
        success, output = manager._run_git(["status"])
        assert success is False
        assert output == "crash"

    @patch("subprocess.run")
    def test_start_not_git_repo(self, mock_run, manager):
        # mock rev-parse --git-dir failure
        mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="not a git repository")
        res = manager.start()
        assert res["status"] == "error"
        assert "Not a Git repository" in res["message"]

    @patch("subprocess.run")
    def test_start_success_no_changes(self, mock_run, manager):
        # 1. rev-parse --git-dir -> success
        # 2. rev-parse HEAD -> commit_hash
        # 3. status --porcelain -> empty (no changes)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=".git", stderr=""), # git-dir
            MagicMock(returncode=0, stdout="abc1234", stderr=""), # HEAD
            MagicMock(returncode=0, stdout="", stderr=""), # status
        ]

        res = manager.start("Test transaction")
        assert res["status"] == "success"
        assert res["transaction_id"].startswith("tx-")
        assert res["checkpoint"] == "abc1234"
        assert res["files_stashed"] == 0

        assert manager.current_transaction is not None
        assert manager.current_transaction.commit_hash == "abc1234"
        assert manager.state_file.exists()

    @patch("subprocess.run")
    def test_start_success_with_changes(self, mock_run, manager):
        # 1. rev-parse --git-dir -> success
        # 2. rev-parse HEAD -> commit_hash
        # 3. status --porcelain -> modified files
        # 4. stash push -> success
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=".git", stderr=""), # git-dir
            MagicMock(returncode=0, stdout="abc1234", stderr=""), # HEAD
            MagicMock(returncode=0, stdout=" M file1.py\n?? file2.py", stderr=""), # status
            MagicMock(returncode=0, stdout="Saved working directory", stderr=""), # stash push
        ]

        res = manager.start()
        assert res["status"] == "success"
        assert res["files_stashed"] == 2
        assert manager.current_transaction.commit_hash == "stash@{0}"

    def test_start_already_in_progress(self, manager):
        manager.current_transaction = TransactionState("tx-1", datetime.now(), "hash", "desc")
        res = manager.start()
        assert res["status"] == "error"
        assert "already in progress" in res["message"]

    @patch("subprocess.run")
    def test_commit_success(self, mock_run, manager):
        manager.current_transaction = TransactionState("tx-1", datetime.now(), "abc1234", "desc")
        manager._save_state()

        res = manager.commit()
        assert res["status"] == "success"
        assert manager.current_transaction is None
        assert not manager.state_file.exists()
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_commit_with_stash_drop(self, mock_run, manager):
        manager.current_transaction = TransactionState("tx-1", datetime.now(), "stash@{0}", "desc")
        manager._save_state()

        mock_run.return_value = MagicMock(returncode=0, stdout="Dropped", stderr="")
        res = manager.commit()
        assert res["status"] == "success"
        assert manager.current_transaction is None
        # Check that stash drop was called (env is ignored in comparison here)
        args, kwargs = mock_run.call_args
        assert args[0] == ["git", "-c", "commit.gpgsign=false", "stash", "drop", "stash@{0}"]

    def test_commit_no_active(self, manager):
        res = manager.commit()
        assert res["status"] == "error"
        assert "No active transaction" in res["message"]

    @patch("subprocess.run")
    def test_rollback_success_commit(self, mock_run, manager):
        manager.current_transaction = TransactionState("tx-1", datetime.now(), "abc1234", "desc")
        manager._save_state()

        # 1. checkout -> success
        # 2. clean -> success
        # 3. reset -> success
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # checkout
            MagicMock(returncode=0, stdout="", stderr=""), # clean
            MagicMock(returncode=0, stdout="", stderr=""), # reset
        ]

        res = manager.rollback()
        assert res["status"] == "success"
        assert manager.current_transaction is None
        assert mock_run.call_count == 3

    @patch("subprocess.run")
    def test_rollback_success_stash(self, mock_run, manager):
        manager.current_transaction = TransactionState("tx-1", datetime.now(), "stash@{0}", "desc")
        manager._save_state()

        # 1. checkout -> success
        # 2. clean -> success
        # 3. stash pop -> success
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # checkout
            MagicMock(returncode=0, stdout="", stderr=""), # clean
            MagicMock(returncode=0, stdout="Popped", stderr=""), # stash pop
        ]

        res = manager.rollback()
        assert res["status"] == "success"
        assert manager.current_transaction is None
        assert mock_run.call_count == 3

    @patch("subprocess.run")
    def test_rollback_stash_pop_fail(self, mock_run, manager):
        manager.current_transaction = TransactionState("tx-1", datetime.now(), "stash@{0}", "desc")
        manager._save_state()

        # 1. checkout -> success
        # 2. clean -> success
        # 3. stash pop -> failure
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="conflict"),
        ]

        res = manager.rollback()
        assert res["status"] == "partial"
        assert "stash restore failed" in res["message"]

    @patch("subprocess.run")
    def test_status_active(self, mock_run, manager):
        manager.current_transaction = TransactionState("tx-1", datetime.now(), "abc1234", "desc", ["f1.py"])
        manager._save_state()

        mock_run.return_value = MagicMock(returncode=0, stdout="XY f2.py", stderr="")

        res = manager.status()
        assert res["status"] == "active"
        assert res["transaction_id"] == "tx-1"
        assert res["files_at_start"] == ["f1.py"]
        assert res["current_changes"] == ["f2.py"]

    def test_status_idle(self, manager):
        res = manager.status()
        assert res["status"] == "idle"

    def test_persistence_corrupt(self, manager):
        manager.state_file.write_text("not json")
        manager._load_state()
        assert manager.current_transaction is None
