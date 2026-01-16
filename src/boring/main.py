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

import asyncio
import logging
import sys
from pathlib import Path

import boring
import typer
from rich.panel import Panel
import rich

from boring.cli import audit, doctor, model, offline
from boring.cli.theme import BORING_THEME
from boring.core.config import settings
from boring.utils.i18n import LocalizedConsole, T

logger = logging.getLogger(__name__)

# ... imports ...

HELP_TEXT = T("cli_help_text")

EPILOG_TEXT = T("cli_epilog_text")

app = typer.Typer(
    name="boring",
    help=HELP_TEXT,
    epilog=EPILOG_TEXT,
    rich_markup_mode="rich",
    add_completion=False,
)


def setup_notifications():
    """Configure notification system from settings."""
    try:
        from .services import notifier

        notifier.configure(
            enable_toast=settings.NOTIFICATIONS_ENABLED,
            enable_sound=settings.NOTIFICATIONS_ENABLED,
            slack_webhook=settings.SLACK_WEBHOOK,
            discord_webhook=settings.DISCORD_WEBHOOK,
            email_recipient=settings.EMAIL_NOTIFY,
        )
    except Exception as exc:
        sys.stderr.write(f"Notification setup failed: {exc}\n")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    provider: str = typer.Option(
        None, "--provider", "-P", help=T("cli_option_provider_help")
    ),
    base_url: str = typer.Option(None, "--base-url", help=T("cli_option_base_url_help")),
    llm_model: str = typer.Option(None, "--llm-model", help=T("cli_option_llm_model_help")),
):
    """
    Boring - Autonomous AI Development Agent
    """
    # Initialize notifications
    setup_notifications()

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

        # Check for first run marker (or lack thereof) to avoid spamming
        # In Lazy Mode, we might want to welcome the user if it's their first time interacting
        # We can use a lightweight marker in the system temp or user home if project root is volatile
        # For simplicity, we just print a header if invoked without arguments
        pass

    # First Run Experience (V14.6)
    # Check if .boring folder exists (indicating initialized project)
    # If not, and we are running a command (or not), we can offer guidance.
    # But let's be less intrusive: Only show welcome if no config found AND no args passed.

    if not boring_dir.exists() and ctx.invoked_subcommand is None:
        from boring.utils.i18n import T

        msg = f"[bold magenta]{T('welcome_title')}[/bold magenta]\n\n"
        msg += f"{T('welcome_intro')}\n\n"
        msg += f"  1. [cyan]boring wizard[/cyan]   - {T('menu_wizard')}\n"
        msg += f"  2. [cyan]boring flow[/cyan]     - {T('menu_flow')}\n"
        msg += f"  3. [cyan]boring doctor[/cyan]   - {T('menu_doctor')}\n"
        msg += f"  4. [cyan]boring offline[/cyan]  - {T('menu_offline')}\n"

        console.print(Panel(msg, title=T("title_getting_started"), border_style="indigo"))
        # consistency check

    # Contextual Onboarding (Project OMNI)
    if ctx.invoked_subcommand is None:
        if os.environ.get("CI") or not sys.stdin.isatty() or not sys.stdout.isatty():
            console.print(ctx.get_help())
            raise typer.Exit()

        from boring.cli.tui import run_console

        run_console()


console = LocalizedConsole(theme=BORING_THEME)


app.add_typer(audit.app, name="audit")
app.add_typer(doctor.app, name="doctor")

# --- The 5 Commandments (Project OMNI) ---


@app.command()
def do(
    request: str = typer.Argument(..., help="Natural language request (e.g. 'fix the bugs')"),
):
    """✨ Magic Intent: Execute natural language requests."""
    from boring.intelligence.intent_engine import IntentEngine

    engine = IntentEngine()
    intent = engine.infer_intent(request)

    if not intent:
        console.print(T("intent_failed", request=request))
        console.print(T("intent_hint"))
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold green]{T('intent_recognized')}: {intent.command}[/bold green]\n"
        f"[dim]{T('intent_confidence')}: {intent.confidence*100:.0f}%[/dim]",
        title="✨ Intent Engine",
        border_style="green"
    ))

    # Dispatcher
    if intent.command == "fix":
        # Pass the original input as the goal context
        fix(think=False, goal=intent.original_input or "Fix detected issues")
    elif intent.command == "predict":
        predict(diff=intent.kwargs.get("diff", False))
    elif intent.command == "flow":
        flow()
    elif intent.command == "dashboard":
        dashboard()
    elif intent.command == "diagnose":
        doctor()
    elif intent.command == "learn":
        learn()
    else:
                console.print(
            f"[yellow]Command '{intent.command}' recognized but not yet auto-dispatched.[/yellow]"
        )


@app.command()
def go():
    """🚀 Start the One Dragon autonomous workflow (Alias for flow)."""
    flow()


@app.command()
def fix(
    think: bool = typer.Option(False, "--think", "-t", help=T("cli_fix_think_help")),
    goal: str | None = typer.Option(None, "--goal", "-g", help="Specific goal or error to fix"),
):
    """🔧 Auto-repair linting and code errors."""
    instruction = goal if goal else "Fix all linting and code errors in this project"

    if think:
        # System 2: Cognitive Reasoning Loop
        from boring.intelligence.reasoning_engine import ReasoningEngine
        engine = ReasoningEngine()

        console.print("[bold cyan]🧠 System 2 Activated: Thinking...[/bold cyan]")
        trace = engine.think(instruction)

        # Display the plan
        console.print("[bold]📋 Reasoning Plan:[/bold]")
        for step in trace.steps:
            console.print(f"  {step.id}. {step.description}")

        # TODO: Execute the steps (Future: Phase 3.2)
        console.print("[dim](Reasoning Engine currently in simulation mode)[/dim]")

    # System 1: Fast One-Shot (Default)
    _run_one_shot(
        instruction,
        thinking_mode=False, # Handled by ReasoningEngine above if enabled
        self_heal=True,
        command_name="fix",
    )


@app.command()
def check(think: bool = typer.Option(False, "--think", "-t", help=T("cli_check_think_help"))):
    """✅ Run Vibe Check health scan."""
    _run_one_shot("Run boring_vibe_check", thinking_mode=think, command_name="check")


@app.command()
def save(think: bool = typer.Option(False, "--think", "-t", help=T("cli_save_think_help"))):
    """💾 Smart commit with generated message."""
    _run_one_shot(
        "Generate a smart commit message and commit changes",
        thinking_mode=think,
        command_name="save",
    )


@app.command()
def use(
    profile: str = typer.Argument(..., help=T("cli_use_profile_help")),
):
    """
    🎛️ Switch active tool profile (e.g. 'boring use standard').
    """
    from boring.mcp.tool_manager import ToolManager

    manager = ToolManager()
    if manager.set_profile(profile):
        console.print(T("profile_switch_success", profile=profile))
        console.print(T("profile_switch_restart_hint"))
    else:
        console.print(T("profile_switch_failed"))
        raise typer.Exit(1)


@app.command()
def guide(query: str | None = typer.Argument(None)):
    """❓ Interactive tool guide and helper."""
    from rich.prompt import Prompt

    from boring.mcp.tool_router import cli_route, get_tool_router

    if query:
        cli_route(query)
        return

    router = get_tool_router()
    router.get_categories_summary()

    q = Prompt.ask(T("guide_prompt_ask_anything"))
    if q:
        cli_route(q)


@app.command()
def watch():
    """👁️ Sentinel Mode: Watch for file changes and suggest fixes."""
    from boring.cli.watch import run_watch

    run_watch(settings.PROJECT_ROOT)


@app.command()
def evolve(
    goal: str = typer.Argument(..., help=T("cli_evolve_goal_help")),
    verify: str = typer.Option("pytest", "--verify", "-v", help=T("cli_evolve_verify_help")),
    steps: int = typer.Option(5, "--steps", "-s", help=T("cli_evolve_steps_help")),
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
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="Custom prompt file path"),
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
    multi_agent: bool = typer.Option(
        False,
        "--multi-agent",
        "-M",
        help="Enable Multi-Agent Orchestration (Architect -> Coder -> Reviewer)",
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
    # console.print(T("cli_start_deprecated_redirect"))
    # flow()
    # return
    # Validate backend
    backend = backend.lower()
    if backend not in ["api", "cli"]:
        console.print(T("cli_invalid_backend", backend=backend))
        console.print(T("cli_valid_backend_options"))
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
            console.print(T("cli_privacy_mode"))
            console.print(T("cli_privacy_mode_hint"))
        else:
            console.print(T("cli_api_mode"))

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
            console.print(T("cli_self_heal_enabled_verbose"))

        # Tutorial Hook
        try:
            from .tutorial import TutorialManager

            tutorial = TutorialManager(settings.PROJECT_ROOT)
            tutorial.show_tutorial("loop_start")
        except Exception as e:
            logger.debug("Tutorial hint unavailable: %s", e)

        # Execute with Debugger Wrapper
        if multi_agent:
            from .agents.orchestrator import MultiAgentOrchestrator

            orch = MultiAgentOrchestrator(settings.PROJECT_ROOT)

            # Use Prompt file as goal if exists
            goal = "Follow the instructions in PROMPT.md"
            if Path(settings.PROMPT_FILE).exists():
                goal = Path(settings.PROMPT_FILE).read_text(encoding="utf-8")

            debugger.run_with_healing(lambda: asyncio.run(orch.execute_goal(goal)))
        else:
            debugger.run_with_healing(loop.run)

    except Exception as e:
        import traceback

        traceback.print_exc()
        console.print(T("cli_fatal_error", error=str(e)))
        if self_heal:
            console.print(T("cli_debugger_heal_failed"))
        else:
            console.print(T("cli_self_heal_tip"))
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
    multi_agent: bool = typer.Option(
        False, "--multi-agent", "-M", help="Enable Multi-Agent Orchestration"
    ),
):
    """
    Execute a single instruction immediately (One-Shot Mode).
    Creates a temporary prompt file and runs the agent loop.
    """
    _run_one_shot(
        instruction=instruction,
        backend=backend,
        model=model,
        verbose=verbose,
        verification=verification,
        debug=debug,
        self_heal=self_heal,
        multi_agent=multi_agent,
        command_name="run",
    )


def _run_one_shot(
    instruction: str,
    backend: str = "api",
    model: str = settings.DEFAULT_MODEL,
    verbose: bool = False,
    verification: str = "STANDARD",
    debug: bool = False,
    self_heal: bool = False,
    thinking_mode: bool = False,
    multi_agent: bool = False,
    command_name: str | None = None,
    context_files: list[str] = None,
):
    """
    Helper to run a one-shot autonomous loop with a specific instruction.
    Injects context awareness (session memory).
    """
    from datetime import datetime

    from boring.intelligence.context_manager import ContextManager

    # 1. Context Injection
    ctx_mgr = ContextManager()
    ctx_mgr.update_activity(command_name)

    context_summary = ctx_mgr.get_context_summary()

    # Resolve vague references if needed (e.g. "fix it")
    resolved_target = ctx_mgr.resolve_reference(instruction)
    if resolved_target:
        instruction += f"\n(Context Note: User might be referring to {resolved_target})"

    full_instruction = instruction
    if context_summary:
        full_instruction = f"Context:\n{context_summary}\n\nTask:\n{instruction}"



    if thinking_mode:
        instruction = f"Use deep thinking (sequentialthinking) to analyze: {instruction}"
        console.print(T("cli_thinking_mode_enabled"))

    # Validate backend
    backend = backend.lower()
    if backend not in ["api", "cli"]:
        console.print(T("cli_invalid_backend", backend=backend))
        raise typer.Exit(code=1)

    # Create temporary prompt file
    tmp_prompt = Path(".boring_run_prompt.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Use the full_instruction which includes context
    content = (
        f"# One-Shot Task ({command_name})\n\n{full_instruction}\n\n"
        f"> Generated by `boring run` at {timestamp}"
    )
    tmp_prompt.write_text(content, encoding="utf-8")

    try:
        # Configure settings for this run
        settings.PROMPT_FILE = str(tmp_prompt)
        use_cli = backend == "cli"

        # Initialize components
        from .debugger import BoringDebugger
        from .loop import AgentLoop
        from .mcp import tools  # noqa

        console.print(T("cli_one_shot_running", instruction=instruction))

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
            console.print(T("cli_self_heal_enabled"))

        if multi_agent:
            from .agents.orchestrator import MultiAgentOrchestrator

            orch = MultiAgentOrchestrator(settings.PROJECT_ROOT)
            debugger.run_with_healing(lambda: asyncio.run(orch.execute_goal(instruction)))
        else:
            debugger.run_with_healing(loop.run)

        # Smart Suggestions (Project OMNI - Phase 2)
        try:
            from boring.cli.suggestions import run_suggestions

            run_suggestions(settings.PROJECT_ROOT, last_command=command_name)
        except Exception:
            pass  # Fail silently for suggestions

    except Exception as e:
        import traceback

        traceback.print_exc()
        console.print(T("cli_fatal_error", error=str(e)))
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

    console.print(T("status_header"))
    console.print(
        T("status_project", project=state.get("project_name", T("status_unknown_project")))
    )
    console.print(T("status_total_loops", count=state.get("total_loops", 0)))
    console.print(
        T(
            "status_success_failed",
            success=state.get("successful_loops", 0),
            failed=state.get("failed_loops", 0),
        )
    )
    console.print(
        T(
            "status_last_activity",
            last_activity=state.get("last_activity", T("status_never")),
        )
    )

    # Show recent history
    history = memory.get_loop_history(last_n=3)
    if history:
        console.print(T("status_recent_loops"))
        for h in history:
            status = h.get("status", "UNKNOWN")
            if status == "SUCCESS":
                status_icon = "✅"
            elif status == "FAILED":
                status_icon = "❌"
            else:
                status_icon = "❓"

            console.print(
                T(
                    "status_loop_entry",
                    icon=status_icon,
                    loop_id=h.get("loop_id", "?"),
                    status=status,
                )
            )


@app.command()
def timeline(
    limit: int = typer.Option(20, "--limit", "-n", help=T("cli_timeline_limit_help")),
):
    """
    📅 Show chronological timeline of agent activity.
    """
    from .monitor.timeline import TimelineViewer

    viewer = TimelineViewer(settings.PROJECT_ROOT)
    viewer.render(limit=limit)


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
    console.print(T("circuit_reset_done"))


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
        console.print(T("extensions_register_success", message=msg))
    else:
        console.print(T("extensions_register_note", message=msg))

    console.print(T("extensions_setup_complete"))


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
        console.print(T("mcp_register_success", message=msg))
        console.print(T("mcp_register_hint"))
    else:
        console.print(T("mcp_register_failed", message=msg))
        raise typer.Exit(1)


@app.command()
def clean(
    all: bool = typer.Option(
        False, "--all", "-a", help="Remove all artifacts including backups and memory"
    ),
    migrate: bool = typer.Option(
        False, "--migrate", "-m", help="Migrate legacy data to .boring/ before cleaning"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    🧹 Clean up temporary files, caches, and session artifacts.
    """
    import shutil

    from rich.prompt import Confirm

    project_root = settings.PROJECT_ROOT

    # Migration Logic (V14.0)
    if migrate:
        console.print(T("clean_migration_start"))
        boring_dir = project_root / ".boring"
        boring_dir.mkdir(exist_ok=True)

        MIGRATION_MAP = {
            ".boring_memory": "memory",
            ".boring_brain": "brain",
            ".boring_cache": "cache",
            ".boring_audit": "audit",
            ".boring_plugins": "plugins",
            "Self-Healing": "self_healing",
        }

        migrated_count = 0
        for old_name, new_sub in MIGRATION_MAP.items():
            old_path = project_root / old_name
            if old_path.exists():
                new_path = boring_dir / new_sub
                if new_path.exists():
                    console.print(
                        T(
                            "clean_migration_skip",
                            old_name=old_name,
                            new_sub=new_sub,
                        )
                    )
                else:
                    try:
                        shutil.move(str(old_path), str(new_path))
                        console.print(
                            T(
                                "clean_migration_success",
                                old_name=old_name,
                                new_sub=new_sub,
                            )
                        )
                        migrated_count += 1
                    except Exception as e:
                        console.print(
                            T("clean_migration_failed", old_name=old_name, error=str(e))
                        )

        if migrated_count > 0:
            console.print(T("clean_migration_summary", count=migrated_count))
        else:
            console.print(T("clean_migration_none"))

    # Core temporary files (Safe to delete)
    temp_files = [
        ".circuit_breaker_state",
        ".circuit_breaker_history",
        ".exit_signals",
        ".last_loop_summary",
        ".last_reset",
        ".call_count",
        ".response_analysis",
        ".boring_run_prompt.md",
        ".boring_tutorial.json",
        "boring.log",
        "gemini_mcp_wrapper.bat",
        "gemini_mcp_wrapper.sh",
        "debug_manual.py",
        "test_output.txt",
    ]

    # Legacy directories (Should be cleaned / migrated)
    legacy_dirs = [
        ".agent",
        ".boring_memory",
        ".boring_brain",
        ".boring_cache",
        ".boring_data",
        ".boring_audit",
        ".boring_plugins",
        "Self-Healing",
    ]

    # Unified State (Only delete with --all)
    unified_dirs = [
        ".boring",
    ]

    # Backups (Only if --all)
    backup_dirs = [
        ".boring_backups",
    ]

    targets = []

    # 1. Scan for temp files
    for f in temp_files:
        p = project_root / f
        if p.exists():
            targets.append(p)

    # 2. Check legacy dirs (Always offer to clean, or strictly with --all?)
    # V14.0 Strategy: Legacy dirs are considered clutter.
    # If --all is passed, we definitely clean them.
    # If not, let's include them if they exist to encourage migration/cleanup.
    for d in legacy_dirs:
        p = project_root / d
        if p.exists():
            targets.append(p)

    # 3. Check state dirs
    if all:
        for d in unified_dirs + backup_dirs:
            p = project_root / d
            if p.exists():
                targets.append(p)

    if not targets:
        console.print(T("clean_no_targets"))
        return

    console.print(T("clean_targets_found", count=len(targets)))
    for t in targets:
        console.print(T("clean_target_item", name=t.name))

    if not force and not Confirm.ask("Delete these files?"):
        console.print(T("clean_aborted"))
        return

    # Delete
    cleaned_count = 0
    for t in targets:
        try:
            if t.is_dir():
                shutil.rmtree(t)
            else:
                t.unlink()
            cleaned_count += 1
        except Exception as e:
            console.print(T("clean_delete_failed", name=t.name, error=str(e)))

    console.print(T("clean_complete", count=cleaned_count))


@app.command()
def doctor(
    generate_context: bool = typer.Option(
        False, "--generate-context", "-g", help="Auto-generate GEMINI.md context file"
    ),
):
    """
    🩺 Run system health checks (Doctor).
    """
    from .cli.doctor import check

    check(generate_context=generate_context)


@app.command("memory-clear", hidden=True)
def memory_clear_deprecated():
    """Deprecated: Use 'boring clean --all' instead."""
    console.print(
        "[yellow]Note: 'memory-clear' is deprecated. running 'clean --all --force'[/yellow]"
    )
    clean(all=True, force=True)


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


@app.command(name="version-info")
def version_info():
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

    console.print(T("version_info_header", version=ver))
    console.print(T("version_info_model", model=settings.DEFAULT_MODEL))
    console.print(T("version_info_project", project=settings.PROJECT_ROOT))


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


@app.command()
def suggest(
    typo: str = typer.Argument(..., help="The mistyped command"),
):
    """
    🤔 Did you mean...? Suggest corrections for typos.
    """
    from .utils.typos import get_boring_commands, suggest_correction

    correction = suggest_correction(typo, get_boring_commands())
    if correction:
        console.print(T("suggestion_did_you_mean", correction=correction))
    else:
        console.print(T("suggestion_no_match", typo=typo))


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
    port: int = typer.Option(9876, "--port", "-p", help=T("cli_lsp_port_help")),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help=T("cli_lsp_host_help")),
):
    """
    Start the Boring LSP/JSON-RPC Server for IDE integration.
    Connect your VS Code extension or JetBrains LSP client to this server.
    """
    import asyncio

    from .vscode_server import VSCodeServer

    console.print(T("lsp_starting", host=host, port=port))
    server = VSCodeServer()
    asyncio.run(server.start(host=host, port=port))


@workflow_app.command("list")
def workflow_list():
    """List local workflows."""
    from .loop import WorkflowManager

    manager = WorkflowManager()
    flows = manager.list_local_workflows()

    console.print(T("workflow_list_header"))
    if not flows:
        console.print(T("workflow_list_empty"))
        return

    for f in flows:
        console.print(T("workflow_list_item", name=f))


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
        console.print(T("workflow_export_success", path=path))
    else:
        console.print(T("workflow_export_failed", message=msg))
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
        console.print(T("workflow_publish_token_missing"))
        console.print(T("workflow_publish_token_hint"))
        console.print(T("workflow_publish_token_url"))
        raise typer.Exit(1)

    from .loop import WorkflowManager

    manager = WorkflowManager()

    with console.status(f"[bold green]Publishing {name} to GitHub Gist...[/bold green]"):
        success, msg = manager.publish_workflow(name, gh_token, public)

    if success:
        console.print(T("workflow_publish_success"))
        console.print(T("workflow_publish_success_message", message=msg))
    else:
        console.print(T("workflow_publish_failed", message=msg))
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
            console.print(T("evaluate_backend_cli"))
        else:
            adapter = GeminiClient(model_name=model)
            if not adapter.is_available:
                console.print(T("evaluate_api_key_missing"))
                raise typer.Exit(1)
            console.print(T("evaluate_backend_api"))

        judge = LLMJudge(adapter)

        # Resolve Targets
        targets = [t.strip() for t in target.split(",")]

        # PAIRWISE MODE
        if level.upper() == "PAIRWISE":
            if len(targets) != 2:
                console.print(T("evaluate_pairwise_requires_two"))
                raise typer.Exit(1)

            path_a = Path(targets[0]).resolve()
            path_b = Path(targets[1]).resolve()

            if not path_a.exists() or not path_b.exists():
                console.print(T("evaluate_files_not_found"))
                raise typer.Exit(1)

            console.print(
                T("evaluate_pairwise_comparing", file_a=path_a.name, file_b=path_b.name)
            )
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
                console.print(
                    T("evaluate_pairwise_winner", winner=winner, confidence=conf, color=color)
                )
                console.print(T("evaluate_pairwise_reasoning", reasoning=reasoning))

        # DIRECT MODE
        else:
            target_path = Path(targets[0]).resolve()
            if not target_path.exists():
                console.print(T("evaluate_target_not_found", target=target))
                raise typer.Exit(1)

            console.print(T("evaluate_target_start", target=target_path.name))
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
                    console.print(T("evaluate_breakdown_header"))
                    for dim, details in result["dimensions"].items():
                        d_score = details.get("score", 0)
                        d_comment = details.get("comment", "")
                        color = "green" if d_score >= 4 else "yellow" if d_score >= 3 else "red"
                        console.print(
                            T(
                                "evaluate_breakdown_item",
                                color=color,
                                dimension=dim,
                                score=d_score,
                                comment=d_comment,
                            )
                        )

                emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
                console.print(T("evaluate_overall_score", emoji=emoji, score=score))
                console.print(T("evaluate_summary", summary=summary))

                if suggestions:
                    console.print(T("evaluate_suggestions_header"))
                    for s in suggestions:
                        console.print(T("evaluate_suggestion_item", suggestion=s))

    except Exception as e:
        console.print(T("evaluate_failed", error=str(e)))
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
        console.print(T("workflow_install_success", message=msg))
    else:
        console.print(T("workflow_install_failed", message=msg))
        raise typer.Exit(1)


@app.command()
def tutorial():
    """Start the interactive gamified tutorial."""
    from .cli import tutorial

    tutorial.start()


@app.command()
def dashboard(
    tui: bool = typer.Option(
        False, "--tui", "-T", help=T("cli_dashboard_tui_help")
    ),
):
    """
    Launch the Boring Visual Dashboard (localhost Web UI or TUI).
    """
    if tui:
        from .cli.dashboard_tui import run_tui_dashboard

        run_tui_dashboard()
        return

    import subprocess
    import sys

    dashboard_path = Path(__file__).parent / "dashboard.py"

    dashboard_path = Path(__file__).parent / "dashboard.py"

    from boring.core.dependencies import DependencyManager

    if not DependencyManager.check_gui():
        console.print(T("dashboard_deps_missing"))
        console.print(T("dashboard_deps_hint"))
        console.print(T("dashboard_deps_install"))
        raise typer.Exit(1)

    console.print(T("dashboard_launching"))
    console.print(T("dashboard_stop_hint"))

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)], check=True)
    except KeyboardInterrupt:
        console.print(T("dashboard_stopped"))
    except Exception as e:
        console.print(T("dashboard_launch_failed", error=str(e)))
        raise typer.Exit(1)


@tutorial_app.command("note")
def tutorial_note():
    """
    Generate a learning note (LEARNING.md) based on your vibe coding journey.
    """
    from .tutorial import TutorialManager

    manager = TutorialManager(settings.PROJECT_ROOT)
    path = manager.generate_learning_note()

    console.print(T("tutorial_note_created"))
    console.print(T("tutorial_note_path", path=path))
    console.print(T("tutorial_note_hint"))


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

    console.print(T("verify_start", level=level))

    verifier = CodeVerifier(settings.PROJECT_ROOT)
    passed, msg = verifier.verify_project(level.upper(), force=force)

    if passed:
        console.print(T("verify_passed"))
        console.print(T("verify_message", message=msg))
    else:
        console.print(T("verify_failed"))
        console.print(T("verify_message", message=msg))
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
        console.print(T("auto_fix_target_not_found", target=target))
        raise typer.Exit(1)

    project_root = target_path.parent
    # Walk up to find project root (marker: .git or pyproject.toml)
    current = project_root
    while current.parent != current:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            project_root = current
            break
        current = current.parent

    console.print(T("auto_fix_start", target=target_path.name, project_root=project_root))

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
                T("auto_fix_success", iterations=result["iterations"])
            )
        else:
            console.print(T("auto_fix_failed", message=result["message"]))

    except Exception as e:
        console.print(T("auto_fix_error", error=str(e)))
        raise typer.Exit(1)


# evaluate_code removed (merged into evaluate)

# ========================================
# Local Teams: Git Hooks Commands
# ========================================
hooks_app = typer.Typer(help="Git hooks for local code quality enforcement.")
app.add_typer(hooks_app, name="hooks")

team_app = typer.Typer(help="Enterprise Team features (Sync Brain, Sync RAG).")
app.add_typer(team_app, name="team")

skill_app = typer.Typer(help="Community Skills Marketplace.")
app.add_typer(skill_app, name="skill")


@skill_app.command("list")
def skill_list():
    """List installed skills."""
    from boring.skills.manager import SkillManager
    manager = SkillManager()
    skills = manager.list_installed_skills()
    if not skills:
        console.print("[dim]No skills installed.[/dim]")
    else:
        for s in skills:
            console.print(f"- {s}")

@skill_app.command("install")
def skill_install(
    url: str = typer.Argument(..., help="Git URL of the skill"),
    name: str = typer.Option(None, help="Name of the skill"),
):
    """Install a skill from a Git URL."""
    from boring.skills.manager import SkillManager
    manager = SkillManager()
    skill_name = name or url.split("/")[-1].replace(".git", "")
    if manager.install_skill(url, skill_name):
        console.print(f"[green]Skill '{skill_name}' installed successfully![/green]")
    else:
        console.print(f"[red]Failed to install skill '{skill_name}'.[/red]")

@skill_app.command("search")
def skill_search(query: str):
    """Search for skills in the registry."""
    from boring.skills.manager import SkillManager
    manager = SkillManager()
    results = manager.search_registry(query)
    if not results:
        console.print(f"[yellow]No skills found for '{query}'[/yellow]")
        return

    from rich.table import Table
    table = Table(title=f"Skill Search Results for '{query}'")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("URL", style="dim")

    for r in results:
        table.add_row(r["name"], r["desc"], r["url"])

    console.print(table)


@hooks_app.command("install")
def hooks_install():
    """Install Boring Git hooks (pre-commit, pre-push)."""
    from .hooks import HooksManager

    manager = HooksManager()
    success, msg = manager.install_all()

    if success:
        console.print(T("hooks_install_success"))
        console.print(T("hooks_install_message", message=msg))
        console.print(T("hooks_install_hint"))
    else:
        console.print(T("hooks_install_failed", message=msg))
        raise typer.Exit(1)


@hooks_app.command("uninstall")
def hooks_uninstall():
    """Remove Boring Git hooks."""
    from .hooks import HooksManager

    manager = HooksManager()
    success, msg = manager.uninstall_all()

    if success:
        console.print(T("hooks_removed"))
        console.print(T("hooks_uninstall_message", message=msg))
    else:
        console.print(T("hooks_uninstall_failed", message=msg))
        raise typer.Exit(1)


@hooks_app.command("status")
def hooks_status():
    """Show status of installed hooks."""
    from .hooks import HooksManager

    manager = HooksManager()
    status = manager.status()

    if not status["is_git_repo"]:
        console.print(T("hooks_status_not_repo"))
        return

    console.print(T("hooks_status_header"))
    for hook_name, info in status["hooks"].items():
        if info["installed"]:
            if info["is_boring_hook"]:
                console.print(
                    T("hooks_status_active", hook_name=hook_name)
                )
            else:
                console.print(
                    T("hooks_status_custom", hook_name=hook_name)
                )
        else:
            console.print(
                T("hooks_status_missing", hook_name=hook_name)
            )


@app.command()
def learn():
    """
    Extract learned patterns from project history (.boring_memory).

    Analyses successful loops and error fixes to create reusable patterns
    in .boring_brain/learned_patterns/.
    """
    from .intelligence.brain_manager import create_brain_manager
    from .storage import SQLiteStorage

    console.print(T("learn_start"))

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
            console.print(T("learn_new_patterns", count=new_count))
        else:
            console.print(T("learn_no_patterns"))

        console.print(T("learn_total_patterns", total=total))
    else:
        console.print(T("learn_failed", error=result.get("error")))
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
    console.print(T("rag_index_start", root=root))

    retriever = create_rag_retriever(root)
    if not retriever.is_available:
        console.print(T("rag_deps_missing"))
        raise typer.Exit(1)

    # If force is True, incremental is effectively False
    if force:
        incremental = False

    count = retriever.build_index(force=force, incremental=incremental)
    stats = retriever.get_stats()

    if stats.index_stats:
        idx = stats.index_stats
        console.print(T("rag_index_ready", status="rebuilt" if force else "ready"))
        console.print(T("rag_index_files", count=idx.total_files))
        console.print(T("rag_index_chunks", count=idx.total_chunks))
        console.print(T("rag_index_functions", count=idx.functions))
        console.print(T("rag_index_classes", count=idx.classes))
        console.print(
            T("rag_index_script_chunks", count=getattr(idx, "script_chunks", 0))
        )
    else:
        console.print(T("rag_index_built", count=count))


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
        console.print(T("rag_not_initialized"))
        raise typer.Exit(1)

    results = retriever.retrieve(query, n_results=limit, threshold=threshold)

    if not results:
        console.print(T("rag_no_results", query=query))
        return

    console.print(T("rag_results_header", query=query))
    for i, res in enumerate(results, 1):
        chunk = res.chunk
        console.print(
            T(
                "rag_result_item",
                index=i,
                file_path=chunk.file_path,
                name=chunk.name,
                score=res.score,
            )
        )
        # Show a snippet
        snippet = chunk.content[:200].replace("\n", " ")
        console.print(T("rag_result_snippet", snippet=snippet))


# ========================================
# Model Management
# ========================================
app.add_typer(model.app, name="model", help="Manage local LLM models (Offline Mode)")
app.add_typer(offline.app, name="offline", help="Manage Offline Mode")

# ========================================
# Workspace Management
# ========================================
workspace_app = typer.Typer(help="Manage multi-project workspace.")
app.add_typer(workspace_app, name="workspace")


@workspace_app.command("list")
def workspace_list(tag: str | None = typer.Option(None, "--tag", "-t", help="Filter by tag")):
    """List all projects in the workspace."""
    from .workspace import get_workspace_manager

    manager = get_workspace_manager()
    projects = manager.list_projects(tag)

    if not projects:
        console.print(T("workspace_empty"))
        return

    console.print(T("workspace_list_header", count=len(projects)))

    for p in projects:
        name = p["name"]
        path = p["path"]
        is_active = p.get("is_active", False)
        marker = "🟢" if is_active else "⚪"
        style = "bold green" if is_active else "white"

        console.print(
            T("workspace_list_item", marker=marker, style=style, name=name, path=path)
        )
        if p.get("description"):
            console.print(T("workspace_list_description", description=p["description"]))


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
        console.print(T("workspace_add_success", name=name))
    else:
        console.print(T("workspace_add_failed", message=result["message"]))
        raise typer.Exit(1)


@workspace_app.command("remove")
def workspace_remove(name: str = typer.Argument(..., help="Project name to remove")):
    """Remove a project from the workspace."""
    from .workspace import get_workspace_manager

    manager = get_workspace_manager()
    result = manager.remove_project(name)

    if result["status"] == "SUCCESS":
        console.print(T("workspace_remove_success", name=name))
    else:
        console.print(T("workspace_remove_failed", message=result["message"]))
        raise typer.Exit(1)


@workspace_app.command("switch")
def workspace_switch(name: str = typer.Argument(..., help="Project name to switch to")):
    """Switch active context to another project."""
    from .workspace import get_workspace_manager

    manager = get_workspace_manager()
    result = manager.switch_project(name)

    if result["status"] == "SUCCESS":
        console.print(T("workspace_switch_success", name=name))
        console.print(T("workspace_switch_path", path=result["path"]))
    else:
        console.print(T("workspace_switch_failed", message=result["message"]))
        raise typer.Exit(1)


# --- Predictive Intelligence CLI Commands (V14.0) ---


@app.command()
def predict(
    diff: bool = typer.Option(False, "--diff", "-d", help="Analyze staged changes only"),
    file: str = typer.Option(None, "--file", "-f", help="Specific file to analyze"),
):
    """
    🔮 Predictive Error Detection - Scan for potential risks before committing.

    Analyzes code for anti-patterns, historical error correlations, and security issues.
    """
    from .mcp.tools.vibe import run_predict_errors

    console.print(T("predict_header"))

    # Use the MCP tool implementation
    try:
        target = file or "."
        with console.status(f"[bold blue]Predicting risks for {target}...[/bold blue]"):
            result = run_predict_errors(file_path=target)
        if isinstance(result, dict) and result.get("status") == "success":
            data = result.get("data") or {}
            predictions = data.get("predictions") or []
            static_issues = data.get("static_issues") or []

            summary = result.get("message")
            if summary:
                console.print(summary)

            if predictions:
                from rich.table import Table

                table = Table(title=T("predict_tui_predictions_title"))
                table.add_column(T("predict_tui_col_rank"), justify="right")
                table.add_column(T("predict_tui_col_type"))
                table.add_column(T("predict_tui_col_confidence"), justify="right")
                table.add_column(T("predict_tui_col_tip"))

                for i, item in enumerate(predictions, 1):
                    table.add_row(
                        str(i),
                        str(item.get("error_type", "")),
                        f"{item.get('confidence', 0) * 100:.0f}%",
                        str(item.get("prevention_tip", "")),
                    )
                console.print(table)

            if static_issues:
                from rich.table import Table

                table = Table(title=T("predict_tui_static_title"))
                table.add_column(T("predict_tui_col_severity"))
                table.add_column(T("predict_tui_col_category"))
                table.add_column(T("predict_tui_col_line"), justify="right")
                table.add_column(T("predict_tui_col_message"))
                table.add_column(T("predict_tui_col_fix"))

                for issue in static_issues:
                    table.add_row(
                        str(issue.get("severity", "")),
                        str(issue.get("category", "")),
                        str(issue.get("line_number", "")),
                        str(issue.get("message", "")),
                        str(issue.get("suggested_fix", "")),
                    )
                console.print(table)
            if not predictions and not static_issues:
                console.print(T("predict_result", result=result))
        else:
            console.print(T("predict_result", result=result))
    except Exception as e:
        console.print(T("predict_failed", error=str(e)))
        raise typer.Exit(1)


@app.command()
def bisect(
    error: str = typer.Argument(
        ..., help="Error message to trace (e.g. 'ValueError: name not defined')"
    ),
    file: str = typer.Option(None, "--file", "-f", help="File where error occurred"),
    depth: int = typer.Option(10, "--depth", "-n", help="Number of recent commits to analyze"),
):
    """
    🔍 AI Git Bisect - Intelligently trace the source of a bug.

    Unlike traditional binary search, this uses semantic analysis and
    Brain pattern matching to identify suspicious commits.
    """
    from .intelligence.predictor import Predictor

    console.print(T("bisect_header"))
    console.print(T("bisect_tracing", error=error))

    try:
        predictor = Predictor()
        with console.status("[bold blue]Tracing bug source across Git history...[/bold blue]"):
            result = predictor.analyze_regression(
                error_message=error,
                target_file=file,
                max_commits=depth,
            )

        if result.get("suspects"):
            console.print(T("bisect_suspects_header"))
            for suspect in result["suspects"][:5]:
                score = suspect.get("score", 0)
                sha = suspect.get("sha", "unknown")[:7]
                msg = suspect.get("message", "No message")[:50]
                console.print(
                    T("bisect_suspect_item", score=score, sha=sha, message=msg)
                )
        else:
            console.print(T("bisect_no_suspects"))

        if result.get("recommendation"):
            console.print(
                T("bisect_recommendation", recommendation=result["recommendation"])
            )

    except Exception as e:
        console.print(T("bisect_failed", error=str(e)))
        raise typer.Exit(1)


@team_app.command("sync-brain")
def team_sync_brain(
    direction: str = typer.Argument("pull", help="Sync direction: 'pull' or 'push'"),
):
    """
    🧠 Sync Team Brain (Patterns & Skills).
    """
    from .services.team import TeamSyncManager

    manager = TeamSyncManager()
    manager.sync_brain(direction=direction)


@team_app.command("sync-rag")
def team_sync_rag(
    direction: str = typer.Argument("pull", help="Sync direction: 'pull' or 'push'"),
):
    """
    📂 Sync Team RAG (Vector Index).
    """
    from .services.team import TeamSyncManager

    manager = TeamSyncManager()
    manager.sync_rag(direction=direction)


@app.command()
def diagnostic(
    last_known_good: str = typer.Option(
        "HEAD~10", "--last-known-good", "-l", help="Last known good commit"
    ),
):
    """
    🩺 Deep Diagnostic - Comprehensive project health analysis.

    Combines predictive analysis with historical patterns for intermittent bugs.
    """
    console.print(T("diagnostic_header"))
    console.print(T("diagnostic_comparing", commit=last_known_good))

    try:
        from .intelligence.predictor import Predictor

        predictor = Predictor()
        with console.status("[bold blue]Analyzing project health...[/bold blue]"):
            result = predictor.deep_diagnostic(since_commit=last_known_good)

        console.print(
            T(
                "diagnostic_risk_score",
                score=result.get("risk_score", "N/A"),
            )
        )

        if result.get("issues"):
            console.print(T("diagnostic_issues_header"))
            for issue in result["issues"][:10]:
                console.print(T("diagnostic_issue_item", issue=issue))

        if result.get("patterns"):
            console.print(T("diagnostic_patterns_header"))
            for pattern in result["patterns"][:3]:
                console.print(T("diagnostic_pattern_item", pattern=pattern))

    except Exception as e:
        console.print(T("diagnostic_failed", error=str(e)))
        raise typer.Exit(1)


@app.command()
def version(
    check: bool = typer.Option(
        False, "--check", "-c", help="Verify consistency across project files"
    ),
):
    """Show version info."""
    from boring import __version__

    console.print(T("version_simple", version=__version__))

    if check:
        console.print(T("version_check_start"))
        try:
            from boring.utils.version import verify_version_consistency

            success, _ = verify_version_consistency()
            if not success:
                raise typer.Exit(1)
        except ImportError:
            console.print(T("version_check_failed"))
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
