try:
    import tomllib as toml
except ImportError:
    try:
        import tomli as toml
    except ImportError:
        try:
            import toml
        except ImportError:
            toml = None
from pathlib import Path


class PolicyEngine:
    """
    Governance Policy Engine (Phase VII).
    Enforces 'Policy-as-Code' for tool execution.
    """

    def __init__(self, project_root: Path):
        self.policy_path = project_root / ".boring" / "policy.toml"
        self.config = self._load_default_policy()
        if self.policy_path.exists():
            try:
                user_policy = toml.loads(self.policy_path.read_text(encoding="utf-8"))
                self.config.update(user_policy)
            except Exception:
                pass  # Fallback to safe defaults

    def _load_default_policy(self):
        return {
            "governance": {
                "allow_dangerous_tools": True,
                "require_manual_approval": [],
                "restricted_paths": [".git", ".boring", "secrets"],
            }
        }

    def check_tool_permission(self, tool_name: str) -> bool:
        """Determines if a tool is allowed under current policy."""
        # Hardcoded critical safety
        if tool_name == "run_command" and not self.config["governance"].get(
            "allow_dangerous_tools", True
        ):
            return False

        restricted = self.config["governance"].get("restricted_tools", [])
        if tool_name in restricted:
            return False

        return True

    def validate_path(self, path: str) -> bool:
        """Blocks AI from touching sensitive system paths."""
        restricted = self.config["governance"].get("restricted_paths", [])
        for r in restricted:
            if r in path:
                return False
        return True

    def get_approval_requirement(self, tool_name: str) -> bool:
        """Checks if a tool requires explicit human confirmation."""
        requires = self.config["governance"].get("require_manual_approval", [])
        return tool_name in requires
