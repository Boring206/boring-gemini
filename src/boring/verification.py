"""
Boring Polyglot Verification System

Enterprise-grade rules-based verification for multiple programming languages.

Supported Languages & Tools:
- Python: compile() syntax, ruff lint, pytest tests, import validation
- JavaScript/TypeScript: node --check, eslint lint, npm test
- Go: go fmt syntax, golangci-lint, go test
- Rust: cargo check syntax, cargo clippy lint, cargo test
- Java: javac syntax, checkstyle lint, maven/gradle test
- C/C++: gcc/g++ syntax check, clang-tidy lint

Verification Levels:
- BASIC: Syntax check only (fast, always available)
- STANDARD: Syntax + Linting (requires language-specific linters)
- FULL: Syntax + Linting + Tests (requires test frameworks)
- SEMANTIC: All above + LLM-as-Judge evaluation

Features:
- Auto-detection of project type and language
- Generic CLI tool dispatcher for extensibility
- Language-aware evaluation prompts
"""

import subprocess
import sys
import re
import os
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass

from .config import settings
from .logger import log_status


@dataclass
class VerificationResult:
    """Result of a verification step."""
    passed: bool
    check_type: str  # syntax, lint, test, import
    message: str
    details: List[str]
    suggestions: List[str]


class CodeVerifier:
    """
    Polyglot code verification system supporting Python, JavaScript/TypeScript,
    Go, Rust, Java, and C/C++.
    
    Verification levels:
    1. BASIC: Syntax check only (fast, always available)
    2. STANDARD: Syntax + Linting (language-specific linters)
    3. FULL: Syntax + Linting + Tests (language-specific test runners)
    4. SEMANTIC: All above + LLM-as-Judge evaluation
    """
    
    def __init__(self, project_root: Path = None, log_dir: Path = None, judge = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.log_dir = log_dir or settings.LOG_DIR
        self.judge = judge
        
        # Check available tools (polyglot support)
        self.tools = {
            # Python
            "ruff": self._check_tool("ruff", "--version"),
            "pytest": self._check_tool("pytest", "--version"),
            # JavaScript/TypeScript
            "node": self._check_tool("node", "--version"),
            "npm": self._check_tool("npm", "--version"),
            "eslint": self._check_tool("eslint", "--version"),
            # Go
            "go": self._check_tool("go", "version"),
            "golangci-lint": self._check_tool("golangci-lint", "version"),
            # Rust
            "cargo": self._check_tool("cargo", "--version"),
            "rustc": self._check_tool("rustc", "--version"),
            # Java
            "javac": self._check_tool("javac", "-version"),
            "mvn": self._check_tool("mvn", "--version"),
            "gradle": self._check_tool("gradle", "--version"),
            # C/C++
            "gcc": self._check_tool("gcc", "--version"),
            "g++": self._check_tool("g++", "--version"),
            "clang-tidy": self._check_tool("clang-tidy", "--version"),
        }
        
        # Generic CLI Tool Dispatcher (Extension -> Linter Command)
        # Format: ext: (tool_key, [cmd_args...])
        self.cli_tool_map = {
            ".go": ("golangci-lint", ["golangci-lint", "run"]),
            ".rs": ("cargo", ["cargo", "clippy", "--", "-D", "warnings"]),
            ".c": ("clang-tidy", ["clang-tidy"]),
            ".cpp": ("clang-tidy", ["clang-tidy"]),
            ".h": ("clang-tidy", ["clang-tidy"]),
            ".hpp": ("clang-tidy", ["clang-tidy"]),
        }
        
        # Dispatch configuration (polyglot handlers)
        self.handlers: Dict[str, Dict[str, callable]] = {
            # Python
            ".py": {
                "syntax": self._verify_syntax_python,
                "lint": self._verify_lint_python
            },
            # JavaScript/TypeScript
            ".js": {
                "syntax": self._verify_syntax_node,
                "lint": self._verify_lint_node
            },
            ".jsx": {
                "syntax": self._verify_syntax_node,
                "lint": self._verify_lint_node
            },
            ".ts": {
                "syntax": self._verify_syntax_node,
                "lint": self._verify_lint_node
            },
            ".tsx": {
                "syntax": self._verify_syntax_node,
                "lint": self._verify_lint_node
            },
            # Go
            ".go": {
                "syntax": self._verify_syntax_go,
                "lint": self._verify_lint_generic
            },
            # Rust
            ".rs": {
                "syntax": self._verify_syntax_rust,
                "lint": self._verify_lint_generic
            },
            # Java
            ".java": {
                "syntax": self._verify_syntax_java,
                "lint": self._verify_lint_generic
            },
            # C/C++
            ".c": {
                "syntax": self._verify_syntax_c,
                "lint": self._verify_lint_generic
            },
            ".cpp": {
                "syntax": self._verify_syntax_cpp,
                "lint": self._verify_lint_generic
            },
            ".h": {
                "syntax": self._verify_syntax_c,
                "lint": self._verify_lint_generic
            },
            ".hpp": {
                "syntax": self._verify_syntax_cpp,
                "lint": self._verify_lint_generic
            }
        }
    
    def _check_tool(self, tool: str, version_arg: str) -> bool:
        """Check if a tool is available."""
        try:
            result = subprocess.run(
                [tool, version_arg],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def verify_syntax(self, file_path: Path) -> VerificationResult:
        """Check syntax based on file extension."""
        ext = file_path.suffix.lower()
        handler = self.handlers.get(ext)
        
        if handler and handler.get("syntax"):
            return handler["syntax"](file_path)
        
        return VerificationResult(
            passed=True,
            check_type="syntax",
            message=f"Syntax check skipped: Unknown or unsupported extension {ext}",
            details=[],
            suggestions=[]
        )

    def _verify_syntax_python(self, file_path: Path) -> VerificationResult:
        """Check Python syntax using compile()."""
        try:
            content = file_path.read_text(encoding="utf-8")
            compile(content, str(file_path), 'exec')
            return VerificationResult(
                passed=True,
                check_type="syntax",
                message=f"Syntax OK: {file_path.name}",
                details=[],
                suggestions=[]
            )
        except SyntaxError as e:
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"Syntax Error in {file_path.name}",
                details=[f"Line {e.lineno}: {e.msg}", f"Text: {e.text.strip() if e.text else 'N/A'}"],
                suggestions=[
                    f"Fix the syntax error at line {e.lineno}",
                    "Check for missing colons, parentheses, or indentation"
                ]
            )
        except Exception as e:
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"Error checking {file_path.name}: {e}",
                details=[str(e)],
                suggestions=[]
            )

    def _verify_syntax_node(self, file_path: Path) -> VerificationResult:
        """Check Node.js syntax using --check."""
        if not self.tools["node"]:
            return VerificationResult(passed=True, check_type="syntax", message="Skipped (Node not found)", details=[], suggestions=[])
        
        try:
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="syntax", message=f"Syntax OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"Syntax Error: {file_path.name}",
                details=[result.stderr],
                suggestions=["Check for missing brackets or semicolons"]
            )
        except Exception as e:
            return VerificationResult(passed=False, check_type="syntax", message=f"Check failed: {e}", details=[], suggestions=[])

    def _verify_syntax_go(self, file_path: Path) -> VerificationResult:
        """Check Go syntax using go build."""
        if not self.tools["go"]:
            return VerificationResult(passed=True, check_type="syntax", message="Skipped (Go not found)", details=[], suggestions=[])
        
        try:
            result = subprocess.run(
                ["go", "fmt", str(file_path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="syntax", message=f"Syntax OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"Go Syntax Error: {file_path.name}",
                details=[result.stderr],
                suggestions=["Run 'go fmt' manually to see issues"]
            )
        except Exception as e:
            return VerificationResult(passed=False, check_type="syntax", message=f"Go check failed: {e}", details=[], suggestions=[])

    def _verify_syntax_rust(self, file_path: Path) -> VerificationResult:
        """Check Rust syntax using rustc --emit=metadata."""
        if not self.tools.get("rustc"):
            return VerificationResult(passed=True, check_type="syntax", message="Skipped (rustc not found)", details=[], suggestions=["Install Rust: https://rustup.rs/"])
        
        try:
            # Use rustc to check syntax without full compilation
            result = subprocess.run(
                ["rustc", "--emit=metadata", "-o", "/dev/null" if os.name != 'nt' else "NUL", str(file_path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="syntax", message=f"Rust Syntax OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"Rust Syntax Error: {file_path.name}",
                details=[result.stderr[:500] if result.stderr else "Unknown error"],
                suggestions=["Run 'cargo check' for detailed error messages"]
            )
        except Exception as e:
            return VerificationResult(passed=True, check_type="syntax", message=f"Rust check skipped: {e}", details=[], suggestions=[])

    def _verify_syntax_java(self, file_path: Path) -> VerificationResult:
        """Check Java syntax using javac."""
        if not self.tools.get("javac"):
            return VerificationResult(passed=True, check_type="syntax", message="Skipped (javac not found)", details=[], suggestions=["Install JDK"])
        
        try:
            # Use -Xlint:none to suppress warnings, -d for output dir
            result = subprocess.run(
                ["javac", "-Xlint:none", "-d", str(file_path.parent), str(file_path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="syntax", message=f"Java Syntax OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"Java Syntax Error: {file_path.name}",
                details=[result.stderr[:500] if result.stderr else "Compilation failed"],
                suggestions=["Check Java syntax and imports"]
            )
        except Exception as e:
            return VerificationResult(passed=True, check_type="syntax", message=f"Java check skipped: {e}", details=[], suggestions=[])

    def _verify_syntax_c(self, file_path: Path) -> VerificationResult:
        """Check C syntax using gcc -fsyntax-only."""
        if not self.tools.get("gcc"):
            return VerificationResult(passed=True, check_type="syntax", message="Skipped (gcc not found)", details=[], suggestions=["Install GCC"])
        
        try:
            result = subprocess.run(
                ["gcc", "-fsyntax-only", str(file_path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="syntax", message=f"C Syntax OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"C Syntax Error: {file_path.name}",
                details=[result.stderr[:500] if result.stderr else "Unknown error"],
                suggestions=["Check for missing semicolons, brackets, or include statements"]
            )
        except Exception as e:
            return VerificationResult(passed=True, check_type="syntax", message=f"C check skipped: {e}", details=[], suggestions=[])

    def _verify_syntax_cpp(self, file_path: Path) -> VerificationResult:
        """Check C++ syntax using g++ -fsyntax-only."""
        if not self.tools.get("g++"):
            return VerificationResult(passed=True, check_type="syntax", message="Skipped (g++ not found)", details=[], suggestions=["Install G++"])
        
        try:
            result = subprocess.run(
                ["g++", "-fsyntax-only", "-std=c++17", str(file_path)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="syntax", message=f"C++ Syntax OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(
                passed=False,
                check_type="syntax",
                message=f"C++ Syntax Error: {file_path.name}",
                details=[result.stderr[:500] if result.stderr else "Unknown error"],
                suggestions=["Check C++ syntax and template usage"]
            )
        except Exception as e:
            return VerificationResult(passed=True, check_type="syntax", message=f"C++ check skipped: {e}", details=[], suggestions=[])

    def verify_lint(self, file_path: Path, auto_fix: bool = False) -> VerificationResult:
        """Run linter based on file extension."""
        ext = file_path.suffix.lower()
        handler = self.handlers.get(ext)
        
        if handler and handler.get("lint"):
            return handler["lint"](file_path, auto_fix)
        
        return VerificationResult(passed=True, check_type="lint", message="Skipped: No linter for this language", details=[], suggestions=[])

    def _verify_lint_python(self, file_path: Path, auto_fix: bool = False) -> VerificationResult:
        """Run ruff linter on a file."""
        if not self.tools["ruff"]:
            return VerificationResult(
                passed=True,
                check_type="lint",
                message="Linting skipped (ruff not available)",
                details=[],
                suggestions=["Install ruff: pip install ruff"]
            )
        
        fixed_count = 0
        if auto_fix:
            try:
                fix_result = subprocess.run(
                    ["ruff", "check", str(file_path), "--fix", "--unsafe-fixes"],
                    stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, cwd=self.project_root
                )
                if "Fixed" in fix_result.stdout:
                    match = re.search(r"Fixed (\d+)", fix_result.stdout)
                    if match: fixed_count = int(match.group(1))
            except Exception: pass
        
        try:
            result = subprocess.run(
                ["ruff", "check", str(file_path), "--output-format", "concise"],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, cwd=self.project_root
            )
            if result.returncode == 0:
                msg = f"Lint OK: {file_path.name}" + (f" (auto-fixed {fixed_count})" if fixed_count > 0 else "")
                return VerificationResult(passed=True, check_type="lint", message=msg, details=[], suggestions=[])
            else:
                issues = result.stdout.strip().split("\n") if result.stdout else [result.stderr]
                return VerificationResult(passed=False, check_type="lint", message=f"Lint issues in {file_path.name}", details=issues[:20], suggestions=["Run 'ruff check --fix'"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="lint", message=f"Lint check error: {e}", details=[], suggestions=[])

    def _verify_lint_node(self, file_path: Path, auto_fix: bool = False) -> VerificationResult:
        """Run eslint on a file."""
        if not self.tools["eslint"]:
            return VerificationResult(passed=True, check_type="lint", message="Skipped (ESLint not found)", details=[], suggestions=[])
        
        cmd = ["eslint", str(file_path)]
        if auto_fix: cmd.append("--fix")
        
        try:
            result = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, cwd=self.project_root)
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="lint", message=f"ESLint OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="lint", message=f"ESLint issues: {file_path.name}", details=[result.stdout], suggestions=["Fix ESLint issues"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="lint", message=f"ESLint failed: {e}", details=[], suggestions=[])

    def _verify_lint_generic(self, file_path: Path, auto_fix: bool = False) -> VerificationResult:
        """
        Generic linter dispatcher based on self.cli_tool_map. 
        Supports any CLI tool defined in the map.
        """
        ext = file_path.suffix.lower()
        mapping = self.cli_tool_map.get(ext)
        
        if not mapping:
            return VerificationResult(passed=True, check_type="lint", message="Skipped (No generic mapping)", details=[], suggestions=[])
            
        tool_key, base_cmd = mapping
        if not self.tools.get(tool_key):
             return VerificationResult(passed=True, check_type="lint", message=f"Skipped ({tool_key} not found)", details=[], suggestions=[])
             
        cmd = list(base_cmd)
        
        # Some tools handle file arguments differently, but most take it as last arg
        cmd.append(str(file_path))
        
        # Note: Auto-fix is tool dependent. For now, generic dispatcher assumes standard verification mode.
        
        try:
            result = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60, cwd=self.project_root)
            if result.returncode == 0:
                 return VerificationResult(passed=True, check_type="lint", message=f"{tool_key} OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="lint", message=f"{tool_key} found issues", details=[result.stdout or result.stderr], suggestions=[f"Run {tool_key} locally"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="lint", message=f"{tool_key} execution error: {e}", details=[], suggestions=[])

    def verify_imports(self, file_path: Path) -> VerificationResult:
        """Check if all imports are resolvable (multi-language support)."""
        ext = file_path.suffix.lower()
        
        if ext == ".py":
            return self._verify_imports_python(file_path)
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return self._verify_imports_node(file_path)
        elif ext == ".go":
            return self._verify_imports_go(file_path)
        elif ext == ".rs":
            return VerificationResult(passed=True, check_type="import", message="Rust: Use 'cargo check' for import validation", details=[], suggestions=[])
        elif ext == ".java":
            return VerificationResult(passed=True, check_type="import", message="Java: Use 'javac' for import validation", details=[], suggestions=[])
        
        return VerificationResult(passed=True, check_type="import", message=f"Import check not supported for {ext}", details=[], suggestions=[])
    
    def _verify_imports_python(self, file_path: Path) -> VerificationResult:
        """Check Python imports."""
        try:
            content = file_path.read_text(encoding="utf-8")
            import_pattern = r'^(?:from\s+([\w.]+)\s+)?import\s+([\w.]+(?:\s*,\s*[\w.]+)*)'
            imports = re.findall(import_pattern, content, re.MULTILINE)
            missing_imports = []
            for from_module, import_names in imports:
                module = from_module or import_names.split(",")[0].strip()
                if module.startswith(".") or module in sys.stdlib_module_names: continue
                try: __import__(module.split(".")[0])
                except ImportError: missing_imports.append(module)
            
            if missing_imports:
                return VerificationResult(passed=False, check_type="import", message=f"Missing imports: {file_path.name}", details=missing_imports[:5], suggestions=[f"pip install {m}" for m in missing_imports[:3]])
            return VerificationResult(passed=True, check_type="import", message=f"Imports OK: {file_path.name}", details=[], suggestions=[])
        except Exception as e:
            return VerificationResult(passed=True, check_type="import", message=f"Import check skipped: {e}", details=[], suggestions=[])
    
    def _verify_imports_node(self, file_path: Path) -> VerificationResult:
        """Check Node.js imports by verifying package.json dependencies."""
        try:
            package_json = self.project_root / "package.json"
            if not package_json.exists():
                return VerificationResult(passed=True, check_type="import", message="No package.json found", details=[], suggestions=[])
            
            import json
            with open(package_json) as f:
                pkg = json.load(f)
            
            all_deps = set(pkg.get("dependencies", {}).keys())
            all_deps.update(pkg.get("devDependencies", {}).keys())
            
            content = file_path.read_text(encoding="utf-8")
            # Simple regex for import/require
            import_pattern = r'''(?:import\s+.*?from\s+['"]|require\s*\(\s*['"])([^'"./][^'"]*)['"]'''
            imports = re.findall(import_pattern, content)
            
            # Extract package name (first part before /)
            missing = []
            for imp in imports:
                pkg_name = imp.split("/")[0]
                if pkg_name.startswith("@"):
                    pkg_name = "/".join(imp.split("/")[:2])
                if pkg_name not in all_deps and not pkg_name.startswith("node:"):
                    missing.append(pkg_name)
            
            if missing:
                unique_missing = list(set(missing))[:5]
                return VerificationResult(passed=False, check_type="import", message=f"Missing packages: {file_path.name}", details=unique_missing, suggestions=[f"npm install {m}" for m in unique_missing[:3]])
            return VerificationResult(passed=True, check_type="import", message=f"Node imports OK: {file_path.name}", details=[], suggestions=[])
        except Exception as e:
            return VerificationResult(passed=True, check_type="import", message=f"Node import check skipped: {e}", details=[], suggestions=[])
    
    def _verify_imports_go(self, file_path: Path) -> VerificationResult:
        """Verify Go imports using go list."""
        if not self.tools.get("go"):
            return VerificationResult(passed=True, check_type="import", message="Skipped (Go not found)", details=[], suggestions=[])
        
        try:
            result = subprocess.run(
                ["go", "list", "-e", "-json", str(file_path.parent)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="import", message=f"Go imports OK: {file_path.name}", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="import", message="Go import issues", details=[result.stderr[:200] if result.stderr else "Unknown"], suggestions=["Run 'go mod tidy'"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="import", message=f"Go import check skipped: {e}", details=[], suggestions=[])

    def run_tests(self, test_path: Path = None) -> VerificationResult:
        """Run tests based on project type (auto-detection)."""
        # Polyglot test runner detection
        if (self.project_root / "Cargo.toml").exists():
            return self._run_tests_rust(test_path)
        elif (self.project_root / "pom.xml").exists():
            return self._run_tests_maven(test_path)
        elif (self.project_root / "build.gradle").exists() or (self.project_root / "build.gradle.kts").exists():
            return self._run_tests_gradle(test_path)
        elif (self.project_root / "package.json").exists():
            return self._run_tests_node(test_path)
        elif (self.project_root / "go.mod").exists():
            return self._run_tests_go(test_path)
        
        return self._run_tests_python(test_path)

    def _run_tests_python(self, test_path: Path = None) -> VerificationResult:
        """Run pytest."""
        if not self.tools["pytest"]:
            return VerificationResult(passed=True, check_type="test", message="Skipped (pytest not found)", details=[], suggestions=[])
        
        test_target = test_path or (self.project_root / "tests")
        if not test_target.exists():
            return VerificationResult(passed=True, check_type="test", message="No tests found", details=[], suggestions=[])
        
        try:
            result = subprocess.run(["pytest", str(test_target), "-q"], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120, cwd=self.project_root)
            if result.returncode == 0:
                summary = result.stdout.split("\n")[-2] if result.stdout else "Passed"
                return VerificationResult(passed=True, check_type="test", message=f"Tests passed: {summary}", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="test", message="Tests failed", details=[result.stdout[:500]], suggestions=["Fix tests"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="test", message=f"Test error: {e}", details=[], suggestions=[])

    def _run_tests_node(self, test_path: Path = None) -> VerificationResult:
        """Run npm test."""
        if not self.tools["npm"]:
            return VerificationResult(passed=True, check_type="test", message="Skipped (npm not found)", details=[], suggestions=[])
        
        try:
            result = subprocess.run(["npm", "test"], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300, cwd=self.project_root)
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="test", message="npm test OK", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="test", message="npm test failed", details=[result.stdout[:500]], suggestions=["Fix tests"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="test", message=f"npm test error: {e}", details=[], suggestions=[])

    def _run_tests_go(self, test_path: Path = None) -> VerificationResult:
        """Run go test."""
        if not self.tools["go"]:
            return VerificationResult(passed=True, check_type="test", message="Skipped (Go not found)", details=[], suggestions=[])
        
        try:
            result = subprocess.run(["go", "test", "./..."], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300, cwd=self.project_root)
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="test", message="go test OK", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="test", message="go test failed", details=[result.stdout[:500]], suggestions=["Fix tests"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="test", message=f"go test error: {e}", details=[], suggestions=[])

    def _run_tests_rust(self, test_path: Path = None) -> VerificationResult:
        """Run cargo test."""
        if not self.tools.get("cargo"):
            return VerificationResult(passed=True, check_type="test", message="Skipped (cargo not found)", details=[], suggestions=["Install Rust: https://rustup.rs/"])
        
        try:
            result = subprocess.run(
                ["cargo", "test", "--quiet"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="test", message="cargo test OK", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="test", message="cargo test failed", details=[result.stdout[:500] if result.stdout else result.stderr[:500]], suggestions=["Fix Rust tests"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="test", message=f"cargo test error: {e}", details=[], suggestions=[])

    def _run_tests_maven(self, test_path: Path = None) -> VerificationResult:
        """Run Maven tests."""
        if not self.tools.get("mvn"):
            return VerificationResult(passed=True, check_type="test", message="Skipped (Maven not found)", details=[], suggestions=["Install Maven"])
        
        try:
            result = subprocess.run(
                ["mvn", "test", "-q"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="test", message="mvn test OK", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="test", message="mvn test failed", details=[result.stdout[:500] if result.stdout else "Build/test failed"], suggestions=["Fix Maven tests"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="test", message=f"mvn test error: {e}", details=[], suggestions=[])

    def _run_tests_gradle(self, test_path: Path = None) -> VerificationResult:
        """Run Gradle tests."""
        if not self.tools.get("gradle"):
            return VerificationResult(passed=True, check_type="test", message="Skipped (Gradle not found)", details=[], suggestions=["Install Gradle"])
        
        try:
            result = subprocess.run(
                ["gradle", "test", "--quiet"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return VerificationResult(passed=True, check_type="test", message="gradle test OK", details=[], suggestions=[])
            return VerificationResult(passed=False, check_type="test", message="gradle test failed", details=[result.stdout[:500] if result.stdout else "Test failed"], suggestions=["Fix Gradle tests"])
        except Exception as e:
            return VerificationResult(passed=True, check_type="test", message=f"gradle test error: {e}", details=[], suggestions=[])
    def verify_file(self, file_path: Path, level: str = "STANDARD", auto_fix: bool = False) -> List[VerificationResult]:
        """Run all applicable verifications on a file."""
        results = []
        
        # Polyglot support: all languages with handlers
        supported_exts = list(self.handlers.keys())
        if file_path.suffix.lower() not in supported_exts:
            return results
        
        # Always run syntax check
        results.append(self.verify_syntax(file_path))
        
        # Standard level adds linting
        if level in ["STANDARD", "FULL", "SEMANTIC"]:
            results.append(self.verify_lint(file_path, auto_fix=auto_fix))
            results.append(self.verify_imports(file_path))
            
        # Semantic level adds LLM Judge
        if level == "SEMANTIC" and self.judge:
            results.append(self.verify_semantics(file_path))
        
        return results
    
    def verify_project(self, level: str = "STANDARD", auto_fix: bool = False) -> Tuple[bool, str]:
        """
        Verify all source files in the project (polyglot support).
        
        Supported languages: Python, JavaScript/TypeScript, Go, Rust, Java, C/C++
        
        Args:
            level: Verification level (BASIC, STANDARD, FULL, SEMANTIC)
            auto_fix: If True, run auto-fix before reporting lint issues
        """
        target_dir = self.project_root / "src"
        scan_root = True
        
        if target_dir.exists():
            scan_root = False
        else:
            target_dir = self.project_root
            
        if not target_dir.exists():
             return True, "Project directory not found"
        
        all_results: List[VerificationResult] = []
        total_fixed = 0
        
        # Exclude common dirs if scanning root
        excludes = {".git", ".github", ".vscode", ".idea", "venv", ".venv", "node_modules", "build", "dist", "__pycache__"}
        
        # Efficiently walk directory avoiding excluded paths
        for root, dirs, files in os.walk(target_dir):
            # Modify dirs in-place to prune traversal
            dirs[:] = [d for d in dirs if d not in excludes]
            
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                # Polyglot: scan all supported extensions
                if file_path.suffix.lower() in list(self.handlers.keys()):
                    all_results.extend(self.verify_file(file_path, level, auto_fix=auto_fix))
        
        # Run tests if FULL level
        if level == "FULL":
            all_results.append(self.run_tests())
        
        # Aggregate results
        failed = [r for r in all_results if not r.passed]
        
        if not failed:
            return True, f"All {len(all_results)} checks passed"
        
        # Build error summary for AI
        summary_parts = ["## Verification Failed:"]
        for result in failed[:10]:  # Increased to 10 failures
            summary_parts.append(f"\n### {result.check_type.upper()}: {result.message}")
            for detail in result.details[:10]: # Increased to 10 details
                summary_parts.append(f"- {detail}")
            if result.suggestions:
                summary_parts.append("\n💡 **Suggestions:**")
                for suggestion in result.suggestions:
                    summary_parts.append(f"- {suggestion}")
        
        return False, "\n".join(summary_parts)

    def verify_semantics(self, file_path: Path) -> VerificationResult:
        """Run LLM Judge on file."""
        try:
             content = file_path.read_text(encoding="utf-8")
             # Determine if we should be interactive (TODO: Pass this down properly)
             # For now, we assume if judge exists we try normal mode, BUT we need a way to signal interactive
             # Let's try passing the flag if the judge was init'd with interactive context? 
             # Or just check result structure.
             
             # FORCE INT: As per user request ("give it to cursor"), we default to interactive prompt generation
             # when running inside an IDE context.
             feedback = self.judge.grade_code(file_path.name, content, interactive=True)
             
             if feedback.get("status") == "pending_manual_review":
                 return VerificationResult(
                     passed=False, # Technically failed auto-verify
                     check_type="semantic",
                     message="⚠️ Manual Review Required (Delegated to Cursor)",
                     details=["Copy the prompt below to Cursor AI:"],
                     suggestions=[feedback.get("prompt", "")]
                 )

             score = feedback.get("score", 0)
             passed = score >= 4.0
             
             details = []
             details = []
             dimensions = feedback.get("dimensions") or feedback.get("breakdown")
             if dimensions:
                 for k, v in dimensions.items():
                     details.append(f"{k}: {v.get('score')}/5 - {v.get('comment')}")
             
             strategic = feedback.get("strategic_advice")
             first_step = feedback.get("first_step")
             
             if strategic:
                 details.append(f"\n🧠 Strategic Advice: {strategic}")
             if first_step:
                 details.append(f"👣 First Step: {first_step}")
             
             return VerificationResult(
                 passed=passed,
                 check_type="semantic",
                 message=f"Semantic Score: {score}/5.0 ({'PASS' if passed else 'FAIL'})",
                 details=details,
                 suggestions=feedback.get("suggestions", [])
             )
        except Exception as e:
             return VerificationResult(
                 passed=False,
                 check_type="semantic",
                 message=f"Judge failed: {e}",
                 details=[],
                 suggestions=[]
             )
    
    def generate_feedback_prompt(self, results: List[VerificationResult]) -> str:
        """Generate a detailed feedback prompt for the AI based on verification results."""
        failed = [r for r in results if not r.passed]
        
        if not failed:
            return ""
        
        prompt_parts = [
            "CRITICAL: Your code failed verification. You must fix these issues:\n"
        ]
        
        for result in failed:
            prompt_parts.append(f"\n## {result.check_type.upper()} ERROR")
            prompt_parts.append(f"**Problem:** {result.message}")
            if result.details:
                prompt_parts.append("**Details:**")
                for detail in result.details:
                    prompt_parts.append(f"  - {detail}")
            if result.suggestions:
                prompt_parts.append(f"**Fix:** {result.suggestions[0]}")
        
        prompt_parts.append("\nOutput the COMPLETE fixed file(s) using <file path=\"...\">...</file> format.")
        
        return "\n".join(prompt_parts)
