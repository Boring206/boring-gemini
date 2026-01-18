# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Manages synchronization of skills to client directories.
    Ensures that when a user installs a skill in Boring (Hub),
    it becomes available in Gemini CLI and Claude Code automatically.
    """

    CLIENT_DIRS = [
        ".gemini/skills",
        ".claude/skills",
        ".cursor/skills",  # Cursor IDE Support
        ".antigravity/skills",
        ".codex/skills",  # OpenAI Codex CLI
    ]

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.hub_dir = self.project_root / ".boring" / "skills"

    def sync_skill(self, skill_name: str) -> list[str]:
        """
        Sync a specific skill from Hub (.boring) to all Client directories.
        Returns list of destination paths synced.
        """
        source_path = self.hub_dir / skill_name

        # Check source existence
        if not source_path.exists():
            # Try checking if it's a single file skill
            source_file = self.hub_dir / f"{skill_name}.md"
            if source_file.exists():
                return self._sync_single_file(source_file, skill_name)

            logger.warning(f"Skill source not found: {source_path}")
            return []

        synced_targets = []

        for client_rel in self.CLIENT_DIRS:
            target_dir = self.project_root / client_rel / skill_name
            try:
                # Ensure parent dir exists
                target_dir.parent.mkdir(parents=True, exist_ok=True)

                # Copy tree
                shutil.copytree(source_path, target_dir, dirs_exist_ok=True)
                synced_targets.append(str(target_dir))
                logger.info(f"Synced skill '{skill_name}' to {target_dir}")

            except Exception as e:
                logger.error(f"Failed to sync to {target_dir}: {e}")

        return synced_targets

    def _sync_single_file(self, source_file: Path, skill_name: str) -> list[str]:
        """Handle syncing of single file skills."""
        synced_targets = []
        for client_rel in self.CLIENT_DIRS:
            target_file = self.project_root / client_rel / f"{skill_name}.md"
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                synced_targets.append(str(target_file))
            except Exception as e:
                logger.error(f"Failed to sync file to {target_file}: {e}")
        return synced_targets

    def ensure_hub_exists(self):
        """Ensure the .boring/skills directory exists."""
        self.hub_dir.mkdir(parents=True, exist_ok=True)
