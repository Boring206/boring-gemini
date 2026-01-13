# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
The Sentinel (boring watch) - Project OMNI Phase 3
Active assistance by monitoring file system changes.
Refactored in Phase 4 for Polyglot Support via CodeVerifier.
"""

import time
from pathlib import Path
from typing import Optional

from rich.console import Console

from boring.verification.verifier import CodeVerifier

console = Console()

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    Observer = None
    FileSystemEventHandler = object


class BoringEventHandler(FileSystemEventHandler):
    def __init__(self, project_root: Path):
        self.root = project_root
        self.last_run = 0
        self.cooldown = 1.0  # seconds
        # Initialize the Polyglot Verifier
        self.verifier = CodeVerifier(project_root=project_root)

    def on_modified(self, event):
        if event.is_directory:
            return

        # Simple debounce
        current = time.time()
        if current - self.last_run < self.cooldown:
            return

        file_path = Path(event.src_path)
        filename = file_path.name

        # Filter for supported code files (let Verifier decide, but basic filter for perf)
        # Using a broad list of common source extensions
        if not filename.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".java", ".c", ".cpp", ".md", ".json")):
            return

        self.last_run = current
        self._handle_change(file_path)

    def _handle_change(self, file_path: Path):
        console.print(f"\n[bold blue]👀 Sentinel detected change:[/bold blue] {file_path.name}")

        # Delegate to the Polyglot CodeVerifier
        results = self.verifier.verify_file(file_path, level="STANDARD")

        if not results:
            console.print(f"[dim]No checks available for {file_path.suffix}[/dim]")
            return

        # Aggregate pass/fail
        all_passed = all(r.passed for r in results)

        if all_passed:
            console.print("[green]✅ Clean[/green]")
        else:
            console.print(f"[red]❌ Issues detected in {file_path.name}:[/red]")
            for r in results:
                if not r.passed:
                    console.print(f"  [bold red]{r.check_type.upper()}:[/bold red] {r.message}")
                    for detail in r.details:
                        console.print(f"    - {detail}")

            console.print("\n👉 [bold cyan]boring fix[/bold cyan] [dim]to auto-repair[/dim]")


def run_watch(project_root: Optional[Path] = None):
    """Start the Sentinel."""
    if Observer is None:
        console.print("[red]Error: 'watchdog' package not installed.[/red]")
        console.print("Run: [cyan]pip install watchdog[/cyan]")
        return

    if project_root is None:
        from boring.core.config import settings
        project_root = settings.PROJECT_ROOT

    console.print(f"[bold green]👁️  The Sentinel is watching {project_root}...[/bold green]")
    console.print("[dim]Polyglot Mode Enabled (Python, JS/TS, Rust, Go, Java, C/C++)[/dim]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    event_handler = BoringEventHandler(project_root)
    observer = Observer()
    observer.schedule(event_handler, str(project_root), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[yellow]Sentinel stopped.[/yellow]")
    observer.join()
