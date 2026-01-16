import argparse
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


def _load_toml(path: Path) -> dict:
    try:
        import tomllib as toml
    except ImportError:
        import tomli as toml

    with path.open("rb") as handle:
        return toml.load(handle)


def _collect_dependencies(pyproject_path: Path, include_optional: bool) -> list[str]:
    data = _load_toml(pyproject_path)
    deps = list(data.get("project", {}).get("dependencies", []))
    if include_optional:
        for group in data.get("project", {}).get("optional-dependencies", {}).values():
            deps.extend(group)
    return deps


def generate_sbom(output_path: Path, include_optional: bool) -> int:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_path.exists():
        print("pyproject.toml not found; run from repo root.", file=sys.stderr)
        return 1

    dependencies = _collect_dependencies(pyproject_path, include_optional)
    if not dependencies:
        print("No dependencies found to build SBOM.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile("w", delete=False, encoding="utf-8") as temp_file:
        temp_file.write("\n".join(dependencies))
        temp_path = Path(temp_file.name)

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "-r",
                str(temp_path),
                "--format",
                "cyclonedx-json",
                "--output",
                str(output_path),
            ],
            check=False,
        )
    finally:
        temp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        print("SBOM generation failed. Ensure pip-audit is installed.", file=sys.stderr)
        return result.returncode

    print(f"SBOM written to {output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CycloneDX SBOM from pyproject.toml")
    parser.add_argument(
        "--output",
        default="sbom.json",
        help="Output path for the SBOM file (default: sbom.json)",
    )
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Include optional dependencies in SBOM",
    )
    args = parser.parse_args()

    return generate_sbom(Path(args.output), args.include_optional)


if __name__ == "__main__":
    raise SystemExit(main())
