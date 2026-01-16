"""
Sandbox Executor for Boring V12.4

Provides temporary directory isolation for executing potentially unsafe scripts.
"""

import logging
import shutil
import subprocess
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """
    Executes code/scripts in an isolated temporary directory.
    """

    def __init__(self, timeout_seconds: int = 30):
        self.timeout = timeout_seconds

    @contextmanager
    def isolation_context(
        self, source_path: Path, copy_files: list[Path] = None
    ) -> Generator[Path, None, None]:
        """
        Context manager that copies files to a temp dir and yields the temp path.

        Args:
            source_path: The main script/file to run.
            copy_files: Additional files/dirs to copy to the sandbox.
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        with tempfile.TemporaryDirectory(prefix="boring_sandbox_") as temp_dir:
            temp_path = Path(temp_dir)

            # Copy main script
            dest_script = temp_path / source_path.name
            if source_path.is_dir():
                shutil.copytree(source_path, dest_script)
            else:
                shutil.copy2(source_path, dest_script)

            # Copy additional dependencies
            if copy_files:
                for item in copy_files:
                    if not item.exists():
                        continue
                    dest = temp_path / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)

            yield dest_script

    def run_script(
        self,
        script_path: Path,
        args: list[str] = None,
        dependencies: list[Path] = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a script in the sandbox.

        Args:
            script_path: Path to the script.
            args: Command line arguments.
            dependencies: List of files/dirs to copy to sandbox.
            cwd: Optional working directory (defaults to sandbox root).

        Returns:
            CompletedProcess result.
        """
        with self.isolation_context(script_path, dependencies) as sandboxed_script:
            sandbox_root = sandboxed_script.parent
            cmd = ["python", str(sandboxed_script)] + (args or [])

            logger.info(f"Executing sandboxed: {cmd} in {sandbox_root}")

            return subprocess.run(
                cmd, cwd=cwd or sandbox_root, capture_output=True, text=True, timeout=self.timeout
            )
