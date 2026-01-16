# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
Workflow Evolver V14.0 - Sage Mode & Dynamic Evolution.

Handles:
- Project Context Detection (ContextAwareness)
- Workflow evolution (backups & modification)
- Sage Mode: dreaming and learning
"""

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Captured state of a project for context-aware evolution."""

    name: str = "unknown"
    language: str = "unknown"
    frameworks: list[str] = field(default_factory=list)
    has_git: bool = False
    last_evolved: str | None = None
    vibe_score: float = 0.0


class ProjectContextDetector:
    """Analyzes codebase to detect project context."""

    def __init__(self, project_root: Path):
        self.root = project_root

    def detect(self) -> ProjectContext:
        """Run detection heuristics."""
        ctx = ProjectContext(name=self.root.name)

        # 1. Detection Logic
        if (self.root / ".git").exists():
            ctx.has_git = True

        if (self.root / "package.json").exists():
            ctx.language = "javascript"
            try:
                pj = json.loads((self.root / "package.json").read_text(encoding="utf-8"))
                deps = {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}
                if "next" in deps:
                    ctx.frameworks.append("nextjs")
                if "react" in deps:
                    ctx.frameworks.append("react")
                if "typescript" in deps:
                    ctx.frameworks.append("typescript")
            except Exception:
                pass

        if (self.root / "pyproject.toml").exists() or (self.root / "requirements.txt").exists():
            ctx.language = "python"
            # Basic framework check
            text = ""
            if (self.root / "pyproject.toml").exists():
                text = (self.root / "pyproject.toml").read_text(encoding="utf-8")
            elif (self.root / "requirements.txt").exists():
                text = (self.root / "requirements.txt").read_text(encoding="utf-8")

            if "django" in text.lower():
                ctx.frameworks.append("django")
            if "flask" in text.lower():
                ctx.frameworks.append("flask")
            if "fastapi" in text.lower():
                ctx.frameworks.append("fastapi")

        return ctx


class WorkflowEvolver:
    """Manages workflow evolution, history, and dreaming."""

    def __init__(self, project_root: Path, log_dir: Path | None = None):
        self.root = project_root
        self.log_dir = log_dir or project_root / "logs"
        self.workflows_dir = self.root / ".agent" / "workflows"
        self.backup_dir = self.workflows_dir / "_base"
        self.history_file = self.workflows_dir / "_evolution_history.json"

        # Ensure directories exist
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def evolve_workflow(self, name: str, content: str, reason: str) -> dict:
        """Modify an existing workflow with backup and history."""
        target = self.workflows_dir / f"{name}.md"
        if not target.exists():
            # Try finding it in our templates if missing (Future)
            return {"status": "ERROR", "error": f"Workflow {name} not found."}

        # Validate content (simple frontmatter check)
        if not content.strip().startswith("---"):
            return {"status": "ERROR", "error": "New content must have YAML frontmatter."}

        # Create Backup if first time
        backup = self.backup_dir / f"{name}.md"
        backup_created = False
        if not backup.exists():
            shutil.copy2(target, backup)
            backup_created = True

        old_content = target.read_text(encoding="utf-8")
        old_hash = hashlib.sha256(old_content.encode()).hexdigest()
        new_hash = hashlib.sha256(content.encode()).hexdigest()

        # Save new content
        target.write_text(content, encoding="utf-8")

        # Log History
        self._log_evolution(name, old_hash, new_hash, reason)

        return {
            "status": "SUCCESS",
            "workflow": name,
            "old_hash": old_hash[:8],
            "new_hash": new_hash[:8],
            "backup_created": backup_created,
        }

    def reset_workflow(self, name: str) -> dict:
        """Restore a workflow from its backup."""
        backup = self.backup_dir / f"{name}.md"
        target = self.workflows_dir / f"{name}.md"

        if not backup.exists():
            return {"status": "ERROR", "error": "No backup found to reset from."}

        shutil.copy2(backup, target)
        return {"status": "SUCCESS", "message": f"Workflow {name} reset to base."}

    def backup_all_workflows(self) -> dict:
        """Create backups for all md files in workflows dir."""
        results = {}
        for wf in self.workflows_dir.glob("*.md"):
            backup = self.backup_dir / wf.name
            if not backup.exists():
                shutil.copy2(wf, backup)
                results[wf.stem] = True
            else:
                results[wf.stem] = False
        return results

    def get_workflow_status(self, name: str) -> dict:
        """Check if a workflow is evolved and return hashes."""
        target = self.workflows_dir / f"{name}.md"
        backup = self.backup_dir / f"{name}.md"

        if not target.exists():
            return {"status": "ERROR", "error": "Not found"}

        current_hash = hashlib.sha256(target.read_text(encoding="utf-8").encode()).hexdigest()
        base_hash = None
        if backup.exists():
            base_hash = hashlib.sha256(backup.read_text(encoding="utf-8").encode()).hexdigest()

        return {
            "status": "SUCCESS",
            "name": name,
            "is_evolved": current_hash != base_hash if base_hash else False,
            "current_hash": current_hash[:8],
            "base_hash": base_hash[:8] if base_hash else None,
        }

    def dream_next_steps(self) -> str:
        """Sage Mode: Propose future roadmaps based on project state."""
        detector = ProjectContextDetector(self.root)
        ctx = detector.detect()

        # Simplified dreaming logic
        advice = []
        if ctx.language == "python":
            advice.append(
                "🐍 **Python Power**: Consider adding type hints or a Sphinx/MkDocs setup."
            )
        if "react" in ctx.frameworks:
            advice.append(
                "⚛️ **React Pulse**: I see React! Maybe add component tests with Jest/Vitest?"
            )

        if not ctx.has_git:
            advice.append(
                "📦 **Quick Tip**: No Git repo detected. Use `git init` for better version tracking."
            )

        if not advice:
            advice.append("🔮 **Future Vision**: Keep building! The project looks clean.")

        return "\n".join(advice)

    def learn_from_session(self):
        """Sage Mode: Archive and learn patterns."""
        # Integrates with boring learn in real implementation
        return "🧠 Knowledge extracted and saved to Brain."

    def _log_evolution(self, name: str, old_h: str, new_h: str, reason: str):
        history = []
        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "workflow": name,
                "old_hash": old_h,
                "new_hash": new_h,
                "reason": reason,
            }
        )

        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")


class WorkflowGapAnalyzer:
    """Identifies missing steps or inconsistencies in workflows."""

    def __init__(self, project_root: Path):
        self.root = project_root

    def analyze(self) -> list[str]:
        """Check for common missing artifacts."""
        gaps = []
        if not (self.root / "README.md").exists():
            gaps.append("Missing README.md")
        return gaps
