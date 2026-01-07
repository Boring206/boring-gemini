# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
Comprehensive unit tests for boring.backup module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from boring.backup import BackupManager

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def backup_dir(tmp_path):
    """Create a temporary backup directory."""
    backup = tmp_path / "backups"
    backup.mkdir()
    return backup


# =============================================================================
# BACKUP MANAGER TESTS
# =============================================================================


class TestBackupManager:
    """Tests for BackupManager class."""

    def test_backup_manager_init(self, temp_project, backup_dir):
        """Test BackupManager initialization."""
        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BACKUP_DIR = backup_dir
            manager = BackupManager(loop_id=1, project_root=temp_project, backup_dir=backup_dir)
            assert manager.loop_id == 1
            assert manager.project_root == temp_project
            assert "loop_1_" in str(manager.snapshot_dir)

    def test_backup_manager_init_defaults(self):
        """Test BackupManager with default values."""
        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = Path("/default")
            mock_settings.BACKUP_DIR = Path("/default/backups")
            manager = BackupManager(loop_id=1)
            assert manager.project_root == Path("/default")

    def test_backup_manager_create_snapshot(self, temp_project, backup_dir):
        """Test create_snapshot method."""
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BACKUP_DIR = backup_dir
            manager = BackupManager(loop_id=1, project_root=temp_project, backup_dir=backup_dir)

            snapshot_path = manager.create_snapshot([test_file])
            assert snapshot_path is not None
            assert snapshot_path.exists()

            # Verify file was backed up
            backed_up_file = snapshot_path / "test.py"
            assert backed_up_file.exists()

    def test_backup_manager_create_snapshot_empty(self, temp_project, backup_dir):
        """Test create_snapshot with empty file list."""
        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BACKUP_DIR = backup_dir
            manager = BackupManager(loop_id=1, project_root=temp_project, backup_dir=backup_dir)

            snapshot_path = manager.create_snapshot([])
            assert snapshot_path is None

    def test_backup_manager_create_snapshot_nonexistent_file(self, temp_project, backup_dir):
        """Test create_snapshot with nonexistent file."""
        nonexistent = temp_project / "nonexistent.py"

        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BACKUP_DIR = backup_dir
            manager = BackupManager(loop_id=1, project_root=temp_project, backup_dir=backup_dir)

            snapshot_path = manager.create_snapshot([nonexistent])
            # Should return None if no files backed up
            assert snapshot_path is None

    def test_backup_manager_create_snapshot_nested_path(self, temp_project, backup_dir):
        """Test create_snapshot with nested file path."""
        nested_dir = temp_project / "src" / "subdir"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "test.py"
        nested_file.write_text("print('test')")

        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BACKUP_DIR = backup_dir
            manager = BackupManager(loop_id=1, project_root=temp_project, backup_dir=backup_dir)

            snapshot_path = manager.create_snapshot([nested_file])
            assert snapshot_path is not None

            # Verify nested structure preserved
            backed_up_file = snapshot_path / "src" / "subdir" / "test.py"
            assert backed_up_file.exists()

    def test_backup_manager_restore_snapshot(self, temp_project, backup_dir):
        """Test restore_snapshot method."""
        test_file = temp_project / "test.py"
        test_file.write_text("original")

        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BACKUP_DIR = backup_dir
            manager = BackupManager(loop_id=1, project_root=temp_project, backup_dir=backup_dir)

            # Create snapshot
            snapshot_path = manager.create_snapshot([test_file])
            assert snapshot_path is not None

            # Modify original file
            test_file.write_text("modified")

            # Restore
            manager.restore_snapshot()

            # Verify file was restored
            assert test_file.read_text() == "original"

    def test_backup_manager_restore_snapshot_nonexistent(self, temp_project, backup_dir):
        """Test restore_snapshot when snapshot doesn't exist."""
        with patch("boring.backup.settings") as mock_settings:
            mock_settings.PROJECT_ROOT = temp_project
            mock_settings.BACKUP_DIR = backup_dir
            manager = BackupManager(loop_id=1, project_root=temp_project, backup_dir=backup_dir)

            # Should not raise exception
            manager.restore_snapshot()

    def test_backup_manager_cleanup_old_backups(self, backup_dir):
        """Test cleanup_old_backups method."""
        # Create multiple backup directories
        for i in range(15):
            backup_subdir = backup_dir / f"loop_{i}_20240101_000000"
            backup_subdir.mkdir()
            (backup_subdir / "file.txt").write_text("test")

        with patch("boring.backup.settings") as mock_settings:
            mock_settings.BACKUP_DIR = backup_dir
            BackupManager.cleanup_old_backups(keep_last=10)

            # Should keep only 10 most recent
            remaining = [d for d in backup_dir.iterdir() if d.is_dir()]
            assert len(remaining) <= 10

    def test_backup_manager_cleanup_old_backups_nonexistent_dir(self):
        """Test cleanup_old_backups when backup dir doesn't exist."""
        with patch("boring.backup.settings") as mock_settings:
            mock_settings.BACKUP_DIR = Path("/nonexistent/backups")
            # Should not raise exception
            BackupManager.cleanup_old_backups()

    def test_backup_manager_cleanup_old_backups_empty(self, backup_dir):
        """Test cleanup_old_backups with empty backup dir."""
        with patch("boring.backup.settings") as mock_settings:
            mock_settings.BACKUP_DIR = backup_dir
            # Should not raise exception
            BackupManager.cleanup_old_backups()
