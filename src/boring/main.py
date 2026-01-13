# Copyright 2025-2026 Frank Bria & Boring206
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from boring.core.config import settings

HELP_TEXT = """
[bold blue]Unified Path Management for Boring (V11.2.2)
 - Enterprise AI Development Agent (MCP)[/bold blue]

A powerful AI coding assistant designed for IDEs (Cursor, VS Code) and Gemini.

[bold yellow]⚠️  Legacy CLI Mode:[/bold yellow]
  Direct usage of `boring start` is deprecated as Gemini CLI auth is no longer supported.
  Please use Boring as an MCP Server in your IDE.

[bold green]✅ Recommended Usage (MCP):[/bold green]
  Configure your IDE to run: `python -m boring.mcp.server`

[bold]🛠️  Maintenance Tools:[/bold]
  $ [cyan]python -m boring hooks install[/cyan]    # Install Git hooks (Best practice)
  $ [cyan]python -m boring dashboard[/cyan]        # Open Web Dashboard
  $ [cyan]pip install tree-sitter-languages[/cyan] # Fix parsing warnings
"""

EPILOG_TEXT = """
[bold]Troubleshooting:[/bold]
  If commands fail, try using [cyan]python -m boring[/cyan] instead of [cyan]boring[/cyan].

  Missing "tree-sitter-languages"?
  $ pip install tree-sitter-languages

[bold]Documentation:[/bold] https://github.com/Boring206/boring-gemini
"""

app = typer.Typer(
    name="boring",
    help=HELP_TEXT,
    epilog=EPILOG_TEXT,
    rich_markup_mode="rich",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    provider: str = typer.Option(
        None, "--provider", "-P", help="LLM Provider: gemini, ollama, openai_compat"
    ),
    base_url: str = typer.Option(None, "--base-url", help="Base URL for local LLM provider"),
    llm_model: str = typer.Option(None, "--llm-model", help="Override default model name"),
):
    """
    Boring - Autonomous AI Development Agent
    """
    # Global settings overrides
    if provider:
        settings.LLM_PROVIDER = provider
    if base_url:
        settings.LLM_BASE_URL = base_url
    if llm_model:
        settings.LLM_MODEL = llm_model

    # V11.2 Lightweight Mode Detection
    import os

    project_root = settings.PROJECT_ROOT
    boring_dir = project_root / ".boring"
    legacy_memory = project_root / ".boring_memory"

    # If no boring structure exists, enable Lazy Mode (Lightweight UX)
    if not boring_dir.exists() and not legacy_memory.exists():
        os.environ["BORING_LAZY_MODE"] = "1"
        # We don't print here to keep output clean, but individual commands might notify.

    # Contextual Onboarding (Project OMNI)
    if ctx.invoked_subcommand is None:
        from boring.cli.tui import run_console
        run_console()


console = Console()


console = Console()


# --- The 5 Commandments (Project OMNI) ---

@app.command()
def go():
    """🚀 Start the One Dragon autonomous workflow (Alias for flow)."""
    flow()


@app.command()
def fix(think: bool = typer.Option(False, "--think", "-t", help="Enable Deep Thinking")):
    """🔧 Auto-repair linting and code errors."""
    _run_one_shot(
        "Fix all linting and code errors in this project",
        thinking_mode=think,
        self_heal=True,
        command_name="fix"
    )


@app.command()
def check(think: bool = typer.Option(False, "--think", "-t", help="Enable Deep Thinking")):
    """✅ Run Vibe Check health scan."""
    _run_one_shot("Run boring_vibe_check", thinking_mode=think, command_name="check")


@app.command()
def save(think: bool = typer.Option(False, "--think", "-t", help="Enable Deep Thinking")):
    """💾 Smart commit with generated message."""
    _run_one_shot("Generate a smart commit message and commit changes", thinking_mode=think, command_name="save")


@app.command()
def guide(query: Optional[str] = typer.Argument(None)):
    """❓ Interactive tool guide and helper."""
    from rich.prompt import Prompt

    from boring.mcp.tool_router import cli_route, get_tool_router

    if query:
        cli_route(query)
        return

    router = get_tool_router()
    router.get_categories_summary()

    q = Prompt.ask("\n[bold]Ask anything:[/bold]")
    if q:
        cli_route(q)


@app.command()
def watch():
    """👁️ Sentinel Mode: Watch for file changes and suggest fixes."""
    from boring.cli.watch import run_watch
    run_watch(settings.PROJECT_ROOT)


@app.command()
def evolve(
    goal: str = typer.Argument(..., help="Evolution goal (e.g. 'Fix all tests')"),
    verify: str = typer.Option("pytest", "--verify", "-v", help="Verification command"),
    steps: int = typer.Option(5, "--steps", "-s", help="Max iterations")
):
    """🧬 God Mode: Autonomous goal-seeking loop."""
    from boring.loop.evolve import run_evolve
    run_evolve(goal, verify, steps)


@app.command()
def flow():
    """
    🐉 Start the One Dragon Workflow (Boring Flow).

    Automatically detects project state and guides you through:
    1. Setup (Constitution)
    2. Design (Plan & Skills)
    3. Build (Execution)
    4. Polish (Verify & Evolve)
    """
    from boring.core.config import settings
    from boring.flow.engine import FlowEngine

    project_root = settings.PROJECT_ROOT
    engine = FlowEngine(project_root)
    engine.run()


@app.command(hidden=True)
def start(
    backend: str = typer.Option(
        "api", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"
    ),
    model: str = typer.Option(settings.DEFAULT_MODEL, "--model", "-m", help="Gemini model to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    verification: str = typer.Option(
        "STANDARD", "--verify", help="Verification level: BASIC, STANDARD, FULL"
    ),
    calls: int = typer.Option(
        settings.MAX_HOURLY_CALLS, "--calls", "-c", help="Max hourly API calls"
    ),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Custom prompt file path"),
    timeout: int = typer.Option(
        settings.TIMEOUT_MINUTES, "--timeout", "-t", help="Timeout in minutes per loop"
    ),
    experimental: bool = typer.Option(
        False, "--experimental", "-x", help="Use new State Pattern architecture (v4.0)"
    ),
    # Debugger / Self-Healing
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable verbose debugger tracing"),
    self_heal: bool = typer.Option(
        False, "--self-heal", "-H", help="Enable crash auto-repair (Self-Healing 2.0)"
    ),
):
    """
    Start the autonomous development loop.

    Backend Options:
    - api: Use Gemini SDK (requires GOOGLE_API_KEY)
    - cli: Use local Gemini CLI (requires 'gemini login')

    Verification Levels:
    - BASIC: Syntax check only
    - STANDARD: Syntax + Linting (ruff)
    - FULL: Syntax + Linting + Tests (pytest)
    """
    # Validate backend
    backend = backend.lower()
    if backend not in ["api", "cli"]:
        console.print(f"[bold red]Invalid backend: {backend}[/bold red]")
        console.print("Valid options: 'api' or 'cli'")
        raise typer.Exit(code=1)

    try:
        # Override settings with CLI options
        settings.MAX_HOURLY_CALLS = calls
        settings.TIMEOUT_MINUTES = timeout
        if prompt:
            settings.PROMPT_FILE = prompt

        # Use CLI backend (privacy mode - no API key needed)
        use_cli = backend == "cli"

        if use_cli:
            console.print("[bold cyan]🔒 Privacy Mode: Using local Gemini CLI[/bold cyan]")
            console.print("[dim]No API key required. Ensure you've run 'gemini login'.[/dim]")
        else:
            console.print("[bold blue]📡 API Mode: Using Gemini SDK[/bold blue]")

        # Debugger Setup
        from .debugger import BoringDebugger
        from .loop import AgentLoop

        debugger = BoringDebugger(
            model_name=model if use_cli else "default", enable_healing=self_heal, verbose=debug
        )

        # Choose loop implementation
        if experimental:
            console.print(
                "[bold magenta]🧪 Experimental: Using State Pattern Architecture[/bold magenta]"
            )
            from .loop import StatefulAgentLoop

            loop = StatefulAgentLoop(
                model_name=model,
                use_cli=use_cli,
                verbose=verbose,
                verification_level=verification.upper(),
                prompt_file=Path(prompt) if prompt else None,
            )
        else:
            loop = AgentLoop(
                model_name=model,
                use_cli=use_cli,
                verbose=verbose,
                verification_level=verification.upper(),
                prompt_file=Path(prompt) if prompt else None,
            )
            console.print(
                f"[bold green]Starting Boring Loop (Timeout: {settings.TIMEOUT_MINUTES}m)[/bold green]"
            )

        if self_heal:
            console.print(
                "[bold yellow]🚑 Self-Healing Enabled: I will attempt to fix crashes automatically.[/bold yellow]"
            )

        # Tutorial Hook
        try:
            from .tutorial import TutorialManager

            tutorial = TutorialManager(settings.PROJECT_ROOT)
            tutorial.show_tutorial("loop_start")
        except Exception:
            pass

        # Execute with Debugger Wrapper
        debugger.run_with_healing(loop.run)

    except Exception as e:
        import traceback

        traceback.print_exc()
        console.print(f"[bold red]Fatal Error:[/bold red] {e}")
        if self_heal:
            console.print("[dim]Debugger failed to heal this crash.[/dim]")
        else:
            console.print("[dim]Tip: Run with --self-heal to attempt auto-repair.[/dim]")
        raise typer.Exit(code=1)


@app.command(hidden=True)
def run(
    instruction: str = typer.Argument(..., help="The instruction to execute"),
    backend: str = typer.Option(
        "api", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"
    ),
    model: str = typer.Option(settings.DEFAULT_MODEL, "--model", "-m", help="Gemini model to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    verification: str = typer.Option(
        "STANDARD", "--verify", help="Verification level: BASIC, STANDARD, FULL"
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable verbose debugger tracing"),
    self_heal: bool = typer.Option(
        False, "--self-heal", "-H", help="Enable crash auto-repair (Self-Healing 2.0)"
    ),
):
    """
    Execute a single instruction immediately (One-Shot Mode).
    Creates a temporary prompt file and runs the agent loop.
    """
def _run_one_shot(
    instruction: str,
    backend: str = "api",
    model: str = settings.DEFAULT_MODEL,
    verbose: bool = False,
    verification: str = "STANDARD",
    debug: bool = False,
    self_heal: bool = False,
    thinking_mode: bool = False,
    command_name: Optional[str] = None,
):
    """Internal helper to run one-shot commands."""
    if thinking_mode:
        instruction = f"Use deep thinking (sequentialthinking) to analyze: {instruction}"
        console.print("[🧠 Thinking Mode Enabled]")


    # Validate backend
    backend = backend.lower()
    if backend not in ["api", "cli"]:
        console.print(f"[bold red]Invalid backend: {backend}[/bold red]")
        raise typer.Exit(code=1)

    # Create temporary prompt file
    tmp_prompt = Path(".boring_run_prompt.md")
    content = f"# One-Shot Task\n\n{instruction}\n\n> Generated by `boring run`"
    tmp_prompt.write_text(content, encoding="utf-8")

    try:
        # Configure settings for this run
        settings.PROMPT_FILE = str(tmp_prompt)
        use_cli = backend == "cli"

        # Initialize components
        from .debugger import BoringDebugger
        from .loop import AgentLoop
        from .mcp import tools  # noqa

        console.print(f"[bold green]Running One-Shot Task:[/bold green] {instruction}")

        debugger = BoringDebugger(
            model_name=model if use_cli else "default", enable_healing=self_heal, verbose=debug
        )

        loop = AgentLoop(
            model_name=model,
            use_cli=use_cli,
            verbose=verbose,
            verification_level=verification.upper(),
            prompt_file=tmp_prompt,
        )

        if self_heal:
            console.print(
                "[bold yellow]🚑 Self-Healing Enabled[/bold yellow]"
            )

        debugger.run_with_healing(loop.run)

        # Smart Suggestions (Project OMNI - Phase 2)
        try:
            from boring.cli.suggestions import run_suggestions
            run_suggestions(settings.PROJECT_ROOT, last_command=command_name)
        except Exception:
            pass # Fail silently for suggestions

    except Exception as e:
        import traceback
        traceback.print_exc()
        console.print(f"[bold red]Fatal Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    finally:
        if tmp_prompt.exists():
            tmp_prompt.unlink()





@app.command()
def status():
    """
    Show current loop status and memory summary.
    """
    from .intelligence import MemoryManager

    memory = MemoryManager(settings.PROJECT_ROOT)
    state = memory.get_project_state()

    console.print("[bold magenta]✨ Vibe Coder Status ✨[/bold magenta]")
    console.print(f"  📂 Project: {state.get('project_name', 'Unknown')}")
    console.print(f"  🔄 Total Loops: {state.get('total_loops', 0)}")
    console.print(
        f"  ✅ Success: {state.get('successful_loops', 0)} | ❌ Failed: {state.get('failed_loops', 0)}"
    )
    console.print(f"  🕒 Last Activity: {state.get('last_activity', 'Never')}")

    # Show recent history
    history = memory.get_loop_history(last_n=3)
    if history:
        console.print("\n[bold]📜 Recent Loops:[/bold]")
        for h in history:
            status = h.get("status", "UNKNOWN")
            if status == "SUCCESS":
                status_icon = "✅"
            elif status == "FAILED":
                status_icon = "❌"
            else:
                status_icon = "❓"

            console.print(f"  {status_icon} Loop #{h.get('loop_id', '?')}: {status}")


@app.command()
def circuit_status():
    """
    Show circuit breaker details.
    """
    from .circuit import show_circuit_status

    show_circuit_status()


@app.command()
def reset_circuit():
    """
    Reset the circuit breaker.
    """
    from .circuit import reset_circuit_breaker

    reset_circuit_breaker("Manual reset via CLI")
    console.print("[green]Circuit breaker reset.[/green]")


@app.command()
def setup_extensions():
    """
    Install recommended Gemini CLI extensions for enhanced capabilities.
    """
    from .extensions import (
        ExtensionsManager,
        create_criticalthink_command,
        create_speckit_command,
        setup_project_extensions,
    )

    setup_project_extensions(settings.PROJECT_ROOT)
    create_criticalthink_command(settings.PROJECT_ROOT)
    create_speckit_command(settings.PROJECT_ROOT)

    # Auto-register as MCP server for the CLI if possible
    manager = ExtensionsManager(settings.PROJECT_ROOT)
    success, msg = manager.register_boring_mcp()
    if success:
        console.print(f"[green]✓ {msg}[/green]")
    else:
        console.print(f"[dim]Note: {msg}[/dim]")

    console.print("[green]Extensions setup complete.[/green]")


@app.command("mcp-register")
def mcp_register():
    """
    Register Boring as an MCP server for the Gemini CLI.
    This allows the 'gemini' command to use Boring's specialized tools.
    """
    from .extensions import ExtensionsManager

    manager = ExtensionsManager(settings.PROJECT_ROOT)

    with console.status("[bold green]Registering Boring MCP with Gemini CLI...[/bold green]"):
        success, msg = manager.register_boring_mcp()

    if success:
        console.print(f"[green]✅ {msg}[/green]")
        console.print(
            "[dim]You can now use Boring tools in the Gemini CLI (e.g. gemini --mcp boring ...)[/dim]"
        )
    else:
        console.print(f"[red]Registration failed: {msg}[/red]")
        raise typer.Exit(1)


@app.command()
def memory_clear():
    """
    Clear the memory/history files (fresh start).
    """
    import shutil

    memory_dir = settings.PROJECT_ROOT / ".boring_memory"
    if memory_dir.exists():
        shutil.rmtree(memory_dir)
        console.print("[yellow]Memory cleared.[/yellow]")
    else:
        console.print("[dim]No memory to clear.[/dim]")


@app.command()
def health(
    backend: str = typer.Option(
        "api", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"
    ),
):
    """
    Run system health checks.

    Verifies:
    - API Key configuration (skipped in CLI mode)
    - Python version compatibility
    - Required dependencies
    - Git repository status
    - PROMPT.md file
    - Optional features
    """
    from .health import print_health_report, run_health_check

    report = run_health_check(backend=backend)
    is_healthy = print_health_report(report)

    if not is_healthy:
        raise typer.Exit(code=1)


@app.command()
def version():
    """
    Show Boring version information.
    """
    from importlib.metadata import version as pkg_version

    try:
        from . import __version__ as ver
    except Exception:
        try:
            ver = pkg_version("boring")
        except Exception:
            ver = "11.1.0"

    console.print(f"[bold blue]Boring[/bold blue] v{ver}")
    console.print(f"  Model: {settings.DEFAULT_MODEL}")
    console.print(f"  Project: {settings.PROJECT_ROOT}")


@app.command("wizard")
@app.command("install-mcp")
def wizard(
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-approve all confirmations"),
):
    """
    Run the Zero-Config Setup Wizard for MCP.
    Automatically detects Claude/Cursor/VS Code and configures them.
    """
    from .cli.wizard import run_wizard

    run_wizard(auto_approve=yes)


# --- Workflow Hub CLI ---
workflow_app = typer.Typer(help="Manage Boring Workflows (Hub)")
app.add_typer(workflow_app, name="workflow")

# --- Tutorial CLI ---
tutorial_app = typer.Typer(help="Vibe Coder Tutorials")
app.add_typer(tutorial_app, name="tutorial")


# --- LSP & IDE Integration CLI ---
lsp_app = typer.Typer(help="IDE Integration & LSP Server")
app.add_typer(lsp_app, name="lsp")


@lsp_app.command("start")
def lsp_start(
    port: int = typer.Option(9876, "--port", "-p", help="LSP Server port"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="LSP Server host"),
):
    """
    Start the Boring LSP/JSON-RPC Server for IDE integration.
    Connect your VS Code extension or JetBrains LSP client to this server.
    """
    import asyncio

    from .vscode_server import VSCodeServer

    console.print(f"[bold green]🚀 Starting Boring LSP Server on {host}:{port}[/bold green]")
    server = VSCodeServer()
    asyncio.run(server.start(host=host, port=port))


@workflow_app.command("list")
def workflow_list():
    """List local workflows."""
    from .loop import WorkflowManager

    manager = WorkflowManager()
    flows = manager.list_local_workflows()

    console.print("[bold blue]Available Workflows:[/bold blue]")
    if not flows:
        console.print("  [dim]No workflows found in .agent/workflows[/dim]")
        return

    for f in flows:
        console.print(f"  - {f}")


@workflow_app.command("export")
def workflow_export(
    name: str = typer.Argument(..., help="Workflow name (e.g. 'speckit-plan')"),
    author: str = typer.Option("Anonymous", "--author", "-a", help="Author name"),
):
    """Export a workflow to .bwf.json package."""
    from .loop import WorkflowManager

    manager = WorkflowManager()
    path, msg = manager.export_workflow(name, author)

    if path:
        console.print(f"[green]✓ Exported to: {path}[/green]")
    else:
        console.print(f"[red]Error: {msg}[/red]")
        raise typer.Exit(1)


@workflow_app.command("publish")
def workflow_publish(
    name: str = typer.Argument(..., help="Workflow name to publish"),
    token: str = typer.Option(
        None, "--token", "-t", help="GitHub Personal Access Token (or set GITHUB_TOKEN env var)"
    ),
    public: bool = typer.Option(True, "--public/--private", help="Make Gist public or secret"),
):
    """Publish a workflow to GitHub Gist registry."""
    import os

    # Resolve token
    gh_token = token or os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        console.print("[red]Error: GitHub Token required.[/red]")
        console.print(
            "Please set [bold]GITHUB_TOKEN[/bold] env var or use [bold]--token[/bold] option."
        )
        console.print("Create one at: https://github.com/settings/tokens (Scpoe: gist)")
        raise typer.Exit(1)

    from .loop import WorkflowManager

    manager = WorkflowManager()

    with console.status(f"[bold green]Publishing {name} to GitHub Gist...[/bold green]"):
        success, msg = manager.publish_workflow(name, gh_token, public)

    if success:
        console.print("[green]✓ Published Successfully![/green]")
        console.print(msg)
    else:
        console.print(f"[red]Publish Failed: {msg}[/red]")
        raise typer.Exit(1)


@app.command()
def evaluate(
    target: str = typer.Argument(
        ..., help="File path(s) to evaluate. For PAIRWISE, use comma-separated paths."
    ),
    level: str = typer.Option(
        "DIRECT", "--level", "-l", help="Evaluation level: DIRECT (1-5) or PAIRWISE (A/B)"
    ),
    context: str = typer.Option("", "--context", "-c", help="Evaluation context or requirements"),
    backend: str = typer.Option(
        "cli", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"
    ),
    model: str = typer.Option("default", "--model", "-m", help="Gemini model to use"),
    mode: str = typer.Option("standard", "--mode", help="Evaluation mode (strictness)"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive mode (returns prompts)"
    ),
):
    """
    Evaluate code quality using LLM Judge (Polyglot & Multi-Backend).
    """
    import json

    from .cli_client import GeminiCLIAdapter
    from .gemini_client import GeminiClient
    from .judge import CODE_QUALITY_RUBRIC, LLMJudge

    # Resolve rubric
    rubric = _get_rubric_for_level(level) if level.upper() != "PAIRWISE" else CODE_QUALITY_RUBRIC

    # Configure strictness
    if mode.lower() == "strict":
        rubric.strictness = "strict"
    elif mode.lower() == "hostile":
        rubric.strictness = "hostile"

    # Initialize Adapter
    try:
        if backend.lower() == "cli":
            adapter = GeminiCLIAdapter(model_name=model)
            console.print("[dim]Using Local CLI Backend[/dim]")
        else:
            adapter = GeminiClient(model_name=model)
            if not adapter.is_available:
                console.print(
                    "[red]Error: API Key not found. Use --backend cli or set GOOGLE_API_KEY.[/red]"
                )
                raise typer.Exit(1)
            console.print("[dim]Using Gemini API Backend[/dim]")

        judge = LLMJudge(adapter)

        # Resolve Targets
        targets = [t.strip() for t in target.split(",")]

        # PAIRWISE MODE
        if level.upper() == "PAIRWISE":
            if len(targets) != 2:
                console.print("[red]❌ PAIRWISE mode requires exactly two files.[/red]")
                raise typer.Exit(1)

            path_a = Path(targets[0]).resolve()
            path_b = Path(targets[1]).resolve()

            if not path_a.exists() or not path_b.exists():
                console.print("[red]❌ Files not found.[/red]")
                raise typer.Exit(1)

            console.print(f"[bold blue]⚖️ Comparing {path_a.name} vs {path_b.name}...[/bold blue]")
            content_a = path_a.read_text(encoding="utf-8", errors="replace")
            content_b = path_b.read_text(encoding="utf-8", errors="replace")

            result = judge.compare_code(
                path_a.name,
                content_a,
                path_b.name,
                content_b,
                context=context,
                interactive=interactive,
            )

            if interactive:
                console.print(json.dumps(result, indent=2))
            else:
                winner = result.get("winner", "TIE")
                conf = result.get("confidence", 0.0)
                reasoning = result.get("reasoning", "")
                color = "green" if winner != "TIE" else "yellow"
                console.print(f"\n[{color}]Winner: {winner}[/{color}] (Confidence: {conf})")
                console.print(f"\nReasoning:\n{reasoning}\n")

        # DIRECT MODE
        else:
            target_path = Path(targets[0]).resolve()
            if not target_path.exists():
                console.print(f"[red]❌ Target '{target}' not found.[/red]")
                raise typer.Exit(1)

            console.print(f"[bold blue]🧐 Evaluating {target_path.name}...[/bold blue]")
            content = target_path.read_text(encoding="utf-8", errors="replace")
            result = judge.grade_code(
                target_path.name, content, rubric=rubric, interactive=interactive
            )

            if interactive:
                console.print(json.dumps(result, indent=2))
            else:
                score = result.get("score", 0)
                summary = result.get("summary", "No summary")
                suggestions = result.get("suggestions", [])

                # Display Dimensions
                if "dimensions" in result:
                    console.print("\n[bold underline]Breakdown:[/bold underline]")
                    for dim, details in result["dimensions"].items():
                        d_score = details.get("score", 0)
                        d_comment = details.get("comment", "")
                        color = "green" if d_score >= 4 else "yellow" if d_score >= 3 else "red"
                        console.print(
                            f"  [{color}]{dim:<25} : {d_score}/5[/] - [dim]{d_comment}[/dim]"
                        )

                emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
                console.print(f"\n[bold]{emoji} Overall Score: {score}/5.0[/bold]")
                console.print(f"[italic]{summary}[/italic]\n")

                if suggestions:
                    console.print("[bold]💡 Suggestions:[/bold]")
                    for s in suggestions:
                        console.print(f"  - {s}")

    except Exception as e:
        console.print(f"[red]Evaluation failed: {e}[/red]")
        raise typer.Exit(1)


def _get_rubric_for_level(level: str):
    """Map verification level/string to Rubric object"""
    from .judge.rubrics import RUBRIC_REGISTRY, get_rubric

    # Direct name match
    if level.lower() in RUBRIC_REGISTRY:
        return get_rubric(level)

    # Level mapping
    level_map = {
        "production": "production",
        "arch": "architecture",
        "security": "security",
        "perf": "performance",
    }

    mapped = level_map.get(level.lower())
    if mapped:
        return get_rubric(mapped)

    return get_rubric("code_quality")  # Default


@workflow_app.command("install")
def workflow_install(source: str = typer.Argument(..., help="File path or URL to .bwf.json")):
    """Install a workflow from file or URL."""
    from .loop import WorkflowManager

    manager = WorkflowManager()
    success, msg = manager.install_workflow(source)

    if success:
        console.print(f"[green]{msg}[/green]")
    else:
        console.print(f"[red]Error: {msg}[/red]")
        raise typer.Exit(1)


@app.command()
def dashboard():
    """
    Launch the Boring Visual Dashboard (localhost Web UI).
    """
    import subprocess
    import sys

    dashboard_path = Path(__file__).parent / "dashboard.py"

    dashboard_path = Path(__file__).parent / "dashboard.py"

    from boring.core.dependencies import DependencyManager

    if not DependencyManager.check_gui():
        console.print("[bold red]❌ The dashboard requires extra dependencies.[/bold red]")
        console.print("\nPlease install the GUI extras:")
        console.print('  [cyan]pip install "boring-aicoding[gui]"[/cyan]')
        raise typer.Exit(1)

    console.print("🚀 Launching Dashboard at [bold green]http://localhost:8501[/bold green]")
    console.print("Press Ctrl+C to stop.")

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)], check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to launch dashboard:[/bold red] {e}")
        raise typer.Exit(1)


@tutorial_app.command("note")
def tutorial_note():
    """
    Generate a learning note (LEARNING.md) based on your vibe coding journey.
    """
    from .tutorial import TutorialManager

    manager = TutorialManager(settings.PROJECT_ROOT)
    path = manager.generate_learning_note()

    console.print("[bold green]✨ 學習筆記已生成！[/bold green]")
    console.print(f"👉 {path}")
    console.print("[dim]快打開來看看你解鎖了哪些成就吧！[/dim]")


@app.command()
def verify(
    level: str = typer.Option(
        "STANDARD", "--level", "-l", help="Verification level: BASIC, STANDARD, FULL, SEMANTIC"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force verification (bypass cache)"),
):
    """
    Run code verification on the project.
    """
    from .verification import CodeVerifier

    console.print(f"[bold blue]🔍 Running Verification (Level: {level})[/bold blue]")

    verifier = CodeVerifier(settings.PROJECT_ROOT)
    passed, msg = verifier.verify_project(level.upper(), force=force)

    if passed:
        console.print("[green]✅ Verification Passed[/green]")
        console.print(msg)
    else:
        console.print("[red]❌ Verification Failed[/red]")
        console.print(msg)
        raise typer.Exit(code=1)


@app.command("auto-fix")
def auto_fix(
    target: str = typer.Argument(..., help="File path to fix"),
    max_attempts: int = typer.Option(3, "--max-attempts", "-n", help="Max fix attempts per cycle"),
    backend: str = typer.Option(
        "cli", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"
    ),
    model: str = typer.Option("default", "--model", "-m", help="Gemini model to use"),
    verification_level: str = typer.Option("STANDARD", "--verify", help="Verification level"),
):
    """
    Auto-fix syntax and linting errors in a file.
    """
    from .auto_fix import AutoFixPipeline
    from .intelligence import MemoryManager
    from .loop import AgentLoop
    from .verification import CodeVerifier

    target_path = Path(target).resolve()
    if not target_path.exists():
        console.print(f"[red]Error: Target '{target}' not found.[/red]")
        raise typer.Exit(1)

    project_root = target_path.parent
    # Walk up to find project root (marker: .git or pyproject.toml)
    current = project_root
    while current.parent != current:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            project_root = current
            break
        current = current.parent

    console.print(f"[bold blue]🔧 Auto-Fixing {target_path.name} in {project_root}...[/bold blue]")

    # Wrapper for Verification
    def verify_wrapper(level, project_path):
        verifier = CodeVerifier(Path(project_path))
        passed, msg = verifier.verify_project(level)
        # We need structured issues if possible, but verifier returns (bool, str)
        # AutoFixPipeline expects dict with 'issues' list if failed.
        # We'll try to parse the msg or just treat it as one issue.
        return {"passed": passed, "message": msg, "issues": [msg] if not passed else []}

    # Wrapper for Agent Loop
    def run_boring_wrapper(task_description, verification_level, max_loops, project_path):
        project_path_obj = Path(project_path)

        # Write task to PROMPT.md (temp arg override)
        prompt_file = project_path_obj / "PROMPT.md"
        original_prompt = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""
        prompt_file.write_text(task_description, encoding="utf-8")

        try:
            # Configure settings locally
            settings.PROJECT_ROOT = project_path_obj
            settings.MAX_LOOPS = max_loops

            loop = AgentLoop(
                model_name=model,
                use_cli=(backend.lower() == "cli"),
                verification_level=verification_level,
                prompt_file=prompt_file,
                verbose=False,  # Keep it cleaner
            )

            # Run loop
            loop.run()

            # Check result
            memory = MemoryManager(project_path_obj)
            history = memory.get_loop_history(last_n=1)

            if history and history[0].get("status") == "SUCCESS":
                return {"status": "SUCCESS", "message": "Fix applied successfully"}
            else:
                return {"status": "FAILED", "message": "Agent failed to fix issues."}

        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        finally:
            # Restore prompt file if it existed
            if original_prompt:
                prompt_file.write_text(original_prompt, encoding="utf-8")
            elif prompt_file.exists():
                prompt_file.unlink()

    try:
        pipeline = AutoFixPipeline(
            project_root=project_root,
            max_iterations=max_attempts,  # Pipeline uses this for overall cycles
            verification_level=verification_level,
        )

        result = pipeline.run(run_boring_wrapper, verify_wrapper)

        if result["status"] == "SUCCESS":
            console.print(
                f"[green]✅ Optimized successfully after {result['iterations']} iterations.[/green]"
            )
        else:
            console.print(f"[red]❌ {result['message']}[/red]")

    except Exception as e:
        console.print(f"[red]Auto-fix failed: {e}[/red]")
        raise typer.Exit(1)


# evaluate_code removed (merged into evaluate)

# ========================================
# Local Teams: Git Hooks Commands
# ========================================
hooks_app = typer.Typer(help="Git hooks for local code quality enforcement.")
app.add_typer(hooks_app, name="hooks")


@hooks_app.command("install")
def hooks_install():
    """Install Boring Git hooks (pre-commit, pre-push)."""
    from .hooks import HooksManager

    manager = HooksManager()
    success, msg = manager.install_all()

    if success:
        console.print("[bold green]✅ Hooks installed![/bold green]")
        console.print(msg)
        console.print("\n[dim]Your commits will now be verified automatically.[/dim]")
    else:
        console.print(f"[red]Error: {msg}[/red]")
        raise typer.Exit(1)


@hooks_app.command("uninstall")
def hooks_uninstall():
    """Remove Boring Git hooks."""
    from .hooks import HooksManager

    manager = HooksManager()
    success, msg = manager.uninstall_all()

    if success:
        console.print("[yellow]Hooks removed.[/yellow]")
        console.print(msg)
    else:
        console.print(f"[red]Error: {msg}[/red]")
        raise typer.Exit(1)


@hooks_app.command("status")
def hooks_status():
    """Show status of installed hooks."""
    from .hooks import HooksManager

    manager = HooksManager()
    status = manager.status()

    if not status["is_git_repo"]:
        console.print("[yellow]Not a Git repository.[/yellow]")
        return

    console.print("[bold]Git Hooks Status:[/bold]")
    for hook_name, info in status["hooks"].items():
        if info["installed"]:
            if info["is_boring_hook"]:
                console.print(f"  ✅ {hook_name}: [green]Boring hook active[/green]")
            else:
                console.print(f"  ⚠️ {hook_name}: [yellow]Custom hook (not Boring)[/yellow]")
        else:
            console.print(f"  ❌ {hook_name}: [dim]Not installed[/dim]")


@app.command()
def learn():
    """
    Extract learned patterns from project history (.boring_memory).

    Analyses successful loops and error fixes to create reusable patterns
    in .boring_brain/learned_patterns/.
    """
    from .intelligence.brain_manager import create_brain_manager
    from .storage import SQLiteStorage

    console.print("[bold blue]🧠 Analyzing Project History...[/bold blue]")

    # 1. Initialize Storage
    storage = SQLiteStorage(settings.PROJECT_ROOT)

    # 2. Initialize Brain
    brain = create_brain_manager(settings.PROJECT_ROOT)

    # 3. Learn
    result = brain.learn_from_memory(storage)

    if result["status"] == "SUCCESS":
        new_count = result.get("new_patterns", 0)
        total = result.get("total_patterns", 0)

        if new_count > 0:
            console.print(f"[green]✨ Learned {new_count} new patterns![/green]")
        else:
            console.print("[dim]No new patterns found in recent history.[/dim]")

        console.print(f"Total Knowledge Base: [bold]{total}[/bold] patterns")
    else:
        console.print(f"[red]Learning failed: {result.get('error')}[/red]")
        raise typer.Exit(1)


# ========================================
# RAG System Commands
# ========================================
rag_app = typer.Typer(help="Manage RAG (Retrieval-Augmented Generation) system.")
app.add_typer(rag_app, name="rag")


@rag_app.command("index")
@app.command("rag-index", hidden=True)
def rag_index(
    force: bool = typer.Option(False, "--force", "-f", help="Force full rebuild of index"),
    incremental: bool = typer.Option(
        True, "--incremental/--full", "-i/-F", help="Incremental indexing (default)"
    ),
    project: str = typer.Option(None, "--project", "-p", help="Explicit project root path"),
):
    """Index the codebase for RAG retrieval."""
    from .rag import create_rag_retriever

    root = Path(project) if project else settings.PROJECT_ROOT
    console.print(f"[bold blue]Indexing project at {root}...[/bold blue]")

    retriever = create_rag_retriever(root)
    if not retriever.is_available:
        console.print("[red]❌ RAG dependencies not found (chromadb, sentence-transformers)[/red]")
        raise typer.Exit(1)

    # If force is True, incremental is effectively False
    if force:
        incremental = False

    count = retriever.build_index(force=force, incremental=incremental)
    stats = retriever.get_stats()

    if stats.index_stats:
        idx = stats.index_stats
        console.print(f"\n[bold green]✅ RAG Index {'rebuilt' if force else 'ready'}[/bold green]")
        console.print(f"  Files indexed: {idx.total_files}")
        console.print(f"  Total chunks: {idx.total_chunks}")
        console.print(f"  - Functions: {idx.functions}")
        console.print(f"  - Classes: {idx.classes}")
        console.print(f"  - Script chunks: {getattr(idx, 'script_chunks', 0)}")
    else:
        console.print(f"[green]✅ Index built with {count} chunks.[/green]")


@rag_app.command("search")
@app.command("rag-search", hidden=True)
def rag_search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    threshold: float = typer.Option(
        0.0, "--threshold", "-t", help="Minimum relevance score (0.0-1.0)"
    ),
    project: str = typer.Option(None, "--project", "-p", help="Explicit project root path"),
):
    """Search the codebase semanticly."""
    from .rag import create_rag_retriever

    root = Path(project) if project else settings.PROJECT_ROOT
    retriever = create_rag_retriever(root)

    if not retriever.is_available:
        console.print("[red]❌ RAG not initialized. Run 'boring rag index' first.[/red]")
        raise typer.Exit(1)

    results = retriever.retrieve(query, n_results=limit, threshold=threshold)

    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        return

    console.print(f"[bold blue]🔍 Results for '{query}':[/bold blue]\n")
    for i, res in enumerate(results, 1):
        chunk = res.chunk
        console.print(
            f"{i}. [bold]{chunk.file_path}[/bold] -> {chunk.name} [dim](score: {res.score:.2f})[/dim]"
        )
        # Show a snippet
        snippet = chunk.content[:200].replace("\n", " ")
        console.print(f"   [italic]{snippet}...[/italic]\n")


# ========================================
# Workspace Management
# ========================================
workspace_app = typer.Typer(help="Manage multi-project workspace.")
app.add_typer(workspace_app, name="workspace")


@workspace_app.command("list")
def workspace_list(tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag")):
    """List all projects in the workspace."""
    from .workspace import get_workspace_manager

    manager = get_workspace_manager()
    projects = manager.list_projects(tag)

    if not projects:
        console.print("[dim]Workspace is empty. Add projects with 'boring workspace add'.[/dim]")
        return

    console.print(f"[bold blue]Workspace Projects ({len(projects)}):[/bold blue]")

    for p in projects:
        name = p["name"]
        path = p["path"]
        is_active = p.get("is_active", False)
        marker = "🟢" if is_active else "⚪"
        style = "bold green" if is_active else "white"

        console.print(f"  {marker} [{style}]{name}[/{style}] [dim]({path})[/dim]")
        if p.get("description"):
            console.print(f"     [dim]└─ {p['description']}[/dim]")


@workspace_app.command("add")
def workspace_add(
    name: str = typer.Argument(..., help="Unique project name"),
    path: str = typer.Argument(".", help="Project path (default: current dir)"),
    description: str = typer.Option("", "--desc", "-d", help="Project description"),
):
    """Add a project to the workspace."""
    from .workspace import get_workspace_manager

    manager = get_workspace_manager()
    result = manager.add_project(name, path, description)

    if result["status"] == "SUCCESS":
        console.print(f"[green]✓ Added project '{name}'[/green]")
    else:
        console.print(f"[red]Error: {result['message']}[/red]")
        raise typer.Exit(1)


@workspace_app.command("remove")
def workspace_remove(name: str = typer.Argument(..., help="Project name to remove")):
    """Remove a project from the workspace."""
    from .workspace import get_workspace_manager

    manager = get_workspace_manager()
    result = manager.remove_project(name)

    if result["status"] == "SUCCESS":
        console.print(f"[yellow]Removed project '{name}'[/yellow]")
    else:
        console.print(f"[red]Error: {result['message']}[/red]")
        raise typer.Exit(1)


@workspace_app.command("switch")
def workspace_switch(name: str = typer.Argument(..., help="Project name to switch to")):
    """Switch active context to another project."""
    from .workspace import get_workspace_manager

    manager = get_workspace_manager()
    result = manager.switch_project(name)

    if result["status"] == "SUCCESS":
        console.print(f"[green]✓ Switched context to '{name}'[/green]")
        console.print(f"[dim]Path: {result['path']}[/dim]")
    else:
        console.print(f"[red]Error: {result['message']}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
