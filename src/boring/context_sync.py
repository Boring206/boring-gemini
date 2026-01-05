# Copyright 2025-2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Context Sync for Cross-Platform Continuity.

Provides context persistence across sessions and devices.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


@dataclass
class ConversationContext:
    """Represents a saved conversation context."""

    context_id: str
    created_at: datetime
    updated_at: datetime
    project_path: str
    summary: str
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class ContextSyncManager:
    """
    Manages context persistence for cross-session continuity.

    Features:
    - Save current conversation context
    - Resume from previous context
    - Context history management
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.context_dir = self.project_root / ".boring_context"
        self.context_dir.mkdir(exist_ok=True)

    def save_context(
        self,
        context_id: str,
        summary: str,
        messages: list[dict] = None,
        metadata: dict = None,
    ) -> dict:
        """
        Save current conversation context.

        Args:
            context_id: Unique identifier for this context
            summary: Brief summary of the conversation state
            messages: List of message dicts
            metadata: Additional metadata

        Returns:
            Save result
        """
        now = datetime.now()
        context = ConversationContext(
            context_id=context_id,
            created_at=now,
            updated_at=now,
            project_path=str(self.project_root),
            summary=summary,
            messages=messages or [],
            metadata=metadata or {},
        )

        context_file = self.context_dir / f"{context_id}.json"
        data = {
            "context_id": context.context_id,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "project_path": context.project_path,
            "summary": context.summary,
            "messages": context.messages,
            "metadata": context.metadata,
        }

        context_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "status": "saved",
            "context_id": context_id,
            "file": str(context_file),
            "message_count": len(context.messages),
        }

    def load_context(self, context_id: str) -> dict:
        """
        Load a saved context.

        Args:
            context_id: Context ID to load

        Returns:
            Context data or error
        """
        context_file = self.context_dir / f"{context_id}.json"

        if not context_file.exists():
            return {"status": "not_found", "context_id": context_id}

        try:
            data = json.loads(context_file.read_text(encoding="utf-8"))
            return {
                "status": "loaded",
                "context_id": data["context_id"],
                "summary": data["summary"],
                "message_count": len(data.get("messages", [])),
                "messages": data.get("messages", []),
                "metadata": data.get("metadata", {}),
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_contexts(self) -> list[dict]:
        """List all saved contexts."""
        contexts = []

        for ctx_file in self.context_dir.glob("*.json"):
            try:
                data = json.loads(ctx_file.read_text(encoding="utf-8"))
                contexts.append(
                    {
                        "context_id": data["context_id"],
                        "summary": data["summary"][:100],
                        "message_count": len(data.get("messages", [])),
                        "updated_at": data["updated_at"],
                    }
                )
            except Exception:
                pass

        return sorted(contexts, key=lambda x: x["updated_at"], reverse=True)

    def delete_context(self, context_id: str) -> dict:
        """Delete a saved context."""
        context_file = self.context_dir / f"{context_id}.json"

        if not context_file.exists():
            return {"status": "not_found", "context_id": context_id}

        context_file.unlink()
        return {"status": "deleted", "context_id": context_id}

    def get_latest_context(self) -> dict:
        """Get the most recently updated context."""
        contexts = self.list_contexts()
        if not contexts:
            return {"status": "empty", "message": "No saved contexts"}

        return self.load_context(contexts[0]["context_id"])


# --- User Profile for Cross-Project Memory ---


@dataclass
class UserProfile:
    """User preferences and coding style."""

    preferred_language: str = "python"
    coding_style: dict = field(default_factory=dict)
    architecture_preferences: dict = field(default_factory=dict)
    common_patterns: list[str] = field(default_factory=list)
    learned_fixes: list[dict] = field(default_factory=list)


class UserProfileManager:
    """
    Manages user profile for cross-project memory.

    Stores:
    - Coding style preferences
    - Architecture decisions
    - Learned patterns and fixes
    """

    def __init__(self):
        # Store in user's home directory for cross-project access
        self.profile_dir = Path.home() / ".boring_brain"
        self.profile_dir.mkdir(exist_ok=True)
        self.profile_file = self.profile_dir / "user_profile.json"

    def load_profile(self) -> UserProfile:
        """Load user profile from disk."""
        if not self.profile_file.exists():
            return UserProfile()

        try:
            data = json.loads(self.profile_file.read_text(encoding="utf-8"))
            return UserProfile(
                preferred_language=data.get("preferred_language", "python"),
                coding_style=data.get("coding_style", {}),
                architecture_preferences=data.get("architecture_preferences", {}),
                common_patterns=data.get("common_patterns", []),
                learned_fixes=data.get("learned_fixes", []),
            )
        except Exception:
            return UserProfile()

    def save_profile(self, profile: UserProfile) -> dict:
        """Save user profile to disk."""
        data = {
            "preferred_language": profile.preferred_language,
            "coding_style": profile.coding_style,
            "architecture_preferences": profile.architecture_preferences,
            "common_patterns": profile.common_patterns,
            "learned_fixes": profile.learned_fixes[-100:],  # Keep last 100 fixes
        }

        self.profile_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {"status": "saved", "file": str(self.profile_file)}

    def update_style(self, key: str, value: Any) -> dict:
        """Update a coding style preference."""
        profile = self.load_profile()
        profile.coding_style[key] = value
        return self.save_profile(profile)

    def add_learned_fix(self, error_pattern: str, fix_pattern: str, context: str = "") -> dict:
        """Record a learned fix pattern."""
        profile = self.load_profile()
        profile.learned_fixes.append(
            {
                "error": error_pattern,
                "fix": fix_pattern,
                "context": context,
                "learned_at": datetime.now().isoformat(),
            }
        )
        return self.save_profile(profile)

    def get_relevant_fixes(self, error_message: str, limit: int = 5) -> list[dict]:
        """Get fixes relevant to an error message."""
        profile = self.load_profile()
        relevant = []

        for fix in profile.learned_fixes:
            if fix["error"].lower() in error_message.lower():
                relevant.append(fix)

        return relevant[:limit]

    def set_architecture_preference(self, key: str, value: Any) -> dict:
        """Set an architecture preference."""
        profile = self.load_profile()
        profile.architecture_preferences[key] = value
        return self.save_profile(profile)


# --- Convenience functions for MCP tools ---


def save_context(context_id: str, summary: str, project_path: str = None) -> dict:
    """Save current context for later resumption."""
    from .config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = ContextSyncManager(path)
    return manager.save_context(context_id, summary)


def load_context(context_id: str, project_path: str = None) -> dict:
    """Load a saved context."""
    from .config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = ContextSyncManager(path)
    return manager.load_context(context_id)


def list_contexts(project_path: str = None) -> dict:
    """List all saved contexts."""
    from .config import settings

    path = Path(project_path) if project_path else settings.PROJECT_ROOT
    manager = ContextSyncManager(path)
    return {"contexts": manager.list_contexts()}


def get_user_profile() -> dict:
    """Get the user's cross-project profile."""
    manager = UserProfileManager()
    profile = manager.load_profile()
    return {
        "preferred_language": profile.preferred_language,
        "coding_style": profile.coding_style,
        "architecture_preferences": profile.architecture_preferences,
        "common_patterns": profile.common_patterns,
        "learned_fixes_count": len(profile.learned_fixes),
    }


def learn_fix(error_pattern: str, fix_pattern: str, context: str = "") -> dict:
    """Record a learned fix for future reference."""
    manager = UserProfileManager()
    return manager.add_learned_fix(error_pattern, fix_pattern, context)
