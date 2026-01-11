# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Atomic Transaction Management for Boring V11.0.

Provides Git-based snapshot and rollback capabilities for safe code changes.

V11.0 Enhancements:
- Exponential backoff retry mechanism for Windows file locking
- Pre-execution file lock detection
- Graceful recovery on disk write failures
"""

import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Callable, Optional, TypeVar

from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

# Type variable for generic retry decorator
T = TypeVar("T")


class WindowsFileLockError(Exception):
    """Raised when a file is locked by another process on Windows."""

    def __init__(self, file_path: Path, message: str = ""):
        self.file_path = file_path
        self.message = message or f"File is locked: {file_path}"
        super().__init__(self.message)


def retry_with_backoff(
    max_retries: int = 5,
    initial_delay: float = 0.1,
    max_delay: float = 5.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (OSError, subprocess.SubprocessError),
) -> Callable:
    """
    Decorator for exponential backoff retry mechanism.

    Designed to handle Windows Mandatory File Locking gracefully.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (default 100ms)
        max_delay: Maximum delay between retries (default 5s)
        backoff_factor: Multiplier for delay after each retry
        retryable_exceptions: Tuple of exceptions that trigger retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Log retry attempt
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )

            # All retries exhausted
            raise last_exception  # type: ignore

        return wrapper

    return decorator


class FileLockDetector:
    """
    Detects file locks on Windows and other platforms.

    Windows uses Mandatory File Locking, which can cause Git operations
    to fail if files are open in an IDE or Agent process.
    """

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return sys.platform == "win32"

    @staticmethod
    def is_file_locked(file_path: Path) -> bool:
        """
        Check if a file is locked by another process.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is locked, False otherwise
        """
        if not file_path.exists():
            return False

        if FileLockDetector.is_windows():
            return FileLockDetector._check_windows_lock(file_path)
        else:
            return FileLockDetector._check_unix_lock(file_path)

    @staticmethod
    def _check_windows_lock(file_path: Path) -> bool:
        """Check file lock on Windows using exclusive open."""
        try:
            # Try to open file with exclusive access
            fd = os.open(str(file_path), os.O_RDWR | os.O_EXCL)
            os.close(fd)
            return False
        except OSError:
            return True
        except Exception:
            return False

    @staticmethod
    def _check_unix_lock(file_path: Path) -> bool:
        """Check file lock on Unix-like systems using fcntl."""
        try:
            import fcntl

            fd = os.open(str(file_path), os.O_RDWR)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
                return False
            except (BlockingIOError, OSError):
                return True
            finally:
                os.close(fd)
        except (ImportError, OSError):
            return False

    @staticmethod
    def find_locked_files(directory: Path, patterns: list[str] = None) -> list[Path]:
        """
        Find all locked files in a directory.

        Args:
            directory: Directory to scan
            patterns: File patterns to check (default: common code files)

        Returns:
            List of locked file paths
        """
        if patterns is None:
            patterns = ["*.py", "*.js", "*.ts", "*.json", "*.yaml", "*.yml", "*.md"]

        locked_files = []

        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                if file_path.is_file() and FileLockDetector.is_file_locked(file_path):
                    locked_files.append(file_path)

        return locked_files

    @staticmethod
    def wait_for_file_unlock(
        file_path: Path,
        timeout: float = 10.0,
        check_interval: float = 0.5,
    ) -> bool:
        """
        Wait for a file to become unlocked.

        Args:
            file_path: Path to the file
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds

        Returns:
            True if file is unlocked, False if timeout reached
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not FileLockDetector.is_file_locked(file_path):
                return True
            time.sleep(check_interval)

        return False


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

    def _run_git(self, args: list[str], with_retry: bool = False) -> tuple[bool, str]:
        """
        Run a git command and return (success, output).

        Args:
            args: Git command arguments
            with_retry: If True, use exponential backoff retry for file lock issues

        Returns:
            Tuple of (success, output)
        """
        # Prevent git from prompting for credentials or GPG keys
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        def _execute_git() -> tuple[bool, str]:
            try:
                # Add -c commit.gpgsign=false to avoid GPG passphrase prompts
                cmd = ["git", "-c", "commit.gpgsign=false"] + args

                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env,
                )
                return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
            except subprocess.TimeoutExpired as e:
                raise OSError(f"Git command timed out: {e}")
            except Exception as e:
                return False, str(e)

        if with_retry:
            # Use retry mechanism for operations that may encounter file locks
            @retry_with_backoff(max_retries=5, initial_delay=0.1, max_delay=5.0)
            def _execute_with_retry() -> tuple[bool, str]:
                success, output = _execute_git()
                if not success and self._is_file_lock_error(output):
                    raise OSError(f"File lock detected: {output}")
                return success, output

            try:
                return _execute_with_retry()
            except OSError as e:
                return False, str(e)
        else:
            return _execute_git()

    def _is_file_lock_error(self, error_message: str) -> bool:
        """Check if error message indicates a file lock issue."""
        lock_indicators = [
            "cannot lock",
            "unable to create",
            "Permission denied",
            "Access is denied",
            "being used by another process",
            "cannot create",
            "file is busy",
            "resource busy",
        ]
        error_lower = error_message.lower()
        return any(indicator.lower() in error_lower for indicator in lock_indicators)

    def _check_file_locks_before_operation(self) -> dict:
        """
        Check for file locks before performing rollback operation.

        Returns:
            Dict with status and any locked files found
        """
        locked_files = FileLockDetector.find_locked_files(self.project_root)

        if locked_files:
            # Attempt to wait for files to unlock
            still_locked = []
            for file_path in locked_files:
                if not FileLockDetector.wait_for_file_unlock(file_path, timeout=3.0):
                    still_locked.append(str(file_path))

            if still_locked:
                return {
                    "status": "warning",
                    "locked_files": still_locked,
                    "message": f"Found {len(still_locked)} locked files. Proceeding with caution.",
                }

        return {"status": "ok", "locked_files": []}

    def _get_current_commit(self) -> str:
        """Get current HEAD commit hash."""
        success, output = self._run_git(["rev-parse", "HEAD"])
        return output if success else ""

    def _get_changed_files(self) -> list[str]:
        """Get list of uncommitted changed files."""
        success, output = self._run_git(["status", "--porcelain"])
        if not success or not output:
            return []
        res = []
        for line in output.split("\n"):
            if line:
                res.append(line[3:])
        return res

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
            return {
                "status": "error",
                "message": "Not a Git repository. Please initialize with: git init",
            }

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

        V11.0 Enhancements:
        - Pre-execution file lock detection
        - Exponential backoff retry for Windows file locking
        - Graceful recovery on disk write failures

        Returns:
            Result as dict
        """
        if not self.current_transaction or not self.current_transaction.is_active:
            return {"status": "error", "message": "No active transaction to rollback"}

        transaction_id = self.current_transaction.transaction_id
        checkpoint = self.current_transaction.commit_hash

        # V11.0: Check for file locks before operation
        lock_check = self._check_file_locks_before_operation()
        if lock_check["status"] == "warning":
            logger.warning(
                f"Proceeding with rollback despite locked files: {lock_check['locked_files']}"
            )

        # Track rollback progress for graceful recovery
        rollback_state = {"checkout_done": False, "clean_done": False, "restore_done": False}

        try:
            # Discard all current changes (with retry for file locks)
            success, output = self._run_git(["checkout", "--", "."], with_retry=True)
            if not success:
                return {
                    "status": "error",
                    "transaction_id": transaction_id,
                    "message": f"Failed to checkout: {output}",
                    "partial_state": rollback_state,
                }
            rollback_state["checkout_done"] = True

            success, output = self._run_git(["clean", "-fd"], with_retry=True)
            if not success:
                logger.warning(f"Clean operation had issues: {output}")
            rollback_state["clean_done"] = True

            # Restore stashed changes if applicable
            if checkpoint.startswith("stash"):
                success, output = self._run_git(["stash", "pop"], with_retry=True)
                if not success:
                    # Attempt graceful recovery: try stash apply instead
                    success, output = self._run_git(["stash", "apply", "stash@{0}"])
                    if success:
                        # Apply worked, drop the stash
                        self._run_git(["stash", "drop", "stash@{0}"])
                    else:
                        return {
                            "status": "partial",
                            "transaction_id": transaction_id,
                            "message": f"Rolled back but stash restore failed: {output}. "
                            "Your changes are still in the stash.",
                            "partial_state": rollback_state,
                        }
                rollback_state["restore_done"] = True
            else:
                # Hard reset to the commit (with retry)
                success, output = self._run_git(["reset", "--hard", checkpoint], with_retry=True)
                if not success:
                    return {
                        "status": "partial",
                        "transaction_id": transaction_id,
                        "message": f"Reset failed: {output}",
                        "partial_state": rollback_state,
                    }
                rollback_state["restore_done"] = True

            # Clear transaction
            self.current_transaction.is_active = False
            self._clear_state()

            return {
                "status": "success",
                "transaction_id": transaction_id,
                "message": "Transaction rolled back. All changes since start() have been reverted.",
            }

        except Exception as e:
            logger.error(f"Rollback encountered an unexpected error: {e}")
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "message": f"Rollback failed with error: {e}",
                "partial_state": rollback_state,
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
    from ..config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    return manager.start(description)


def commit_transaction(project_path: str = None) -> dict:
    """Commit the current transaction."""
    from ..config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    manager._load_state()
    return manager.commit()


def rollback_transaction(project_path: str = None) -> dict:
    """Rollback the current transaction."""
    from ..config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    manager._load_state()
    return manager.rollback()


def transaction_status(project_path: str = None) -> dict:
    """Get transaction status."""
    from ..config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = TransactionManager(path)
    return manager.status()
