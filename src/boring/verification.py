"""
Boring Verification System

Implements rules-based verification for generated code:
- Syntax checking (Python compile)
- Linting (ruff if available)
- Testing (pytest if available)
- Import validation
"""

import subprocess
import sys
import re
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
    Comprehensive code verification system.
    
    Verification levels:
    1. BASIC: Syntax check only (fast, always available)
    2. STANDARD: Syntax + Linting (requires ruff)
    3. FULL: Syntax + Linting + Tests (requires pytest)
    """
    
    def __init__(self, project_root: Path = None, log_dir: Path = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.log_dir = log_dir or settings.LOG_DIR
        
        # Check available tools
        self.has_ruff = self._check_tool("ruff", "--version")
        self.has_pytest = self._check_tool("pytest", "--version")
    
    def _check_tool(self, tool: str, version_arg: str) -> bool:
        """Check if a tool is available."""
        try:
            result = subprocess.run(
                [tool, version_arg],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def verify_syntax(self, file_path: Path) -> VerificationResult:
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
    
    def verify_lint(self, file_path: Path) -> VerificationResult:
        """Run ruff linter on a file."""
        if not self.has_ruff:
            return VerificationResult(
                passed=True,
                check_type="lint",
                message="Linting skipped (ruff not available)",
                details=[],
                suggestions=["Install ruff: pip install ruff"]
            )
        
        try:
            result = subprocess.run(
                ["ruff", "check", str(file_path), "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return VerificationResult(
                    passed=True,
                    check_type="lint",
                    message=f"Lint OK: {file_path.name}",
                    details=[],
                    suggestions=[]
                )
            else:
                # Parse ruff output
                issues = result.stdout.strip().split("\n") if result.stdout else []
                return VerificationResult(
                    passed=False,
                    check_type="lint",
                    message=f"Lint issues in {file_path.name}",
                    details=issues[:10],  # Limit to 10 issues
                    suggestions=["Run 'ruff check --fix' to auto-fix some issues"]
                )
        except Exception as e:
            return VerificationResult(
                passed=True,  # Don't fail on linting errors
                check_type="lint",
                message=f"Lint check error: {e}",
                details=[],
                suggestions=[]
            )
    
    def verify_imports(self, file_path: Path) -> VerificationResult:
        """Check if all imports are resolvable."""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Extract import statements
            import_pattern = r'^(?:from\s+([\w.]+)\s+)?import\s+([\w.]+(?:\s*,\s*[\w.]+)*)'
            imports = re.findall(import_pattern, content, re.MULTILINE)
            
            missing_imports = []
            for from_module, import_names in imports:
                module = from_module or import_names.split(",")[0].strip()
                
                # Skip relative imports and standard library
                if module.startswith(".") or module in sys.stdlib_module_names:
                    continue
                
                # Check if module exists
                try:
                    __import__(module.split(".")[0])
                except ImportError:
                    missing_imports.append(module)
            
            if missing_imports:
                return VerificationResult(
                    passed=False,
                    check_type="import",
                    message=f"Missing imports in {file_path.name}",
                    details=[f"Cannot import: {m}" for m in missing_imports[:5]],
                    suggestions=[f"pip install {m.split('.')[0]}" for m in missing_imports[:3]]
                )
            
            return VerificationResult(
                passed=True,
                check_type="import",
                message=f"Imports OK: {file_path.name}",
                details=[],
                suggestions=[]
            )
        except Exception as e:
            return VerificationResult(
                passed=True,
                check_type="import",
                message=f"Import check skipped: {e}",
                details=[],
                suggestions=[]
            )
    
    def run_tests(self, test_path: Path = None) -> VerificationResult:
        """Run pytest on the project or specific path."""
        if not self.has_pytest:
            return VerificationResult(
                passed=True,
                check_type="test",
                message="Testing skipped (pytest not available)",
                details=[],
                suggestions=["Install pytest: pip install pytest"]
            )
        
        test_target = test_path or (self.project_root / "tests")
        if not test_target.exists():
            return VerificationResult(
                passed=True,
                check_type="test",
                message="No tests directory found",
                details=[],
                suggestions=["Create a tests/ directory with test files"]
            )
        
        try:
            result = subprocess.run(
                ["pytest", str(test_target), "-v", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                # Extract passed count
                summary = result.stdout.split("\n")[-2] if result.stdout else ""
                return VerificationResult(
                    passed=True,
                    check_type="test",
                    message=f"Tests passed: {summary}",
                    details=[],
                    suggestions=[]
                )
            else:
                # Parse failed tests
                failed_lines = [l for l in result.stdout.split("\n") if "FAILED" in l][:5]
                return VerificationResult(
                    passed=False,
                    check_type="test",
                    message="Some tests failed",
                    details=failed_lines,
                    suggestions=["Fix failing tests before continuing"]
                )
        except subprocess.TimeoutExpired:
            return VerificationResult(
                passed=False,
                check_type="test",
                message="Tests timed out",
                details=["Tests took longer than 120 seconds"],
                suggestions=["Check for infinite loops or hanging tests"]
            )
        except Exception as e:
            return VerificationResult(
                passed=True,
                check_type="test",
                message=f"Test check error: {e}",
                details=[],
                suggestions=[]
            )
    
    def verify_file(self, file_path: Path, level: str = "STANDARD") -> List[VerificationResult]:
        """Run all applicable verifications on a file."""
        results = []
        
        if not file_path.suffix == ".py":
            return results
        
        # Always run syntax check
        results.append(self.verify_syntax(file_path))
        
        # Standard level adds linting
        if level in ["STANDARD", "FULL"]:
            results.append(self.verify_lint(file_path))
            results.append(self.verify_imports(file_path))
        
        return results
    
    def verify_project(self, level: str = "STANDARD") -> Tuple[bool, str]:
        """
        Verify all Python files in the project.
        
        Returns:
            (all_passed, summary_message)
        """
        src_dir = self.project_root / "src"
        if not src_dir.exists():
            return True, "No src directory found"
        
        all_results: List[VerificationResult] = []
        
        for py_file in src_dir.rglob("*.py"):
            all_results.extend(self.verify_file(py_file, level))
        
        # Run tests if FULL level
        if level == "FULL":
            all_results.append(self.run_tests())
        
        # Aggregate results
        failed = [r for r in all_results if not r.passed]
        
        if not failed:
            return True, f"All {len(all_results)} checks passed"
        
        # Build error summary for AI
        summary_parts = ["## Verification Failed:"]
        for result in failed[:5]:  # Limit to 5 failures
            summary_parts.append(f"\n### {result.check_type.upper()}: {result.message}")
            for detail in result.details[:3]:
                summary_parts.append(f"- {detail}")
            if result.suggestions:
                summary_parts.append(f"💡 Suggestion: {result.suggestions[0]}")
        
        return False, "\n".join(summary_parts)
    
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
