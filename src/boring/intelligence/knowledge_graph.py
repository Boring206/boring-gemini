"""
Project Knowledge Graph (Context Continuity)

Maintains a persistent graph of project knowledge:
- Tech Stack
- Key Dependencies
- Architectural Decisions
- Critical Paths

This file ensures the agent doesn't "forget" the project context between sessions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class KnowledgeGraph:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        from boring.paths import BoringPaths

        self.paths = BoringPaths(project_root)
        self.graph_file = self.paths.brain / "knowledge_graph.json"
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if self.graph_file.exists():
            try:
                return json.loads(self.graph_file.read_text(encoding="utf-8"))
            except Exception:
                return self._default_structure()
        return self._default_structure()

    def _default_structure(self) -> dict[str, Any]:
        return {
            "tech_stack": [],
            "dependencies": {},
            "architecture": {"patterns": [], "decisions": []},
            "last_updated": None,
            "last_accessed": None,  # For future pruning
        }

    def save(self):
        # Update timestamp only on modification
        self._data["last_updated"] = datetime.now().isoformat()
        self._write_disk()

    def _write_disk(self):
        self.paths.brain.mkdir(parents=True, exist_ok=True)
        self.graph_file.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def update_tech_stack(self, technologies: list[str]):
        """Update known technologies (e.g. ['React', 'FastAPI'])."""
        current = set(self._data["tech_stack"])
        current.update(technologies)
        self._data["tech_stack"] = list(current)
        self.save()

    def get_context_summary(self) -> str:
        """Generate a summary string for system prompt injection."""
        # Update access time for pruning logic
        self._data["last_accessed"] = datetime.now().isoformat()
        self._write_disk()

        if not self._data["tech_stack"]:
            return ""

        stack = ", ".join(self._data["tech_stack"])
        return f"Project Context: Tech Stack [{stack}]. Last updated: {self._data['last_updated']}"


def get_project_knowledge(root: Path) -> KnowledgeGraph:
    return KnowledgeGraph(root)
