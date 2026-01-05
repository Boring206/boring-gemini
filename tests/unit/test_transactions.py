# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

import pytest

from boring.transactions import TransactionManager


@pytest.fixture
def mock_git_manager(tmp_path):
    manager = TransactionManager(tmp_path)
    # Mock _run_git to avoid actual git operations
    manager._run_git = MagicMock(return_value=(True, ""))
    return manager


def test_transaction_start(mock_git_manager):
    """Test starting a transaction."""
    mock_git_manager._get_current_commit = MagicMock(return_value="abc1234")
    mock_git_manager._get_changed_files = MagicMock(return_value=["file1.py"])

    # Mock successful stash
    mock_git_manager._run_git.side_effect = [
        (True, ".git"),      # check git dir
        (True, "stash output") # stash push
    ]

    result = mock_git_manager.start("Test transaction")

    assert result["status"] == "success"
    assert mock_git_manager.current_transaction is not None
    assert mock_git_manager.current_transaction.is_active
    assert mock_git_manager.current_transaction.description == "Test transaction"


def test_transaction_commit(mock_git_manager):
    """Test committing a transaction."""
    # Setup active transaction
    mock_git_manager.start("Test")
    mock_git_manager._run_git.reset_mock() # Clear calls from start()

    result = mock_git_manager.commit()

    assert result["status"] == "success"
    assert not mock_git_manager.current_transaction  # Should be cleared

    # Verify stash drop was called (since we mocked files changed)
    # The actual call args check depends on how many times _run_git was called
    # Here we just ensure current_transaction is gone


def test_transaction_rollback(mock_git_manager):
    """Test rolling back a transaction."""
    # Setup active transaction
    mock_git_manager.start("Test")
    mock_git_manager._run_git.reset_mock()

    result = mock_git_manager.rollback()

    assert result["status"] == "success"
    assert not mock_git_manager.current_transaction

    # Verify reset/clean calls were made
    calls = [c[0][0] for c in mock_git_manager._run_git.call_args_list]
    assert "checkout" in calls[0]
    assert "clean" in calls[1]


def test_transaction_status(mock_git_manager):
    """Test status reporting."""
    status = mock_git_manager.status()
    assert status["status"] == "idle"

    mock_git_manager.start("Active Tx")
    status = mock_git_manager.status()
    assert status["status"] == "active"
    assert status["description"] == "Active Tx"
