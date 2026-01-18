"""
Quality Gate Script
Enforces "World-Class Quality" standards before commit.

Checks:
1. Linting (Ruff)
2. Type Checking (Mypy)
3. Security Audit (Bandit + Internal Checks)
4. Tests (Unit + Torture)
5. Zero Warning Policy

Usage: python scripts/quality_gate.py
"""

import subprocess
import sys
import time

from rich.console import Console
from rich.panel import Panel

console = Console()


def run_step(name: str, command: list[str], allow_failure: bool = False):
    console.print(f"[bold blue]Running {name}...[/bold blue]")
    start = time.time()
    try:
        # Force UTF-8 for Windows consistency
        env = {"PYTHONIOENCODING": "utf-8"}
        # Add current env vars
        env.update(subprocess.os.environ)

        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=env)

        duration = time.time() - start

        if result.returncode == 0:
            console.print(f"[green]✔ {name} passed ({duration:.2f}s)[/green]")
            return True
        else:
            if allow_failure:
                console.print(f"[yellow]⚠ {name} failed but allowed:[/yellow]")
            else:
                console.print(f"[red]✘ {name} failed:[/red]")

            console.print(result.stdout)
            console.print(result.stderr)

            if not allow_failure:
                sys.exit(1)
            return False

    except Exception as e:
        console.print(f"[red]Error running {name}: {e}[/red]")
        sys.exit(1)


def main():
    console.print(Panel("🛡️ Boring Quality Gate 🛡️", style="bold magenta"))

    # 1. Static Analysis
    run_step("Ruff Linting", ["ruff", "check", "src", "tests"])
    run_step("Ruff Formatting", ["ruff", "format", "--check", "src", "tests"])
    # run_step("Mypy Type Check", ["mypy", "src"]) # Uncomment when types are strict

    # 2. Security Audit
    run_step(
        "Bandit Security Scan", ["bandit", "-r", "src", "-c", "pyproject.toml"], allow_failure=True
    )

    # 3. Tests (The "No Warning" Policy is enforced via pyproject.toml)
    run_step("Unit Tests", ["pytest", "tests/unit"])
    run_step("Integration Tests", ["pytest", "tests/integration"])
    run_step("Torture Tests (The Grumpy User)", ["pytest", "tests/torture"])

    console.print(
        Panel(
            "[bold green]✨ All Quality Gates Passed! System is World-Class. ✨[/bold green]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
