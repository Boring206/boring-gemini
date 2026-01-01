"""
TUI Dashboard Module for Boring V4.0

Provides a real-time Text User Interface for monitoring:
- Loop count and status
- Token consumption rate
- Current task progress
- Memory and error patterns

Uses Rich library for beautiful terminal output.
"""

import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax

from .config import settings
from .logger import log_status


console = Console()


@dataclass
class LoopMetrics:
    """Metrics for a single loop iteration."""
    loop_id: int
    status: str  # RUNNING, SUCCESS, FAILED
    start_time: float
    end_time: Optional[float] = None
    files_modified: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    tokens_used: int = 0


@dataclass
class DashboardState:
    """Current state of the dashboard."""
    total_loops: int = 0
    successful_loops: int = 0
    failed_loops: int = 0
    current_loop: Optional[LoopMetrics] = None
    current_task: str = ""
    current_status: str = "IDLE"
    total_tokens: int = 0
    start_time: Optional[float] = None
    recent_logs: List[str] = field(default_factory=list)
    circuit_breaker_state: str = "CLOSED"
    
    def add_log(self, message: str):
        """Add a log message, keeping only last 10."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.recent_logs.append(f"[{timestamp}] {message}")
        if len(self.recent_logs) > 10:
            self.recent_logs = self.recent_logs[-10:]


class Dashboard:
    """
    Real-time TUI dashboard for monitoring Boring loops.
    
    Usage:
        dashboard = Dashboard()
        with dashboard:
            # Run your loop
            dashboard.update_loop(1, "RUNNING")
            # ... do work ...
            dashboard.update_loop(1, "SUCCESS")
    """
    
    def __init__(self, project_root: Optional[Path] = None, log_dir: Optional[Path] = None):
        self.project_root = project_root or settings.PROJECT_ROOT
        self.log_dir = log_dir or settings.LOG_DIR
        self.state = DashboardState()
        self.live: Optional[Live] = None
        self._running = False
    
    def __enter__(self):
        """Start the live dashboard."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the live dashboard."""
        self.stop()
    
    def start(self):
        """Start the live dashboard display."""
        self._running = True
        self.state.start_time = time.time()
        self.live = Live(
            self._generate_layout(),
            console=console,
            refresh_per_second=2,
            screen=True
        )
        self.live.start()
    
    def stop(self):
        """Stop the live dashboard display."""
        self._running = False
        if self.live:
            self.live.stop()
    
    def update(self):
        """Refresh the dashboard display."""
        if self.live and self._running:
            self.live.update(self._generate_layout())
    
    def update_loop(self, loop_id: int, status: str, task: str = ""):
        """Update current loop information."""
        if status == "RUNNING":
            self.state.current_loop = LoopMetrics(
                loop_id=loop_id,
                status=status,
                start_time=time.time()
            )
            self.state.current_status = "RUNNING"
            self.state.add_log(f"Loop #{loop_id} started")
        elif status in ["SUCCESS", "FAILED"]:
            if self.state.current_loop:
                self.state.current_loop.status = status
                self.state.current_loop.end_time = time.time()
            
            self.state.total_loops += 1
            if status == "SUCCESS":
                self.state.successful_loops += 1
            else:
                self.state.failed_loops += 1
            
            self.state.current_status = "IDLE"
            self.state.add_log(f"Loop #{loop_id} {status.lower()}")
        
        if task:
            self.state.current_task = task
        
        self.update()
    
    def update_task(self, task: str):
        """Update current task description."""
        self.state.current_task = task
        self.state.add_log(f"Task: {task[:50]}...")
        self.update()
    
    def update_tokens(self, tokens: int):
        """Update token consumption."""
        self.state.total_tokens += tokens
        self.update()
    
    def update_circuit_breaker(self, state: str):
        """Update circuit breaker state."""
        self.state.circuit_breaker_state = state
        self.state.add_log(f"Circuit Breaker: {state}")
        self.update()
    
    def add_file_modified(self, file_path: str):
        """Record a modified file."""
        if self.state.current_loop:
            self.state.current_loop.files_modified.append(file_path)
        self.state.add_log(f"Modified: {file_path}")
        self.update()
    
    def add_error(self, error: str):
        """Record an error."""
        if self.state.current_loop:
            self.state.current_loop.errors.append(error)
        self.state.add_log(f"⚠ {error[:60]}...")
        self.update()
    
    def _generate_layout(self) -> Layout:
        """Generate the dashboard layout."""
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        layout["left"].split(
            Layout(name="metrics", size=10),
            Layout(name="logs", ratio=1)
        )
        
        # Header
        layout["header"].update(self._create_header())
        
        # Metrics panel
        layout["metrics"].update(self._create_metrics_panel())
        
        # Logs panel
        layout["logs"].update(self._create_logs_panel())
        
        # Right panel (status)
        layout["right"].update(self._create_status_panel())
        
        # Footer
        layout["footer"].update(self._create_footer())
        
        return layout
    
    def _create_header(self) -> Panel:
        """Create header panel."""
        elapsed = 0
        if self.state.start_time:
            elapsed = int(time.time() - self.state.start_time)
        
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        title = Text()
        title.append("🤖 ", style="bold")
        title.append("Boring Dashboard", style="bold blue")
        title.append(f"  |  Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}", style="dim")
        
        return Panel(title, style="blue")
    
    def _create_metrics_panel(self) -> Panel:
        """Create metrics panel."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        success_rate = 0
        if self.state.total_loops > 0:
            success_rate = (self.state.successful_loops / self.state.total_loops) * 100
        
        table.add_row(
            "Total Loops", str(self.state.total_loops),
            "Success Rate", f"{success_rate:.1f}%"
        )
        table.add_row(
            "✓ Successful", str(self.state.successful_loops),
            "✗ Failed", str(self.state.failed_loops)
        )
        table.add_row(
            "Tokens Used", f"{self.state.total_tokens:,}",
            "Circuit Breaker", self._get_cb_display()
        )
        
        return Panel(table, title="📊 Metrics", border_style="green")
    
    def _get_cb_display(self) -> str:
        """Get circuit breaker display string."""
        state = self.state.circuit_breaker_state
        if state == "CLOSED":
            return "[green]CLOSED[/green]"
        elif state == "OPEN":
            return "[red]OPEN[/red]"
        else:
            return f"[yellow]{state}[/yellow]"
    
    def _create_logs_panel(self) -> Panel:
        """Create logs panel."""
        logs = "\n".join(self.state.recent_logs[-8:])
        if not logs:
            logs = "[dim]No logs yet...[/dim]"
        
        return Panel(logs, title="📜 Recent Activity", border_style="yellow")
    
    def _create_status_panel(self) -> Panel:
        """Create current status panel."""
        content = []
        
        # Current status
        status_icon = "🟢" if self.state.current_status == "RUNNING" else "⚪"
        content.append(f"{status_icon} Status: [bold]{self.state.current_status}[/bold]\n")
        
        # Current loop
        if self.state.current_loop:
            loop = self.state.current_loop
            content.append(f"Loop: #{loop.loop_id}")
            
            if loop.files_modified:
                content.append(f"Files: {len(loop.files_modified)}")
            
            if loop.start_time:
                elapsed = int(time.time() - loop.start_time)
                content.append(f"Time: {elapsed}s")
        
        # Current task
        if self.state.current_task:
            task_display = self.state.current_task[:30]
            if len(self.state.current_task) > 30:
                task_display += "..."
            content.append(f"\n[bold]Task:[/bold]\n{task_display}")
        
        return Panel("\n".join(content), title="🎯 Current", border_style="cyan")
    
    def _create_footer(self) -> Panel:
        """Create footer panel."""
        footer = Text()
        footer.append("Press ", style="dim")
        footer.append("Ctrl+C", style="bold yellow")
        footer.append(" to stop  |  ", style="dim")
        footer.append("boring status", style="bold cyan")
        footer.append(" for details", style="dim")
        
        return Panel(footer, style="dim")


def create_dashboard(project_root: Optional[Path] = None) -> Dashboard:
    """Factory function to create a dashboard instance."""
    return Dashboard(project_root=project_root)


def run_standalone_dashboard():
    """Run the dashboard in standalone mode for monitoring."""
    console.print("[bold blue]Starting Boring Dashboard...[/bold blue]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")
    
    dashboard = Dashboard()
    
    try:
        with dashboard:
            # Demo mode - just keep running and updating
            loop_id = 0
            while True:
                time.sleep(3)
                # In real usage, this would be updated by the loop
                # For demo, we just show the dashboard running
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
