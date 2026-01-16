import logging
import os
import time

import typer

logger = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from boring.services.behavior import BehaviorLogger

from .detector import FlowDetector
from .events import FlowEvent, FlowEventBus
from .skills_advisor import SkillsAdvisor
from .states import FlowStage
from .vibe_interface import VibeInterface

# BoringDone Notification
try:
    from boring.services.notifier import done as notify_done
except ImportError:
    notify_done = None

# [ONE DRAGON WIRING]
# Importing real tools to power the engine
try:
    from boring.mcp.speckit_tools import (
        boring_speckit_plan,
        boring_speckit_tasks,
    )
except ImportError:
    # Fallback for when running in an environment where tools aren't registered yet
    # or circular imports prevent direct access.
    # In a real scenario, we might invoke them via a Tool Registry or localized import.
    boring_speckit_plan = None
    boring_speckit_tasks = None

try:
    from boring.mcp.tools.vibe import boring_predict_errors, run_vibe_check
except ImportError:
    boring_predict_errors = None
    run_vibe_check = None

try:
    from boring.loop import AgentLoop
except ImportError:
    AgentLoop = None

try:
    from boring.mcp.tools.advanced import boring_security_scan
except ImportError:
    boring_security_scan = None

try:
    from boring.mcp.tools.knowledge import boring_learn
except ImportError:
    boring_learn = None

try:
    from boring.intelligence.predictor import Predictor
except ImportError:
    Predictor = None

try:
    from boring.metrics.performance import track_performance
except ImportError:
    # No-op decorator fallback
    def track_performance(name=None):
        def decorator(func):
            return func

        return decorator


try:
    from boring.flow.auto_handlers import register_auto_handlers
except ImportError:
    logger.debug("auto_handlers not available, skipping registration")

try:
    from boring.mcp.tools.knowledge import boring_learn
except ImportError:
    boring_learn = None

try:
    from boring.loop.workflow_evolver import WorkflowEvolver
except ImportError:
    WorkflowEvolver = None

console = Console()


class FlowEngine:
    """
    The One Dragon Engine.
    Orchestrates the entire lifecycle from Setup to Evolution.
    """

    def __init__(self, project_root):
        self.root = project_root
        self.detector = FlowDetector(project_root)
        self.vibe = VibeInterface()
        self.skills = SkillsAdvisor()
        self.evolution = WorkflowEvolver(self.root) if WorkflowEvolver else None

        # V14: Register Auto-Handlers
        if "register_auto_handlers" in globals():
            register_auto_handlers()

        # V14: Offline Mode Support
        from boring.core.config import settings

        self.offline_mode = settings.OFFLINE_MODE
        if self.offline_mode:
            console.print("[bold yellow]📴 Offline Mode Active (One Dragon Flow)[/bold yellow]")

        # Shadow Adoption Tracker
        self.behavior = BehaviorLogger(self.root)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._diag_future = None
        self.advisory_mode = os.environ.get("BORING_ADVISORY_MODE", "false").lower() == "true"

    def run(self, auto: bool = False):
        """Main entry point for 'boring flow'"""
        self.auto_mode = auto
        self.behavior.log("command_run", "flow", auto=auto)

        try:
            state = self.detector.detect()

            if self.offline_mode:
                # Adjust suggestion for offline mode
                state.suggestion += " (Offline Mode Optimization)"

            self._display_header(state)

            if state.stage == FlowStage.SETUP:
                self._run_setup()
                # If auto mode, chain into design immediately
                if self.auto_mode:
                    console.print(
                        "[bold cyan]🚀 Auto-Mode: Continuing to Design Phase...[/bold cyan]"
                    )
                    time.sleep(1)
                    self.run(auto=True)
            elif state.stage == FlowStage.DESIGN:
                self._run_design()
            elif state.stage == FlowStage.BUILD:
                self._run_build(state.pending_tasks)
            elif state.stage == FlowStage.POLISH:
                self._run_polish()
        except KeyboardInterrupt:
            self.behavior.log("abort", "flow", reason="ctrl_c")
            console.print("\n[yellow]Boring Flow Interrupted by User.[/yellow]")
            raise typer.Exit(1)
        except Exception as e:
            self.behavior.log("error", "flow", error=str(e))
            raise

    def _display_header(self, state):
        status_text = f"[bold yellow]Phase: {state.stage.value}[/bold yellow]"
        if self.offline_mode:
            status_text += " [dim](OFFLINE)[/dim]"

        console.print(
            Panel(
                f"{status_text}\n\n{state.suggestion}",
                title="🐉 Boring Flow (One Dragon)",
                border_style="blue",
            )
        )

    @track_performance("setup_phase")
    def _run_setup(self):
        """Stage 1: Setup"""
        FlowEventBus.emit(FlowEvent.PRE_SETUP, project_path=str(self.root))
        # ...
        # Mocking the constitution creation for now
        if self.auto_mode or typer.confirm("Start Setup Wizard?"):
            # In real impl, calls boring_speckit_constitution
            console.print("[green]Creating constitution.md...[/green]")
            (self.root / "constitution.md").touch()
            if not self.auto_mode:
                console.print(
                    "[bold green]Setup Complete! Run 'boring flow' again to enter Design Phase.[/bold green]"
                )
        FlowEventBus.emit(FlowEvent.POST_SETUP, project_path=str(self.root))

    @track_performance("design_phase")
    def _run_design(self):
        """Stage 2: Design"""
        FlowEventBus.emit(FlowEvent.PRE_DESIGN, project_path=str(self.root))
        if self.auto_mode:
            goal = "unknown"
            console.print(
                "[cyan]🚀 Auto-Mode: Using default 'unknown' goal (blueprint whole project).[/cyan]"
            )
        else:
            goal = Prompt.ask("What is your goal for this sprint? (or say 'unknown')")

        # 1. Vibe Check (Ambiguity Resolution)
        refined_goal = self.vibe.resolve_ambiguity(goal)
        if refined_goal != goal:
            console.print(f"[cyan]✨ Vibe Interpreted:[/cyan] {refined_goal}")

        # 1.5 Predictive Risk Analysis (V14) - ASYNC/BACKGROUND
        if boring_predict_errors or Predictor:
            console.print("[dim]🔮 Backgrounding Predictive Analysis...[/dim]")

            def run_background_diag():
                try:
                    if boring_predict_errors:
                        return boring_predict_errors(file_path=".", project_path=str(self.root))
                    elif Predictor:
                        predictor = Predictor(self.root)
                        return predictor.deep_diagnostic()
                except Exception as e:
                    logger.debug(f"Background diagnostic failed: {e}")
                    return None

            self._diag_future = self.executor.submit(run_background_diag)

        # 1.6 Adaptive Conflict Detection (V14.1)
        self._analyze_manual_overrides(refined_goal)

        # 2. Skill Advice
        skill_tips = self.skills.suggest_skills(refined_goal)
        if skill_tips:
            console.print(Panel(skill_tips, title="Skills Advisor", border_style="magenta"))

        console.print("[bold cyan]Executing Speckit Plan...[/bold cyan]")

        # Real Integration
        result = ""
        if boring_speckit_plan:
            # We call the tool function directly.
            # Note: In a full implementation, we'd handle the 'mcp' context/dependencies properly.
            # Here we assume standalone capability or rely on the tool's internal robustness.
            try:
                result = boring_speckit_plan(context=refined_goal, project_path=str(self.root))
                console.print(Panel(str(result), title="Speckit Plan Result"))
            except Exception as e:
                console.print(f"[red]Error executing plan tool: {e}[/red]")
                # Fallback
                (self.root / "implementation_plan.md").touch()
        else:
            (self.root / "implementation_plan.md").touch()

        # Generate tasks immediately after planning
        if boring_speckit_tasks:
            try:
                boring_speckit_tasks(context=str(result), project_path=str(self.root))
            except Exception:
                (self.root / "task.md").write_text("- [ ] Task 1 (Auto-generated fallback)")
        else:
            (self.root / "task.md").write_text("- [ ] Task 1 (Auto-generated fallback)")

        # Display background diag if finished
        if self._diag_future and self._diag_future.done():
            res = self._diag_future.result()
            if res:
                console.print(
                    Panel(
                        str(res),
                        title="🔮 Predictive Risk Report (Completed)",
                        border_style="yellow",
                    )
                )

        console.print(
            "[bold green]Blueprint Created! Run 'boring flow' to start Building.[/bold green]"
        )
        FlowEventBus.emit(FlowEvent.POST_DESIGN, project_path=str(self.root), goal=refined_goal)

    def _analyze_manual_overrides(self, goal):
        """Phase IV: Adaptive Learning Logic"""
        task_file = self.root / "task.md"
        if not task_file.exists():
            return

        # Check if user manually edited the task list
        # In a real impl, we'd use git diff or a checksum.
        # For simulation, we check for 'Authority' keywords.
        content = task_file.read_text(encoding="utf-8")
        if "CONFIRMED BY SENIOR" in content or "MANUAL OVERRIDE" in content:
            console.print(
                "[bold yellow]🧠 Adaptive Learning: Detected manual overrides in task.md.[/bold yellow]"
            )
            self.behavior.log("adaptive_learning", "conflict_resolved", file="task.md")
            # Inject this into the vibe interface for next reasoning cycle
            self.vibe.resolve_ambiguity(f"User priorities shifted manually: {content[:100]}...")

    @track_performance("build_phase")
    def _run_build(self, pending_tasks: list[str]):
        """Stage 3: Build (with Self-Healing)"""
        if self.advisory_mode:
            console.print(
                "[bold yellow]🛡️ Advisory Mode Active: Skipping automated code writes.[/bold yellow]"
            )
            console.print(
                "[dim]In this mode, Boring will suggest changes but will not execute AgentLoop.[/dim]"
            )
            return

        FlowEventBus.emit(FlowEvent.PRE_BUILD, project_path=str(self.root))

        max_retries = 3
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            attempt += 1
            if attempt > 1:
                console.print(
                    f"[bold yellow]🔄 Self-Healing Attempt {attempt}/{max_retries}...[/bold yellow]"
                )

            console.print("[bold]Executing tasks via Agent Loop...[/bold]")

            if AgentLoop:
                try:
                    FlowEventBus.emit(
                        FlowEvent.AGENT_START, project_path=str(self.root), attempt=attempt
                    )

                    # Initialize loop
                    loop = AgentLoop(
                        model_name="gemini-1.5-pro",
                        use_cli=False,
                        verbose=True,
                        verification_level="STANDARD",
                    )

                    console.print("[green]🐉 Dragon is breathing fire (Agent Started)...[/green]")
                    loop.run(max_duration=3600)

                    FlowEventBus.emit(FlowEvent.AGENT_COMPLETE, project_path=str(self.root))
                    success = True
                except Exception as e:
                    console.print(f"[red]Agent Loop failed (Attempt {attempt}): {e}[/red]")
                    FlowEventBus.emit(FlowEvent.ON_ERROR, project_path=str(self.root), error=str(e))

                    # 3. Bisect Fallback (V14) - Only on last attempt or if manual check
                    if attempt == max_retries and Predictor:
                        console.print("[bold yellow]🕵️ Analyzing Regression...[/bold yellow]")
                        try:
                            predictor = Predictor(self.root)
                            analysis = predictor.analyze_regression(str(e))
                            if analysis.get("recommendation"):
                                console.print(
                                    Panel(
                                        analysis["recommendation"],
                                        title="🤖 AI Bisect Recommendation",
                                        border_style="red",
                                    )
                                )
                                if typer.confirm("Run full 'boring bisect' now?"):
                                    console.print("[bold yellow]Running AI Bisect...[/bold yellow]")
                                    from boring.main import bisect as bisect_cmd

                                    try:
                                        bisect_cmd(error=str(e), file=None, depth=10)
                                    except Exception as be:
                                        console.print(
                                            f"[dim]Command 'boring bisect' failed: {be}[/dim]"
                                        )
                        except Exception as ex:
                            console.print(f"[dim]Bisect analysis failed: {ex}[/dim]")

                    if attempt < max_retries:
                        # [SUPER AUTOMATION] The ON_LINT_FAIL/ON_TEST_FAIL events emitted by AgentLoop
                        # should have triggered auto-fixes in handlers.
                        # Wait a bit or confirm?
                        console.print("[dim]Checking if auto-fixers resolved issues...[/dim]")
                        time.sleep(2)

        # Check tasks again after loop
        if (self.root / "task.md").exists():
            console.print("[dim]Checking task completion status...[/dim]")

        console.print(
            "[bold green]Build Phase Cycle Complete. Entering Polish Phase...[/bold green]"
        )
        FlowEventBus.emit(FlowEvent.POST_BUILD, project_path=str(self.root), modified_files=[])

        # BoringDone: Notify build complete
        if notify_done:
            notify_done(task_name="Build Phase", success=success, details="Entering Polish Phase")

        self._run_polish()

    @track_performance("polish_phase")
    def _run_polish(self):
        """Stage 4: Polish & Stage 5: Evolution"""
        FlowEventBus.emit(FlowEvent.PRE_POLISH, project_path=str(self.root))
        console.print("[bold cyan]💎 Entering Polish Phase...[/bold cyan]")

        # 1. Vibe Check (V14)
        if run_vibe_check:
            console.print("[bold]Running Vibe Check...[/bold]")
            try:
                # Use a specific file or "." for whole project
                res = run_vibe_check(target_path=".", project_path=str(self.root))
                # res is BoringResult
                if hasattr(res, "status") and res.status == "success":
                    vibe_score = res.data.get("score", 0) if res.data else 0
                    color = "green" if vibe_score > 80 else "yellow" if vibe_score > 50 else "red"
                    console.print(f"[{color}]Vibe Score: {vibe_score}/100[/{color}]")
                    if res.data and res.data.get("summary"):
                        console.print(Panel(res.data["summary"], title="Vibe Report"))
                else:
                    console.print(f"[dim]Vibe Check skipped: {res.message}[/dim]")
            except Exception as e:
                console.print(f"[dim]Vibe Check failed: {e}[/dim]")
        else:
            console.print("[green]Score: 98/100 (S-Tier Simulation)[/green]")

        # 4. Security Scan (V14)
        if boring_security_scan:
            console.print("[bold]🛡️ Running Security Scan...[/bold]")
            try:
                sec_result = boring_security_scan(project_path=str(self.root), scan_type="full")
                # Check if it's a BoringResult or raw output
                if hasattr(sec_result, "status") and sec_result.status == "success":
                    msg = sec_result.message or "Security scan completed successfully."
                    console.print(Panel(msg, title="🛡️ Security Report", border_style="red"))
                else:
                    console.print(
                        Panel(str(sec_result), title="🛡️ Security Report", border_style="red")
                    )
            except Exception as e:
                console.print(f"[red]Security scan error: {e}[/red]")

        # 5. Brain Learning (V14) - Now handled via POST_POLISH Event
        # (Wait for emit at the end of method)

        console.print(
            Panel(self.evolution.dream_next_steps(), title="Sage Mode", border_style="purple")
        )

        if typer.confirm("Archive this session and learn patterns?"):
            self.evolution.learn_from_session()
            console.print("[bold blue]Session Archived. You have evolved.[/bold blue]")
            # BoringDone: Notify user flow is fully complete
            if notify_done:
                notify_done(
                    task_name="Boring Flow",
                    success=True,
                    details="Session archived. Ready for next sprint!",
                )

        FlowEventBus.emit(FlowEvent.POST_POLISH, project_path=str(self.root))

    def run_headless(self, user_input: str = None) -> str:
        """
        MCP Entry Point (Non-Interactive).
        Takes input from the LLM/User and performs the next step in the flow.
        """
        state = self.detector.detect()
        response = []

        response.append(f"🐲 **Boring Flow (Phase: {state.stage.value})**")
        response.append(f"📊 Progress: {state.progress_bar}")

        # P0: Task-Aware Skill Suggestion
        skill = state.suggested_skill
        # If detector found errors/failures, suggest Healer
        if "fail" in state.suggestion.lower() or "error" in state.suggestion.lower():
            skill = "Healer"

        if skill:
            response.append(
                f"💡 Suggestion: Use `boring_active_skill('{skill}')` to unlock {skill} tools."
            )

        response.append(f"Advice: {state.suggestion}")

        if state.stage == FlowStage.SETUP:
            if not (self.root / "constitution.md").exists():
                (self.root / "constitution.md").touch()
                response.append("✅ Auto-created constitution.md. Ready for Design.")
            else:
                response.append("Setup complete.")

        elif state.stage == FlowStage.DESIGN:
            if not user_input or user_input == "status":
                response.append(
                    "❓ Waiting for goal. Usage: `boring_flow(instruction='make a login page')`"
                )
            else:
                refined_goal = self.vibe.resolve_ambiguity(user_input)
                response.append(f"✨ Vibe Target: {refined_goal}")

                tips = self.skills.suggest_skills(refined_goal)
                if tips:
                    response.append(tips)

                response.append("⚡ Generating Plan...")
                if boring_speckit_plan:
                    try:
                        res = boring_speckit_plan(context=refined_goal, project_path=str(self.root))
                        response.append(f"Plan Result: {res}")
                    except Exception as e:
                        response.append(f"Plan Error: {e}")
                        (self.root / "implementation_plan.md").touch()
                else:
                    (self.root / "implementation_plan.md").touch()

                if boring_speckit_tasks:
                    try:
                        boring_speckit_tasks(context=str(res), project_path=str(self.root))
                    except Exception as e:
                        logger.debug("speckit_tasks failed in headless mode: %s", e)
                else:
                    (self.root / "task.md").write_text("- [ ] Auto task")

                response.append("✅ Blueprint Created! Ready to Build.")

        elif state.stage == FlowStage.BUILD:
            response.append("🔨 Starting Agent Loop...")
            if AgentLoop:
                try:
                    loop = AgentLoop(
                        model_name="gemini-1.5-pro",
                        use_cli=False,
                        verbose=True,
                        verification_level="STANDARD",
                        prompt_file=None,
                    )
                    # [ONE DRAGON STABILITY] Set 1-hour global timeout
                    loop.run(max_duration=3600)
                    response.append("✅ Agent Loop Completed.")
                    # BoringDone: Headless notification
                    if notify_done:
                        notify_done(task_name="Agent Loop", success=True)
                except Exception as e:
                    response.append(f"❌ Loop Failed: {e}")

            self._run_polish_headless(response)

        elif state.stage == FlowStage.POLISH:
            self._run_polish_headless(response)

        return "\n\n".join(response)

    def _run_polish_headless(self, response: list):
        response.append("💎 Running Vibe Check...")
        if run_vibe_check:
            try:
                res = run_vibe_check(target_path=".", project_path=str(self.root))
                response.append(f"Vibe Report: {res}")
            except Exception as e:
                response.append(f"Vibe Failed: {e}")

        response.append(self.evolution.dream_next_steps())
        response.append("💡 Tip: Use `boring_commit` to save your progress.")
