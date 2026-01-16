"""
Tool Manager for Dynamic Tool Activation (V12.5)

Manages tool profiles and context-aware tool filtering.
"""

import os
from pathlib import Path

from boring.core.config import settings
from boring.core.logger import get_logger
from boring.mcp.tool_profiles import ToolProfile, get_profile

logger = get_logger(__name__)


class ToolManager:
    """
    Manages active tool profiles and dynamic context activation.
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.config_path = self.project_root / ".boring.toml"

    def set_profile(self, profile_name: str) -> bool:
        """
        Set the active tool profile in .boring.toml.

        Args:
            profile_name: Name of the profile (lite, standard, full, etc.)

        Returns:
            True if successful
        """
        try:
            # Validate profile name
            try:
                profile_enum = ToolProfile(profile_name.lower())
            except ValueError:
                logger.error(f"Invalid profile name: {profile_name}")
                return False

            # Update .boring.toml
            self._update_config_file(profile_enum.value)

            # Update env var for current session too?
            # (Only affects child processes if we export, but good for validity)
            os.environ["BORING_MCP_PROFILE"] = profile_enum.value

            logger.info(f"Switched to profile: {profile_enum.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set profile: {e}")
            return False

    def get_active_profile(self) -> str:
        """Get current active profile name."""
        return get_profile().name

    def activate_context_tools(self, context_keywords: list[str]) -> list[str]:
        """
        Identify and suggest tools based on context keywords.

        Args:
            context_keywords: List of intent keywords (e.g. ['security', 'audit'])

        Returns:
            List of suggested tool names
        """
        # This simulates "Dynamic Activation" by analyzing intent vs available tools.
        # In a real dynamic system, this would unlock them.
        # For now, it returns suggestions for the 'Adaptive' profile to use.

        suggestions = []
        from boring.mcp.tool_router import TOOL_CATEGORIES

        for kw in context_keywords:
            for cat in TOOL_CATEGORIES.values():
                if kw in cat.keywords:
                    suggestions.extend(cat.tools)

        return list(set(suggestions))

    def _update_config_file(self, profile_name: str):
        """Update the profile in .boring.toml."""
        # Simple TOML updater to preserve other comments/settings if possible
        # Or just use a TOML library if available.
        # boring-gemini uses simple file writing in many places.

        # Check if file exists
        if not self.config_path.exists():
            content = f'[mcp]\nprofile = "{profile_name}"\n'
            self.config_path.write_text(content, encoding="utf-8")
            return

        lines = self.config_path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        in_mcp_section = False
        profile_set = False

        for line in lines:
            if line.strip().startswith("[mcp]"):
                in_mcp_section = True
                new_lines.append(line)
                continue

            if in_mcp_section and line.strip().startswith("["):
                # New section starting
                in_mcp_section = False

            if in_mcp_section and line.strip().startswith("profile"):
                new_lines.append(f'profile = "{profile_name}"')
                profile_set = True
            else:
                new_lines.append(line)

        if not profile_set:
            if not any(line.strip() == "[mcp]" for line in lines):
                new_lines.append("\n[mcp]")
            new_lines.append(f'profile = "{profile_name}"')

        self.config_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
