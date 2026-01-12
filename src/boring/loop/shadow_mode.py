"""
Shadow Mode - Human-in-the-Loop Protection

Provides guardrails against destructive AI operations.

Per user decision:
- Mode: ENABLED (default) - only block HIGH/CRITICAL operations
- Read operations are NEVER blocked
- Human approval via callback or pending queue
"""

import ast
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from boring.core.utils import TransactionalFileWriter

logger = logging.getLogger(__name__)

# Import trust rules (lazy to avoid circular import)
_trust_manager = None


def _get_trust_manager(project_root):
    """Lazy-load trust manager to avoid circular imports."""
    global _trust_manager
    if _trust_manager is None:
        try:
            from ..trust_rules import get_trust_manager

            _trust_manager = get_trust_manager(project_root)
        except ImportError:
            _trust_manager = None
    return _trust_manager


class ShadowModeLevel(Enum):
    """Shadow mode protection levels."""

    DISABLED = "DISABLED"  # All operations auto-approved
    ENABLED = "ENABLED"  # Block HIGH/CRITICAL only (DEFAULT)
    STRICT = "STRICT"  # Block ALL write operations


class OperationSeverity(Enum):
    """Severity levels for operations."""

    LOW = "low"  # Read operations, non-destructive queries
    MEDIUM = "medium"  # Large edits, batch operations
    HIGH = "high"  # File deletion, config changes
    CRITICAL = "critical"  # Secrets, system files, mass deletion


@dataclass
class PendingOperation:
    """An operation awaiting human approval."""

    operation_id: str
    operation_type: str
    file_path: str
    severity: OperationSeverity
    description: str
    preview: str  # What the change looks like
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    approved: Optional[bool] = None
    approver_note: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "file_path": self.file_path,
            "severity": self.severity.value,
            "description": self.description,
            "preview": self.preview[:500],
            "timestamp": self.timestamp,
            "approved": self.approved,
            "approver_note": self.approver_note,
        }


# Type alias for approval callback
ApprovalCallback = Callable[[PendingOperation], bool]


class ShadowModeGuard:
    """
    Intercepts and validates operations before execution.

    Modes (per user decision - ENABLED is default):
    - DISABLED: All operations auto-approved
    - ENABLED: Only HIGH/CRITICAL ops require approval
    - STRICT: ALL file modifications require approval

    Design principles:
    - Read operations NEVER blocked (avoid alert fatigue)
    - Only side-effect operations need approval
    - Quick approve/reject via callback or queue
    """

    # Patterns for sensitive files
    SENSITIVE_PATTERNS = {
        ".env",
        "secret",
        "password",
        "credential",
        "key",
        "token",
        "auth",
        "private",
        "api_key",
        ".pem",
        ".key",
    }

    # Config files that warrant extra caution
    CONFIG_PATTERNS = {
        "config",
        "settings",
        "pyproject.toml",
        "package.json",
        "docker-compose",
        "Dockerfile",
        ".yaml",
        ".yml",
    }

    # Files that should NEVER be modified by automation
    PROTECTED_FILES = {".git/config", ".git/HEAD", "~/.ssh/", "/etc/"}

    def __init__(
        self,
        project_root: Path,
        mode: ShadowModeLevel = ShadowModeLevel.ENABLED,
        approval_callback: Optional[ApprovalCallback] = None,
        pending_file: Optional[Path] = None,
    ):
        """
        Initialize Shadow Mode guard.

        Args:
            project_root: Project root directory
            mode: Protection level (default ENABLED)
            approval_callback: Sync callback for approval (returns bool)
            pending_file: Path to save pending operations queue
        """
        self.project_root = Path(project_root)
        self._mode = mode  # Use private attr to avoid triggering setter persistence
        self.approval_callback = approval_callback

        self.pending_file = pending_file or (self.project_root / ".boring_pending_approval.json")
        self._mode_file = self.project_root / ".boring_shadow_mode"

        self.pending_queue: list[PendingOperation] = []
        self._operation_counter = 0

        # Load persisted mode (overrides constructor default if file exists)
        self._load_mode()

        # Load any existing pending operations
        self._load_pending()

    @property
    def mode(self) -> ShadowModeLevel:
        """Get current protection mode."""
        return self._mode

    @mode.setter
    def mode(self, value: ShadowModeLevel) -> None:
        """Set protection mode and persist to disk."""
        self._mode = value
        self._persist_mode()

    def check_operation(self, operation: dict[str, Any]) -> Optional[PendingOperation]:
        """
        Check if an operation should be blocked for approval.

        Args:
            operation: Dict with 'name' and 'args'

        Returns:
            PendingOperation if blocked, None if auto-approved
        """
        if self.mode == ShadowModeLevel.DISABLED:
            return None

        op_name = operation.get("name", "")
        args = operation.get("args", {})

        # Classify operation
        pending = self._classify_operation(op_name, args)
        if not pending:
            return None

        # Check trust rules BEFORE blocking
        trust_manager = _get_trust_manager(self.project_root)
        if trust_manager:
            severity_str = pending.severity.value if pending.severity else "medium"
            matched_rule = trust_manager.check_trust(op_name, args, severity_str)
            if matched_rule:
                logger.info(f"✅ Auto-approved by trust rule: {op_name}")
                return None  # Trusted operation, no blocking

        # Check protection level
        if self.mode == ShadowModeLevel.STRICT:
            # Block ALL write operations (unless trusted above)
            return pending

        # ENABLED mode: only block HIGH and CRITICAL
        if pending.severity in (OperationSeverity.HIGH, OperationSeverity.CRITICAL):
            return pending

        return None  # Auto-approve LOW/MEDIUM

    def request_approval(self, pending: PendingOperation) -> bool:
        """
        Request approval for a pending operation.

        Returns:
            True if approved, False if rejected/pending
        """
        # Try callback first
        if self.approval_callback:
            try:
                return self.approval_callback(pending)
            except Exception as e:
                logger.warning(f"Approval callback failed: {e}")

        # Fall back to queue
        self.pending_queue.append(pending)
        self._save_pending()

        logger.info(
            f"⚠️ Operation queued for approval: {pending.operation_type} "
            f"on {pending.file_path} ({pending.severity.value})"
        )

        return False  # Not approved yet

    def approve_operation(self, operation_id: str, note: str = None) -> bool:
        """
        Approve a pending operation by ID.

        Returns:
            True if found and approved
        """
        for op in self.pending_queue:
            if op.operation_id == operation_id:
                op.approved = True
                op.approver_note = note
                self._save_pending()
                return True
        return False

    def reject_operation(self, operation_id: str, note: str = None) -> bool:
        """
        Reject a pending operation by ID.

        Returns:
            True if found and rejected
        """
        for op in self.pending_queue:
            if op.operation_id == operation_id:
                op.approved = False
                op.approver_note = note
                self._remove_pending(operation_id)
                return True
        return False

    def get_pending_operations(self) -> list[PendingOperation]:
        """Get all pending operations awaiting approval."""
        return [op for op in self.pending_queue if op.approved is None]

    def clear_pending(self) -> int:
        """Clear all pending operations. Returns count cleared."""
        count = len(self.pending_queue)
        self.pending_queue.clear()
        self._save_pending()
        return count

    def is_operation_approved(self, operation_id: str) -> Optional[bool]:
        """
        Check if an operation has been approved.

        Returns:
            True if approved, False if rejected, None if pending
        """
        for op in self.pending_queue:
            if op.operation_id == operation_id:
                return op.approved
        return None

    def _classify_operation(self, op_name: str, args: dict[str, Any]) -> Optional[PendingOperation]:
        """Classify an operation by severity."""
        file_path = args.get("file_path", "") or args.get("path", "")

        # Generate unique ID
        self._operation_counter += 1
        op_id = f"op_{self._operation_counter}_{datetime.now().strftime('%H%M%S')}"

        # ==================
        # FILE DELETION - HIGH
        # ==================
        if op_name in ("delete_file", "remove_file", "rm"):
            return PendingOperation(
                operation_id=op_id,
                operation_type="DELETE",
                file_path=file_path,
                severity=OperationSeverity.HIGH,
                description=f"Delete file: {file_path}",
                preview="[File will be permanently deleted]",
            )

        # ==================
        # SECRETS/SENSITIVE - CRITICAL
        # ==================
        if op_name in ("write_file", "create_file", "search_replace"):
            if self._is_sensitive_file(file_path):
                content = args.get("content", "") or args.get("replace", "")
                return PendingOperation(
                    operation_id=op_id,
                    operation_type="SENSITIVE_CHANGE",
                    file_path=file_path,
                    severity=OperationSeverity.CRITICAL,
                    description=f"Modify sensitive file: {file_path}",
                    preview=self._safe_preview(content),
                )

        # ==================
        # CONFIG FILES - HIGH
        # ==================
        if op_name in ("write_file", "create_file", "search_replace"):
            if self._is_config_file(file_path):
                content = args.get("content", "") or args.get("replace", "")
                return PendingOperation(
                    operation_id=op_id,
                    operation_type="CONFIG_CHANGE",
                    file_path=file_path,
                    severity=OperationSeverity.HIGH,
                    description=f"Modify config file: {file_path}",
                    preview=self._safe_preview(content),
                )

        # ==================
        # LARGE DELETIONS - MEDIUM
        # ==================
        if op_name == "search_replace":
            search_content = args.get("search", "")
            if len(search_content) > 1000 or search_content.count("\n") > 30:
                return PendingOperation(
                    operation_id=op_id,
                    operation_type="LARGE_EDIT",
                    file_path=file_path,
                    severity=OperationSeverity.MEDIUM,
                    description=f"Large edit in {file_path} ({len(search_content)} chars, {search_content.count(chr(10))} lines)",
                    preview=f"Removing:\n{search_content[:300]}...",
                )

        # ==================
        # SHELL COMMANDS - HIGH
        # ==================
        if op_name in ("exec", "shell", "run_command", "subprocess"):
            cmd = args.get("command", "") or args.get("cmd", "")
            return PendingOperation(
                operation_id=op_id,
                operation_type="SHELL_COMMAND",
                file_path="[shell]",
                severity=OperationSeverity.HIGH,
                description="Execute shell command",
                preview=cmd[:200],
            )

        # ==================
        # PROTECTED PATHS - CRITICAL
        # ==================
        if self._is_protected_path(file_path):
            return PendingOperation(
                operation_id=op_id,
                operation_type="PROTECTED_PATH",
                file_path=file_path,
                severity=OperationSeverity.CRITICAL,
                description=f"Attempt to modify protected path: {file_path}",
                preview="[BLOCKED - Protected system path]",
            )

        # ==================
        # CATCH-ALL WRITES - LOW
        # ==================
        if op_name in ("write_file", "create_file", "search_replace", "apply_patch"):
            content = args.get("content", "") or args.get("replace", "")
            return PendingOperation(
                operation_id=op_id,
                operation_type="WRITE_FILE",
                file_path=file_path,
                severity=OperationSeverity.LOW,
                description=f"Modify file: {file_path}",
                preview=self._safe_preview(content),
            )

        return None  # No special handling needed

    def _is_sensitive_file(self, path: str) -> bool:
        """Check if file might contain sensitive data."""
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in self.SENSITIVE_PATTERNS)

    def _is_config_file(self, path: str) -> bool:
        """Check if file is a configuration file."""
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in self.CONFIG_PATTERNS)

    def _is_protected_path(self, path: str) -> bool:
        """Check if path is in protected list."""
        return any(protected in path for protected in self.PROTECTED_FILES)

    def _safe_preview(self, content: str, max_len: int = 300) -> str:
        """Create safe preview of content (redact sensitive data)."""
        if not content:
            return "[empty]"

        # Redact potential secrets
        import re

        redacted = re.sub(
            r'(password|secret|key|token|api_key)\s*[=:]\s*["\']?[^"\'\s]+',
            r"\1=[REDACTED]",
            content,
            flags=re.IGNORECASE,
        )

        if len(redacted) > max_len:
            return redacted[:max_len] + "..."

        return redacted

    def _load_pending(self) -> None:
        """Load pending operations from file."""
        if self.pending_file.exists():
            try:
                data = json.loads(self.pending_file.read_text())
                self.pending_queue = [
                    PendingOperation(
                        operation_id=op["operation_id"],
                        operation_type=op["operation_type"],
                        file_path=op["file_path"],
                        severity=OperationSeverity(op["severity"]),
                        description=op["description"],
                        preview=op["preview"],
                        timestamp=op.get("timestamp", ""),
                        approved=op.get("approved"),
                        approver_note=op.get("approver_note"),
                    )
                    for op in data
                ]
            except Exception as e:
                logger.warning(f"Failed to load pending operations: {e}")

    def _save_pending(self) -> None:
        """Save pending operations to file."""
        try:
            data = [op.to_dict() for op in self.pending_queue]
            TransactionalFileWriter.write_json(self.pending_file, data, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save pending operations: {e}")

    def _remove_pending(self, operation_id: str) -> None:
        """Remove an operation from the queue."""
        self.pending_queue = [op for op in self.pending_queue if op.operation_id != operation_id]
        self._save_pending()

    def _persist_mode(self) -> None:
        """Persist current mode to disk for cross-session consistency."""
        try:
            TransactionalFileWriter.write_text(self._mode_file, self._mode.value)
            logger.debug(f"Shadow Mode persisted: {self._mode.value}")
        except Exception as e:
            logger.warning(f"Failed to persist Shadow Mode: {e}")

    def _load_mode(self) -> None:
        """Load persisted mode from disk if available."""
        if self._mode_file.exists():
            try:
                mode_str = self._mode_file.read_text().strip().upper()
                if mode_str in ("DISABLED", "ENABLED", "STRICT"):
                    self._mode = ShadowModeLevel[mode_str]
                    logger.debug(f"Loaded persisted Shadow Mode: {mode_str}")
            except Exception as e:
                logger.warning(f"Failed to load persisted Shadow Mode: {e}")


# ============================================================================
# Console UI for approval
# ============================================================================


def interactive_approval_ui(pending: PendingOperation) -> bool:
    """
    Console-based approval UI for Shadow Mode.

    Returns:
        True if approved, False if rejected
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        # Build display
        table = Table(title="⚠️ Approval Required", show_header=True)
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("Type", pending.operation_type)
        table.add_row("File", pending.file_path)
        table.add_row("Severity", f"[red]{pending.severity.value}[/red]")
        table.add_row("Description", pending.description)

        console.print(Panel(table, border_style="red"))

        if pending.preview:
            console.print(Panel(pending.preview[:500], title="Preview", border_style="yellow"))

        # Get input
        response = console.input("[bold yellow]Approve this operation? (y/N): [/]")
        return response.lower() in ("y", "yes")

    except ImportError:
        # Fallback without Rich
        print("\n⚠️ APPROVAL REQUIRED")
        print(f"Type: {pending.operation_type}")
        print(f"File: {pending.file_path}")
        print(f"Severity: {pending.severity.value}")
        print(f"Description: {pending.description}")

        response = input("Approve? (y/N): ")
        return response.lower() in ("y", "yes")


# ============================================================================
# Factory and convenience functions
# ============================================================================


def create_shadow_guard(
    project_root: Path, mode: str = "ENABLED", interactive: bool = False
) -> ShadowModeGuard:
    """
    Create a Shadow Mode guard with sensible defaults.

    Args:
        project_root: Project root directory
        mode: "DISABLED", "ENABLED", or "STRICT"
        interactive: If True, use console UI for approval

    Returns:
        Configured ShadowModeGuard
    """
    # Parse mode
    try:
        level = ShadowModeLevel[mode.upper()]
    except KeyError:
        level = ShadowModeLevel.ENABLED

    # Set callback if interactive
    callback = interactive_approval_ui if interactive else None

    return ShadowModeGuard(project_root=project_root, mode=level, approval_callback=callback)


# ============================================================================
# Static Analysis for Synthesized Tools (V2 Safety)
# ============================================================================
class SynthesizedToolValidator:
    """
    Validates generated code before execution using AST analysis.
    Prevents injection of dangerous system calls in synthesized tools.
    """

    FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "shutil", "socket", "pickle", "importlib"}
    FORBIDDEN_FUNCTIONS = {"exec", "eval", "compile", "open", "__import__", "breakpoint"}

    @classmethod
    def validate(cls, code: str) -> list[str]:
        """
        Analyze code for suppressed security risks.

        Returns:
            List of violation messages (empty if safe).
        """
        violations = []
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"Syntax Error: {e}"]

        for node in ast.walk(tree):
            # 1. Check Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    if root_pkg in cls.FORBIDDEN_IMPORTS:
                        violations.append(f"Forbidden import: '{root_pkg}' (Sandbox Violation)")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    if root_pkg in cls.FORBIDDEN_IMPORTS:
                        violations.append(f"Forbidden import: '{root_pkg}' (Sandbox Violation)")

            # 2. Check Function Calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in cls.FORBIDDEN_FUNCTIONS:
                        violations.append(
                            f"Forbidden function call: '{node.func.id}' (Sandbox Violation)"
                        )

        return violations
