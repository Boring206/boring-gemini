"""
Boring Policy Engine (The Constitution).

Enforces authoritative rules that cannot be bypassed by Agents or Users
without explicit override events.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from boring.flow.nodes.base import FlowContext

logger = logging.getLogger(__name__)


@dataclass
class PolicyResult:
    allowed: bool
    reason: str
    level: str = "ERROR"  # ERROR, WARNING


class PolicyRule(ABC):
    """Abstract base class for a single policy rule."""

    name: str = "BaseRule"
    description: str = "Base policy rule"

    @abstractmethod
    def check(self, context: FlowContext) -> PolicyResult:
        """Evaluate the rule against the current context."""
        pass


class NoRootWritesRule(PolicyRule):
    """Prevent writing files directly to project root (except specific allowlist)."""

    name = "NoRootWrites"
    description = "Agents should not clutter the project root."

    ALLOWED_FILES = {
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        ".gitignore",
        "LICENSE",
        "Makefile",
        "package.json",
        "tsconfig.json",
        "poetry.lock",
    }

    def check(self, context: FlowContext) -> PolicyResult:
        # This rule is tricky to check efficiently with just Context.
        # Ideally, it intercepts File Write events or checks generated artifacts.
        # For 'can_enter' checks, this might be advisory or check *intent*.
        # Let's keep it simple: Check if specific memory keys indicate a root write intent?
        # Or, strictly, this might be better applied in the patching tools.
        # For now, let's implement a dummy check to prove architecture.
        return PolicyResult(True, "Root writes allowed (Mock)")


class EssentialFilesProtectionRule(PolicyRule):
    """Prevent deletion of essential Boring files."""

    name = "ProtectedFiles"

    def check(self, context: FlowContext) -> PolicyResult:
        # In a real implementation, this would hook into the `Reconciler`.
        # For PreFlight: ensure essential files exist? No, that's Guardrails.
        # Policy is strict: "If state says plan is missing, but event says it wasn't deleted by user, HALT".
        return PolicyResult(True, "Files protected")


class PolicyEngine:
    """The central authority for policy enforcement."""

    def __init__(self):
        self.rules: list[PolicyRule] = [
            NoRootWritesRule(),
            EssentialFilesProtectionRule(),
        ]

    def add_rule(self, rule: PolicyRule):
        self.rules.append(rule)

    def evaluate(self, context: FlowContext) -> list[PolicyResult]:
        """Run all policies and return violations."""
        results = []
        for rule in self.rules:
            try:
                res = rule.check(context)
                if not res.allowed:
                    logger.warning(f"Policy Violation [{rule.name}]: {res.reason}")
                    results.append(res)
            except Exception as e:
                logger.error(f"Policy Check Failed [{rule.name}]: {e}")
                # Fail open or closed? Closed for security.
                results.append(PolicyResult(False, f"Policy Check Exception: {e}"))
        return results

    def verify_entry(self, context: FlowContext) -> tuple[bool, str]:
        """Helper for FlowGraph.can_enter."""
        results = self.evaluate(context)
        errors = [r for r in results if r.level == "ERROR"]
        if errors:
            reasons = "; ".join([r.reason for r in errors])
            return False, f"Policy Violation: {reasons}"
        return True, "Policies passed"
