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

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console

from .config import settings
from .loop import AgentLoop
from .circuit import show_circuit_status, reset_circuit_breaker, CB_STATE_FILE

HELP_TEXT = """
[bold blue]Boring - Autonomous AI Development Agent[/bold blue]

A powerful AI coding assistant that iteratively improves your project using:
- [green]Memory System[/green]: Learns from mistakes across sessions
- [green]Advanced Verification[/green]: Syntax, Linting (ruff), and Testing (pytest)
- [green]Context Injection[/green]: Smart project context management

[bold]Common Usage:[/bold]
  $ [cyan]boring-setup "my-new-project"[/cyan]   # Create a new project
  $ [cyan]cd my-new-project[/cyan]                # Enter project
  $ [cyan]boring start[/cyan]                      # Start coding loop
  $ [cyan]boring start --verify FULL[/cyan]        # Start with strict verification
"""

EPILOG_TEXT = """
[bold]Examples:[/bold]
  [dim]# Run with full verification (Syntax + Lint + Tests)[/dim]
  $ boring start --verify FULL --model gemini-3-pro

  [dim]# Install extensions (context7, criticalthink)[/dim]
  $ boring setup-extensions

  [dim]# Check project health[/dim]
  $ boring status

[bold]Documentation:[/bold] https://github.com/your-username/boring-gemini
"""

app = typer.Typer(
    name="boring",
    help=HELP_TEXT,
    epilog=EPILOG_TEXT,
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()

@app.command()
def start(
    backend: str = typer.Option("api", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"),
    model: str = typer.Option(settings.DEFAULT_MODEL, "--model", "-m", help="Gemini model to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    verification: str = typer.Option("STANDARD", "--verify", help="Verification level: BASIC, STANDARD, FULL"),
    calls: int = typer.Option(settings.MAX_HOURLY_CALLS, "--calls", "-c", help="Max hourly API calls"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Custom prompt file path"),
    timeout: int = typer.Option(settings.TIMEOUT_MINUTES, "--timeout", "-t", help="Timeout in minutes per loop"),
    experimental: bool = typer.Option(False, "--experimental", "-x", help="Use new State Pattern architecture (v4.0)"),
    # Debugger / Self-Healing
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable verbose debugger tracing"),
    self_heal: bool = typer.Option(False, "--self-heal", "-H", help="Enable crash auto-repair (Self-Healing 2.0)"),
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
        use_cli = (backend == "cli")
        
        if use_cli:
            console.print("[bold cyan]🔒 Privacy Mode: Using local Gemini CLI[/bold cyan]")
            console.print("[dim]No API key required. Ensure you've run 'gemini login'.[/dim]")
        else:
            console.print("[bold blue]📡 API Mode: Using Gemini SDK[/bold blue]")

        # Debugger Setup
        from .debugger import BoringDebugger
        debugger = BoringDebugger(model_name=model if use_cli else "default", enable_healing=self_heal, verbose=debug)

        # Choose loop implementation
        if experimental:
            console.print("[bold magenta]🧪 Experimental: Using State Pattern Architecture[/bold magenta]")
            from .loop import StatefulAgentLoop
            loop = StatefulAgentLoop(
                model_name=model,
                use_cli=use_cli,
                verbose=verbose,
                verification_level=verification.upper(),
                prompt_file=Path(prompt) if prompt else None
            )
        else:
            loop = AgentLoop(
                model_name=model,
                use_cli=use_cli,
                verbose=verbose,
                verification_level=verification.upper(),
                prompt_file=Path(prompt) if prompt else None
            )
            console.print(f"[bold green]Starting Boring Loop (Timeout: {settings.TIMEOUT_MINUTES}m)[/bold green]")
        
        if self_heal:
            console.print("[bold yellow]🚑 Self-Healing Enabled: I will attempt to fix crashes automatically.[/bold yellow]")

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

@app.command()
def status():
    """
    Show current loop status and memory summary.
    """
    from .memory import MemoryManager
    
    memory = MemoryManager(settings.PROJECT_ROOT)
    state = memory.get_project_state()
    
    console.print("[bold blue]Boring Project Status[/bold blue]")
    console.print(f"  Project: {state.get('project_name', 'Unknown')}")
    console.print(f"  Total Loops: {state.get('total_loops', 0)}")
    console.print(f"  Success: {state.get('successful_loops', 0)} | Failed: {state.get('failed_loops', 0)}")
    console.print(f"  Last Activity: {state.get('last_activity', 'Never')}")
    
    # Show recent history
    history = memory.get_loop_history(last_n=3)
    if history:
        console.print("\n[bold]Recent Loops:[/bold]")
        for h in history:
            status_icon = "✓" if h.get("status") == "SUCCESS" else "✗"
            console.print(f"  {status_icon} Loop #{h.get('loop_id', '?')}: {h.get('status', 'UNKNOWN')}")

@app.command()
def circuit_status():
    """
    Show circuit breaker details.
    """
    show_circuit_status()

@app.command()
def reset_circuit():
    """
    Reset the circuit breaker.
    """
    reset_circuit_breaker("Manual reset via CLI")
    console.print("[green]Circuit breaker reset.[/green]")

@app.command()
def setup_extensions():
    """
    Install recommended Gemini CLI extensions for enhanced capabilities.
    """
    from .extensions import setup_project_extensions, create_criticalthink_command, create_speckit_command
    
    setup_project_extensions(settings.PROJECT_ROOT)
    create_criticalthink_command(settings.PROJECT_ROOT)
    create_speckit_command(settings.PROJECT_ROOT)
    console.print("[green]Extensions setup complete.[/green]")

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
    backend: str = typer.Option("api", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)")
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
    from .health import run_health_check, print_health_report
    
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
        ver = pkg_version("boring-gemini")
    except Exception:
        ver = "7.0.0"
    
    console.print(f"[bold blue]Boring[/bold blue] v{ver}")
    console.print(f"  Model: {settings.DEFAULT_MODEL}")
    console.print(f"  Project: {settings.PROJECT_ROOT}")

# --- Workflow Hub CLI ---
workflow_app = typer.Typer(help="Manage Boring Workflows (Hub)")
app.add_typer(workflow_app, name="workflow")

@workflow_app.command("list")
def workflow_list():
    """List local workflows."""
    from .workflow_manager import WorkflowManager
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
    author: str = typer.Option("Anonymous", "--author", "-a", help="Author name")
):
    """Export a workflow to .bwf.json package."""
    from .workflow_manager import WorkflowManager
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
    token: str = typer.Option(None, "--token", "-t", help="GitHub Personal Access Token (or set GITHUB_TOKEN env var)"),
    public: bool = typer.Option(True, "--public/--private", help="Make Gist public or secret")
):
    """Publish a workflow to GitHub Gist registry."""
    import os
    
    # Resolve token
    gh_token = token or os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        console.print("[red]Error: GitHub Token required.[/red]")
        console.print("Please set [bold]GITHUB_TOKEN[/bold] env var or use [bold]--token[/bold] option.")
        console.print("Create one at: https://github.com/settings/tokens (Scpoe: gist)")
        raise typer.Exit(1)

    from .workflow_manager import WorkflowManager
    manager = WorkflowManager()
    
    with console.status(f"[bold green]Publishing {name} to GitHub Gist...[/bold green]"):
        success, msg = manager.publish_workflow(name, gh_token, public)
    
    if success:
        console.print(f"[green]✓ Published Successfully![/green]")
        console.print(msg)
    else:
        console.print(f"[red]Publish Failed: {msg}[/red]")
        raise typer.Exit(1)

@app.command()
def evaluate(
    target: str = typer.Argument(..., help="File path to evaluate"),
    context: str = typer.Option("", "--context", "-c", help="Optional context"),
    level: str = typer.Option("DIRECT", "--level", "-l", help="Evaluation level"),
    backend: str = typer.Option("cli", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"),
    model: str = typer.Option("default", "--model", "-m", help="Gemini model to use")
):
    """
    Evaluate code quality using LLM-as-a-Judge.
    """
    from .judge import LLMJudge
    from .cli_client import GeminiCLIAdapter
    from .gemini_client import GeminiClient
    
    # Check if target exists
    target_path = Path(target)
    if not target_path.exists():
        console.print(f"[red]Error: Target '{target}' not found.[/red]")
        raise typer.Exit(1)
        
    console.print(f"[bold blue]🤔 Evaluating {target_path.name}...[/bold blue]")

    try:
        if backend.lower() == "cli":
            adapter = GeminiCLIAdapter(model_name=model)
            console.print("[dim]Using Local CLI Backend[/dim]")
        else:
            # API Mode
            adapter = GeminiClient(model_name=model)
            if not adapter.is_available:
                console.print("[red]Error: API Key not found. Use --backend cli or set GOOGLE_API_KEY.[/red]")
                raise typer.Exit(1)
            console.print("[dim]Using Gemini API Backend[/dim]")

        judge = LLMJudge(adapter)
        
        content = target_path.read_text(encoding="utf-8")
        result = judge.grade_code(target_path.name, content)
        
        score = result.get("score", 0)
        summary = result.get("summary", "No summary")
        suggestions = result.get("suggestions", [])
        
        emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
        console.print(f"\n[bold]{emoji} Score: {score}/5.0[/bold]")
        console.print(f"[italic]{summary}[/italic]\n")
        
        if suggestions:
            console.print("[bold]💡 Suggestions:[/bold]")
            for s in suggestions:
                console.print(f"  - {s}")
                
    except Exception as e:
        console.print(f"[red]Evaluation failed: {e}[/red]")
        raise typer.Exit(1)

@workflow_app.command("install")
def workflow_install(
    source: str = typer.Argument(..., help="File path or URL to .bwf.json")
):
    """Install a workflow from file or URL."""
    from .workflow_manager import WorkflowManager
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
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        console.print("[bold red]❌ Dashboard dependencies not found.[/bold red]")
        console.print("\nPlease install the GUI extras:")
        console.print("  [cyan]pip install -e \".\\[gui\\]\"[/cyan]")
        raise typer.Exit(1)

    console.print(f"🚀 Launching Dashboard at [bold green]http://localhost:8501[/bold green]")
    console.print("Press Ctrl+C to stop.")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(dashboard_path)],
            check=True
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to launch dashboard:[/bold red] {e}")
        raise typer.Exit(1)



@app.command()
def verify(
    level: str = typer.Option("STANDARD", "--level", "-l", help="Verification level: BASIC, STANDARD, FULL, SEMANTIC"),
):
    """
    Run code verification on the project.
    """
    from .verification import CodeVerifier
    
    console.print(f"[bold blue]🔍 Running Verification (Level: {level})[/bold blue]")
    
    verifier = CodeVerifier(settings.PROJECT_ROOT)
    passed, msg = verifier.verify_project(level.upper())
    
    if passed:
        console.print(f"[green]✅ Verification Passed[/green]")
        console.print(msg)
    else:
        console.print(f"[red]❌ Verification Failed[/red]")
        console.print(msg)
        raise typer.Exit(code=1)

@app.command("auto-fix")

def auto_fix(
    target: str = typer.Argument(..., help="File path to fix"),
    max_attempts: int = typer.Option(3, "--max-attempts", "-n", help="Max fix attempts per cycle"),
    backend: str = typer.Option("cli", "--backend", "-b", help="Backend: 'api' (SDK) or 'cli' (local CLI)"),
    model: str = typer.Option("default", "--model", "-m", help="Gemini model to use"),
    verification_level: str = typer.Option("STANDARD", "--verify", help="Verification level")
):
    """
    Auto-fix syntax and linting errors in a file.
    """
    from .auto_fix import AutoFixPipeline
    from .cli_client import GeminiCLIAdapter
    from .gemini_client import GeminiClient
    from .verification import CodeVerifier
    from .loop import AgentLoop
    from .memory import MemoryManager
    
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
        return {
            "passed": passed,
            "message": msg,
            "issues": [msg] if not passed else []
        }

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
                verbose=False # Keep it cleaner
            )
            
            # Run loop
            loop.run()
            
            # Check result
            memory = MemoryManager(project_path_obj)
            history = memory.get_loop_history(last_n=1)
            
            if history and history[0].get('status') == 'SUCCESS':
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
            max_iterations=max_attempts, # Pipeline uses this for overall cycles
            verification_level=verification_level
        )
        
        result = pipeline.run(run_boring_wrapper, verify_wrapper)
        
        if result["status"] == "SUCCESS":
            console.print(f"[green]✅ Optimized successfully after {result['iterations']} iterations.[/green]")
        else:
            console.print(f"[red]❌ {result['message']}[/red]")
            
    except Exception as e:
        console.print(f"[red]Auto-fix failed: {e}[/red]")
        raise typer.Exit(1)

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
        console.print(f"[bold green]✅ Hooks installed![/bold green]")
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
        console.print(f"[yellow]Hooks removed.[/yellow]")
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
    from .brain_manager import create_brain_manager
    from .storage import SQLiteStorage
    
    console.print(f"[bold blue]🧠 Analyzing Project History...[/bold blue]")
    
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
        name = p['name']
        path = p['path']
        is_active = p.get('is_active', False)
        marker = "🟢" if is_active else "⚪"
        style = "bold green" if is_active else "white"
        
        console.print(f"  {marker} [{style}]{name}[/{style}] [dim]({path})[/dim]")
        if p.get('description'):
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
