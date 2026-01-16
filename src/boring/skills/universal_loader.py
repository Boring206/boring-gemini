# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # Handle gracefully if not installed

logger = logging.getLogger(__name__)

# Standard skill directories across platforms
SKILL_DIRECTORIES = [
    ".boring/skills",  # Boring Hub (Master)
    ".antigravity/skills",  # Antigravity (Native)
    ".gemini/skills",  # Gemini CLI
    ".claude/skills",  # Claude Code
    ".codex/skills",  # OpenAI Codex CLI
]


@dataclass
class UniversalSkill:
    """Represents a standardized skill across any platform."""

    name: str
    description: str
    content: str  # The markdown instruction body
    path: Path
    platform: str  # "boring", "antigravity", "gemini", "claude"
    metadata: dict[str, Any]  # Extra YAML fields (model, allowed-tools, etc.)

    # Standard Directory Structure Support (OpenAI / SkillsMP)
    scripts_dir: Path | None = None
    references_dir: Path | None = None
    assets_dir: Path | None = None
    examples_dir: Path | None = None
    resources_dir: Path | None = None

    @property
    def activation_prompt(self) -> str:
        """Generating the system prompt payload."""
        payload = [f'<skill_activation name="{self.name}">']
        payload.append(self.content)

        # Append info about available resources
        if self.scripts_dir and self.scripts_dir.exists():
            scripts = [f.name for f in self.scripts_dir.glob("*") if f.is_file()]
            if scripts:
                payload.append(
                    f"\nAvailable Scripts ({self.scripts_dir.name}): {', '.join(scripts)}"
                )

        if self.references_dir and self.references_dir.exists():
            refs = [f.name for f in self.references_dir.glob("*") if f.is_file()]
            if refs:
                payload.append(f"\nReferences ({self.references_dir.name}): {', '.join(refs)}")

        if self.examples_dir and self.examples_dir.exists():
            exs = [f.name for f in self.examples_dir.glob("*") if f.is_file()]
            if exs:
                payload.append(f"\nExamples ({self.examples_dir.name}): {', '.join(exs)}")

        payload.append("</skill_activation>")
        payload.append("</skill_activation>")
        return "\n".join(payload)

    def execute_script(
        self, script_name: str, args: list[str] | None = None, timeout: int = 30
    ) -> dict[str, Any]:
        """
        Execute a script from this skill in a secure sandbox.

        Args:
            script_name: Name of the script in scripts_dir
            args: Command line arguments
            timeout: Execution timeout in seconds

        Returns:
            Dict containing return_code, stdout, stderr, or error message
        """
        if not self.scripts_dir:
            return {"status": "ERROR", "error": "No scripts directory defined for this skill"}

        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            return {"status": "ERROR", "error": f"Script {script_name} not found"}

        try:
            from ..security.sandbox import SandboxExecutor

            executor = SandboxExecutor(timeout_seconds=timeout)

            # Identify dependencies (copy whole scripts dir + resources/assets)
            dependencies = []

            # Add sibling scripts if any
            for f in self.scripts_dir.glob("*"):
                if f != script_path:
                    dependencies.append(f)

            # Add resources if available
            if self.resources_dir and self.resources_dir.exists():
                dependencies.append(self.resources_dir)

            result = executor.run_script(script_path, args=args, dependencies=dependencies)

            return {
                "status": "SUCCESS" if result.returncode == 0 else "FAILED",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except ImportError:
            return {"status": "ERROR", "error": "SandboxExecutor not available"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}


class UniversalSkillLoader:
    """
    Loads skills from multiple standard directories (Universal Compatibility).
    Supports: Boring, Antigravity, Gemini CLI, Claude Code formats.
    """

    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        # Ensure yaml is available
        if yaml is None:
            logger.warning("PyYAML not installed. Skill frontmatter parsing may fail.")

    def discover_all(self) -> list[UniversalSkill]:
        """Scan all known skill directories and return unique skills."""
        found_skills: dict[str, UniversalSkill] = {}

        # Scan in order of priority (Master overrides others)
        for rel_dir in SKILL_DIRECTORIES:
            platform_name = rel_dir.split("/")[0].replace(".", "")
            full_path = self.project_root / rel_dir

            if not full_path.exists():
                continue

            for item in full_path.iterdir():
                skill = self._load_skill_from_path(item, platform_name)
                if skill:
                    # If duplicate name, keeping the first one encountered (Priority order)
                    if skill.name not in found_skills:
                        found_skills[skill.name] = skill

        return list(found_skills.values())

    def match(self, request: str, threshold: float = 0.0) -> UniversalSkill | None:
        """
        Simple semantic matching based on description keywords.
        In a full implementation, this uses vector search.
        Current: Keyword overlap.
        """
        skills = self.discover_all()
        request_lower = request.lower()

        best_skill = None
        best_score = 0

        for skill in skills:
            score = 0
            # Name match (High weight)
            if skill.name in request_lower:
                score += 5

            # Description keywords
            desc_words = set(skill.description.lower().split())
            req_words = set(request_lower.split())
            intersection = desc_words.intersection(req_words)
            score += len(intersection)

            if score > best_score and score > threshold:
                best_score = score
                best_skill = skill

        return best_skill

    def load_by_name(self, name: str) -> UniversalSkill | None:
        """Directly load a skill by name."""
        skills = self.discover_all()
        for skill in skills:
            if skill.name == name:
                return skill
        return None

    def _load_skill_from_path(self, path: Path, platform: str) -> UniversalSkill | None:
        """Parse a skill file or directory."""
        target_file = None
        scripts_dir = None
        references_dir = None
        assets_dir = None
        examples_dir = None
        resources_dir = None

        # Case 1: Directory with SKILL.md (Standard Structure)
        if path.is_dir():
            skill_md = path / "SKILL.md"
            if skill_md.exists():
                target_file = skill_md
                # Check for standard subdirectories
                if (path / "scripts").exists():
                    scripts_dir = path / "scripts"
                if (path / "references").exists():
                    references_dir = path / "references"
                if (path / "assets").exists():
                    assets_dir = path / "assets"
                if (path / "examples").exists():  # New standard
                    examples_dir = path / "examples"
                if (path / "resources").exists():  # New standard
                    resources_dir = path / "resources"

        # Case 2: Single .md file
        elif path.suffix.lower() == ".md":
            target_file = path

        if not target_file:
            return None

        try:
            content = target_file.read_text(encoding="utf-8")
            return self._parse_frontmatter(
                content,
                target_file,
                platform,
                scripts_dir,
                references_dir,
                assets_dir,
                examples_dir,
                resources_dir,
            )
        except Exception as e:
            logger.error(f"Failed to load skill from {path}: {e}")
            return None

    def _parse_frontmatter(
        self,
        raw_content: str,
        path: Path,
        platform: str,
        scripts_dir: Path | None = None,
        references_dir: Path | None = None,
        assets_dir: Path | None = None,
        examples_dir: Path | None = None,
        resources_dir: Path | None = None,
    ) -> UniversalSkill | None:
        """Parse YAML frontmatter from markdown."""
        # Regex to find YAML block: ^---$ ... ^---$
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, raw_content, re.DOTALL)

        if not match:
            # Fallback: No frontmatter, treat whole file as content, use filename as name
            return UniversalSkill(
                name=path.stem,
                description=f"Skill loaded from {path.name}",
                content=raw_content,
                path=path,
                platform=platform,
                metadata={},
                scripts_dir=scripts_dir,
                references_dir=references_dir,
                assets_dir=assets_dir,
                examples_dir=examples_dir,
                resources_dir=resources_dir,
            )

        yaml_text = match.group(1)
        markdown_body = match.group(2)

        try:
            metadata = yaml.safe_load(yaml_text) if yaml else {}
            if not isinstance(metadata, dict):
                metadata = {}

            name = metadata.get("name", path.parent.name if path.name == "SKILL.md" else path.stem)
            description = metadata.get("description", "No description provided.")

            return UniversalSkill(
                name=name,
                description=description,
                content=markdown_body,
                path=path,
                platform=platform,
                metadata=metadata,
                scripts_dir=scripts_dir,
                references_dir=references_dir,
                assets_dir=assets_dir,
                examples_dir=examples_dir,
                resources_dir=resources_dir,
            )
        except Exception as e:
            logger.error(f"Error parsing YAML for {path}: {e}")
            return None
