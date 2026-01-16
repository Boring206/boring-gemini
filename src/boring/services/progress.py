"""
Progress Persistence Service (V12.5)

Saves and restores agent loop state to enable session resumption.
"""

import json
import time
from pathlib import Path
from typing import Any

from boring.core.config import settings
from boring.core.logger import get_logger
from boring.loop.context import LoopContext

logger = get_logger(__name__)


class ProgressManager:
    """
    Manages persistence of agent loop progress.
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        from boring.paths import BoringPaths

        self.progress_file = BoringPaths(self.project_root).state / ".boring_progress.json"

    def has_progress(self) -> bool:
        """Check if a progress file exists."""
        return self.progress_file.exists()

    def load_progress(self) -> dict[str, Any] | None:
        """Load progress from file."""
        if not self.has_progress():
            return None

        try:
            return json.loads(self.progress_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            return None

    def save_progress(self, ctx: LoopContext) -> bool:
        """
        Save current loop context to file.
        Only saves serializable and relevant fields.
        """
        try:
            data = {
                "timestamp": time.time(),
                "loop_count": ctx.loop_count,
                "current_task_type": ctx.current_task_type,
                "session_keywords": ctx.session_keywords,
                "task_history": ctx.task_history,
                "error_history": ctx.error_history,
                "file_access_history": ctx.file_access_history,
                "files_modified": ctx.files_modified,
                "files_created": ctx.files_created,
                "prompt_file": str(ctx.prompt_file) if ctx.prompt_file else None,
            }

            self.progress_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            return False

    def restore_context(self, ctx: LoopContext) -> bool:
        """
        Restore context from saved progress.
        """
        data = self.load_progress()
        if not data:
            return False

        try:
            ctx.loop_count = data.get("loop_count", 0)
            ctx.current_task_type = data.get("current_task_type", "general")
            ctx.session_keywords = data.get("session_keywords", [])
            ctx.task_history = data.get("task_history", [])
            ctx.error_history = data.get("error_history", [])
            ctx.file_access_history = data.get("file_access_history", [])

            # These are cumulative, but maybe we only want to track what happened in PREVIOUS sessions?
            # For now, let's restore them so the agent knows what it did.
            ctx.files_modified = data.get("files_modified", [])
            ctx.files_created = data.get("files_created", [])

            # Prompt file check?
            saved_prompt = data.get("prompt_file")
            if saved_prompt:
                path = Path(saved_prompt)
                if path.exists() and ctx.prompt_file != path:
                    logger.warning(
                        f"Restored prompt file {path} differs from current {ctx.prompt_file}"
                    )
                    # Optionally switch prompt file?
                    # ctx.prompt_file = path

            logger.info(f"Restored session state (Loop {ctx.loop_count})")
            return True

        except Exception as e:
            logger.error(f"Failed to restore context: {e}")
            return False

    def clear_progress(self):
        """Delete specific progress file."""
        if self.has_progress():
            try:
                self.progress_file.unlink()
            except Exception as e:
                logger.error(f"Failed to clear progress: {e}")
