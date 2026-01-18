import shutil
from pathlib import Path


class MigrationEngine:
    """
    Project Evolution & Migration Engine (Phase VII).
    Handles schema upgrades and legacy file consolidation.
    """

    def __init__(self, project_root: Path):
        self.root = project_root
        self.unified_dir = project_root / ".boring"

    def migrate(self) -> dict:
        """Runs the migration logic."""
        results = {"migrated": [], "cleaned": [], "errors": []}

        if not self.unified_dir.exists():
            self.unified_dir.mkdir(parents=True, exist_ok=True)

        # 1. Legacy Memory Consolidation
        legacy_memory = self.root / ".boring_memory"
        if legacy_memory.exists():
            try:
                target = self.unified_dir / "memory"
                if not target.exists():
                    shutil.copytree(legacy_memory, target)
                    # Rename legacy after successful copy to prevent future usage
                    legacy_memory.rename(legacy_memory.with_suffix(".bak"))
                    results["migrated"].append(
                        ".boring_memory -> .boring/memory (and renamed to .bak)"
                    )
                else:
                    results["errors"].append(
                        "Could not migrate .boring_memory - .boring/memory already exists"
                    )
            except Exception as e:
                results["errors"].append(f"Memory migration failed: {str(e)}")

        # 2. Logs Consolidation
        legacy_logs = self.root / "logs"
        if legacy_logs.exists() and legacy_logs.is_dir():
            try:
                target_logs = self.unified_dir / "logs"
                if not target_logs.exists():
                    shutil.move(str(legacy_logs), str(target_logs))
                    results["migrated"].append("logs/ -> .boring/logs/")
                else:
                    results["errors"].append("Could not move logs/ - .boring/logs/ already exists")
            except Exception as e:
                results["errors"].append(f"Logs migration failed: {str(e)}")

        # 3. Legacy Brain Consolidation
        legacy_brain = self.root / ".boring_brain"
        if legacy_brain.exists():
            try:
                target = self.unified_dir / "brain"
                if not target.exists():
                    shutil.copytree(legacy_brain, target)
                    legacy_brain.rename(legacy_brain.with_suffix(".bak"))
                    results["migrated"].append(".boring_brain -> .boring/brain")
                else:
                    results["errors"].append(
                        "Could not migrate .boring_brain - .boring/brain already exists"
                    )
            except Exception as e:
                results["errors"].append(f"Brain migration failed: {str(e)}")

        # 4. Legacy Agent/Workflows Consolidation
        legacy_agent = self.root / ".agent"
        if legacy_agent.exists():
            try:
                target = self.unified_dir / "agent"
                if not target.exists():
                    shutil.copytree(legacy_agent, target)
                    legacy_agent.rename(legacy_agent.with_suffix(".bak"))
                    results["migrated"].append(".agent -> .boring/agent")
                else:
                    results["errors"].append(
                        "Could not migrate .agent - .boring/agent already exists"
                    )
            except Exception as e:
                results["errors"].append(f"Agent migration failed: {str(e)}")

        # 5. .boring.toml Consolidation
        legacy_config = self.root / ".boring.toml"
        if legacy_config.exists():
            try:
                target_config = self.unified_dir / ".boring.toml"
                if not target_config.exists():
                    shutil.move(str(legacy_config), str(target_config))
                    results["migrated"].append(".boring.toml -> .boring/.boring.toml")
                else:
                    results["errors"].append(
                        "Could not move .boring.toml - .boring/.boring.toml already exists"
                    )
            except Exception as e:
                results["errors"].append(f"Config migration failed: {str(e)}")

        # 4. Schema Versioning
        version_file = self.unified_dir / ".version"
        current_ver = "15.0"  # Target Version
        version_file.write_text(current_ver, encoding="utf-8")
        results["status"] = f"Project successfully migrated to Schema V{current_ver}"

        return results
