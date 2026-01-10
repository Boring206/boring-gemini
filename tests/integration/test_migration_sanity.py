import shutil
from pathlib import Path

import pytest

from boring.paths import check_needs_migration, get_migration_plan


@pytest.fixture
def legacy_project(tmp_path):
    """Create a project with legacy structure."""
    project_root = tmp_path / "legacy_project"
    project_root.mkdir()

    # Create legacy folders
    (project_root / ".boring_memory").mkdir()
    (project_root / ".boring_memory" / "memory.db").touch()

    (project_root / ".boring_brain").mkdir()
    (project_root / ".boring_brain" / "patterns.json").touch()

    return project_root


def test_migration_detection(legacy_project):
    """
    Verify that the system correctly detects a project needing migration
    from v10.x (.boring_*) to v10.31+ (.boring/).
    """
    # 1. Assert migration needed (check_needs_migration returns dict)
    needs_migration = check_needs_migration(legacy_project)
    assert any(needs_migration.values()), "Should detect need for migration"

    # 2. Get Plan
    plan = get_migration_plan(legacy_project)

    # 3. Verify Plan Content
    assert len(plan) >= 2, "Should have at least 2 migration steps (memory, brain)"

    # Check moves (plan is list of tuples (src, dst))
    sources = [str(src) for src, dst in plan]
    destinations = [str(dst) for src, dst in plan]

    assert any(".boring_memory" in s for s in sources)
    assert any(".boring_brain" in s for s in sources)
    assert any(".boring" in d and "memory" in d for d in destinations)


def test_fresh_project_no_migration(tmp_path):
    """Verify fresh project doesn't trigger migration."""
    project_root = tmp_path / "fresh_project"
    project_root.mkdir()

    needs_migration = check_needs_migration(project_root)
    assert not any(needs_migration.values()), "Fresh project should not need migration"


if __name__ == "__main__":
    # Allow manual run
    legacy_dir = Path("./temp_legacy_test")
    if legacy_dir.exists():
        shutil.rmtree(legacy_dir)

    legacy_dir.mkdir()
    (legacy_dir / ".boring_memory").mkdir()

    print(f"Checking migration for {legacy_dir}...")
    if check_needs_migration(legacy_dir):
        print("✅ Migration detected correctly.")
        plan = get_migration_plan(legacy_dir)
        print(f"📋 Plan: {plan}")
    else:
        print("❌ Failed to detect migration.")

    shutil.rmtree(legacy_dir)
