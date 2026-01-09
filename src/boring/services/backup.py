import shutil
import time
from pathlib import Path
from typing import Optional

from rich.console import Console

from boring.core.config import settings

console = Console()


class BackupManager:
    """
    Manages file snapshots before modification.
    """

    def __init__(
        self, loop_id: int, project_root: Optional[Path] = None, backup_dir: Optional[Path] = None
    ):
        self.loop_id = loop_id
        self.project_root = project_root or settings.PROJECT_ROOT
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_base = backup_dir or settings.BACKUP_DIR
        self.snapshot_dir = backup_base / f"loop_{loop_id}_{self.timestamp}"

    def create_snapshot(self, file_paths: list[Path]) -> Optional[Path]:
        """
        Copies the specified files to the snapshot directory.
        Returns the path to the snapshot directory if successful, None if no files needed backup.
        """
        if not file_paths:
            return None

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        backed_up_count = 0

        for file_path in file_paths:
            if file_path.exists() and file_path.is_file():
                # Create directory structure in snapshot (with Windows-safe relative_to)
                try:
                    rel_path = (
                        file_path.relative_to(self.project_root)
                        if file_path.is_absolute()
                        else file_path
                    )
                except ValueError:
                    # Windows path case mismatch - use just the filename
                    rel_path = Path(file_path.name)
                dest_path = self.snapshot_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(file_path, dest_path)
                backed_up_count += 1

        if backed_up_count > 0:
            console.print(
                f"[dim]Saved backup of {backed_up_count} files to {self.snapshot_dir}[/dim]"
            )
            return self.snapshot_dir
        else:
            # Cleanup empty dir if nothing backed up
            if self.snapshot_dir.exists() and not any(self.snapshot_dir.iterdir()):
                shutil.rmtree(self.snapshot_dir)
            return None

    def restore_snapshot(self):
        """
        Restores files from the snapshot directory.
        """
        if not self.snapshot_dir.exists():
            console.print("[yellow]No backup found to restore.[/yellow]")
            return

        console.print(f"[bold red]Restoring backup from {self.snapshot_dir}...[/bold red]")

        for file_path in self.snapshot_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.snapshot_dir)
                original_path = settings.PROJECT_ROOT / rel_path

                # Ensure parent dir exists
                original_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, original_path)
                console.print(f"[red]Restored: {rel_path}[/red]")

    @staticmethod
    def cleanup_old_backups(keep_last: int = 10):
        """
        Removes old backup directories, keeping only the most recent ones.
        """
        if not settings.BACKUP_DIR.exists():
            return

        # Get all backup directories sorted by modification time (oldest first)
        backup_dirs = sorted(
            [d for d in settings.BACKUP_DIR.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
        )

        # Remove old backups if we have more than keep_last
        if len(backup_dirs) > keep_last:
            dirs_to_remove = backup_dirs[:-keep_last]
            for old_dir in dirs_to_remove:
                try:
                    shutil.rmtree(old_dir)
                    console.print(f"[dim]Cleaned up old backup: {old_dir.name}[/dim]")
                except Exception:
                    pass
