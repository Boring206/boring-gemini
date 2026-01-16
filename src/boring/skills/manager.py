"""
Skills Marketplace Manager for Boring-Gemini V14.0

Empowers the community to share and install custom skills (MCP tools, workflows, prompts).
"""

import logging
import shutil

from boring.core.config import settings

logger = logging.getLogger(__name__)

# Trusted skill registries (Safety mechanism)
TRUSTED_DOMAINS = ["github.com", "raw.githubusercontent.com", "gitlab.com", "gist.github.com"]


class SkillManager:
    """
    Manages installation, update, and removal of Boring Skills.
    Skills are essentially folders with a `SKILL.md` and optional scripts/resources.
    """

    def __init__(self):
        self.skills_dir = settings.PROJECT_ROOT / ".boring" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.registry_url = (
            "https://raw.githubusercontent.com/Boring206/boring-skills/main/registry.json"
        )

    def list_installed_skills(self) -> list[str]:
        """List names of installed skills."""
        return [d.name for d in self.skills_dir.iterdir() if d.is_dir()]

    def install_skill(self, skill_url: str, name: str) -> bool:
        """
        Install a skill from a git repo or direct URL.
        (Simplified version: clones git repo)
        """
        # Security check
        domain = skill_url.split("/")[2]
        if domain not in TRUSTED_DOMAINS:
            logger.warning(f"Installing skill from untrusted domain: {domain}")
            # In a real CLI, we would ask for confirmation here

        target_dir = self.skills_dir / name
        if target_dir.exists():
            logger.warning(f"Skill {name} already installed.")
            return False

        try:
            # For MVP, we assume git clone
            # In future: support zip download, checking manifest, etc.
            from git import Repo

            Repo.clone_from(skill_url, target_dir)
            logger.info(f"Skill {name} installed successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to install skill: {e}")
            return False

    def uninstall_skill(self, name: str) -> bool:
        """Remove an installed skill."""
        target_dir = self.skills_dir / name
        if not target_dir.exists():
            return False

        shutil.rmtree(target_dir)
        return True

    def search_registry(self, query: str) -> list[dict]:
        """
        Search the central skill registry (simulated for now).
        """
        # Simulated registry data
        registry = [
            {
                "name": "security-scanner",
                "desc": "Advanced security audit tools",
                "url": "https://github.com/boring/security-skill",
            },
            {
                "name": "react-expert",
                "desc": "React/Next.js specialized prompts",
                "url": "https://github.com/boring/react-skill",
            },
            {
                "name": "python-optimizer",
                "desc": "Performance profiling tools",
                "url": "https://github.com/boring/python-skill",
            },
        ]

        return [s for s in registry if query.lower() in s["name"] or query.lower() in s["desc"]]
