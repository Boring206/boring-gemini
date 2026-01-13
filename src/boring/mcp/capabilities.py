# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
MCP Capabilities Detection - Context-Aware Feature Gating (V11.4.1)

This module detects the current project context to determine which
MCP tool sets should be exposed to the agent.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ProjectCapabilities:
    """Detected capabilities of the current project context."""

    # Tech Stacks
    is_python: bool = False
    is_node: bool = False
    is_rust: bool = False
    is_go: bool = False

    # Version Control
    is_git: bool = False

    # Environment
    is_windows: bool = (os.name == "nt")
    has_boring_config: bool = False

    # Metadata
    root_path: Path = field(default_factory=Path.cwd)
    detected_at: float = field(default_factory=lambda: getattr(os.times(), "elapsed", 0.0))

    def summary(self) -> str:
        """Return a human-readable summary of detected capabilities."""
        stacks = []
        if self.is_python:
            stacks.append("Python")
        if self.is_node:
            stacks.append("Node.js")
        if self.is_rust:
            stacks.append("Rust")
        if self.is_go:
            stacks.append("Go")

        vcs = "Git" if self.is_git else "None"

        return f"Stack: {', '.join(stacks) if stacks else 'Generic'} | VCS: {vcs} | OS: {'Windows' if self.is_windows else 'POSIX'}"


def detect_project_capabilities(root: Optional[Path] = None) -> ProjectCapabilities:
    """
    Detect project capabilities starting from the given root.
    """
    from .utils import detect_project_root

    # 1. Detect Project Root
    if root is None:
        root_path = detect_project_root() or Path.cwd()
    else:
        root_path = root

    caps = ProjectCapabilities(root_path=root_path)

    # 2. Detect Tech Stacks
    if (root_path / "pyproject.toml").exists() or (root_path / "setup.py").exists() or (root_path / "requirements.txt").exists():
        caps.is_python = True

    if (root_path / "package.json").exists():
        caps.is_node = True

    if (root_path / "Cargo.toml").exists():
        caps.is_rust = True

    if (root_path / "go.mod").exists():
        caps.is_go = True

    # 3. Detect VCS
    if (root_path / ".git").exists():
        caps.is_git = True
    else:
        # Check parent directories for git root if we are in a subfolder
        try:
            current = root_path
            for _ in range(5): # Limit upward search
                if (current / ".git").exists():
                    caps.is_git = True
                    break
                if current.parent == current:
                    break
                current = current.parent
        except Exception:
            pass

    # 4. Detect Boring Config
    if (root_path / ".boring.toml").exists() or (root_path / "boring.toml").exists():
        caps.has_boring_config = True

    return caps


# Global cache
_cached_caps: Optional[ProjectCapabilities] = None

def get_capabilities(refresh: bool = False) -> ProjectCapabilities:
    """Get detected capabilities (cached)."""
    global _cached_caps
    if _cached_caps is None or refresh:
        _cached_caps = detect_project_capabilities()
    return _cached_caps
