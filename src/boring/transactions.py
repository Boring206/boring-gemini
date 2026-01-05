# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Atomic Transaction Management for Boring.

Provides Git-based snapshot and rollback capabilities for safe code changes.
"""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


@dataclass
class TransactionState:
    """State of a transaction."""

    transaction_id: str
    started_at: datetime
    commit_hash: str  # Git commit or stash reference
    description: str
    files_changed: list[str] = field(default_factory=list)
    is_active: bool = True


class TransactionManager:
    """
    Manages atomic transactions using Git snapshots.

    Provides:
    - start() - Create a checkpoint before making changes
    - commit() - Confirm changes and clear checkpoint
    - rollback() - Revert to checkpoint
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.state_file = self.project_root / ".boring_transaction"
        self.current_transaction: Optional[TransactionState] = None

    def _run_git(self, args: list[str]) -> tuple[bool, str]:
        """Run a git command and return (success, output)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def _get_current_commit(self) -> str:
        """Get current HEAD commit hash."""
        success, output = self._run_git(["rev-parse", "HEAD"])
        return output if success else ""

    def _get_changed_files(self) -> list[str]:
        """Get list of uncommitted changed files."""
        success, output = self._run_git(["status", "--porcelain"])
        if not success or not output:
            return []
        return [line[3:] for line in output.split("\n") if line]

    def start(self, description: str = "Boring transaction") -> dict:
        """
        Start a new transaction by creating a Git checkpoint.

        Args:
            description: Description of the transaction

        Returns:
            Transaction state as dict
        """
        if self.current_transaction and self.current_transaction.is_active:
            return {
                "status": "error",
                "message": "Transaction already in progress. Commit or rollback first.",
                "transaction_id": self.current_transaction.transaction_id,
            }

        # Check if we're in a git repo
        success, _ = self._run_git(["rev-parse", "--git-dir"])
        if not success:
            return {"status": "error", "message": "Not a Git repository"}

        # Get current state
        commit_hash = self._get_current_commit()
        changed_files = self._get_changed_files()

        # Create stash if there are uncommitted changes
        stash_ref = None
        if changed_files:
            success, output = self._run_git(
                ["stash", "push", "-m", f"boring-transaction-{datetime.now().isoformat()}"]
            )
            if success:
                stash_ref = "stash@{0}"

        # Generate transaction ID
        transaction_id = f"tx-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Create transaction state
        self.current_transaction = TransactionState(
            transaction_id=transaction_id,
            started_at=datetime.now(),
            commit_hash=stash_ref or commit_hash,
            description=description,
            files_changed=changed_files,
            is_active=True,
        )

        # Save state to file
        self._save_state()

        return {
            "status": "success",
            "transaction_id": transaction_id,
            "checkpoint": commit_hash,
            "files_stashed": len(changed_files) if stash_ref else 0,
            "message": "Transaction started. Use rollback to revert if needed.",
        }

    def commit(self) -> dict:
        """
        Commit the transaction, keeping all changes.

        Returns:
            Result as dict
        """
        if not self.current_transaction or not self.current_transaction.is_active:
            return {"status": "error", "message": "No active transaction to commit"}

        transaction_id = self.current_transaction.transaction_id

        # Clear the stash if we created one
        if self.current_transaction.commit_hash.startswith("stash"):
            self._run_git(["stash", "drop", "stash@{0}"])

        # Mark transaction as complete
        self.current_transaction.is_active = False
        self._clear_state()

        return {
            "status": "success",
            "transaction_id": transaction_id,
            "message": "Transaction committed. Changes are permanent.",
        }

    def rollback(self) -> dict:
        """
        Rollback to the checkpoint, discarding all changes since start().

        Returns:
            Result as dict
        """
        if not self.current_transaction or not self.current_transaction.is_active:
            return {"status": "error", "message": "No active transaction to rollback"}

        transaction_id = self.current_transaction.transaction_id
        checkpoint = self.current_transaction.commit_hash

        # Discard all current changes
        self._run_git(["checkout", "--", "."])
        self._run_git(["clean", "-fd"])

        # Restore stashed changes if applicable
        if checkpoint.startswith("stash"):
            success, output = self._run_git(["stash", "pop"])
            if not success:
                return {
                    "status": "partial",
                    "transaction_id": transaction_id,
                    "message": f"Rolled back but stash restore failed: {output}",
                }
        else:
            # Hard reset to the commit
            self._run_git(["reset", "--hard", checkpoint])

        # Clear transaction
        self.current_transaction.is_active = False
        self._clear_state()

        return {
            "status": "success",
            "transaction_id": transaction_id,
            "message": "Transaction rolled back. All changes since start() have been reverted.",
        }

    def status(self) -> dict:
        """Get current transaction status."""
        self._load_state()

        if not self.current_transaction or not self.current_transaction.is_active:
            return {"status": "idle", "message": "No active transaction"}

        return {
            "status": "active",
            "transaction_id": self.current_transaction.transaction_id,
            "started_at": self.current_transaction.started_at.isoformat(),
            "description": self.current_transaction.description,
            "files_at_start": self.current_transaction.files_changed,
            "current_changes": self._get_changed_files(),
        }

    def _save_state(self):
        """Save transaction state to file."""
        import json

        if self.current_transaction:
            data = {
                "transaction_id": self.current_transaction.transaction_id,
                "started_at": self.current_transaction.started_at.isoformat(),
                "commit_hash": self.current_transaction.commit_hash,
                "description": self.current_transaction.description,
                "files_changed": self.current_transaction.files_changed,
                "is_active": self.current_transaction.is_active,
            }
            self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_state(self):
        """Load transaction state from file."""
        import json

        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.current_transaction = TransactionState(
                    transaction_id=data["transaction_id"],
                    started_at=datetime.fromisoformat(data["started_at"]),
                    commit_hash=data["commit_hash"],
                    description=data["description"],
                    files_changed=data.get("files_changed", []),
                    is_active=data.get("is_active", True),
                )
            except Exception:
                self.current_transaction = None

    def _clear_state(self):
        """Clear saved transaction state."""
        if self.state_file.exists():
            self.state_file.unlink()
        self.current_transaction = None


# --- Convenience functions for MCP tools ---


def start_transaction(project_path: str = None, description: str = "Boring transaction") -> dict:
    """Start a new atomic transaction."""
    from .config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    return manager.start(description)


def commit_transaction(project_path: str = None) -> dict:
    """Commit the current transaction."""
    from .config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    manager._load_state()
    return manager.commit()


def rollback_transaction(project_path: str = None) -> dict:
    """Rollback the current transaction."""
    from .config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    manager._load_state()
    return manager.rollback()


def transaction_status(project_path: str = None) -> dict:
    """Get transaction status."""
    from .config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    return manager.status()
