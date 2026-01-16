"""
Role-Based Access Control (RBAC) Service.
Enforces permissions for MCP tools based on user roles.
"""

import fnmatch
import json
import os
from pathlib import Path
from typing import Optional

# Default Policy: Admin has full access. Viewer has read-only.
DEFAULT_POLICY = {
    "roles": {
        "admin": {"description": "Full access to all tools", "allow": ["*"], "deny": []},
        "developer": {
            "description": "Can code but restricted from dangerous system ops",
            "allow": ["*"],
            "deny": ["boring_system_*", "boring_security_bypass"],
        },
        "viewer": {
            "description": "Read-only access",
            "allow": [
                "read_*",
                "list_*",
                "search_*",
                "get_*",
                "view_*",
                "boring_help",
                "boring_status",
                "boring_dashboard",
                "boring_discover",
                "boring_inspect_tool",
            ],
            "deny": [],  # Implicit deny handles the rest
        },
    }
}


class RoleManager:
    _instance: Optional["RoleManager"] = None

    def __init__(self, policy_path: Path | None = None):
        if not policy_path:
            self.policy_path = Path.home() / ".boring" / "policy.json"
        else:
            self.policy_path = policy_path

        self.policy = DEFAULT_POLICY
        self._load_policy()

        # Determine current role from Env, defaulting to admin
        self.current_role = os.environ.get("BORING_USER_ROLE", "admin")

    @classmethod
    def get_instance(cls) -> "RoleManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_policy(self):
        """Load policy from file if exists."""
        if self.policy_path.exists():
            try:
                content = self.policy_path.read_text(encoding="utf-8")
                custom = json.loads(content)
                # Deep merge or replace? Replace for now
                self.policy = custom
            except Exception:
                pass  # Fallback to default

    def check_access(self, tool_name: str) -> bool:
        """
        Check if current role can access the tool.
        Returns True if allowed.
        """
        role_def = self.policy.get("roles", {}).get(self.current_role)
        if not role_def:
            # Unknown role -> Deny by default? Or fallback to viewer?
            # Safe default: Deny
            return False

        # Check Deny first
        for pattern in role_def.get("deny", []):
            if fnmatch.fnmatch(tool_name.lower(), pattern.lower()):
                return False

        # Check Allow
        for pattern in role_def.get("allow", []):
            if fnmatch.fnmatch(tool_name.lower(), pattern.lower()):
                return True

        # Default deny if not explicitly allowed
        return False
