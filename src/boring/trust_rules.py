"""
Trust Rules for Shadow Mode

Allows users to define rules that auto-approve specific operations,
reducing approval prompts for trusted tools and patterns.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from boring.paths import get_boring_path

logger = logging.getLogger(__name__)


@dataclass
class TrustRule:
    """A rule that auto-approves matching operations."""

    tool_name: str  # e.g., "boring_commit", "*" for all
    auto_approve: bool = True
    path_pattern: Optional[str] = None  # e.g., "src/*" - if set, only matches these paths
    max_severity: str = "high"  # auto-approve up to this severity: low, medium, high
    description: str = ""

    def matches(self, op_name: str, args: dict[str, Any]) -> bool:
        """Check if this rule matches an operation."""
        # Match tool name
        if self.tool_name != "*" and self.tool_name != op_name:
            return False

        # Match path pattern if specified
        if self.path_pattern:
            file_path = args.get("file_path", "") or args.get("path", "") or ""
            if not self._match_pattern(file_path, self.path_pattern):
                return False

        return True

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Simple glob-like pattern matching."""
        import fnmatch

        return fnmatch.fnmatch(path, pattern)

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "auto_approve": self.auto_approve,
            "path_pattern": self.path_pattern,
            "max_severity": self.max_severity,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrustRule":
        return cls(
            tool_name=data.get("tool_name", "*"),
            auto_approve=data.get("auto_approve", True),
            path_pattern=data.get("path_pattern"),
            max_severity=data.get("max_severity", "high"),
            description=data.get("description", ""),
        )


class TrustRuleManager:
    """Manages trust rules for Shadow Mode."""

    SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.brain_dir = get_boring_path(self.project_root, "brain")
        self.rules_file = self.brain_dir / "trust_rules.json"
        self.rules: list[TrustRule] = []

        # Ensure directory exists
        self.brain_dir.mkdir(parents=True, exist_ok=True)

        # Load existing rules
        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from disk."""
        if not self.rules_file.exists():
            return

        try:
            data = json.loads(self.rules_file.read_text(encoding="utf-8"))
            self.rules = [TrustRule.from_dict(r) for r in data.get("rules", [])]
            logger.info(f"Loaded {len(self.rules)} trust rules")
        except Exception as e:
            logger.warning(f"Failed to load trust rules: {e}")

    def _save_rules(self) -> None:
        """Save rules to disk."""
        try:
            data = {"rules": [r.to_dict() for r in self.rules]}
            self.rules_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save trust rules: {e}")

    def add_rule(
        self,
        tool_name: str,
        auto_approve: bool = True,
        path_pattern: Optional[str] = None,
        max_severity: str = "high",
        description: str = "",
    ) -> TrustRule:
        """Add a new trust rule."""
        rule = TrustRule(
            tool_name=tool_name,
            auto_approve=auto_approve,
            path_pattern=path_pattern,
            max_severity=max_severity,
            description=description,
        )

        # Remove existing rule for same tool+pattern combo
        self.rules = [
            r
            for r in self.rules
            if not (r.tool_name == tool_name and r.path_pattern == path_pattern)
        ]

        self.rules.append(rule)
        self._save_rules()

        logger.info(f"Added trust rule: {tool_name} (auto_approve={auto_approve})")
        return rule

    def remove_rule(self, tool_name: str, path_pattern: Optional[str] = None) -> bool:
        """Remove a trust rule."""
        original_count = len(self.rules)
        self.rules = [
            r
            for r in self.rules
            if not (r.tool_name == tool_name and r.path_pattern == path_pattern)
        ]

        if len(self.rules) < original_count:
            self._save_rules()
            return True
        return False

    def check_trust(
        self, op_name: str, args: dict[str, Any], severity: str = "medium"
    ) -> Optional[TrustRule]:
        """
        Check if an operation is trusted (should be auto-approved).

        Args:
            op_name: Operation/tool name
            args: Operation arguments
            severity: Current operation severity

        Returns:
            Matching TrustRule if trusted, None otherwise
        """
        severity_level = self.SEVERITY_ORDER.get(severity.lower(), 2)

        for rule in self.rules:
            if not rule.auto_approve:
                continue

            if not rule.matches(op_name, args):
                continue

            # Check if severity is within rule's threshold
            max_level = self.SEVERITY_ORDER.get(rule.max_severity.lower(), 3)
            if severity_level <= max_level:
                logger.debug(
                    f"Operation {op_name} auto-approved by trust rule: {rule.description or rule.tool_name}"
                )
                return rule

        return None

    def list_rules(self) -> list[dict]:
        """List all rules as dictionaries."""
        return [r.to_dict() for r in self.rules]

    def clear_rules(self) -> int:
        """Clear all rules. Returns count removed."""
        count = len(self.rules)
        self.rules = []
        self._save_rules()
        return count


# Singleton instance (per project)
_managers: dict[str, TrustRuleManager] = {}


def get_trust_manager(project_root: Path) -> TrustRuleManager:
    """Get or create TrustRuleManager for project."""
    key = str(project_root.resolve())
    if key not in _managers:
        _managers[key] = TrustRuleManager(project_root)
    return _managers[key]
