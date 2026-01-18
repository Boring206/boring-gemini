"""
Constraint Store (Project Rules Memory)

Manages dynamic user constraints and project rules.
Ensures the agent remembers "Don't use any" or "Always use strict typing"
even after long conversations.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Constraint:
    id: str
    rule: str
    source: str
    created_at: float
    active: bool = True


class ConstraintStore:
    def __init__(self, project_root: Path):
        from boring.paths import BoringPaths

        self.paths = BoringPaths(project_root)
        self.store_file = self.paths.brain / "constraints.json"
        self._data: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if self.store_file.exists():
            try:
                return json.loads(self.store_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self):
        self.paths.brain.mkdir(parents=True, exist_ok=True)
        self.store_file.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add_constraint(self, rule: str, source: str = "user") -> Constraint:
        c = Constraint(
            id=str(uuid.uuid4())[:8], rule=rule, source=source, created_at=time.time(), active=True
        )
        self._data.append(asdict(c))
        self._save()
        return c

    def remove_constraint(self, constraint_id: str) -> bool:
        for c in self._data:
            if c["id"] == constraint_id:
                c["active"] = False
                self._save()
                return True
        return False

    def get_active_constraints(self) -> list[str]:
        return [c["rule"] for c in self._data if c.get("active", True)]

    def get_context_block(self) -> str:
        rules = self.get_active_constraints()
        if not rules:
            return ""

        lines = ["# PROJECT CONSTRAINTS"]
        for i, rule in enumerate(rules, 1):
            lines.append(f"{i}. {rule}")
        return "\n".join(lines)


def get_constraint_store(root: Path) -> ConstraintStore:
    return ConstraintStore(root)
