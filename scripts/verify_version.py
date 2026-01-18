import re
import sys
from pathlib import Path


def _extract_first_version(text: str) -> str | None:
    match = re.search(r"V(\d+\.\d+\.\d+)", text)
    if match:
        return match.group(1)
    return None


def check_versions():
    root = Path(__file__).parent.parent

    # 1. Check pyproject.toml
    pyproject_path = root / "pyproject.toml"
    with open(pyproject_path, encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if not match:
            print("❌ Could not find version in pyproject.toml")
            return False
        pyproject_version = match.group(1)
        print(f"✅ pyproject.toml: {pyproject_version}")

    major_version = pyproject_version.split(".")[0]

    # 2. Check __init__.py
    init_path = root / "src" / "boring" / "__init__.py"
    with open(init_path, encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        if not match:
            print("❌ Could not find version in src/boring/__init__.py")
            return False
        init_version = match.group(1)

    if init_version == pyproject_version:
        print(f"✅ __init__.py: {init_version}")
    else:
        print(f"❌ __init__.py mismatch: {init_version} != {pyproject_version}")
        return False

    # 3. Check CHANGELOG.md
    changelog_path = root / "CHANGELOG.md"
    with open(changelog_path, encoding="utf-8") as f:
        content = f.read()
        if f"## [{pyproject_version}]" in content:
            print(f"✅ CHANGELOG.md: Found entry for {pyproject_version}")
        else:
            print(f"❌ CHANGELOG.md: Missing entry for {pyproject_version}")
            return False

    # 4. Check docs/index.md current version
    docs_index_path = root / "docs" / "index.md"
    with open(docs_index_path, encoding="utf-8") as f:
        content = f.read()
        doc_version = _extract_first_version(content)
        if doc_version == pyproject_version:
            print(f"✅ docs/index.md: Current Version V{doc_version}")
        else:
            print(f"❌ docs/index.md: Version mismatch {doc_version} != {pyproject_version}")
            return False

    # 5. Check mkdocs.yml site_description
    mkdocs_path = root / "mkdocs.yml"
    with open(mkdocs_path, encoding="utf-8") as f:
        content = f.read()
        mkdocs_version = _extract_first_version(content)
        if mkdocs_version == pyproject_version:
            print(f"✅ mkdocs.yml: site_description V{mkdocs_version}")
        else:
            print(f"❌ mkdocs.yml: Version mismatch {mkdocs_version} != {pyproject_version}")
            return False

    # 6. Check SECURITY.md supported major version
    security_path = root / "SECURITY.md"
    with open(security_path, encoding="utf-8") as f:
        content = f.read()
        if f"{major_version}.x" in content:
            print(f"✅ SECURITY.md: Supported {major_version}.x")
        else:
            print(f"❌ SECURITY.md: Missing support for {major_version}.x")
            return False

    print("\n🎉 All versions synchronized!")
    return True


if __name__ == "__main__":
    success = check_versions()
    sys.exit(0 if success else 1)
