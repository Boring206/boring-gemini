"""
Git Hooks Module for Boring Local Teams.

Provides pre-commit and pre-push hooks that run Boring verification
before allowing commits/pushes. This implements a local version of
"Boring for Teams" without requiring server infrastructure.
"""

import os
import stat
from pathlib import Path
from typing import Tuple
from rich.console import Console

console = Console()

# Hook Templates
PRE_COMMIT_HOOK = '''#!/bin/sh
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
'''

PRE_PUSH_HOOK = '''#!/bin/sh
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
'''

SPEC_GUARD_HOOK = '''#!/bin/sh
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
'''


class HooksManager:
    """Manages Git hooks installation and removal."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.git_dir = self.project_root / ".git"
        self.hooks_dir = self.git_dir / "hooks"
        
    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        return self.git_dir.exists() and self.git_dir.is_dir()
    
    def install_hook(self, hook_name: str, content: str) -> Tuple[bool, str]:
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
        
        # Write new hook
        hook_path.write_text(content, encoding="utf-8")
        
        # Make executable (Unix systems)
        try:
            current_mode = os.stat(hook_path).st_mode
            os.chmod(hook_path, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass  # Windows doesn't need this
            
        return True, f"Installed {hook_name} hook."
    
    def install_all(self) -> Tuple[bool, str]:
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
    
    def uninstall_hook(self, hook_name: str) -> Tuple[bool, str]:
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
    
    def uninstall_all(self) -> Tuple[bool, str]:
        """Remove all Boring hooks."""
        results = []
        
        for hook_name in ["pre-commit", "pre-push"]:
            success, msg = self.uninstall_hook(hook_name)
            results.append(msg)
        
        return True, "\n".join(results)
    
    def status(self) -> dict:
        """Get status of installed hooks."""
        status = {
            "is_git_repo": self.is_git_repo(),
            "hooks": {}
        }
        
        if not self.is_git_repo():
            return status
        
        for hook_name in ["pre-commit", "pre-push"]:
            hook_path = self.hooks_dir / hook_name
            if hook_path.exists():
                content = hook_path.read_text(encoding="utf-8", errors="ignore")
                is_boring = "Boring" in content
                status["hooks"][hook_name] = {
                    "installed": True,
                    "is_boring_hook": is_boring
                }
            else:
                status["hooks"][hook_name] = {
                    "installed": False,
                    "is_boring_hook": False
                }
        
        return status
