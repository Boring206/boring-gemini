from pathlib import Path

import tomllib

import boring
from boring.utils.version import get_project_version


def test_version_consistency():
    # 1. Check module version
    module_version = boring.__version__
    assert module_version == "14.0.0"

    # 2. Check pyproject.toml
    root = Path(__file__).resolve().parents[2]
    pyproject = root / "pyproject.toml"
    assert pyproject.exists()

    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
        toml_version = data["project"]["version"]

    assert toml_version == module_version

    # 3. Check CHANGELOG.md (first entry)
    changelog = root / "CHANGELOG.md"
    assert changelog.exists()
    content = changelog.read_text(encoding="utf-8")
    assert "## [14.0.0]" in content or "## [V14.0.0]" in content


def test_version_utils():
    # Test the utility function
    v = get_project_version()
    assert v == "14.0.0"
