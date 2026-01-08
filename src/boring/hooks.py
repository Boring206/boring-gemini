"""
Git Hooks Module for Boring Local Teams.

Provides pre-commit and pre-push hooks that run Boring verification
before allowing commits/pushes. This implements a local version of
"Boring for Teams" without requiring server infrastructure.
"""

import os
import stat
import sys
from pathlib import Path

from rich.console import Console

console = Console()

# Hook Templates
PRE_COMMIT_HOOK = """#!/bin/sh
# Boring Pre-Commit Hook
# Runs STANDARD verification before each commit

echo "🔍 Boring: Running pre-commit verification..."

# Run boring verify
boring verify --level STANDARD

# Check exit code
if [ $? -ne 0 ]; then
    echo "❌ Boring: Verification failed. Commit blocked."
    echo "   Fix the issues above and try again."
    exit 1
fi

echo "✅ Boring: Verification passed."
exit 0
"""

PRE_PUSH_HOOK = """#!/bin/sh
# Boring Pre-Push Hook
# Runs FULL verification (including tests) before each push

echo "🔍 Boring: Running pre-push verification (FULL)..."

# Run boring verify with FULL level
boring verify --level FULL

# Check exit code
if [ $? -ne 0 ]; then
    echo "❌ Boring: Full verification failed. Push blocked."
    echo "   Fix the issues above and try again."
    exit 1
fi

echo "✅ Boring: Full verification passed. Pushing..."
exit 0
"""

SPEC_GUARD_HOOK = """#!/bin/sh
# Boring Spec Guard Hook
# Ensures code consistency with spec.md before commit

echo "🛡️ Boring: Running Spec Guard..."

# Run boring verify with spec consistency check
boring verify --level STANDARD

# Also run spec analysis if available
if command -v boring &> /dev/null; then
    boring speckit-analyze 2>/dev/null || true
fi

if [ $? -ne 0 ]; then
    echo "❌ Boring: Spec Guard failed. Commit blocked."
    exit 1
fi

echo "✅ Boring: Spec Guard passed."
exit 0
"""

# Polyglot Quick Check Hook - runs language-specific linters on staged files
QUICK_CHECK_HOOK = r"""#!/bin/sh
# Boring Quick Check Hook (Polyglot)
# Fast verification for staged files only (<5 seconds target)

echo "⚡ Boring: Quick check on staged files..."

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    echo "✅ No staged files to check."
    exit 0
fi

FAILED=0

# Python files
PY_FILES=$(echo "$STAGED_FILES" | grep -E '\.py$' || true)
if [ -n "$PY_FILES" ]; then
    echo "🐍 Checking Python files..."
    if command -v ruff &> /dev/null; then
        echo "$PY_FILES" | xargs ruff check --select=E,F,W 2>/dev/null || FAILED=1
    fi
fi

# JavaScript/TypeScript files
JS_FILES=$(echo "$STAGED_FILES" | grep -E '\.(js|jsx|ts|tsx)$' || true)
if [ -n "$JS_FILES" ]; then
    echo "📜 Checking JavaScript/TypeScript files..."
    if command -v eslint &> /dev/null; then
        echo "$JS_FILES" | xargs eslint --max-warnings=0 2>/dev/null || FAILED=1
    fi
fi

# Go files
GO_FILES=$(echo "$STAGED_FILES" | grep -E '\.go$' || true)
if [ -n "$GO_FILES" ]; then
    echo "🐹 Checking Go files..."
    if command -v gofmt &> /dev/null; then
        GOFMT_OUTPUT=$(echo "$GO_FILES" | xargs gofmt -l 2>/dev/null)
        if [ -n "$GOFMT_OUTPUT" ]; then
            echo "Go format issues in: $GOFMT_OUTPUT"
            FAILED=1
        fi
    fi
fi

# Rust files
RS_FILES=$(echo "$STAGED_FILES" | grep -E '\.rs$' || true)
if [ -n "$RS_FILES" ]; then
    echo "🦀 Checking Rust files..."
    if command -v cargo &> /dev/null; then
        cargo check --quiet 2>/dev/null || FAILED=1
    fi
fi

if [ $FAILED -ne 0 ]; then
    echo "❌ Boring: Quick check failed. Fix issues and re-stage."
    exit 1
fi

echo "✅ Boring: Quick check passed."
exit 0
"""


class HooksManager:
    """Manages Git hooks installation and removal."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.git_dir = self.project_root / ".git"
        self.hooks_dir = self.git_dir / "hooks"

    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        return self.git_dir.exists() and self.git_dir.is_dir()

    def install_hook(self, hook_name: str, content: str) -> tuple[bool, str]:
        """Install a single Git hook."""
        if not self.is_git_repo():
            return False, "Not a Git repository. Run 'git init' first."

        # Ensure hooks directory exists
        self.hooks_dir.mkdir(exist_ok=True)

        hook_path = self.hooks_dir / hook_name

        # Check for existing hook
        if hook_path.exists():
            # Backup existing hook
            backup_path = hook_path.with_suffix(".backup")
            hook_path.rename(backup_path)
            console.print(f"[yellow]Backed up existing {hook_name} to {hook_name}.backup[/yellow]")

        # Get absolute path to current python executable
        # Ensure forward slashes for shell script compatibility (even on Windows)
        python_exe = sys.executable.replace("\\", "/")

        # Replace 'boring' command with explicit python module invocation
        # This ensures the hook runs in the same environment where it was installed
        final_content = content.replace("boring verify", f'"{python_exe}" -m boring verify')
        final_content = final_content.replace(
            "boring speckit-analyze", f'"{python_exe}" -m boring speckit-analyze'
        )

        # Replace existence check
        check_cmd = f'"{python_exe}" -m boring --help'
        final_content = final_content.replace("command -v boring", check_cmd)

        # Write new hook
        hook_path.write_text(final_content, encoding="utf-8")

        # Make executable (Unix systems)
        try:
            current_mode = os.stat(hook_path).st_mode
            os.chmod(hook_path, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass  # Windows doesn't need this

        return True, f"Installed {hook_name} hook."

    def install_all(self) -> tuple[bool, str]:
        """Install all Boring hooks."""
        if not self.is_git_repo():
            return False, "Not a Git repository. Run 'git init' first."

        results = []

        # Install pre-commit
        success, msg = self.install_hook("pre-commit", PRE_COMMIT_HOOK)
        results.append(msg)

        # Install pre-push
        success, msg = self.install_hook("pre-push", PRE_PUSH_HOOK)
        results.append(msg)

        return True, "\n".join(results)

    def uninstall_hook(self, hook_name: str) -> tuple[bool, str]:
        """Remove a Boring hook (restores backup if exists)."""
        hook_path = self.hooks_dir / hook_name
        backup_path = hook_path.with_suffix(".backup")

        if not hook_path.exists():
            return False, f"No {hook_name} hook found."

        hook_path.unlink()

        # Restore backup if exists
        if backup_path.exists():
            backup_path.rename(hook_path)
            return True, f"Removed Boring {hook_name} and restored backup."

        return True, f"Removed Boring {hook_name} hook."

    def uninstall_all(self) -> tuple[bool, str]:
        """Remove all Boring hooks."""
        results = []

        for hook_name in ["pre-commit", "pre-push"]:
            success, msg = self.uninstall_hook(hook_name)
            results.append(msg)

        return True, "\n".join(results)

    def status(self) -> dict:
        """Get status of installed hooks."""
        status = {"is_git_repo": self.is_git_repo(), "hooks": {}}

        if not self.is_git_repo():
            return status

        for hook_name in ["pre-commit", "pre-push"]:
            hook_path = self.hooks_dir / hook_name
            if hook_path.exists():
                content = hook_path.read_text(encoding="utf-8", errors="ignore")
                is_boring = "Boring" in content
                status["hooks"][hook_name] = {"installed": True, "is_boring_hook": is_boring}
            else:
                status["hooks"][hook_name] = {"installed": False, "is_boring_hook": False}

        return status
