# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

import time

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()
app = typer.Typer(help="Interactive Boring Tutorial 2.0")

TUTORIAL_STEPS = [
    {
        "title": "Welcome to Boring!",
        "content": """
# Welcome, Agent! 🕵️

Boring is your autonomous AI coding partner. This tutorial will guide you through the basics.

**Goal**: Complete 3 missions to earn your "Cadet" badge.
""",
        "action": None,
    },
    {
        "title": "Mission 1: The Setup",
        "content": """
### Mission 1: Configuration

Boring needs to know your environment.

Run `boring wizard` to auto-detect your tools.
(We'll simulate this for the tutorial)
""",
        "action": "Simulating wizard scan...",
    },
    {
        "title": "Mission 2: Design Phase",
        "content": """
### Mission 2: One Dragon Flow

Boring uses a "One Dragon" flow: `Design -> Implement -> Polish`.

In Design mode, we plan before we code.
""",
        "action": "Analyzing requirements...",
    },
    {
        "title": "Mission 3: The Brain",
        "content": """
### Mission 3: Knowledge Persistence

Boring learns from mistakes. It saves patterns to `~/.boring/brain`.

Next time you encounter a similar error, Boring will auto-fix it!
""",
        "action": "Saving synaptic pattern...",
    },
]


@app.command()
def start():
    """Start the interactive tutorial."""
    console.print(
        Panel("[bold green]🎮 Level 0: Loading Simulation...[/bold green]", border_style="green")
    )
    time.sleep(1)

    score = 0

    for i, step in enumerate(TUTORIAL_STEPS):
        console.clear()
        console.print(
            Panel(
                Markdown(step["content"]),
                title=f"[bold blue]{step['title']}[/bold blue]",
                border_style="blue",
            )
        )

        if step["action"]:
            with console.status(f"[yellow]{step['action']}[/yellow]"):
                time.sleep(2)
            console.print(f"[green]✔ {step['action']} Complete![/green]")
            score += 100

        if i < len(TUTORIAL_STEPS) - 1:
            if not Confirm.ask("Ready for next mission?"):
                console.print("[red]Mission Aborted.[/red]")
                return

    console.clear()
    console.print(
        Panel(
            f"""
# 🎉 Mission Accomplished!

**Score**: {score} XP
**Rank**: 🎖️ Cadet

You are now ready to use Boring for real projects.
Try running: [cyan]boring start[/cyan]
""",
            title="[bold gold1]Tutorial Complete[/bold gold1]",
            border_style="gold1",
        )
    )


if __name__ == "__main__":
    app()
