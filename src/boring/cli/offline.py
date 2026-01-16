import re

import typer
from rich.console import Console

from boring.core.config import settings, update_toml_config

app = typer.Typer(help="Manage Offline Mode")
console = Console()


def _update_env_value(key: str, value: str) -> bool:
    """Update or insert a key in .env for persistence."""
    env_file = settings.PROJECT_ROOT / ".env"
    val = value

    if not env_file.exists():
        env_file.write_text(f"{key}={val}\n", encoding="utf-8")
        return True

    content = env_file.read_text(encoding="utf-8")

    # Regex to find existing key
    pattern = re.compile(f"^{key}=.*$", re.MULTILINE)

    if pattern.search(content):
        new_content = pattern.sub(f"{key}={val}", content)
    else:
        # Ensure newline at end of existing content before appending
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + f"{key}={val}\n"

    env_file.write_text(new_content, encoding="utf-8")
    return True


def _update_env_file(enable: bool):
    """Fallback method: Update .env file for persistence."""
    key = "BORING_OFFLINE_MODE"
    val = "true" if enable else "false"
    return _update_env_value(key, val)


@app.command()
def enable():
    """
    Enable Offline Mode.

    Disconnects from Cloud APIs and forces local tool usage.
    Persists setting to .boring.toml (priority) or .env.
    """
    success = False
    method = ""

    # 1. Check if we have a local model configured/downloaded
    from boring.llm.local_llm import LocalLLM

    # Try initializing to see if it finds a model
    llm = LocalLLM.from_settings()
    if not llm.is_available:
        console.print("[yellow]⚠️  No local LLM model found.[/yellow]")
        if typer.confirm("Would you like to run the setup wizard to download one?"):
            setup(enable_offline=True)  # Call setup directly
            return
        else:
            console.print("[dim]You can run `boring offline setup` later.[/dim]")

    # 1. Try TOML (Project Config)
    if update_toml_config("offline_mode", True):
        success = True
        method = ".boring.toml"
    # 2. Try .env (Environment Config)
    elif _update_env_file(True):
        success = True
        method = ".env"

    if success:
        console.print(f"[bold green]🔌 Offline Mode ENABLED[/bold green] (saved to {method})")
        console.print("Cloud API calls will be blocked. Local LLMs will be prioritized.")
    else:
        console.print("[bold red]Failed to persist configuration.[/bold red]")
        raise typer.Exit(1)


@app.command()
def disable():
    """
    Disable Offline Mode.

    Restores Cloud API access.
    """
    success = False
    method = ""

    # 1. Try TOML
    if update_toml_config("offline_mode", False):
        success = True
        method = ".boring.toml"
    # 2. Try .env (set to false to override any true)
    elif _update_env_file(False):
        success = True
        method = ".env"

    if success:
        console.print(f"[bold green]🌐 Offline Mode DISABLED[/bold green] (saved to {method})")
        console.print("Cloud API access restored.")
    else:
        console.print("[bold red]Failed to persist configuration.[/bold red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Check current Offline Mode status."""
    is_offline = settings.OFFLINE_MODE

    if is_offline:
        console.print("[bold blue]Status: OFFLINE[/bold blue]")
        console.print("No internet connection required for core functions.")
    else:
        console.print("[bold cyan]Status: ONLINE[/bold cyan]")
        console.print("Cloud APIs are enabled.")


@app.command()
def setup(
    model_id: str = typer.Option(
        "qwen2.5-coder-1.5b",
        "--model",
        "-m",
        help="Recommended model ID to download",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download"),
    enable_offline: bool = typer.Option(True, "--enable/--no-enable", help="Enable Offline Mode"),
):
    """
    One-click offline setup.

    Downloads a recommended local model and configures environment
    for offline-first operation.
    """
    from boring.llm.local_llm import RECOMMENDED_MODELS, download_model

    if model_id not in RECOMMENDED_MODELS:
        console.print(f"[red]Unknown model ID: {model_id}[/red]")
        console.print(f"Available: {', '.join(RECOMMENDED_MODELS.keys())}")
        raise typer.Exit(1)

    console.print(f"[bold green]⬇️  Downloading model: {model_id}[/bold green]")
    path = download_model(model_id, progress=True)
    if not path:
        console.print("[red]Download failed.[/red]")
        raise typer.Exit(1)

    if update_toml_config("local_llm_model", str(path)):
        console.print("[green]Saved local model path to .boring.toml[/green]")
    else:
        _update_env_value("BORING_LOCAL_LLM_MODEL", str(path))
        console.print("[green]Saved local model path to .env[/green]")

    if enable_offline:
        if update_toml_config("offline_mode", True):
            console.print("[green]Offline Mode ENABLED (saved to .boring.toml)[/green]")
        else:
            _update_env_file(True)
            console.print("[green]Offline Mode ENABLED (saved to .env)[/green]")

    console.print("[bold green]✅ Offline setup complete![/bold green]")


if __name__ == "__main__":
    app()
