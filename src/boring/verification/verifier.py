import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from ..cache import VerificationCache
from ..config import settings
from ..logger import logger
from ..models import VerificationResult
from . import handlers, test_runners
from .config import load_custom_rules
from .tools import ToolManager


class CodeVerifier:
    """
    Polyglot code verification system.
    Refactored in V10.15 for better modularity.
    """

    def __init__(
        self, project_root: Path = None, log_dir: Path = None, judge=None, use_cache: bool = True
    ):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.log_dir = log_dir or settings.LOG_DIR
        self.judge = judge
        self.cache = VerificationCache(self.project_root) if use_cache else None

        self.custom_rules = load_custom_rules(self.project_root)
        self.tools = ToolManager()

        # Dispatch configuration
        self.handlers = {
            ".py": {
                "syntax": handlers.verify_syntax_python,
                "lint": handlers.verify_lint_python,
                "import": handlers.verify_imports_python,
            },
            ".js": {
                "syntax": handlers.verify_syntax_node,
                "lint": handlers.verify_lint_node,
                "import": handlers.verify_imports_node,
            },
            ".jsx": {
                "syntax": handlers.verify_syntax_node,
                "lint": handlers.verify_lint_node,
                "import": handlers.verify_imports_node,
            },
            ".ts": {
                "syntax": handlers.verify_syntax_node,
                "lint": handlers.verify_lint_node,
                "import": handlers.verify_imports_node,
            },
            ".tsx": {
                "syntax": handlers.verify_syntax_node,
                "lint": handlers.verify_lint_node,
                "import": handlers.verify_imports_node,
            },
            ".go": {
                "syntax": handlers.verify_syntax_go,
                "lint": handlers.verify_lint_generic,
                "import": handlers.verify_imports_go,
            },
            ".rs": {
                "syntax": handlers.verify_syntax_rust,
                "lint": handlers.verify_lint_generic,
                "import": None,
            },
            ".java": {
                "syntax": handlers.verify_syntax_java,
                "lint": handlers.verify_lint_generic,
                "import": None,
            },
            ".c": {
                "syntax": handlers.verify_syntax_c,
                "lint": handlers.verify_lint_generic,
                "import": None,
            },
            ".cpp": {
                "syntax": handlers.verify_syntax_cpp,
                "lint": handlers.verify_lint_generic,
                "import": None,
            },
            ".h": {
                "syntax": handlers.verify_syntax_c,
                "lint": handlers.verify_lint_generic,
                "import": None,
            },
            ".hpp": {
                "syntax": handlers.verify_syntax_cpp,
                "lint": handlers.verify_lint_generic,
                "import": None,
            },
        }

    def verify_syntax(self, file_path: Path) -> VerificationResult:
        """Check syntax based on file extension."""
        ext = file_path.suffix.lower()
        handler = self.handlers.get(ext)
        if handler and handler.get("syntax"):
            return handler["syntax"](file_path, self.project_root, self.tools)
        return VerificationResult(
            passed=True, check_type="syntax", message=f"Skipped: {ext}", details=[], suggestions=[]
        )

    def verify_lint(self, file_path: Path, auto_fix: bool = False) -> VerificationResult:
        """Run linter based on file extension."""
        ext = file_path.suffix.lower()
        handler = self.handlers.get(ext)
        if handler and handler.get("lint"):
            return handler["lint"](file_path, self.project_root, self.tools, auto_fix=auto_fix)
        return VerificationResult(
            passed=True, check_type="lint", message="Skipped", details=[], suggestions=[]
        )

    def verify_imports(self, file_path: Path) -> VerificationResult:
        """Check imports based on file extension."""
        ext = file_path.suffix.lower()
        handler = self.handlers.get(ext)
        if handler and handler.get("import"):
            func = handler["import"]
            if ext == ".go":
                return func(file_path, self.project_root, self.tools)
            return func(file_path, self.project_root)
        return VerificationResult(
            passed=True, check_type="import", message="Skipped", details=[], suggestions=[]
        )

    def _verify_lint_generic(self, file_path: Path) -> VerificationResult:
        """Compatibility wrapper for handlers.verify_lint_generic."""
        return handlers.verify_lint_generic(file_path, self.project_root, self.tools)

    def verify_file(
        self, file_path: Path, level: str = "STANDARD", auto_fix: bool = False
    ) -> list[VerificationResult]:
        """Run all applicable verifications on a file."""
        results = []
        ext = file_path.suffix.lower()
        if ext not in self.handlers:
            return results

        # Always run syntax check
        results.append(self.verify_syntax(file_path))

        # Standard level adds linting and imports
        if level in ["STANDARD", "FULL", "SEMANTIC"]:
            results.append(self.verify_lint(file_path, auto_fix=auto_fix))
            results.append(self.verify_imports(file_path))

        if level == "SEMANTIC" and self.judge:
            results.append(self.verify_semantics(file_path))

        return results

    def verify_semantics(self, file_path: Path) -> VerificationResult:
        """Run LLM Judge on file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            feedback = self.judge.grade_code(file_path.name, content, interactive=True)

            if feedback.get("status") == "pending_manual_review":
                return VerificationResult(
                    passed=False,
                    check_type="semantic",
                    message="⚠️ Manual Review Required (Delegated to Cursor)",
                    details=["Copy the prompt below to Cursor AI:"],
                    suggestions=[feedback.get("prompt", "")],
                )

            score = feedback.get("score", 0)
            passed = score >= 4.0

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
                suggestions=feedback.get("suggestions", []),
            )
        except Exception as e:
            return VerificationResult(
                passed=False,
                check_type="semantic",
                message=f"Judge failed: {e}",
                details=[],
                suggestions=[],
            )

    def run_tests(self, test_path: Path = None) -> VerificationResult:
        """Run tests based on project type."""
        # Detect project type
        if (self.project_root / "Cargo.toml").exists():
            return test_runners.run_tests_rust(self.project_root, self.tools, test_path)
        elif (self.project_root / "pom.xml").exists():
            return test_runners.run_tests_maven(self.project_root, self.tools, test_path)
        elif (self.project_root / "build.gradle").exists() or (
            self.project_root / "build.gradle.kts"
        ).exists():
            return test_runners.run_tests_gradle(self.project_root, self.tools, test_path)
        elif (self.project_root / "package.json").exists():
            return test_runners.run_tests_node(self.project_root, self.tools, test_path)
        elif (self.project_root / "go.mod").exists():
            return test_runners.run_tests_go(self.project_root, self.tools, test_path)

        return test_runners.run_tests_python(self.project_root, self.tools, test_path)

    def _aggregate_results(
        self, file_path: Path, results: list[VerificationResult]
    ) -> VerificationResult:
        passed = all(r.passed for r in results)
        details = []
        suggestions = []
        messages = []
        for r in results:
            if not r.passed:
                messages.append(f"{r.check_type}: {r.message}")
            details.extend(r.details)
            suggestions.extend(r.suggestions)

        return VerificationResult(
            passed=passed,
            check_type="file_comparison",
            message="; ".join(messages) if messages else f"All checks passed: {file_path.name}",
            details=details,
            suggestions=list(set(suggestions)),
        )

    def _get_git_changed_files(self) -> list[Path]:
        """Get list of files changed in Git."""
        try:
            staged = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            unstaged = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            changed = set()
            for output in [staged.stdout, unstaged.stdout]:
                for line in output.strip().split("\n"):
                    if line:
                        changed.add(self.project_root / line)
            return list(changed)
        except Exception:
            return []

    def verify_project(
        self,
        level: str = "STANDARD",
        auto_fix: bool = False,
        max_workers: int = 4,
        force: bool = False,
        incremental: bool = False,
    ) -> tuple[bool, str]:
        target_dir = self.project_root / "src"
        if not target_dir.exists():
            target_dir = self.project_root
        if not target_dir.exists():
            return True, "Project directory not found"

        all_results: list[VerificationResult] = []
        excludes = set(settings.VERIFICATION_EXCLUDES)

        target_files = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in excludes]
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in list(self.handlers.keys()):
                    target_files.append(file_path)

        if incremental:
            git_changed = self._get_git_changed_files()
            if git_changed:
                target_files = [f for f in target_files if f in git_changed]
            if not target_files:
                return True, "No changed files to verify (incremental mode)"

        files_to_verify = []
        if self.cache and not force:
            for f in target_files:
                cached = self.cache.get(f)
                if cached:
                    all_results.append(cached)
                else:
                    files_to_verify.append(f)
        else:
            files_to_verify = target_files

        cache_updates = {}
        if files_to_verify:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                transient=True,
            ) as progress:
                task_id = progress.add_task(
                    f"Verifying {len(files_to_verify)} files...", total=len(files_to_verify)
                )
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_file = {
                        executor.submit(self.verify_file, f, level, auto_fix=auto_fix): f
                        for f in files_to_verify
                    }
                    for future in as_completed(future_to_file):
                        file_path = future_to_file[future]
                        progress.advance(task_id)
                        try:
                            results = future.result()
                            all_results.extend(results)
                            if self.cache:
                                aggregate = self._aggregate_results(file_path, results)
                                cache_updates[file_path] = aggregate
                        except Exception as e:
                            logger.error(f"Error verifying {file_path}: {e}")

        if self.cache and cache_updates:
            self.cache.bulk_update(cache_updates)

        if level == "FULL":
            all_results.append(self.run_tests())

        failed = [r for r in all_results if not r.passed]
        if not failed:
            return True, f"All {len(all_results)} checks passed"

        summary_parts = ["## Verification Failed:"]
        for result in failed[:10]:
            summary_parts.append(f"\n### {result.check_type.upper()}: {result.message}")
            for detail in result.details[:10]:
                summary_parts.append(f"- {detail}")
            if result.suggestions:
                summary_parts.append("\n💡 **Suggestions:**")
                for suggestion in result.suggestions:
                    summary_parts.append(f"- {suggestion}")

        return False, "\n".join(summary_parts)

    def generate_feedback_prompt(self, results: list[VerificationResult]) -> str:
        failed = [r for r in results if not r.passed]
        if not failed:
            return ""
        prompt_parts = ["CRITICAL: Your code failed verification. You must fix these issues:\n"]
        for result in failed:
            prompt_parts.append(f"\n## {result.check_type.upper()} ERROR")
            prompt_parts.append(f"**Problem:** {result.message}")
            if result.details:
                prompt_parts.append("**Details:**")
                for detail in result.details:
                    prompt_parts.append(f"  - {detail}")
            if result.suggestions:
                prompt_parts.append(f"**Fix:** {result.suggestions[0]}")
        prompt_parts.append(
            '\nOutput the COMPLETE fixed file(s) using <file path="...">...</file> format.'
        )
        return "\n".join(prompt_parts)
