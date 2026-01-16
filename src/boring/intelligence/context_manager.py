"""
Context Manager for Boring-Gemini V14.0

Provides stateful session memory and context awareness.
Allows the agent to remember "what happened last time" and understand
context-dependent user requests (e.g. "fix it", "why did that fail?").
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from boring.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Persistent state for the current user session."""

    session_id: str
    last_activity_time: float
    last_command: str = ""
    last_error: str | None = None
    last_modified_files: list[str] = field(default_factory=list)
    active_focus_files: list[str] = field(default_factory=list)
    recent_tool_outputs: list[dict[str, Any]] = field(default_factory=list)

    # "Working Memory" - Short term context
    user_intent_history: list[str] = field(default_factory=list)


class ContextManager:
    """
    Manages the 'Working Memory' of the Boring Agent.
    """

    def __init__(self, project_root: Path | None = None):
        self.root = project_root or settings.PROJECT_ROOT
        self.context_dir = self.root / ".boring" / "context"
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.context_dir / "session_state.json"

        self.state = self._load_state()

    def _load_state(self) -> SessionState:
        """Load session state from disk or create new."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                # Basic schema migration/safety
                return SessionState(
                    **{k: v for k, v in data.items() if k in SessionState.__annotations__}
                )
            except Exception as e:
                logger.warning(f"Failed to load session state: {e}")

        return SessionState(session_id=f"sess_{int(time.time())}", last_activity_time=time.time())

    def save(self):
        """Persist current state to disk."""
        try:
            data = asdict(self.state)
            self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save context state: {e}")

    def update_activity(self, command: str):
        """Update last activity timestamp and command."""
        self.state.last_activity_time = time.time()
        self.state.last_command = command
        self.save()

    def set_last_error(self, error: str):
        """Record the last encountered error."""
        self.state.last_error = error
        self.save()

    def track_file_modification(self, file_path: str):
        """Track that a file was modified."""
        if file_path not in self.state.last_modified_files:
            self.state.last_modified_files.insert(0, file_path)
            # Keep only last 10
            self.state.last_modified_files = self.state.last_modified_files[:10]
        self.save()

    def get_context_summary(self) -> str:
        """
        Generate a natural language summary of the current context.
        Used for injecting into LLM prompts.
        """
        parts = []

        # Recency check (e.g. 1 hour)
        is_recent = (time.time() - self.state.last_activity_time) < 3600

        if self.state.last_command:
            time_str = "just now" if is_recent else "previously"
            parts.append(f"User {time_str} ran command '{self.state.last_command}'.")

        if self.state.last_error and is_recent:
            parts.append(f"The last operation failed with error: {self.state.last_error[:200]}...")

        if self.state.last_modified_files:
            files = ", ".join([Path(f).name for f in self.state.last_modified_files[:3]])
            parts.append(f"Recently modified files: {files}")

        return "\n".join(parts)

    def resolve_reference(self, reference: str) -> str | None:
        """
        Resolve vague references like "it", "that file", "the error".
        """
        ref_lower = reference.lower()

        if "error" in ref_lower or "failure" in ref_lower:
            return self.state.last_error

        if "file" in ref_lower or "it" in ref_lower:
            if self.state.last_modified_files:
                return self.state.last_modified_files[0]

        return None
