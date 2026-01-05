"""
PatchingState - Handles function call processing and file writing.

This state is responsible for:
1. Processing function calls (write_file, search_replace)
2. Creating backups before modifications
3. Writing files to disk
"""

from pathlib import Path
from typing import Any, Optional

from ...backup import BackupManager
from ...logger import console, log_status
from ...security import sanitize_content, validate_file_path
from ..base import LoopState, StateResult
from ..context import LoopContext


class PatchingState(LoopState):
    """
    State for applying file changes from function calls.

    Transitions:
    - SUCCESS → VerifyingState (if files written)
    - FAILURE → RecoveryState (if no files or errors)
    """

    @property
    def name(self) -> str:
        return "Patching"

    def on_enter(self, context: LoopContext) -> None:
        """Log state entry."""
        context.start_state()
        log_status(
            context.log_dir,
            "INFO",
            f"[State: {self.name}] Processing {len(context.function_calls)} function calls...",
        )
        console.print(f"[yellow]🔧 Patching ({len(context.function_calls)} calls)...[/yellow]")

    def handle(self, context: LoopContext) -> StateResult:
        """Process function calls and write files."""
        if not context.function_calls:
            context.errors_this_loop.append("No function calls to process")
            return StateResult.FAILURE

        # Separate function calls by type
        write_calls = []
        replace_calls = []

        for call in context.function_calls:
            name = call.get("name", "")
            if name == "write_file":
                write_calls.append(call)
            elif name == "search_replace":
                replace_calls.append(call)
            elif name == "report_status":
                pass

        # Create backup of files to be modified
        files_to_backup = self._get_files_to_modify(context, write_calls, replace_calls)
        if files_to_backup:
            backup_mgr = BackupManager(
                context.loop_count,
                project_root=context.project_root,
                backup_dir=context.project_root / ".boring_backups",
            )
            snapshot = backup_mgr.create_snapshot(files_to_backup)
            if snapshot:
                log_status(context.log_dir, "INFO", f"Created backup: {snapshot}")

        # Process write_file calls
        for call in write_calls:
            self._process_write_file(context, call)

        # Process search_replace calls
        for call in replace_calls:
            self._process_search_replace(context, call)

        # Check results
        total_modified = len(context.files_modified) + len(context.files_created)

        if total_modified > 0:
            log_status(
                context.log_dir,
                "SUCCESS",
                f"Modified {len(context.files_modified)}, Created {len(context.files_created)} files",
            )
            return StateResult.SUCCESS
        else:
            if context.patch_errors:
                context.errors_this_loop.extend(context.patch_errors)
            else:
                context.errors_this_loop.append("No files were modified")
            return StateResult.FAILURE

    def next_state(self, context: LoopContext, result: StateResult) -> Optional[LoopState]:
        """Determine next state based on patching result."""
        # Record telemetry
        self._record_metrics(context, result)

        if result == StateResult.SUCCESS:
            from .verifying import VerifyingState

            return VerifyingState()
        else:
            from .recovery import RecoveryState

            return RecoveryState()

    def _get_files_to_modify(
        self, context: LoopContext, write_calls: list[dict], replace_calls: list[dict]
    ) -> list[Path]:
        """Get list of existing files that will be modified."""
        files = []

        for call in write_calls:
            path = call.get("args", {}).get("file_path", "")
            if path:
                full_path = context.project_root / path
                if full_path.exists():
                    files.append(full_path)

        for call in replace_calls:
            path = call.get("args", {}).get("file_path", "")
            if path:
                full_path = context.project_root / path
                if full_path.exists():
                    files.append(full_path)

        return list(set(files))  # Deduplicate

    def _process_write_file(self, context: LoopContext, call: dict[str, Any]) -> None:
        """Process a write_file function call."""
        args = call.get("args", {})
        file_path = args.get("file_path", "").strip()
        content = args.get("content", "")

        if not file_path:
            context.patch_errors.append("write_file: missing file_path")
            return

        # Security validation
        validation = validate_file_path(file_path, context.project_root, log_dir=context.log_dir)
        if not validation.is_valid:
            context.patch_errors.append(f"write_file: {validation.reason}")
            log_status(context.log_dir, "WARN", f"Blocked: {file_path} - {validation.reason}")
            return

        # Use normalized path
        if validation.normalized_path:
            file_path = validation.normalized_path

        full_path = context.project_root / file_path
        is_new = not full_path.exists()

        # Sanitize content
        content = sanitize_content(content)

        try:
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            full_path.write_text(content, encoding="utf-8")

            if is_new:
                context.files_created.append(file_path)
                log_status(context.log_dir, "SUCCESS", f"✨ Created: {file_path}")
            else:
                context.files_modified.append(file_path)
                log_status(context.log_dir, "SUCCESS", f"✏️ Modified: {file_path}")

        except Exception as e:
            context.patch_errors.append(f"write_file {file_path}: {e}")
            log_status(context.log_dir, "ERROR", f"Failed to write {file_path}: {e}")

    def _process_search_replace(self, context: LoopContext, call: dict[str, Any]) -> None:
        """Process a search_replace function call."""
        args = call.get("args", {})
        file_path = args.get("file_path", "").strip()
        search = args.get("search", "")
        replace = args.get("replace", "")

        if not file_path or not search:
            context.patch_errors.append("search_replace: missing file_path or search")
            return

        # Security validation
        validation = validate_file_path(file_path, context.project_root, log_dir=context.log_dir)
        if not validation.is_valid:
            context.patch_errors.append(f"search_replace: {validation.reason}")
            return

        if validation.normalized_path:
            file_path = validation.normalized_path

        full_path = context.project_root / file_path

        if not full_path.exists():
            context.patch_errors.append(f"search_replace: file not found: {file_path}")
            return

        try:
            content = full_path.read_text(encoding="utf-8")

            if search not in content:
                context.patch_errors.append(f"search_replace: search text not found in {file_path}")
                log_status(context.log_dir, "WARN", f"Search text not found in {file_path}")
                return

            new_content = content.replace(search, replace, 1)  # Replace first occurrence
            full_path.write_text(new_content, encoding="utf-8")

            context.files_modified.append(file_path)
            log_status(context.log_dir, "SUCCESS", f"🔄 Replaced in: {file_path}")

        except Exception as e:
            context.patch_errors.append(f"search_replace {file_path}: {e}")
            log_status(context.log_dir, "ERROR", f"Failed to replace in {file_path}: {e}")

    def _record_metrics(self, context: LoopContext, result: StateResult) -> None:
        """Record telemetry for this state."""
        if context.storage:
            try:
                context.storage.record_metric(
                    name="state_patching",
                    value=context.get_state_duration(),
                    metadata={
                        "loop": context.loop_count,
                        "result": result.value,
                        "files_modified": len(context.files_modified),
                        "files_created": len(context.files_created),
                        "errors": len(context.patch_errors),
                    },
                )
            except Exception:
                pass
