# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.transactions module.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from boring.transactions import (
    TransactionManager,
    TransactionState,
    commit_transaction,
    rollback_transaction,
    start_transaction,
    transaction_status,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with git repository."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "file1.py").write_text("print('hello')")
    return project


@pytest.fixture
def transaction_manager(temp_project):
    """Create a TransactionManager instance."""
    return TransactionManager(temp_project)


# =============================================================================
# TRANSACTION STATE TESTS
# =============================================================================


class TestTransactionState:
    """Tests for TransactionState dataclass."""

    def test_transaction_state_creation(self):
        """Test TransactionState creation."""
        state = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Test transaction",
            files_changed=["file1.py"],
        )
        assert state.transaction_id == "tx-123"
        assert state.is_active is True  # Default value

    def test_transaction_state_defaults(self):
        """Test TransactionState with default values."""
        state = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Test",
        )
        assert state.files_changed == []
        assert state.is_active is True


# =============================================================================
# TRANSACTION MANAGER TESTS
# =============================================================================


class TestTransactionManager:
    """Tests for TransactionManager class."""

    def test_transaction_manager_init(self, temp_project):
        """Test TransactionManager initialization."""
        manager = TransactionManager(temp_project)
        assert manager.project_root == temp_project
        assert manager.state_file == temp_project / ".boring_transaction"
        assert manager.current_transaction is None

    def test_transaction_manager_run_git_success(self, transaction_manager):
        """Test _run_git with successful command."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            success, output = transaction_manager._run_git(["status"])
            assert success is True
            assert output == "success output"

    def test_transaction_manager_run_git_failure(self, transaction_manager):
        """Test _run_git with failed command."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "error message"
            mock_run.return_value = mock_result

            success, output = transaction_manager._run_git(["invalid"])
            assert success is False
            assert "error" in output.lower()

    def test_transaction_manager_run_git_exception(self, transaction_manager):
        """Test _run_git with exception."""
        with patch("subprocess.run", side_effect=Exception("Command error")):
            success, output = transaction_manager._run_git(["status"])
            assert success is False
            assert "error" in output.lower()

    def test_transaction_manager_get_current_commit(self, transaction_manager):
        """Test _get_current_commit."""
        with patch.object(transaction_manager, "_run_git", return_value=(True, "abc123")):
            commit = transaction_manager._get_current_commit()
            assert commit == "abc123"

    def test_transaction_manager_get_current_commit_failure(self, transaction_manager):
        """Test _get_current_commit with failure."""
        with patch.object(transaction_manager, "_run_git", return_value=(False, "")):
            commit = transaction_manager._get_current_commit()
            assert commit == ""

    def test_transaction_manager_get_changed_files(self, transaction_manager):
        """Test _get_changed_files."""
        with patch.object(
            transaction_manager, "_run_git", return_value=(True, " M file1.py\n M file2.py")
        ):
            files = transaction_manager._get_changed_files()
            assert len(files) == 2
            assert "file1.py" in files

    def test_transaction_manager_get_changed_files_empty(self, transaction_manager):
        """Test _get_changed_files with no changes."""
        with patch.object(transaction_manager, "_run_git", return_value=(True, "")):
            files = transaction_manager._get_changed_files()
            assert files == []

    def test_transaction_manager_start_no_git_repo(self, transaction_manager):
        """Test start when not in git repository."""
        with patch.object(transaction_manager, "_run_git", return_value=(False, "")):
            result = transaction_manager.start()
            assert result["status"] == "error"
            assert "Not a Git repository" in result["message"]

    def test_transaction_manager_start_already_active(self, transaction_manager):
        """Test start when transaction already active."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Active",
            is_active=True,
        )

        result = transaction_manager.start()
        assert result["status"] == "error"
        assert "already in progress" in result["message"]

    def test_transaction_manager_start_success(self, transaction_manager):
        """Test successful transaction start."""
        with patch.object(transaction_manager, "_run_git") as mock_git:

            def side_effect(args):
                if args == ["rev-parse", "--git-dir"]:
                    return (True, ".git")
                elif args == ["rev-parse", "HEAD"]:
                    return (True, "abc123")
                elif args[0] == "status":
                    return (True, "")
                return (False, "")

            mock_git.side_effect = side_effect

            result = transaction_manager.start("Test transaction")
            assert result["status"] == "success"
            assert "transaction_id" in result
            assert transaction_manager.current_transaction is not None

    def test_transaction_manager_commit_no_active(self, transaction_manager):
        """Test commit with no active transaction."""
        result = transaction_manager.commit()
        assert result["status"] == "error"
        assert "No active transaction" in result["message"]

    def test_transaction_manager_commit_success(self, transaction_manager):
        """Test successful commit."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Test",
            is_active=True,
        )

        with patch.object(transaction_manager, "_run_git"):
            result = transaction_manager.commit()
            assert result["status"] == "success"
            assert transaction_manager.current_transaction is None

    def test_transaction_manager_commit_with_stash(self, transaction_manager):
        """Test commit with stash reference."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="stash@{0}",
            description="Test",
            is_active=True,
        )

        with patch.object(transaction_manager, "_run_git"):
            result = transaction_manager.commit()
            assert result["status"] == "success"

    def test_transaction_manager_rollback_no_active(self, transaction_manager):
        """Test rollback with no active transaction."""
        result = transaction_manager.rollback()
        assert result["status"] == "error"
        assert "No active transaction" in result["message"]

    def test_transaction_manager_rollback_success(self, transaction_manager):
        """Test successful rollback."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Test",
            is_active=True,
        )

        with patch.object(transaction_manager, "_run_git", return_value=(True, "")):
            result = transaction_manager.rollback()
            assert result["status"] == "success"
            assert transaction_manager.current_transaction is None

    def test_transaction_manager_rollback_with_stash(self, transaction_manager):
        """Test rollback with stash."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="stash@{0}",
            description="Test",
            is_active=True,
        )

        with patch.object(transaction_manager, "_run_git", return_value=(True, "")):
            result = transaction_manager.rollback()
            assert result["status"] == "success"

    def test_transaction_manager_rollback_stash_failure(self, transaction_manager):
        """Test rollback with stash restore failure."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="stash@{0}",
            description="Test",
            is_active=True,
        )

        def side_effect(args):
            if args == ["stash", "pop"]:
                return (False, "Stash error")
            return (True, "")

        with patch.object(transaction_manager, "_run_git", side_effect=side_effect):
            result = transaction_manager.rollback()
            assert result["status"] == "partial"

    def test_transaction_manager_status_idle(self, transaction_manager):
        """Test status with no active transaction."""
        result = transaction_manager.status()
        assert result["status"] == "idle"

    def test_transaction_manager_status_active(self, transaction_manager):
        """Test status with active transaction."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Test",
            files_changed=["file1.py"],
            is_active=True,
        )

        with patch.object(transaction_manager, "_get_changed_files", return_value=[]):
            result = transaction_manager.status()
            assert result["status"] == "active"
            assert result["transaction_id"] == "tx-123"

    def test_transaction_manager_save_state(self, transaction_manager):
        """Test saving transaction state."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Test",
            files_changed=["file1.py"],
            is_active=True,
        )

        transaction_manager._save_state()
        assert transaction_manager.state_file.exists()
        data = json.loads(transaction_manager.state_file.read_text())
        assert data["transaction_id"] == "tx-123"

    def test_transaction_manager_load_state(self, transaction_manager):
        """Test loading transaction state."""
        state_data = {
            "transaction_id": "tx-123",
            "started_at": datetime.now().isoformat(),
            "commit_hash": "abc123",
            "description": "Test",
            "files_changed": ["file1.py"],
            "is_active": True,
        }
        transaction_manager.state_file.write_text(json.dumps(state_data))

        transaction_manager._load_state()
        assert transaction_manager.current_transaction is not None
        assert transaction_manager.current_transaction.transaction_id == "tx-123"

    def test_transaction_manager_load_state_invalid_json(self, transaction_manager):
        """Test loading state with invalid JSON."""
        transaction_manager.state_file.write_text("invalid json{")
        transaction_manager._load_state()
        # Should handle gracefully
        assert transaction_manager.current_transaction is None

    def test_transaction_manager_clear_state(self, transaction_manager):
        """Test clearing transaction state."""
        transaction_manager.current_transaction = TransactionState(
            transaction_id="tx-123",
            started_at=datetime.now(),
            commit_hash="abc123",
            description="Test",
        )
        transaction_manager.state_file.write_text("test")

        transaction_manager._clear_state()
        assert transaction_manager.current_transaction is None
        assert not transaction_manager.state_file.exists()


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @patch("boring.loop.transactions.TransactionManager")
    def test_start_transaction(self, mock_manager_class, tmp_path):
        """Test start_transaction function."""
        mock_manager = MagicMock()
        mock_manager.start.return_value = {"status": "success"}
        mock_manager_class.return_value = mock_manager

        with patch("boring.config.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            result = start_transaction(str(tmp_path))
            assert result["status"] == "success"

    @patch("boring.loop.transactions.TransactionManager")
    def test_commit_transaction(self, mock_manager_class, tmp_path):
        """Test commit_transaction function."""
        mock_manager = MagicMock()
        mock_manager.commit.return_value = {"status": "success"}
        mock_manager_class.return_value = mock_manager

        # Since project_path is provided, settings is not used
        result = commit_transaction(str(tmp_path))
        assert result["status"] == "success"

    @patch("boring.loop.transactions.TransactionManager")
    def test_rollback_transaction(self, mock_manager_class, tmp_path):
        """Test rollback_transaction function."""
        mock_manager = MagicMock()
        mock_manager.rollback.return_value = {"status": "success"}
        mock_manager_class.return_value = mock_manager

        # Since project_path is provided, settings is not used
        result = rollback_transaction(str(tmp_path))
        assert result["status"] == "success"

    @patch("boring.transactions.TransactionManager")
    def test_transaction_status(self, mock_manager_class, tmp_path):
        """Test transaction_status function."""
        mock_manager = MagicMock()
        mock_manager.status.return_value = {"status": "idle"}
        mock_manager_class.return_value = mock_manager

        with patch("boring.config.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = tmp_path
            result = transaction_status(str(tmp_path))
            assert result["status"] == "idle"
