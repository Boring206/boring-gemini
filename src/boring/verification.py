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
    Comprehensive code verification system.
    
    Verification levels:
    1. BASIC: Syntax check only (fast, always available)
    2. STANDARD: Syntax + Linting (requires ruff)
    3. FULL: Syntax + Linting + Tests (requires pytest)
    """
    
    def __init__(self, project_root: Path = None, log_dir: Path = None, judge = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.log_dir = log_dir or settings.LOG_DIR
        self.judge = judge
        
        # Check available tools
        self.has_ruff = self._check_tool("ruff", "--version")
        self.has_pytest = self._check_tool("pytest", "--version")
    
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
    
    def verify_lint(self, file_path: Path, auto_fix: bool = False) -> VerificationResult:
        """Run ruff linter on a file, optionally auto-fixing issues first."""
        if not self.has_ruff:
            return VerificationResult(
                passed=True,
                check_type="lint",
                message="Linting skipped (ruff not available)",
                details=[],
                suggestions=["Install ruff: pip install ruff"]
            )
        
        fixed_count = 0
        
        # Auto-fix if requested
        if auto_fix:
            try:
                fix_result = subprocess.run(
                    ["ruff", "check", str(file_path), "--fix", "--unsafe-fixes"],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.project_root
                )
                # Count fixed issues from output
                if "Fixed" in fix_result.stdout:
                    import re
                    match = re.search(r"Fixed (\d+)", fix_result.stdout)
                    if match:
                        fixed_count = int(match.group(1))
            except Exception:
                pass  # Continue with normal check
        
        try:
            result = subprocess.run(
                ["ruff", "check", str(file_path), "--output-format", "concise"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                message = f"Lint OK: {file_path.name}"
                if fixed_count > 0:
                    message = f"Lint OK: {file_path.name} (auto-fixed {fixed_count} issues)"
                return VerificationResult(
                    passed=True,
                    check_type="lint",
                    message=message,
                    details=[],
                    suggestions=[]
                )
            else:
                # Parse ruff output
                issues = result.stdout.strip().split("\n") if result.stdout else []
                if not issues and result.stderr:
                    issues = [f"Error: {result.stderr.strip()}"]
                
                details = issues[:20]
                if fixed_count > 0:
                    details.insert(0, f"✅ Auto-fixed {fixed_count} issues")
                
                return VerificationResult(
                    passed=False,
                    check_type="lint",
                    message=f"Lint issues in {file_path.name}",
                    details=details,
                    suggestions=["Remaining issues require manual fix" if auto_fix else "Run 'ruff check --fix' to auto-fix some issues"]
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
                stdin=subprocess.DEVNULL,
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
    
    def verify_file(self, file_path: Path, level: str = "STANDARD", auto_fix: bool = False) -> List[VerificationResult]:
        """Run all applicable verifications on a file."""
        results = []
        
        if not file_path.suffix == ".py":
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
        Verify all Python files in the project.
        
        Args:
            level: Verification level (BASIC, STANDARD, FULL, SEMANTIC)
            auto_fix: If True, run ruff --fix before reporting lint issues
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
                if file.endswith(".py"):
                    file_path = root_path / file
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
             if "breakdown" in feedback:
                 for k, v in feedback["breakdown"].items():
                     details.append(f"{k}: {v.get('score')}/5 - {v.get('comment')}")
             
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
