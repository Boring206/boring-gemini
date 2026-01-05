# Copyright 2025 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Streaming Progress Reporter for long-running operations.

Provides real-time progress updates for operations like run_boring,
enabling better UX in IDE integrations.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class ProgressStage(Enum):
    """Stages of a Boring task execution."""

    INITIALIZING = "initializing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressEvent:
    """A single progress update event."""

    stage: ProgressStage
    message: str
    percentage: float  # 0.0 to 100.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class ProgressReporter:
    """
    Reports progress for long-running Boring operations.

    Supports multiple output modes:
    - Callbacks: Direct function calls for IDE integration
    - File: Write to a JSON file for polling
    - Memory: Store in memory for later retrieval
    """

    def __init__(
        self,
        task_id: str,
        total_stages: int = 4,
        output_file: Optional[Path] = None,
        callback: Optional[Callable[[ProgressEvent], None]] = None,
    ):
        self.task_id = task_id
        self.total_stages = total_stages
        self.output_file = output_file
        self.callback = callback

        self.events: list[ProgressEvent] = []
        self.current_stage = 0
        self.start_time = time.time()

    def report(
        self,
        stage: ProgressStage,
        message: str,
        sub_percentage: float = 0.0,
        metadata: Optional[dict] = None,
    ):
        """
        Report a progress update.

        Args:
            stage: Current execution stage
            message: Human-readable progress message
            sub_percentage: Percentage within current stage (0-100)
            metadata: Optional additional data
        """
        # Calculate overall percentage
        stage_index = list(ProgressStage).index(stage)
        base_percentage = (stage_index / self.total_stages) * 100
        stage_contribution = (sub_percentage / 100) * (100 / self.total_stages)
        overall_percentage = min(base_percentage + stage_contribution, 100.0)

        event = ProgressEvent(
            stage=stage, message=message, percentage=overall_percentage, metadata=metadata or {}
        )

        self.events.append(event)

        # Invoke callback if provided
        if self.callback:
            try:
                self.callback(event)
            except Exception:
                pass  # Don't let callback errors break execution

        # Write to file if configured
        if self.output_file:
            self._write_to_file(event)

    def _write_to_file(self, event: ProgressEvent):
        """Write progress to JSON file for polling."""
        data = {
            "task_id": self.task_id,
            "stage": event.stage.value,
            "message": event.message,
            "percentage": event.percentage,
            "timestamp": event.timestamp.isoformat(),
            "elapsed_seconds": time.time() - self.start_time,
            "metadata": event.metadata,
        }

        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def get_latest(self) -> Optional[ProgressEvent]:
        """Get the most recent progress event."""
        return self.events[-1] if self.events else None

    def get_all_events(self) -> list[dict]:
        """Get all progress events as dictionaries."""
        return [
            {
                "stage": e.stage.value,
                "message": e.message,
                "percentage": e.percentage,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self.events
        ]

    def complete(self, success: bool = True, message: str = "Task completed"):
        """Mark the task as completed."""
        stage = ProgressStage.COMPLETED if success else ProgressStage.FAILED
        self.report(stage, message, 100.0)

    def get_duration(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time


class StreamingTaskManager:
    """
    Manages multiple concurrent streaming tasks.

    Enables tracking of multiple run_boring operations simultaneously.
    """

    def __init__(self):
        self._reporters: dict[str, ProgressReporter] = {}

    def create_reporter(
        self, task_id: str, output_dir: Optional[Path] = None, callback: Optional[Callable] = None
    ) -> ProgressReporter:
        """Create a new progress reporter for a task."""
        output_file = None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{task_id}.progress.json"

        reporter = ProgressReporter(task_id=task_id, output_file=output_file, callback=callback)

        self._reporters[task_id] = reporter
        return reporter

    def get_reporter(self, task_id: str) -> Optional[ProgressReporter]:
        """Get an existing reporter by task ID."""
        return self._reporters.get(task_id)

    def get_all_active(self) -> list[dict]:
        """Get status of all active tasks."""
        return [
            {
                "task_id": task_id,
                "latest": reporter.get_latest().__dict__ if reporter.get_latest() else None,
                "duration": reporter.get_duration(),
            }
            for task_id, reporter in self._reporters.items()
        ]

    def cleanup_completed(self):
        """Remove completed tasks from tracking."""
        to_remove = [
            task_id
            for task_id, reporter in self._reporters.items()
            if reporter.get_latest()
            and reporter.get_latest().stage in [ProgressStage.COMPLETED, ProgressStage.FAILED]
        ]
        for task_id in to_remove:
            del self._reporters[task_id]


# Global manager instance
_manager = StreamingTaskManager()


def get_streaming_manager() -> StreamingTaskManager:
    """Get the global streaming task manager."""
    return _manager
