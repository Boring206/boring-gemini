from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

from boring.mcp.tools.git import boring_checkpoint


def test_boring_checkpoint_create_success():
    """Test creating a checkpoint."""
    with (
        patch("boring.mcp.tools.git.get_project_root_or_error") as mock_root,
        patch("boring.mcp.tools.git.configure_runtime_for_project"),
        patch("subprocess.run") as mock_run,
    ):
        mock_root.return_value = (MagicMock(), None)

        # Simulate rev-parse (does not exist -> RAISE ERROR) then tag (success)
        mock_run.side_effect = [
            CalledProcessError(1, ["git", "rev-parse"]),  # rev-parse fails (does not exist)
            MagicMock(returncode=0, stdout="Created tag"),  # tag succeeds
        ]

        result = boring_checkpoint(action="create", name="test-cp", project_path="/tmp")

        assert result["status"] == "success", f"Failed with: {result}"
        assert "created" in result["message"]
        # Verify calls
        assert mock_run.call_count == 2


def test_boring_checkpoint_create_exists():
    """Test creating a checkpoint that already exists."""
    with (
        patch("boring.mcp.tools.git.get_project_root_or_error") as mock_root,
        patch("boring.mcp.tools.git.configure_runtime_for_project"),
        patch("subprocess.run") as mock_run,
    ):
        mock_root.return_value = (MagicMock(), None)

        # Simulate rev-parse (exists)
        mock_run.side_effect = [
            MagicMock(returncode=0),  # rev-parse succeeds (bad for create)
        ]

        result = boring_checkpoint(action="create", name="test-cp", project_path="/tmp")

        assert result["status"] == "error"
        assert "already exists" in result["message"]


def test_boring_checkpoint_restore_success():
    """Test restoring a checkpoint."""
    with (
        patch("boring.mcp.tools.git.get_project_root_or_error") as mock_root,
        patch("boring.mcp.tools.git.configure_runtime_for_project"),
        patch("subprocess.run") as mock_run,
    ):
        mock_root.return_value = (MagicMock(), None)

        # Sequence:
        # 1. rev-parse (check tag exists) -> OK
        # 2. status --porcelain (check dirty) -> Dirty
        # 3. stash save -> OK
        # 4. reset --hard -> OK
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Check tag
            MagicMock(returncode=0, stdout="M file.txt"),  # Check dirty
            MagicMock(returncode=0, stdout="Saved working directory"),  # Stash
            MagicMock(returncode=0, stdout="HEAD is now at..."),  # Reset
        ]

        result = boring_checkpoint(
            action="restore", name="test-cp", stash_changes=True, project_path="/tmp"
        )

        assert result["status"] == "success"
        assert "Restored to checkpoint" in result["message"]
        assert "Current changes stashed" in result["message"]


def test_boring_checkpoint_list():
    """Test listing checkpoints."""
    with (
        patch("boring.mcp.tools.git.get_project_root_or_error") as mock_root,
        patch("boring.mcp.tools.git.configure_runtime_for_project"),
        patch("subprocess.run") as mock_run,
    ):
        mock_root.return_value = (MagicMock(), None)

        mock_run.return_value = MagicMock(
            returncode=0, stdout="checkpoint/cp1\ncheckpoint/cp2\nother-tag"
        )

        result = boring_checkpoint(action="list", project_path="/tmp")

        assert result["status"] == "success"
        assert result["data"]["checkpoints"] == ["cp1", "cp2"]  # Filtered prefix
