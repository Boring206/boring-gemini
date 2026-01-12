# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Background Agent for Boring.

Provides async task execution using local thread pool.
"""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from rich.console import Console

console = Console()


@dataclass
class BackgroundTask:
    """Represents a background task."""

    task_id: str
    name: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    progress: int = 0  # 0-100


class BackgroundTaskRunner:
    """
    Manages background task execution using thread pool.

    Features:
    - Non-blocking task submission
    - Status tracking
    - Result retrieval
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_workers: int = 4):
        if self._initialized:
            return
        self._initialized = True
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="boring-bg-")
        self.tasks: dict[str, BackgroundTask] = {}
        self.futures: dict[str, Any] = {}

    def submit(
        self,
        func: Callable,
        *args: Any,
        name: str = "Background task",
        **kwargs: Any,
    ) -> str:
        """
        Submit a task for background execution.

        Args:
            func: Function to execute
            name: Task name for display
            *args: Arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            task_id for tracking
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"

        task = BackgroundTask(
            task_id=task_id,
            name=name,
            status="pending",
            created_at=datetime.now(),
        )
        self.tasks[task_id] = task

        def wrapper():
            task.status = "running"
            task.started_at = datetime.now()
            try:
                result = func(*args, **kwargs)
                task.result = result
                task.status = "completed"
            except Exception as e:
                task.error = str(e)
                task.status = "failed"
            finally:
                task.completed_at = datetime.now()

        future = self.executor.submit(wrapper)
        self.futures[task_id] = future

        return task_id

    def get_status(self, task_id: str) -> dict:
        """Get status of a task."""
        task = self.tasks.get(task_id)
        if not task:
            return {"status": "not_found", "task_id": task_id}

        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress": task.progress,
            "result": task.result if task.status == "completed" else None,
            "error": task.error,
        }

    def get_result(self, task_id: str, timeout: float = None) -> dict:
        """Wait for and get result of a task."""
        future = self.futures.get(task_id)
        if not future:
            return {"status": "not_found", "task_id": task_id}

        try:
            future.result(timeout=timeout)
        except Exception:
            pass

        return self.get_status(task_id)

    def list_tasks(self, status_filter: str = None) -> list[dict]:
        """List all tasks, optionally filtered by status."""
        tasks = []
        for task in self.tasks.values():
            if status_filter and task.status != status_filter:
                continue
            tasks.append(
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                }
            )
        return sorted(tasks, key=lambda x: x["created_at"], reverse=True)

    def cancel(self, task_id: str) -> dict:
        """Attempt to cancel a pending task."""
        future = self.futures.get(task_id)
        if not future:
            return {"status": "not_found", "task_id": task_id}

        task = self.tasks[task_id]
        if task.status != "pending":
            return {"status": "cannot_cancel", "message": f"Task is {task.status}"}

        if future.cancel():
            task.status = "cancelled"
            return {"status": "cancelled", "task_id": task_id}

        return {"status": "cancel_failed", "task_id": task_id}

    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        self.executor.shutdown(wait=wait)


# --- Global instance ---
_runner: Optional[BackgroundTaskRunner] = None


def get_runner() -> BackgroundTaskRunner:
    """Get or create the global background runner."""
    global _runner
    if _runner is None:
        _runner = BackgroundTaskRunner()
    return _runner


# --- Convenience functions for MCP tools ---


def submit_background_task(
    task_type: str,
    task_args: dict = None,
    project_path: str = None,
) -> dict:
    """
    Submit a background task.

    Supported task types:
    - verify: Run verification in background
    - test: Run tests in background
    - lint: Run linting in background
    - security_scan: Run security scan in background

    Returns:
        Task info with task_id
    """
    from ..config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    runner = get_runner()
    args = task_args or {}

    if task_type == "verify":
        from ..verification import CodeVerifier

        def run_verify():
            verifier = CodeVerifier(path)
            return verifier.verify_project(args.get("level", "STANDARD"))

        task_id = runner.submit(run_verify, name=f"Verify ({args.get('level', 'STANDARD')})")

    elif task_type == "security_scan":
        from ..security import run_security_scan

        task_id = runner.submit(lambda: run_security_scan(str(path)), name="Security Scan")

    elif task_type == "test":
        import subprocess

        def run_tests():
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {"passed": result.returncode == 0, "output": result.stdout[-2000:]}

        task_id = runner.submit(run_tests, name="Run Tests")

    elif task_type == "lint":
        import subprocess

        def run_lint():
            result = subprocess.run(
                ["ruff", "check", "src/"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {"passed": result.returncode == 0, "output": result.stdout[-1000:]}

        task_id = runner.submit(run_lint, name="Lint Check")

    else:
        return {"status": "error", "message": f"Unknown task type: {task_type}"}

    return {
        "status": "submitted",
        "task_id": task_id,
        "task_type": task_type,
        "message": f"Task submitted. Use boring_task_status('{task_id}') to check progress.",
    }


def get_task_status(task_id: str) -> dict:
    """Get status of a background task."""
    return get_runner().get_status(task_id)


def list_background_tasks(status: str = None) -> dict:
    """List all background tasks."""
    return {"tasks": get_runner().list_tasks(status)}
