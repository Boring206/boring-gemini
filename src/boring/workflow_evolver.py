"""
Workflow Evolver Module for Boring V10.18

Enables dynamic evolution of SpecKit workflows based on project analysis.
AI can modify workflow content to adapt to specific project needs.

Key Features:
- Backup original workflows to _base/ directory
- Track all modifications in _evolution_log.json
- Rollback to base template when needed
- [V10.18+] Automatic project context detection
- [V10.18+] Gap analysis for workflow completeness
- [V10.18+] Intelligent workflow suggestion generation
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logger import log_status

# =============================================================================
# Project Context Detection
# =============================================================================


@dataclass
class ProjectContext:
    """Detected project context and metadata files."""

    project_type: str  # python, node, go, rust, docker, mcp, etc.
    detected_files: list[str] = field(default_factory=list)
    version_files: list[str] = field(default_factory=list)
    doc_languages: list[str] = field(default_factory=list)  # en, zh, ja, ko, es, fr, de, etc.
    is_multilingual: bool = False  # True if more than 1 language detected
    suggested_checks: list[str] = field(default_factory=list)


class ProjectContextDetector:
    """
    Automatically detects project type and required sync files.

    Usage:
        detector = ProjectContextDetector(project_root)
        context = detector.analyze()
        print(context.project_type)  # 'mcp_server'
        print(context.version_files)  # ['pyproject.toml', 'smithery.yaml']
    """

    # File patterns that indicate project type
    PROJECT_INDICATORS = {
        "python": ["pyproject.toml", "setup.py", "requirements.txt"],
        "node": ["package.json", "package-lock.json", "yarn.lock"],
        "go": ["go.mod", "go.sum"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "mcp_server": ["smithery.yaml", "gemini-extension.json"],
    }

    # Files that contain version info and need syncing
    VERSION_FILES = {
        "pyproject.toml": r'version\s*=\s*["\']([^"\']+)["\']',
        "package.json": r'"version"\s*:\s*"([^"]+)"',
        "Cargo.toml": r'version\s*=\s*"([^"]+)"',
        "smithery.yaml": r'version:\s*["\']?([^"\'"\n]+)',
        "gemini-extension.json": r'"version"\s*:\s*"([^"]+)"',
        "__init__.py": r'__version__\s*=\s*["\']([^"\']+)["\']',
    }

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def analyze(self) -> ProjectContext:
        """Analyze project and return detected context."""
        detected_files = []
        version_files = []
        project_types = set()

        # Scan for indicator files
        for ptype, indicators in self.PROJECT_INDICATORS.items():
            for indicator in indicators:
                if (self.project_root / indicator).exists():
                    detected_files.append(indicator)
                    project_types.add(ptype)

        # Scan for version files
        for vfile, _pattern in self.VERSION_FILES.items():
            # Check root and src/*/
            paths_to_check = [
                self.project_root / vfile,
                *list(self.project_root.glob(f"src/*/{vfile}")),
            ]
            for path in paths_to_check:
                if path.exists():
                    version_files.append(str(path.relative_to(self.project_root)))

        # Detect multilingual docs
        doc_languages = self._detect_doc_languages()
        is_multilingual = len(doc_languages) > 1

        # Determine primary project type
        primary_type = self._determine_primary_type(project_types)

        # Generate suggested checks
        suggested = self._generate_suggested_checks(primary_type, version_files, is_multilingual)

        return ProjectContext(
            project_type=primary_type,
            detected_files=detected_files,
            version_files=version_files,
            doc_languages=doc_languages,
            is_multilingual=is_multilingual,
            suggested_checks=suggested,
        )

    # Supported language suffixes (ISO 639-1 codes)
    LANGUAGE_SUFFIXES = {
        "_zh": "zh",  # Chinese
        "_ja": "ja",  # Japanese
        "_ko": "ko",  # Korean
        "_es": "es",  # Spanish
        "_fr": "fr",  # French
        "_de": "de",  # German
        "_pt": "pt",  # Portuguese
        "_ru": "ru",  # Russian
        "_ar": "ar",  # Arabic
        "_it": "it",  # Italian
        "_nl": "nl",  # Dutch
        "_vi": "vi",  # Vietnamese
        "_th": "th",  # Thai
    }

    def _detect_doc_languages(self) -> list[str]:
        """Detect documentation languages from file suffixes."""
        languages = set()
        docs_dir = self.project_root / "docs"

        if docs_dir.exists():
            for md_file in docs_dir.rglob("*.md"):
                name = md_file.stem
                detected = False
                for suffix, lang_code in self.LANGUAGE_SUFFIXES.items():
                    if name.endswith(suffix):
                        languages.add(lang_code)
                        detected = True
                        break
                if not detected:
                    languages.add("en")  # Default to English

        return sorted(languages)

    def _determine_primary_type(self, types: set[str]) -> str:
        """Determine primary project type from detected types."""
        # Priority order
        priority = ["mcp_server", "docker", "rust", "go", "node", "python"]
        for ptype in priority:
            if ptype in types:
                return ptype
        return "unknown"

    def _generate_suggested_checks(
        self, project_type: str, version_files: list[str], is_multilingual: bool
    ) -> list[str]:
        """Generate suggested workflow checks based on context."""
        checks = []

        # Version sync checks
        if len(version_files) > 1:
            checks.append(f"Sync version across: {', '.join(version_files)}")

        # Project-type specific checks
        type_checks = {
            "python": ["Run pytest", "Check ruff lint"],
            "node": ["Run npm test", "Check eslint"],
            "mcp_server": ["Validate smithery.yaml", "Test MCP startup"],
            "docker": ["Build Docker image", "Run container tests"],
        }
        checks.extend(type_checks.get(project_type, []))

        # Multilingual checks
        if is_multilingual:
            checks.append("Verify multilingual doc parity across all language versions")

        return checks


# =============================================================================
# Gap Analysis
# =============================================================================


@dataclass
class WorkflowGap:
    """A detected gap in workflow coverage."""

    gap_type: str  # 'missing_file', 'missing_check', 'outdated'
    description: str
    suggested_fix: str
    severity: str  # 'low', 'medium', 'high'


class WorkflowGapAnalyzer:
    """
    Analyzes workflow content against project context to find gaps.

    Usage:
        analyzer = WorkflowGapAnalyzer(project_root)
        gaps = analyzer.analyze_release_workflow(workflow_content)
        for gap in gaps:
            print(f"[{gap.severity}] {gap.description}")
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.detector = ProjectContextDetector(project_root)
        self._context: Optional[ProjectContext] = None

    @property
    def context(self) -> ProjectContext:
        if self._context is None:
            self._context = self.detector.analyze()
        return self._context

    def analyze_release_workflow(self, workflow_content: str) -> list[WorkflowGap]:
        """Analyze release workflow and return gaps."""
        gaps = []
        content_lower = workflow_content.lower()

        # Check version file coverage
        for vfile in self.context.version_files:
            if vfile.lower() not in content_lower:
                gaps.append(
                    WorkflowGap(
                        gap_type="missing_file",
                        description=f"Version file '{vfile}' not mentioned in workflow",
                        suggested_fix=f"- [ ] Sync version in `{vfile}`",
                        severity="high"
                        if "pyproject" in vfile or "package.json" in vfile
                        else "medium",
                    )
                )

        # Check multilingual doc parity
        if self.context.is_multilingual:
            bilingual_keywords = ["bilingual", "雙語", "parity", "translation", "_zh"]
            if not any(kw in content_lower for kw in bilingual_keywords):
                gaps.append(
                    WorkflowGap(
                        gap_type="missing_check",
                        description="Bilingual documentation parity check missing",
                        suggested_fix="- [ ] Verify bilingual doc parity (`docs/*.md` ↔ `*_zh.md`)",
                        severity="medium",
                    )
                )

        # Check project-type specific
        if self.context.project_type == "mcp_server":
            if "smithery" not in content_lower:
                gaps.append(
                    WorkflowGap(
                        gap_type="missing_file",
                        description="MCP server project but smithery.yaml not in workflow",
                        suggested_fix="- [ ] Update `smithery.yaml` metadata",
                        severity="high",
                    )
                )

        return gaps

    def generate_enhanced_workflow(self, original_content: str) -> str:
        """Generate enhanced workflow content with gap fixes."""
        gaps = self.analyze_release_workflow(original_content)

        if not gaps:
            return original_content

        # Find insertion point (before last checkbox or at end)
        lines = original_content.split("\n")
        insert_idx = len(lines)

        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith("- ["):
                insert_idx = i + 1
                break

        # Generate new lines
        new_lines = ["\n## Auto-Detected Checks (WorkflowEvolver)"]
        for gap in gaps:
            new_lines.append(gap.suggested_fix)

        # Insert
        lines = lines[:insert_idx] + new_lines + lines[insert_idx:]
        return "\n".join(lines)


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
        "release-prep",
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

    # =========================================================================
    # V10.18+ Autonomous Evolution Methods
    # =========================================================================

    def analyze_project(self) -> dict[str, Any]:
        """
        Analyze project context and return detected information.

        Returns:
            Dict with project_type, version_files, doc_languages, suggested_checks
        """
        detector = ProjectContextDetector(self.project_root)
        context = detector.analyze()
        return {
            "project_type": context.project_type,
            "detected_files": context.detected_files,
            "version_files": context.version_files,
            "doc_languages": context.doc_languages,
            "is_multilingual": context.is_multilingual,
            "suggested_checks": context.suggested_checks,
        }

    def analyze_gaps(self, workflow_name: str = "release-prep") -> list[dict]:
        """
        Analyze gaps in a workflow against project context.

        Args:
            workflow_name: Name of workflow to analyze

        Returns:
            List of gaps with type, description, suggested_fix, severity
        """
        workflow_path = self.workflows_dir / f"{workflow_name}.md"
        if not workflow_path.exists():
            return [{"error": f"Workflow not found: {workflow_name}"}]

        content = workflow_path.read_text(encoding="utf-8")
        analyzer = WorkflowGapAnalyzer(self.project_root)
        gaps = analyzer.analyze_release_workflow(content)

        return [
            {
                "gap_type": g.gap_type,
                "description": g.description,
                "suggested_fix": g.suggested_fix,
                "severity": g.severity,
            }
            for g in gaps
        ]

    def auto_evolve(self, workflow_name: str = "release-prep") -> dict[str, Any]:
        """
        Automatically evolve a workflow based on project context analysis.

        This is the main entry point for autonomous workflow optimization.
        It detects project context, analyzes gaps, and applies fixes.

        Args:
            workflow_name: Name of workflow to evolve (default: release-prep)

        Returns:
            Result dict with status, gaps_found, gaps_fixed, new_content preview

        Usage:
            evolver = WorkflowEvolver(project_root)
            result = evolver.auto_evolve("release-prep")
            if result["status"] == "EVOLVED":
                print(f"Fixed {result['gaps_fixed']} gaps")
        """
        if workflow_name not in self.EVOLVABLE_WORKFLOWS:
            return {
                "status": "ERROR",
                "error": f"Workflow '{workflow_name}' is not evolvable",
            }

        workflow_path = self.workflows_dir / f"{workflow_name}.md"
        if not workflow_path.exists():
            return {
                "status": "ERROR",
                "error": f"Workflow not found: {workflow_path}",
            }

        # Analyze project and gaps
        analyzer = WorkflowGapAnalyzer(self.project_root)
        original_content = workflow_path.read_text(encoding="utf-8")
        gaps = analyzer.analyze_release_workflow(original_content)

        if not gaps:
            return {
                "status": "NO_GAPS",
                "message": "Workflow is already complete for this project",
                "project_type": analyzer.context.project_type,
            }

        # Generate enhanced content
        enhanced_content = analyzer.generate_enhanced_workflow(original_content)

        # Apply evolution
        result = self.evolve_workflow(
            workflow_name,
            enhanced_content,
            reason=f"Auto-evolved: fixed {len(gaps)} gaps ({', '.join(g.gap_type for g in gaps)})",
        )

        if result["status"] == "SUCCESS":
            return {
                "status": "EVOLVED",
                "gaps_found": len(gaps),
                "gaps_fixed": len(gaps),
                "gaps_details": [
                    {"type": g.gap_type, "desc": g.description, "severity": g.severity}
                    for g in gaps
                ],
                "project_type": analyzer.context.project_type,
                "old_hash": result.get("old_hash"),
                "new_hash": result.get("new_hash"),
            }

        return result


def create_workflow_evolver(project_root: Path, log_dir: Optional[Path] = None) -> WorkflowEvolver:
    """Factory function to create WorkflowEvolver instance."""
    return WorkflowEvolver(project_root, log_dir)
