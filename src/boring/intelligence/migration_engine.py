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

        # 1. Legacy Memory Consolidation
        legacy_memory = self.root / ".boring_memory"
        if legacy_memory.exists():
            try:
                target = self.unified_dir / "memory"
                if not target.exists():
                    shutil.copytree(legacy_memory, target)
                    results["migrated"].append(".boring_memory -> .boring/memory")
                # After copy, we don't delete immediately to be safe, but mark for cleanup
            except Exception as e:
                results["errors"].append(f"Memory migration failed: {str(e)}")

        # 2. Schema Versioning
        version_file = self.unified_dir / ".version"
        current_ver = "15.0"  # Target Version

        if not self.unified_dir.exists():
            self.unified_dir.mkdir(parents=True)

        version_file.write_text(current_ver, encoding="utf-8")
        results["status"] = f"Project successfully migrated to Schema V{current_ver}"

        return results
