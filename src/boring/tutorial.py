# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TutorialManager:
    """
    Manages interactive tutorial state and progress persistence.
    Works in tandem with the CLI tutorial but handles logic/backend.
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize with project root."""
        if project_root is None:
            from .utils import get_project_root_or_error

            self.project_root = get_project_root_or_error()
        else:
            self.project_root = project_root

        self.state_file = self.project_root / ".boring_tutorial.json"
        self._state = self._load_state()

    def _load_state(self) -> dict:
        """Load state from JSON file."""
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load tutorial state: {e}")
            return {}

    def _save_state(self):
        """Save state to JSON file."""
        try:
            self.state_file.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save tutorial state: {e}")

    def show_tutorial(self, tutorial_id: str):
        """
        Show a tutorial if it hasn't been seen yet.
        For now, this just marks it as seen in the backend state.
        The actual UI display is handled by the CLI or MCP tool response.
        """
        if self._state.get(tutorial_id):
            return  # Already seen

        # Mark as seen
        self._state[tutorial_id] = True
        self._save_state()
        logger.info(f"Tutorial '{tutorial_id}' marked as complete.")

    def generate_learning_note(self) -> Path:
        """
        Generate a learning summary/note based on achievements.
        Returns the path to the generated note.
        """
        import json

        note_content = "# Vibe Coder 學習筆記\n\n"
        note_content += f"**產生時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        note_content += "## 🏆 成就解鎖\n"

        if self._state.get("first_project"):
            note_content += "- 🎉 恭喜建立第一個專案\n"

        note_content += "\n## 📊 工具使用統計\n"

        # Try to read from audit.jsonl file first (for testing compatibility)
        log_file = self.project_root / "logs" / "audit.jsonl"
        tool_counts = {}

        if log_file.exists():
            try:
                with open(log_file, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            log = json.loads(line)
                            tool = log.get("tool") or log.get("resource", "")
                            if tool:
                                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            except Exception:
                pass

        # Fallback to AuditLogger if no JSONL file
        if not tool_counts:
            try:
                from .services.audit import AuditLogger

                logs = AuditLogger.get_instance().get_logs(limit=100)
                for log in logs:
                    tool = log.get("resource", "")
                    if tool:
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1
            except Exception:
                pass

        for tool, count in tool_counts.items():
            note_content += f"- `{tool}`: ({count} 次)\n"

        # Save to project docs
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        note_path = docs_dir / "learning_note.md"
        note_path.write_text(note_content, encoding="utf-8")

        return note_path
