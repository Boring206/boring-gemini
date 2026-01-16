import importlib
import logging
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger("boring.mcp.reloader")


class ToolReloadHandler(FileSystemEventHandler):
    def __init__(self, mcp_instance, root_path: Path):
        self.mcp = mcp_instance
        self.root_path = root_path
        self.last_reload = 0

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return

        # Debounce
        current_time = time.time()
        if current_time - self.last_reload < 1.0:
            return
        self.last_reload = current_time

        changed_path = Path(event.src_path)
        try:
            # Convert path to module name
            # e.g. src/boring/mcp/tools/git.py -> boring.mcp.tools.git
            rectified_path = changed_path.resolve()

            # Simple heuristic: find 'boring' in path parts
            parts = rectified_path.parts
            if "boring" in parts:
                idx = parts.index("boring")
                module_parts = parts[idx:]
                module_name = ".".join(module_parts).replace(".py", "")

                logger.info(f"[Hot Reload] Detected change in {module_name}")
                sys.stderr.write(f"[boring-mcp] 🔥 Hot Reload: {module_name} changed\n")

                # Reload logic
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    importlib.reload(module)
                    # Re-registration happens if the module calls mcp.tool() at top level
                    # Note: Ideally we should explicitly re-register, but V14 architecture
                    # relies on side-effects of imports for decorators.
                    sys.stderr.write(f"[boring-mcp] ✅ Reloaded {module_name}\n")

        except Exception as e:
            logger.error(f"Reload failed: {e}")
            sys.stderr.write(f"[boring-mcp] ❌ Reload failed: {e}\n")


def start_reloader(mcp_instance):
    """Start the tool reloader observer."""
    try:
        # Detect tools directory
        # Assuming we are in src/boring/mcp/reloader.py
        current_file = Path(__file__)
        tools_dir = current_file.parent / "tools"

        if not tools_dir.exists():
            return

        handler = ToolReloadHandler(mcp_instance, tools_dir)
        observer = Observer()
        observer.schedule(handler, str(tools_dir), recursive=True)
        observer.start()

        sys.stderr.write(f"[boring-mcp] 🔥 Hot Reload Enabled (watching {tools_dir})\n")
        return observer
    except Exception as e:
        sys.stderr.write(f"[boring-mcp] Failed to start hot reload: {e}\n")
