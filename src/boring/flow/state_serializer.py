"""
State Serializer

Handles serialization and deserialization of FlowContext to enable Pause/Resume.
"""

import logging
import pickle
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
                "memory": context.memory,
                "errors": context.errors,
                "auto_mode": getattr(context, "auto_mode", False),
                "metadata": {"step_count": step_count, "current_node": current_node},
            }

            checkpoint_file = self.checkpoint_dir / "latest.pkl"
            with open(checkpoint_file, "wb") as f:
                pickle.dump(data, f)

            return checkpoint_file
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return None

    def load_checkpoint(self) -> dict | None:
        """Load the latest checkpoint."""
        checkpoint_file = self.checkpoint_dir / "latest.pkl"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, "rb") as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
