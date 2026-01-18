"""
Boring Memory System

Implements structured, persistent memory for the autonomous agent loop.
Uses SQLite for reliable, concurrent-safe storage.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import settings
from ..paths import get_boring_path
from ..storage import LoopRecord, SQLiteStorage


@dataclass
class LoopMemory:
    """Memory entry for a single loop iteration."""

    loop_id: int
    timestamp: str
    status: str  # SUCCESS, FAILED, PARTIAL
    files_modified: list[str]
    tasks_completed: list[str]
    errors: list[str]
    ai_output_summary: str
    duration_seconds: float


@dataclass
class ProjectMemory:
    """Overall project memory state."""

    project_name: str
    total_loops: int
    successful_loops: int
    failed_loops: int
    last_activity: str
    current_focus: str
    completed_milestones: list[str]
    pending_issues: list[str]
    learned_patterns: list[str]  # Things AI learned to avoid/prefer


class MemoryManager:
    """
    Manages persistent memory across Boring sessions.

    Storage Backend: SQLite (via SQLiteStorage)

    Database Tables:
    - loops: Loop execution history
    - error_patterns: Common errors and solutions
    - project_state: Overall project state (singleton)
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.memory_dir = get_boring_path(self.project_root, "memory")
        # Ensure dir exists is handled by get_boring_path if create=True (default)

        # Initialize SQLite storage backend
        self._storage = SQLiteStorage(self.memory_dir)

        # Cache project name
        self._project_name = self.project_root.name

    def get_project_state(self) -> dict[str, Any]:
        """Load current project state from SQLite."""
        return self._storage.get_project_state(self._project_name)

    def update_project_state(self, updates: dict[str, Any]):
        """Update project state in SQLite."""
        self._storage.update_project_state(updates, self._project_name)

    def record_loop(self, memory: LoopMemory):
        """Record a loop's outcome to SQLite."""
        # Convert LoopMemory to LoopRecord for storage
        record = LoopRecord(
            loop_id=memory.loop_id,
            timestamp=memory.timestamp,
            status=memory.status,
            files_modified=memory.files_modified,
            tasks_completed=memory.tasks_completed,
            errors=memory.errors,
            duration_seconds=memory.duration_seconds,
            output_summary=memory.ai_output_summary,
        )
        self._storage.record_loop(record)

        # Update project stats
        is_success = memory.status == "SUCCESS"
        self._storage.increment_loop_stats(is_success)

    def get_loop_history(self, last_n: int = 20) -> list[dict]:
        """Get recent loop history from SQLite."""
        return self._storage.get_recent_loops(last_n)

    def get_last_loop_summary(self) -> str:
        """Get a human-readable summary of the last loop."""
        history = self._storage.get_recent_loops(1)
        if not history:
            return "No previous loop recorded."

        last = history[0]
        files_modified = last.get("files_modified", [])
        if isinstance(files_modified, str):
            try:
                files_modified = json.loads(files_modified)
            except (json.JSONDecodeError, TypeError):
                files_modified = []

        tasks_completed = last.get("tasks_completed", [])
        if isinstance(tasks_completed, str):
            try:
                tasks_completed = json.loads(tasks_completed)
            except (json.JSONDecodeError, TypeError):
                tasks_completed = []

        errors = last.get("errors", [])
        if isinstance(errors, str):
            try:
                errors = json.loads(errors)
            except (json.JSONDecodeError, TypeError):
                errors = []

        return f"""## Previous Loop Summary (#{last.get("loop_id", "?")})
- **Status:** {last.get("status", "UNKNOWN")}
- **Files Modified:** {len(files_modified)}
- **Tasks Completed:** {", ".join(tasks_completed) if tasks_completed else "None"}
- **Errors:** {", ".join(errors) if errors else "None"}
- **Summary:** {str(last.get("output_summary", "N/A"))[:200]}
"""

    def record_error_pattern(self, error_type: str, error_message: str, solution: str = ""):
        """Learn from errors to avoid repeating them."""
        self._storage.record_error(error_type, error_message, context="")
        if solution:
            self._storage.add_solution(error_type, error_message, solution)

    def get_error_patterns(self) -> list[dict]:
        """Get known error patterns from SQLite."""
        return self._storage.get_top_errors(50)

    def record_metric(self, name: str, value: float, metadata: dict | None = None):
        """Record a performance or usage metric."""
        self._storage.record_metric(name, value, metadata)

    def get_common_errors_warning(self) -> str:
        """Generate a warning about common errors for the AI."""
        patterns = self._storage.get_top_errors(5)
        if not patterns:
            return ""

        warning_lines = ["## ⚠️ Common Errors to Avoid:"]
        for err in patterns:
            solution = err.get("solution", "")
            solution_text = f" → Fix: {solution}" if solution else ""
            warning_lines.append(
                f"- **{err['error_type']}** ({err.get('occurrence_count', 1)}x): "
                f"{str(err['error_message'])[:100]}{solution_text}"
            )

        return "\n".join(warning_lines)

    def generate_context_injection(self) -> str:
        """Generate a complete context injection for the AI."""
        parts = []

        # 1. Project State
        state = self.get_project_state()
        parts.append(f"""## Project State
- **Name:** {state.get("project_name", "Unknown")}
- **Total Loops:** {state.get("total_loops", 0)} ({state.get("successful_loops", 0)} success, {state.get("failed_loops", 0)} failed)
- **Current Focus:** {state.get("current_focus", "Not set")}
""")

        # 2. Last Loop Summary
        last_summary = self.get_last_loop_summary()
        if "No previous loop" not in last_summary:
            parts.append(last_summary)

        # 3. Common Error Warnings
        error_warning = self.get_common_errors_warning()
        if error_warning:
            parts.append(error_warning)

        return "\n".join(parts)

    def export_sync_state(self, file_path: Path) -> None:
        """
        Export critical project state to a JSON file for Git synchronization.
        This enables 'Serverless Collaboration' by allowing the state to be versioned.
        """
        state = self.get_project_state()
        sync_data = {
            "version": "1.0",
            "project_state": state,
            # We can expand this to include task lists, architectural decisions, etc.
        }
        file_path.write_text(json.dumps(sync_data, indent=2, sort_keys=True), encoding="utf-8")

    def import_sync_state(self, file_path: Path) -> dict[str, Any]:
        """
        Import and merge project state from a sync JSON file.
        Returns a diff/summary of what changed.

        Strategy: Union Merge for lists, Latest Wins for scalars (simplified).
        """
        if not file_path.exists():
            return {"status": "no_file"}

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            remote_state = data.get("project_state", {})
            local_state = self.get_project_state()

            changes = []

            # 1. Merge Lists (Privacy-preserving union)
            for key in ["completed_milestones", "pending_issues", "learned_patterns"]:
                local_list = set(local_state.get(key, []) or [])
                remote_list = set(remote_state.get(key, []) or [])
                new_items = remote_list - local_list
                if new_items:
                    # Update local state list
                    updated_list = list(local_list | remote_list)
                    # Ideally we want to preserve order, but set destroys it.
                    # For sync, existence is more important than order.
                    updated_list.sort()
                    local_state[key] = updated_list
                    changes.append(f"Merged {len(new_items)} items into {key}")

            # 2. Update Scalars if remote looks "newer" or different?
            # For now, we only merge lists. Scalars like 'total_loops' are strictly local metrics.
            # 'current_focus' might be interesting to sync.
            if remote_state.get("current_focus") and remote_state[
                "current_focus"
            ] != local_state.get("current_focus"):
                local_state["current_focus"] = remote_state["current_focus"]
                changes.append(f"Updated focus to: {remote_state['current_focus']}")

            # Save back to SQLite
            self.update_project_state(local_state)

            return {"status": "merged", "changes": changes}

        except Exception as e:
            return {"status": "error", "error": str(e)}
