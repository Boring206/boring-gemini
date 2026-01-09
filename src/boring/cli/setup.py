import os
import re
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

console = Console()
templates_dir = Path(__file__).parent / "templates"

setup_app = typer.Typer(help="Boring project setup commands.")
import_app = typer.Typer(help="Boring PRD import commands.")

# Templates removed in v10.19.0 - we now recommend using official Gemini/Claude Skills
# See: docs/skills_guide.md


@setup_app.command("new")
def setup_new_project(
    project_name: str = typer.Argument(..., help="Name for the new Boring project."),
    template: str = typer.Option(
        None,
        "--template",
        "-t",
        help="[DEPRECATED] Templates removed. We now recommend using Gemini/Claude Skills. See docs/skills_guide.md",
    ),
):
    project_path = Path(project_name)
    if not project_path.is_absolute():
        project_path = Path.cwd() / project_name

    if project_path.exists():
        console.print(
            f"[bold red]Error:[/bold red] Project directory '{project_name}' already exists."
        )
        raise typer.Exit(1)

    console.print(f"🚀 Setting up Boring project: [bold green]{project_name}[/bold green]")

    project_path.mkdir(parents=True, exist_ok=False)
    os.chdir(project_path)  # Change to new project directory

    # Create structure
    (project_path / "specs/stdlib").mkdir(parents=True, exist_ok=True)
    (project_path / "src").mkdir(parents=True, exist_ok=True)
    (project_path / "examples").mkdir(parents=True, exist_ok=True)
    (project_path / "logs").mkdir(parents=True, exist_ok=True)
    (project_path / "docs/generated").mkdir(parents=True, exist_ok=True)

    # Create openspec structure (Spec-Driven Development)
    (project_path / "openspec/specs").mkdir(parents=True, exist_ok=True)
    (project_path / "openspec/changes").mkdir(parents=True, exist_ok=True)

    # Template deprecation notice
    if template:
        console.print("\n[bold yellow]⚠️ 範本功能已移除 (Templates Deprecated)[/bold yellow]")
        console.print("我們建議使用官方的 Gemini Skills 或 Claude Skills，它們更強大且持續更新。")
        console.print(
            "📚 詳情請參考: [link=file://docs/skills_guide.md]docs/skills_guide.md[/link]\n"
        )

    # Create default PROMPT.md
    (project_path / "PROMPT.md").write_text(
        f"# {project_name}\n\n"
        "## Goal\n"
        "Describe your project goal here.\n\n"
        "## Tech Stack\n"
        "- Define your technology choices\n\n"
        "## Features\n"
        "- [ ] Feature 1\n"
        "- [ ] Feature 2\n\n"
        "## 💡 Pro Tip\n"
        "Use Gemini CLI Skills (`.gemini/skills/`) or Claude Skills (`.claude/skills/`)\n"
        "for advanced templates. See `docs/skills_guide.md` for recommendations.\n",
        encoding="utf-8",
    )

    # Create default GEMINI.md
    (project_path / "GEMINI.md").write_text(
        "# Boring Context\n\nRole: Autonomous AI developer\n", encoding="utf-8"
    )

    # Create CONTEXT.md for AI agent guidance
    (project_path / "CONTEXT.md").write_text(
        "# Project Context\n\n"
        "## Purpose\n"
        f"**{project_name}** - A Boring-managed autonomous development project.\n\n"
        "## Conventions\n"
        "- Type hints mandatory\n"
        "- Google-style docstrings\n"
        "- Run tests after changes\n\n"
        "## How to Work\n"
        "1. Follow PROMPT.md instructions\n"
        "2. Update @fix_plan.md as tasks complete\n"
        "3. Signal completion when all tasks are done\n",
        encoding="utf-8",
    )

    # Create openspec/project.md
    (project_path / "openspec/project.md").write_text(
        f"# {project_name}\n\n"
        "## Tech Stack\n"
        "- Language: [Define]\n"
        "- Testing: Pytest\n\n"
        "## Conventions\n"
        "- Type hints required\n"
        "- Google-style docstrings\n",
        encoding="utf-8",
    )

    # Copy specs templates
    if (templates_dir / "specs").exists():
        shutil.copytree(templates_dir / "specs", project_path / "specs", dirs_exist_ok=True)

    # Copy workflow templates (Agentic Workflows)
    if (templates_dir / "workflows").exists():
        workflows_dest = project_path / ".agent" / "workflows"
        workflows_dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(templates_dir / "workflows", workflows_dest, dirs_exist_ok=True)

    # Initialize git
    subprocess.run(["git", "init"], stdin=subprocess.DEVNULL, check=True, capture_output=True)
    (project_path / "README.md").write_text(f"# {project_name}\n")
    subprocess.run(["git", "add", "."], stdin=subprocess.DEVNULL, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial Boring project setup"],
        stdin=subprocess.DEVNULL,
        check=True,
        capture_output=True,
    )

    # Success message
    console.print(f"\n[bold green]✅ Project '{project_name}' created successfully![/bold green]")
    console.print(f"Location: {project_path}")

    # Tutorial Hook
    from .tutorial import TutorialManager

    tutorial = TutorialManager(project_path)
    tutorial.show_tutorial("first_project")

    console.print("\n[bold]Next Steps:[/bold]")
    console.print(f"  $ cd {project_name}")
    console.print("  $ boring health         # Verify environment")
    console.print("  $ boring verify         # Check initial state")
    console.print("  # Then add to your IDE as an MCP Server")


@import_app.command("prd")
def import_prd_to_project(
    source_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="Path to your PRD/specification file (any format)."
    ),
    project_name: str = typer.Argument(
        None, help="Name for the new Boring project (optional, defaults to filename)."
    ),
):
    """
    Converts a PRD/specification file into a Boring project using Gemini.
    """
    if not project_name:
        project_name = source_file.stem  # Use filename as project name

    if not source_file.is_file():
        console.print(
            f"[bold red]Error:[/bold red] Source path '{source_file}' is a directory. Please provide a file path."
        )
        raise typer.Exit(1)

    project_path = Path.cwd() / project_name

    if project_path.exists():
        console.print(
            f"[bold red]Error:[/bold red] Project directory '{project_name}' already exists."
        )
        raise typer.Exit(1)

    console.print(
        f"🚀 Importing PRD '[bold green]{source_file.name}[/bold green]' into project: [bold green]{project_name}[/bold green]"
    )

    # Create new project first using the setup_new_project logic
    # Temporarily change directory to create project in correct location
    original_cwd = Path.cwd()
    try:
        os.chdir(original_cwd)  # Ensure we are in the correct CWD before calling setup_new_project
        setup_new_project(project_name)
    finally:
        os.chdir(original_cwd)  # Change back if needed, though setup_new_project changes it

    # Now, change into the newly created project directory
    os.chdir(project_path)

    # Copy source file into the new project for Gemini to access
    shutil.copy(original_cwd / source_file, project_path / source_file.name)

    # Define the conversion prompt for Gemini
    conversion_prompt_content = f"""
# PRD to Boring Conversion Task

You are tasked with converting the attached Product Requirements Document (PRD) or specification file
into the format required by the "Boring for Gemini" autonomous agent.

## Input Analysis
Analyze the provided specification file (named `{source_file.name}`) and extract:
- Project goals and objectives
- Core features and requirements
- Technical constraints and preferences
- Priority levels and phases

## Required Outputs

Create these files in the current directory:

### 1. PROMPT.md
Transform the PRD into concise, actionable development instructions for the Boring agent.
This should be the main set of goals and principles for the AI.

### 2. @fix_plan.md
Convert the requirements into a prioritized, actionable task list in Markdown checklist format.
For example:
```markdown
# Boring Fix Plan

## High Priority
- [ ] Implement user authentication
- [ ] Design database schema

## Medium Priority
- [ ] Add password reset functionality

## Completed
- [x] Project setup
```

### 3. specs/requirements.md
Extract detailed technical specifications from the PRD into this file. Preserve as much technical detail as possible.

## Instructions
1. Read and analyze the content of the attached specification file (`{source_file.name}`).
2. Create the three files above (`PROMPT.md`, `@fix_plan.md`, `specs/requirements.md`) with content derived from the PRD.
3. Ensure all requirements are captured and properly prioritized.
4. Make the `PROMPT.md` file actionable for autonomous development by a Gemini-based agent.
5. Structure `@fix_plan.md` with clear, implementable tasks.
6. Only output the file contents, no conversational text.
7. IMPORTANT: You MUST wrap each file's content in a code block with the filename specified exactly like this:
```markdown FILE:PROMPT.md
(Content of PROMPT.md)
```
```markdown FILE:@fix_plan.md
(Content of @fix_plan.md)
```
```markdown FILE:specs/requirements.md
(Content of specs/requirements.md)
```
    """

    # Prepare for Gemini call
    gemini_output_file = project_path / ".gemini_conversion_output.md"

    gemini_exec = shutil.which("gemini")
    if not gemini_exec:
        console.print(
            "[bold red]Error:[/bold red] Gemini CLI command 'gemini' not found. Is it installed and in PATH?"
        )
        raise typer.Exit(1)

    # Use stdin to pipe the prompt - more reliable for long prompts
    # gemini CLI reads from stdin when not in interactive mode
    gemini_cmd = [gemini_exec, "-p", str(source_file.name)]

    console.print("[blue]Calling Gemini to convert PRD... (This may take a moment)[/blue]")
    try:
        process = subprocess.run(
            gemini_cmd,
            input=conversion_prompt_content,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=300,  # 5 minutes timeout for conversion
        )
        gemini_response = process.stdout + process.stderr
        gemini_output_file.write_text(gemini_response)

        if process.returncode != 0:
            console.print(
                f"[bold red]Error:[/bold red] Gemini conversion failed with code {process.returncode}."
            )
            console.print(f"[red]Gemini output: {gemini_response[:500]}[/red]")
            raise typer.Exit(1)

        # Parse Gemini's output to extract files
        extracted_files = {}
        current_file_name = None
        current_file_content = []

        # Regex to find ```FILE:filename and ```
        file_start_pattern = re.compile(r"```(?:\w+)?\s*FILE:(\S+)")
        file_end_pattern = re.compile(r"```")

        for line in gemini_response.splitlines():
            file_start_match = file_start_pattern.match(line)
            if file_start_match:
                if current_file_name and current_file_content:
                    extracted_files[current_file_name] = "\n".join(current_file_content).strip()
                current_file_name = file_start_match.group(1).strip()
                current_file_content = []
            elif file_end_pattern.match(line) and current_file_name:
                extracted_files[current_file_name] = "\n".join(current_file_content).strip()
                current_file_name = None
                current_file_content = []
            elif current_file_name is not None:
                current_file_content.append(line)

        if current_file_name and current_file_content:  # Catch last file if no closing ```
            extracted_files[current_file_name] = "\n".join(current_file_content).strip()

        if not extracted_files:
            console.print(
                "[bold orange]Warning:[/bold orange] No files were extracted from Gemini's response. Please check .gemini_conversion_output.md for raw output."
            )
            console.print("[bold yellow]DEBUG - Raw output (first 1000 chars):[/bold yellow]")
            console.print(gemini_response[:1000] if gemini_response else "[Empty response]")
            console.print(
                "[bold red]Error:[/bold red] PRD conversion failed to generate required files."
            )
            raise typer.Exit(1)

        # Write out extracted files
        for fname, content in extracted_files.items():
            file_path = project_path / fname
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            console.print(f"Created: [green]{file_path.relative_to(project_path)}[/green]")

        console.print(
            f"✅ PRD imported successfully into project [bold green]{project_name}[/bold green]!"
        )
        console.print("\nNext steps:")
        console.print(
            Markdown(f"""
  1. `cd {project_name}`
  2. Review and edit the generated files (`PROMPT.md`, `@fix_plan.md`, `specs/requirements.md`).
  3. Verify environment: `boring health`
  4. Start autonomous verification: `boring verify --level STANDARD`
  5. Recommended: Add to Cursor/Claude Desktop as an MCP Server.
    """)
        )

    except subprocess.TimeoutExpired:
        console.print("[bold red]Error:[/bold red] Gemini conversion timed out after 300 seconds.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during PRD import: {e}[/bold red]")
        raise typer.Exit(1)
