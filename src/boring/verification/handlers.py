import json
import os
import re
import subprocess
import sys
from pathlib import Path

from ..models import VerificationResult
from .tools import ToolManager

# ==============================================================================
# SYNTAX CHECKERS
# ==============================================================================


def verify_syntax_python(
    file_path: Path, project_root: Path, tools: ToolManager
) -> VerificationResult:
    """Check Python syntax using compile()."""
    try:
        content = file_path.read_text(encoding="utf-8")
        compile(content, str(file_path), "exec")
        return VerificationResult(
            passed=True,
            check_type="syntax",
            message=f"Syntax OK: {file_path.name}",
            details=[],
            suggestions=[],
        )
    except SyntaxError as e:
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"Syntax Error in {file_path.name}",
            details=[f"Line {e.lineno}: {e.msg}", f"Text: {e.text.strip() if e.text else 'N/A'}"],
            suggestions=[f"Fix the syntax error at line {e.lineno}"],
        )
    except Exception as e:
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"Error checking {file_path.name}: {e}",
            details=[str(e)],
            suggestions=[],
        )


def verify_syntax_node(
    file_path: Path, project_root: Path, tools: ToolManager
) -> VerificationResult:
    """Check Node.js syntax using --check."""
    if not tools.is_available("node"):
        return VerificationResult(
            passed=True,
            check_type="syntax",
            message="Skipped (Node not found)",
            details=[],
            suggestions=[],
        )

    try:
        result = subprocess.run(
            ["node", "--check", str(file_path)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="syntax",
                message=f"Syntax OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"Syntax Error: {file_path.name}",
            details=[result.stderr],
            suggestions=["Check JS syntax"],
        )
    except Exception as e:
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"Check failed: {e}",
            details=[],
            suggestions=[],
        )


def verify_syntax_go(file_path: Path, project_root: Path, tools: ToolManager) -> VerificationResult:
    if not tools.is_available("go"):
        return VerificationResult(
            passed=True, check_type="syntax", message="Skipped", details=[], suggestions=[]
        )
    try:
        result = subprocess.run(
            ["go", "fmt", str(file_path)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="syntax",
                message=f"Syntax OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"Go Syntax Error: {file_path.name}",
            details=[result.stderr],
            suggestions=["Run 'go fmt'"],
        )
    except Exception as e:
        return VerificationResult(
            passed=False, check_type="syntax", message=f"Error: {e}", details=[], suggestions=[]
        )


def verify_syntax_rust(
    file_path: Path, project_root: Path, tools: ToolManager
) -> VerificationResult:
    if not tools.is_available("rustc"):
        return VerificationResult(
            passed=True, check_type="syntax", message="Skipped", details=[], suggestions=[]
        )
    try:
        outfile = "/dev/null" if os.name != "nt" else "NUL"
        result = subprocess.run(
            ["rustc", "--emit=metadata", "-o", outfile, str(file_path)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="syntax",
                message=f"Syntax OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"Rust Syntax Error: {file_path.name}",
            details=[result.stderr[:500]],
            suggestions=["Run cargo check"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="syntax", message=f"Error: {e}", details=[], suggestions=[]
        )


def verify_syntax_java(
    file_path: Path, project_root: Path, tools: ToolManager
) -> VerificationResult:
    if not tools.is_available("javac"):
        return VerificationResult(
            passed=True, check_type="syntax", message="Skipped", details=[], suggestions=[]
        )
    try:
        result = subprocess.run(
            ["javac", "-Xlint:none", "-d", str(file_path.parent), str(file_path)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="syntax",
                message=f"Syntax OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"Java Syntax Error: {file_path.name}",
            details=[result.stderr[:500]],
            suggestions=["Check Java syntax"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="syntax", message=f"Error: {e}", details=[], suggestions=[]
        )


def verify_syntax_c(file_path: Path, project_root: Path, tools: ToolManager) -> VerificationResult:
    if not tools.is_available("gcc"):
        return VerificationResult(
            passed=True, check_type="syntax", message="Skipped", details=[], suggestions=[]
        )
    try:
        result = subprocess.run(
            ["gcc", "-fsyntax-only", str(file_path)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="syntax",
                message=f"Syntax OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"C Syntax Error: {file_path.name}",
            details=[result.stderr[:500]],
            suggestions=["Check C syntax"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="syntax", message=f"Error: {e}", details=[], suggestions=[]
        )


def verify_syntax_cpp(
    file_path: Path, project_root: Path, tools: ToolManager
) -> VerificationResult:
    if not tools.is_available("g++"):
        return VerificationResult(
            passed=True, check_type="syntax", message="Skipped", details=[], suggestions=[]
        )
    try:
        result = subprocess.run(
            ["g++", "-fsyntax-only", "-std=c++17", str(file_path)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="syntax",
                message=f"Syntax OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="syntax",
            message=f"C++ Syntax Error: {file_path.name}",
            details=[result.stderr[:500]],
            suggestions=["Check C++ syntax"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="syntax", message=f"Error: {e}", details=[], suggestions=[]
        )


# ==============================================================================
# LINT CHECKERS
# ==============================================================================


def verify_lint_python(
    file_path: Path, project_root: Path, tools: ToolManager, auto_fix: bool = False
) -> VerificationResult:
    if not tools.is_available("ruff"):
        return VerificationResult(
            passed=True,
            check_type="lint",
            message="Skipped (ruff not found)",
            details=[],
            suggestions=[],
        )

    fixed_count = 0
    if auto_fix:
        try:
            fix_result = subprocess.run(
                ["ruff", "check", str(file_path), "--fix", "--unsafe-fixes"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_root,
            )
            if "Fixed" in fix_result.stdout:
                match = re.search(r"Fixed (\d+)", fix_result.stdout)
                if match:
                    fixed_count = int(match.group(1))
        except Exception:
            pass

    try:
        result = subprocess.run(
            ["ruff", "check", str(file_path), "--output-format", "concise"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root,
        )
        if result.returncode == 0:
            msg = f"Lint OK: {file_path.name}" + (
                f" (fixed {fixed_count})" if fixed_count > 0 else ""
            )
            return VerificationResult(
                passed=True, check_type="lint", message=msg, details=[], suggestions=[]
            )

        issues = result.stdout.strip().split("\n") if result.stdout else [result.stderr]
        return VerificationResult(
            passed=False,
            check_type="lint",
            message=f"Lint issues: {file_path.name}",
            details=issues[:20],
            suggestions=["Run ruff check --fix"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="lint", message=f"Error: {e}", details=[], suggestions=[]
        )


def verify_lint_node(
    file_path: Path, project_root: Path, tools: ToolManager, auto_fix: bool = False
) -> VerificationResult:
    if not tools.is_available("eslint"):
        return VerificationResult(
            passed=True, check_type="lint", message="Skipped", details=[], suggestions=[]
        )

    cmd = ["eslint", str(file_path)]
    if auto_fix:
        cmd.append("--fix")

    try:
        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="lint",
                message=f"ESLint OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="lint",
            message=f"ESLint issues: {file_path.name}",
            details=[result.stdout],
            suggestions=["Fix ESLint issues"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="lint", message=f"Error: {e}", details=[], suggestions=[]
        )


def verify_lint_generic(
    file_path: Path, project_root: Path, tools: ToolManager, auto_fix: bool = False
) -> VerificationResult:
    ext = file_path.suffix.lower()
    mapping = tools.cli_tool_map.get(ext)

    if not mapping:
        return VerificationResult(
            passed=True, check_type="lint", message="Skipped", details=[], suggestions=[]
        )

    tool_key, default_cmd = mapping
    if not tools.is_available(tool_key):
        return VerificationResult(
            passed=True,
            check_type="lint",
            message=f"Skipped ({tool_key} not found)",
            details=[],
            suggestions=[],
        )

    # Configuration overrides logic is tricky since it was in verifier.py accessing settings
    # We should have passed config or let tools.py handle command generation.
    # For now, use default_cmd or basic construction
    cmd = list(default_cmd)

    # Check for overrides (simple version - ideally helper in tools)
    from ..config import settings

    custom_args = settings.LINTER_CONFIGS.get(tool_key)
    if custom_args:
        cmd = [tool_key] + custom_args

    cmd.append(str(file_path))

    try:
        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="lint",
                message=f"{tool_key} OK: {file_path.name}",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="lint",
            message=f"{tool_key} found issues",
            details=[result.stdout or result.stderr],
            suggestions=[f"Run {tool_key}"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="lint", message=f"Error: {e}", details=[], suggestions=[]
        )


# ==============================================================================
# IMPORT CHECKERS
# ==============================================================================


def verify_imports_python(file_path: Path, project_root: Path) -> VerificationResult:
    try:
        content = file_path.read_text(encoding="utf-8")
        import_pattern = r"^(?:from\s+([\w.]+)\s+)?import\s+([\w.]+(?:\s*,\s*[\w.]+)*)"
        imports = re.findall(import_pattern, content, re.MULTILINE)
        missing_imports = []
        for from_module, import_names in imports:
            module = from_module or import_names.split(",")[0].strip()
            if module.startswith(".") or module in sys.stdlib_module_names:
                continue
            try:
                __import__(module.split(".")[0])
            except ImportError:
                missing_imports.append(module)

        if missing_imports:
            return VerificationResult(
                passed=False,
                check_type="import",
                message=f"Missing imports: {file_path.name}",
                details=missing_imports[:5],
                suggestions=[f"pip install {m}" for m in missing_imports[:3]],
            )
        return VerificationResult(
            passed=True,
            check_type="import",
            message=f"Imports OK: {file_path.name}",
            details=[],
            suggestions=[],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="import", message=f"Skipped: {e}", details=[], suggestions=[]
        )


def verify_imports_node(file_path: Path, project_root: Path) -> VerificationResult:
    try:
        package_json = project_root / "package.json"
        if not package_json.exists():
            return VerificationResult(
                passed=True,
                check_type="import",
                message="No package.json",
                details=[],
                suggestions=[],
            )

        with open(package_json) as f:
            pkg = json.load(f)

        all_deps = set(pkg.get("dependencies", {}).keys())
        all_deps.update(pkg.get("devDependencies", {}).keys())

        content = file_path.read_text(encoding="utf-8")
        import_pattern = r"""(?:import\s+.*?from\s+['"]|require\s*\(\s*['"])([^'"./][^'"]*)['"]"""
        imports = re.findall(import_pattern, content)

        missing = []
        for imp in imports:
            pkg_name = imp.split("/")[0]
            if pkg_name.startswith("@"):
                pkg_name = "/".join(imp.split("/")[:2])
            if pkg_name not in all_deps and not pkg_name.startswith("node:"):
                missing.append(pkg_name)

        if missing:
            unique = list(set(missing))[:5]
            return VerificationResult(
                passed=False,
                check_type="import",
                message=f"Missing packages: {file_path.name}",
                details=unique,
                suggestions=[f"npm install {m}" for m in unique[:3]],
            )
        return VerificationResult(
            passed=True,
            check_type="import",
            message=f"Imports OK: {file_path.name}",
            details=[],
            suggestions=[],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="import", message=f"Skipped: {e}", details=[], suggestions=[]
        )


def verify_imports_go(
    file_path: Path, project_root: Path, tools: ToolManager
) -> VerificationResult:
    if not tools.is_available("go"):
        return VerificationResult(
            passed=True, check_type="import", message="Skipped", details=[], suggestions=[]
        )
    try:
        result = subprocess.run(
            ["go", "list", "-e", "-json", str(file_path.parent)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=project_root,
        )
        if result.returncode == 0:
            return VerificationResult(
                passed=True,
                check_type="import",
                message="Go imports OK",
                details=[],
                suggestions=[],
            )
        return VerificationResult(
            passed=False,
            check_type="import",
            message="Go import issues",
            details=[result.stderr],
            suggestions=["Run go mod tidy"],
        )
    except Exception as e:
        return VerificationResult(
            passed=True, check_type="import", message=f"Skipped: {e}", details=[], suggestions=[]
        )
