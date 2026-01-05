"""
Workflow Evolver Module for Boring V5.0

Enables dynamic evolution of SpecKit workflows based on project analysis.
AI can modify workflow content to adapt to specific project needs.

Key Features:
- Backup original workflows to _base/ directory
- Track all modifications in _evolution_log.json
- Rollback to base template when needed
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logger import log_status


@dataclass
class WorkflowEvolution:
    """Record of a workflow evolution."""

    workflow_name: str
    original_hash: str
    new_hash: str
    reason: str
    timestamp: str
    changes_summary: str


class WorkflowEvolver:
    """
    Enables AI to dynamically modify SpecKit workflows.

    Usage:
        evolver = WorkflowEvolver(project_root)

        # Evolve a workflow
        result = evolver.evolve_workflow(
            "speckit-plan",
            new_content="...",
            reason="Adapting for TypeScript project"
        )

        # Rollback to base
        evolver.reset_workflow("speckit-plan")
    """

    EVOLVABLE_WORKFLOWS = [
        "speckit-plan",
        "speckit-tasks",
        "speckit-constitution",
        "speckit-clarify",
        "speckit-analyze",
        "speckit-checklist",
    ]

    def __init__(self, project_root: Path, log_dir: Optional[Path] = None):
        self.project_root = Path(project_root)
        self.workflows_dir = self.project_root / ".agent" / "workflows"
        self.base_dir = self.workflows_dir / "_base"
        self.brain_dir = self.project_root / ".boring_brain"
        self.log_dir = log_dir or self.project_root / "logs"
        self.evolution_log_path = self.workflows_dir / "_evolution_log.json"

        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_brain_structure()

    def _ensure_brain_structure(self):
        """Ensure .boring_brain directory structure exists."""
        subdirs = ["workflow_adaptations", "learned_patterns", "rubrics"]
        for subdir in subdirs:
            (self.brain_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _load_evolution_log(self) -> list[dict]:
        """Load evolution history from JSON."""
        if self.evolution_log_path.exists():
            try:
                return json.loads(self.evolution_log_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return []
        return []

    def _save_evolution_log(self, log: list[dict]):
        """Save evolution history to JSON."""
        self.evolution_log_path.write_text(
            json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def ensure_base_backup(self, workflow_name: str) -> bool:
        """
        Ensure base template exists for rollback.
        Creates backup if not exists.

        Returns:
            True if base exists or was created successfully
        """
        if workflow_name not in self.EVOLVABLE_WORKFLOWS:
            return False

        workflow_path = self.workflows_dir / f"{workflow_name}.md"
        base_path = self.base_dir / f"{workflow_name}.base.md"

        if not workflow_path.exists():
            log_status(self.log_dir, "WARN", f"Workflow not found: {workflow_name}")
            return False

        # Only create backup if not exists (preserve original)
        if not base_path.exists():
            content = workflow_path.read_text(encoding="utf-8")
            base_path.write_text(content, encoding="utf-8")
            log_status(self.log_dir, "INFO", f"Created base backup: {base_path.name}")

        return True

    def backup_all_workflows(self) -> dict[str, bool]:
        """Backup all evolvable workflows to _base directory."""
        results = {}
        for workflow in self.EVOLVABLE_WORKFLOWS:
            results[workflow] = self.ensure_base_backup(workflow)
        return results

    def evolve_workflow(self, workflow_name: str, new_content: str, reason: str) -> dict[str, Any]:
        """
        Evolve a workflow with new content.

        Args:
            workflow_name: Name of workflow (without .md extension)
            new_content: Complete new workflow content
            reason: Why this evolution is needed

        Returns:
            Result dict with status, old_hash, new_hash
        """
        if workflow_name not in self.EVOLVABLE_WORKFLOWS:
            return {
                "status": "ERROR",
                "error": f"Workflow '{workflow_name}' is not evolvable. Valid: {self.EVOLVABLE_WORKFLOWS}",
            }

        workflow_path = self.workflows_dir / f"{workflow_name}.md"

        if not workflow_path.exists():
            return {"status": "ERROR", "error": f"Workflow not found: {workflow_path}"}

        # Ensure base backup exists
        self.ensure_base_backup(workflow_name)

        # Read current content
        current_content = workflow_path.read_text(encoding="utf-8")
        current_hash = self._compute_hash(current_content)
        new_hash = self._compute_hash(new_content)

        if current_hash == new_hash:
            return {"status": "NO_CHANGE", "message": "Content unchanged, no evolution needed"}

        # Write new content
        workflow_path.write_text(new_content, encoding="utf-8")

        # Record evolution
        evolution = WorkflowEvolution(
            workflow_name=workflow_name,
            original_hash=current_hash,
            new_hash=new_hash,
            reason=reason,
            timestamp=datetime.now().isoformat(),
            changes_summary=f"Evolved {workflow_name}: {reason[:100]}",
        )

        log = self._load_evolution_log()
        log.append(asdict(evolution))
        self._save_evolution_log(log)

        log_status(
            self.log_dir,
            "INFO",
            f"Evolved workflow: {workflow_name} ({current_hash} -> {new_hash})",
        )

        return {
            "status": "SUCCESS",
            "workflow": workflow_name,
            "old_hash": current_hash,
            "new_hash": new_hash,
            "reason": reason,
        }

    def reset_workflow(self, workflow_name: str) -> dict[str, Any]:
        """
        Reset workflow to base template.

        Args:
            workflow_name: Name of workflow to reset

        Returns:
            Result dict with status
        """
        if workflow_name not in self.EVOLVABLE_WORKFLOWS:
            return {"status": "ERROR", "error": f"Workflow '{workflow_name}' is not evolvable"}

        workflow_path = self.workflows_dir / f"{workflow_name}.md"
        base_path = self.base_dir / f"{workflow_name}.base.md"

        if not base_path.exists():
            return {"status": "ERROR", "error": f"Base template not found: {base_path}"}

        # Restore from base
        base_content = base_path.read_text(encoding="utf-8")
        workflow_path.write_text(base_content, encoding="utf-8")

        # Record the reset
        log = self._load_evolution_log()
        log.append(
            {
                "workflow_name": workflow_name,
                "action": "RESET",
                "timestamp": datetime.now().isoformat(),
                "reason": "Reset to base template",
            }
        )
        self._save_evolution_log(log)

        log_status(self.log_dir, "INFO", f"Reset workflow to base: {workflow_name}")

        return {"status": "SUCCESS", "workflow": workflow_name, "message": "Reset to base template"}

    def get_workflow_status(self, workflow_name: str) -> dict[str, Any]:
        """Get current status of a workflow."""
        workflow_path = self.workflows_dir / f"{workflow_name}.md"
        base_path = self.base_dir / f"{workflow_name}.base.md"

        if not workflow_path.exists():
            return {"status": "NOT_FOUND"}

        current_content = workflow_path.read_text(encoding="utf-8")
        current_hash = self._compute_hash(current_content)

        result = {
            "workflow": workflow_name,
            "current_hash": current_hash,
            "has_base": base_path.exists(),
            "is_evolvable": workflow_name in self.EVOLVABLE_WORKFLOWS,
        }

        # Check if evolved from base
        if base_path.exists():
            base_content = base_path.read_text(encoding="utf-8")
            base_hash = self._compute_hash(base_content)
            result["base_hash"] = base_hash
            result["is_evolved"] = current_hash != base_hash

        return result

    def get_evolution_history(self, workflow_name: Optional[str] = None) -> list[dict]:
        """Get evolution history, optionally filtered by workflow."""
        log = self._load_evolution_log()

        if workflow_name:
            return [e for e in log if e.get("workflow_name") == workflow_name]

        return log


def create_workflow_evolver(project_root: Path, log_dir: Optional[Path] = None) -> WorkflowEvolver:
    """Factory function to create WorkflowEvolver instance."""
    return WorkflowEvolver(project_root, log_dir)
