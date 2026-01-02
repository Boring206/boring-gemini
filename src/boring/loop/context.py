"""
Loop Context - Shared state container for the state machine.

This dataclass holds all mutable state that is shared between states,
eliminating the need for complex parameter passing.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..gemini_client import GeminiClient
    from ..memory import MemoryManager
    from ..verification import CodeVerifier
    from ..storage import SQLiteStorage
    from ..extensions import ExtensionsManager

from ..config import settings


@dataclass
class LoopContext:
    """
    Shared mutable context passed between all states.
    
    This replaces the scattered instance variables in the old AgentLoop,
    providing a clean, explicit container for loop state.
    """
    
    # === Configuration (immutable during loop) ===
    model_name: str = settings.DEFAULT_MODEL
    use_cli: bool = False
    verbose: bool = False
    interactive: bool = False
    verification_level: str = "STANDARD"
    project_root: Path = field(default_factory=lambda: settings.PROJECT_ROOT)
    log_dir: Path = field(default_factory=lambda: settings.LOG_DIR)
    prompt_file: Path = field(default_factory=lambda: settings.PROJECT_ROOT / settings.PROMPT_FILE)
    
    # === Injected Subsystems ===
    gemini_client: Optional["GeminiClient"] = None
    memory: Optional["MemoryManager"] = None
    verifier: Optional["CodeVerifier"] = None
    storage: Optional["SQLiteStorage"] = None
    extensions: Optional["ExtensionsManager"] = None
    
    # === Loop Counters ===
    loop_count: int = 0
    max_loops: int = field(default_factory=lambda: settings.MAX_LOOPS)
    retry_count: int = 0
    max_retries: int = 3
    empty_output_count: int = 0
    
    # === Timing ===
    loop_start_time: float = 0.0
    state_start_time: float = 0.0
    
    # === Generation State ===
    output_content: str = ""
    output_file: Optional[Path] = None
    function_calls: List[Dict[str, Any]] = field(default_factory=list)
    status_report: Optional[Dict[str, Any]] = None
    
    # === Patching State ===
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    patch_errors: List[str] = field(default_factory=list)
    
    # === Verification State ===
    verification_passed: bool = False
    verification_error: str = ""
    
    # === Control Flags ===
    should_exit: bool = False
    exit_reason: str = ""
    
    # === Accumulated Errors ===
    errors_this_loop: List[str] = field(default_factory=list)
    tasks_completed: List[str] = field(default_factory=list)
    
    def start_loop(self) -> None:
        """Reset per-loop state at beginning of each iteration."""
        self.loop_start_time = time.time()
        self.output_content = ""
        self.output_file = None
        self.function_calls = []
        self.status_report = None
        self.files_modified = []
        self.files_created = []
        self.patch_errors = []
        self.verification_passed = False
        self.verification_error = ""
        self.errors_this_loop = []
        self.tasks_completed = []
    
    def start_state(self) -> None:
        """Record state entry time for telemetry."""
        self.state_start_time = time.time()
    
    def get_state_duration(self) -> float:
        """Get duration of current state in seconds."""
        return time.time() - self.state_start_time
    
    def get_loop_duration(self) -> float:
        """Get duration of current loop in seconds."""
        return time.time() - self.loop_start_time
    
    def increment_loop(self) -> None:
        """Increment loop counter and reset retry count."""
        self.loop_count += 1
        self.retry_count = 0
        self.start_loop()
    
    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1
    
    def can_retry(self) -> bool:
        """Check if more retries are allowed."""
        return self.retry_count < self.max_retries
    
    def should_continue(self) -> bool:
        """Check if loop should continue."""
        return not self.should_exit and self.loop_count < self.max_loops
    
    def mark_exit(self, reason: str) -> None:
        """Mark loop for exit with reason."""
        self.should_exit = True
        self.exit_reason = reason
