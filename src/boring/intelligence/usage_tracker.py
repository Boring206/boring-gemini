import atexit
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class ToolUsage:
    tool_name: str
    count: int = 0
    last_used: float = 0.0

@dataclass
class UsageStats:
    tools: dict[str, ToolUsage] = field(default_factory=dict)
    total_calls: int = 0
    last_updated: float = 0.0

class AnomalyDetectedError(Exception):
    """Raised when an anomaly (stuck loop) is detected."""
    def __init__(self, tool_name: str, count: int):
        self.tool_name = tool_name
        self.count = count
        super().__init__(f"Tool loop detected: {tool_name} called {count} times consecutively with identical arguments.")

class UsageTracker:
    """
    Tracks usage of MCP tools to enable Adaptive Profiles.
    """
    def __init__(self, persistence_path: Optional[Path] = None):
        if persistence_path is None:
            # Default to ~/.boring/usage.json
            persistence_path = Path.home() / ".boring" / "usage.json"

        self.persistence_path = persistence_path
        self.stats = UsageStats()
        self._dirty = False
        self._write_count = 0
        self._WRITE_INTERVAL = 10  # Flush every 10 calls
        self._load()

        # Anomaly Detection State (Ephemeral)
        self.last_tool_name: Optional[str] = None
        self.last_tool_args: Optional[str] = None
        self.repeat_count: int = 0
        self.ANOMALY_THRESHOLD = 50

    def track(self, tool_name: str, tool_args: Any = None):
        """
        Track a call to a tool.

        Args:
            tool_name: Name of the tool.
            tool_args: Arguments passed to the tool (used for loop detection).
        """
        now = time.time()

        # --- P5: Anomaly Detection ---
        # Serialize args to string for comparison (lists/dicts are not hashable)
        current_args_str = str(tool_args) if tool_args is not None else ""

        if tool_name == self.last_tool_name and current_args_str == self.last_tool_args:
            self.repeat_count += 1
        else:
            self.last_tool_name = tool_name
            self.last_tool_args = current_args_str
            self.repeat_count = 1

        if self.repeat_count > self.ANOMALY_THRESHOLD:
             # Reset to avoid spamming exceptions on every subsequent call if caller ignores it?
             # No, keeps warning.
             raise AnomalyDetectedError(tool_name, self.repeat_count)
        # -----------------------------

        now = time.time()
        if tool_name not in self.stats.tools:
            self.stats.tools[tool_name] = ToolUsage(tool_name=tool_name)

        usage = self.stats.tools[tool_name]
        usage.count += 1
        usage.last_used = now

        self.stats.total_calls += 1
        self.stats.last_updated = now

        # Debounced write: only write every N calls
        self._dirty = True
        self._write_count += 1
        if self._write_count >= self._WRITE_INTERVAL:
            self.flush()

    def flush(self):
        """Flush stats to disk if dirty."""
        if self._dirty:
            self._save()
            self._dirty = False
            self._write_count = 0

    def get_top_tools(self, limit: int = 20) -> list[str]:
        """Get the most frequently used tools."""
        sorted_tools = sorted(
            self.stats.tools.values(),
            key=lambda x: x.count,
            reverse=True
        )
        return [t.tool_name for t in sorted_tools[:limit]]

    def _save(self):
        """Save stats to disk."""
        try:
            self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "total_calls": self.stats.total_calls,
                "last_updated": self.stats.last_updated,
                "tools": {k: asdict(v) for k, v in self.stats.tools.items()}
            }

            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # Log error but continue to avoid interrupting tool execution
            logger.warning(f"Failed to save usage stats: {e}")

    def _load(self):
        """Load stats from disk."""
        if not self.persistence_path.exists():
            return

        try:
            with open(self.persistence_path, encoding="utf-8") as f:
                data = json.load(f)

            self.stats.total_calls = data.get("total_calls", 0)
            self.stats.last_updated = data.get("last_updated", 0.0)

            for name, usage_data in data.get("tools", {}).items():
                self.stats.tools[name] = ToolUsage(**usage_data)
        except Exception as e:
            # Log and start fresh if corrupted
            logger.warning(f"Failed to load usage stats: {e}")

# Singleton instance with thread safety
_tracker: Optional[UsageTracker] = None
_tracker_lock = __import__('threading').Lock()

def get_tracker() -> UsageTracker:
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:  # Double-check locking
                _tracker = UsageTracker()
                # Register atexit to flush on shutdown
                atexit.register(_tracker.flush)
    return _tracker
