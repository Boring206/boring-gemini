"""
Loop Context - Shared state container for the state machine (V10.23 Enhanced).

This dataclass holds all mutable state that is shared between states,
eliminating the need for complex parameter passing.

V10.23 enhancements:
- Sliding window memory management
- Context summarization for long sessions
- Task-aware state tracking
- Memory usage monitoring
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..extensions import ExtensionsManager
    from ..gemini_client import GeminiClient
    from ..intelligence.memory import MemoryManager
    from ..storage import SQLiteStorage
    from ..verification import CodeVerifier

from ..config import settings

# V10.23: Memory management constants
MAX_ERROR_HISTORY = 50
MAX_TASK_HISTORY = 100
MAX_FILE_HISTORY = 200


@dataclass
class LoopContext:
    """
    Shared mutable context passed between all states (V10.23 Enhanced).

    This replaces the scattered instance variables in the old AgentLoop,
    providing a clean, explicit container for loop state.

    V10.23 features:
    - Sliding window for error/task history
    - Memory usage tracking
    - Task context for RAG integration
    """

    # === Configuration (immutable during loop) ===
    model_name: str = settings.DEFAULT_MODEL
    use_cli: bool = False
    verbose: bool = False
    interactive: bool = False
    verification_level: str = "STANDARD"
    project_root: Path = field(default_factory=lambda: settings.PROJECT_ROOT)
    log_dir: Path = field(default_factory=lambda: settings.LOG_DIR)
    prompt_file: Path = field(default_factory=lambda: settings.PROJECT_ROOT / settings.PROMPT_FILE)

    # === Injected Subsystems ===
    gemini_client: Optional["GeminiClient"] = None
    memory: Optional["MemoryManager"] = None
    verifier: Optional["CodeVerifier"] = None
    storage: Optional["SQLiteStorage"] = None
    extensions: Optional["ExtensionsManager"] = None

    # === Loop Counters ===
    loop_count: int = 0
    max_loops: int = field(default_factory=lambda: settings.MAX_LOOPS)
    retry_count: int = 0
    max_retries: int = 3
    empty_output_count: int = 0

    # === Timing ===
    loop_start_time: float = 0.0
    state_start_time: float = 0.0

    # === Generation State ===
    output_content: str = ""
    output_file: Optional[Path] = None
    function_calls: list[dict[str, Any]] = field(default_factory=list)
    status_report: Optional[dict[str, Any]] = None

    # === Patching State ===
    files_modified: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    patch_errors: list[str] = field(default_factory=list)

    # === Verification State ===
    verification_passed: bool = False
    verification_error: str = ""

    # === Control Flags ===
    should_exit: bool = False
    exit_reason: str = ""

    # === Accumulated Errors ===
    errors_this_loop: list[str] = field(default_factory=list)
    tasks_completed: list[str] = field(default_factory=list)

    # === V10.23: Enhanced State Tracking ===
    error_history: list[dict[str, Any]] = field(default_factory=list)  # Sliding window
    task_history: list[dict[str, Any]] = field(default_factory=list)  # Sliding window
    file_access_history: list[str] = field(default_factory=list)  # Sliding window
    current_task_type: str = "general"  # "debugging", "feature", "refactoring", "testing"
    session_keywords: list[str] = field(default_factory=list)
    memory_warnings: int = 0

    def start_loop(self) -> None:
        """Reset per-loop state at beginning of each iteration."""
        self.loop_start_time = time.time()
        self.output_content = ""
        self.output_file = None
        self.function_calls = []
        self.status_report = None
        self.files_modified = []
        self.files_created = []
        self.patch_errors = []
        self.verification_passed = False
        self.verification_error = ""
        self.errors_this_loop = []
        self.tasks_completed = []

    def start_state(self) -> None:
        """Record state entry time for telemetry."""
        self.state_start_time = time.time()

    def get_state_duration(self) -> float:
        """Get duration of current state in seconds."""
        return time.time() - self.state_start_time

    def get_loop_duration(self) -> float:
        """Get duration of current loop in seconds."""
        return time.time() - self.loop_start_time

    def increment_loop(self) -> None:
        """Increment loop counter and reset retry count."""
        self.loop_count += 1
        self.retry_count = 0
        self.start_loop()

    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1

    def can_retry(self) -> bool:
        """Check if more retries are allowed."""
        return self.retry_count < self.max_retries

    def should_continue(self) -> bool:
        """Check if loop should continue."""
        return not self.should_exit and self.loop_count < self.max_loops

    def mark_exit(self, reason: str) -> None:
        """Mark loop for exit with reason."""
        self.should_exit = True
        self.exit_reason = reason

    # =========================================================================
    # V10.23: Enhanced Memory Management Methods
    # =========================================================================

    def record_error(self, error_type: str, error_msg: str, file_path: str = "") -> None:
        """
        V10.23: Record an error with sliding window management.

        Keeps only the most recent MAX_ERROR_HISTORY errors.
        """
        self.error_history.append(
            {
                "type": error_type,
                "message": error_msg[:500],  # Truncate long messages
                "file": file_path,
                "timestamp": time.time(),
                "loop": self.loop_count,
            }
        )

        # Sliding window: keep only recent errors
        if len(self.error_history) > MAX_ERROR_HISTORY:
            self.error_history = self.error_history[-MAX_ERROR_HISTORY:]

    def record_task(self, task_description: str, status: str = "completed") -> None:
        """
        V10.23: Record a completed task with sliding window management.
        """
        self.task_history.append(
            {
                "description": task_description[:200],
                "status": status,
                "timestamp": time.time(),
                "loop": self.loop_count,
            }
        )

        # Sliding window
        if len(self.task_history) > MAX_TASK_HISTORY:
            self.task_history = self.task_history[-MAX_TASK_HISTORY:]

    def record_file_access(self, file_path: str) -> None:
        """
        V10.23: Record file access for RAG context.
        """
        # Avoid duplicates in recent history
        if file_path not in self.file_access_history[-10:]:
            self.file_access_history.append(file_path)

        # Sliding window
        if len(self.file_access_history) > MAX_FILE_HISTORY:
            self.file_access_history = self.file_access_history[-MAX_FILE_HISTORY:]

    def set_task_context(self, task_type: str, keywords: Optional[list[str]] = None) -> None:
        """
        V10.23: Set the current task context for RAG integration.

        Args:
            task_type: One of "debugging", "feature", "refactoring", "testing", "general"
            keywords: Keywords extracted from the current task
        """
        self.current_task_type = task_type
        if keywords:
            # Merge with existing, keeping unique
            existing = set(self.session_keywords)
            existing.update(keywords)
            self.session_keywords = list(existing)[-50:]  # Keep last 50

    def get_recent_focus_files(self, limit: int = 5) -> list[str]:
        """
        V10.23: Get recently accessed files for RAG focus.
        """
        # Deduplicate while preserving order (most recent first)
        seen = set()
        result = []
        for f in reversed(self.file_access_history):
            if f not in seen:
                seen.add(f)
                result.append(f)
                if len(result) >= limit:
                    break
        return result

    def get_error_summary(self) -> dict[str, int]:
        """
        V10.23: Get summary of recent errors by type.
        """
        from collections import Counter

        return dict(Counter(e["type"] for e in self.error_history))

    def get_session_context_for_rag(self) -> dict:
        """
        V10.23: Get session context formatted for RAG retriever.
        """
        return {
            "task_type": self.current_task_type,
            "focus_files": self.get_recent_focus_files(),
            "keywords": self.session_keywords[-20:],  # Last 20 keywords
            "recent_errors": [e["type"] for e in self.error_history[-5:]],
        }

    def estimate_memory_usage(self) -> dict[str, int]:
        """
        V10.23: Estimate memory usage of context data.
        """
        import sys

        def safe_sizeof(obj) -> int:
            try:
                return sys.getsizeof(obj)
            except TypeError:
                return 0

        return {
            "error_history": safe_sizeof(self.error_history),
            "task_history": safe_sizeof(self.task_history),
            "file_access_history": safe_sizeof(self.file_access_history),
            "function_calls": safe_sizeof(self.function_calls),
            "output_content": len(self.output_content),
            "total_estimate": (
                safe_sizeof(self.error_history)
                + safe_sizeof(self.task_history)
                + safe_sizeof(self.file_access_history)
                + safe_sizeof(self.function_calls)
                + len(self.output_content)
            ),
        }

    def compact_if_needed(self, threshold_kb: int = 1024) -> bool:
        """
        V10.23: Compact history if memory exceeds threshold.

        Returns:
            True if compaction was performed
        """
        memory = self.estimate_memory_usage()
        total_kb = memory["total_estimate"] / 1024

        if total_kb > threshold_kb:
            self.memory_warnings += 1

            # Aggressive compaction
            self.error_history = self.error_history[-20:]
            self.task_history = self.task_history[-30:]
            self.file_access_history = self.file_access_history[-50:]
            self.session_keywords = self.session_keywords[-20:]

            return True
        return False

    def get_context_summary(self) -> str:
        """
        V10.23: Get a human-readable summary of context state.
        """
        memory = self.estimate_memory_usage()
        error_summary = self.get_error_summary()

        lines = [
            "📊 Loop Context Summary (V10.23)",
            f"├─ Loop: {self.loop_count}/{self.max_loops}",
            f"├─ Task Type: {self.current_task_type}",
            f"├─ Files Accessed: {len(self.file_access_history)}",
            f"├─ Errors Recorded: {len(self.error_history)}",
        ]

        if error_summary:
            top_errors = sorted(error_summary.items(), key=lambda x: x[1], reverse=True)[:3]
            lines.append(f"│  └─ Top: {', '.join(f'{k}({v})' for k, v in top_errors)}")

        lines.extend(
            [
                f"├─ Tasks Completed: {len(self.task_history)}",
                f"├─ Memory Usage: ~{memory['total_estimate'] / 1024:.1f} KB",
                f"└─ Memory Warnings: {self.memory_warnings}",
            ]
        )

        return "\n".join(lines)
