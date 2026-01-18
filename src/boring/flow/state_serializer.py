import json
import logging
from pathlib import Path

from .nodes.base import FlowContext

logger = logging.getLogger(__name__)


class StateSerializer:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.checkpoint_dir = self.root / ".boring" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self, context: FlowContext, step_count: int, current_node: str
    ) -> Path | None:
        """Save current flow state to disk."""
        try:
            # Create a serializable dict from context
            # Exclude non-serializable objects like state_manager (re-hydrate later)
            data = {
                "project_root": str(context.project_root),
                "user_goal": context.user_goal,
                # Convert memory objects to dict/list if needed, assuming they constitute simple types here for now
                "memory": context.memory if isinstance(context.memory, (dict, list, str, int, float, bool, type(None))) else str(context.memory),
                "errors": context.errors,
                "auto_mode": getattr(context, "auto_mode", False),
                "metadata": {"step_count": step_count, "current_node": current_node},
            }

            checkpoint_file = self.checkpoint_dir / "latest.json"
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return checkpoint_file
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return None

    def load_checkpoint(self) -> dict | None:
        """Load the latest checkpoint."""
        checkpoint_file = self.checkpoint_dir / "latest.json"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
