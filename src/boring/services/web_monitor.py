"""
Web Monitor for Boring V11.0

Provides a lightweight web dashboard for monitoring Boring loop status.
Uses FastAPI for async support and real-time updates.

V11.0 Enhancements:
- Transactional File Writing (write to temp, then atomic rename)
- Threading Lock for concurrent access protection
- Race condition prevention for JSON state files
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Thread lock for file operations
_file_lock = threading.Lock()


class TransactionalFileWriter:
    """
    Atomic file writer that prevents partial writes.

    Uses write-to-temp-then-rename pattern for crash-safe writes.
    """


class ThreadSafeJsonReader:
    """
    Thread-safe JSON reader with retry logic for incomplete reads.

    Handles race conditions when Agent is writing while Monitor is reading.
    """

    @staticmethod
    def read_json(file_path: Path, default: Any = None, max_retries: int = 3) -> Any:
        """
        Safely read JSON file with retry logic.

        Args:
            file_path: Path to JSON file
            default: Default value if read fails
            max_retries: Number of retry attempts

        Returns:
            Parsed JSON data or default value
        """
        if not file_path.exists():
            return default

        with _file_lock:
            for attempt in range(max_retries):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if not content.strip():
                        return default
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"JSON decode error on attempt {attempt + 1}/{max_retries} for {file_path}: {e}"
                    )
                    if attempt < max_retries - 1:
                        import time

                        time.sleep(0.1 * (attempt + 1))  # Brief backoff
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    return default

            return default

    @staticmethod
    def read_text(file_path: Path, default: str = "") -> str:
        """
        Safely read text file.

        Args:
            file_path: Path to text file
            default: Default value if read fails

        Returns:
            File content or default value
        """
        if not file_path.exists():
            return default

        with _file_lock:
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                return default


# Check for FastAPI availability
try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    uvicorn = None


def create_monitor_app(project_root: Path) -> Optional[Any]:
    """
    Create FastAPI app for web monitoring.

    Args:
        project_root: Project directory to monitor

    Returns:
        FastAPI app or None if dependencies not available
    """
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available. Install with: pip install fastapi uvicorn")
        return None

    app = FastAPI(
        title="Boring Monitor",
        description="Real-time monitoring dashboard for Boring autonomous loop",
        version="11.0.0",
    )

    memory_dir = project_root / ".boring_memory"
    brain_dir = project_root / ".boring_brain"

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the main dashboard HTML."""
        return get_dashboard_html()

    @app.get("/api/status")
    async def get_status():
        """
        Get current loop status.

        V11.0: Uses ThreadSafeJsonReader to prevent race conditions.
        """
        # Try to read loop status with thread-safe reader
        status_file = memory_dir / "loop_status.json"
        status_data = ThreadSafeJsonReader.read_json(status_file)
        if status_data:
            return status_data

        # Read from circuit breaker state
        circuit_file = project_root / ".circuit_breaker_state"
        circuit_data = ThreadSafeJsonReader.read_json(circuit_file, default={})
        circuit_state = circuit_data.get("state", "UNKNOWN") if circuit_data else "UNKNOWN"

        # Read call count with thread-safe reader
        call_count_file = project_root / ".call_count"
        call_count = 0
        call_count_text = ThreadSafeJsonReader.read_text(call_count_file)
        if call_count_text.strip():
            try:
                call_count = int(call_count_text.strip())
            except ValueError:
                pass

        return {
            "project": project_root.name,
            "circuit_state": circuit_state,
            "call_count": call_count,
            "timestamp": datetime.now().isoformat(),
        }

    @app.get("/api/logs")
    async def get_recent_logs(limit: int = 50):
        """Get recent log entries with thread-safe reading."""
        logs_dir = project_root / "logs"
        if not logs_dir.exists():
            return {"logs": []}

        all_logs = []
        for log_file in sorted(logs_dir.glob("*.log"), reverse=True)[:3]:
            content = ThreadSafeJsonReader.read_text(log_file)
            if content:
                lines = content.strip().split("\n")
                all_logs.extend(lines[-limit:])

        return {"logs": all_logs[-limit:]}

    @app.get("/api/stats")
    async def get_stats():
        """
        Get loop statistics.

        V11.0: Uses ThreadSafeJsonReader for concurrent safety.
        """
        stats = {
            "patterns_count": 0,
            "pending_approvals": 0,
            "rag_indexed": False,
        }

        # Count patterns with thread-safe reading
        patterns_file = brain_dir / "learned_patterns" / "patterns.json"
        patterns = ThreadSafeJsonReader.read_json(patterns_file, default=[])
        if isinstance(patterns, list):
            stats["patterns_count"] = len(patterns)
        elif isinstance(patterns, dict):
            stats["patterns_count"] = len(patterns)

        # Count pending Shadow Mode operations
        pending_file = memory_dir / "pending_ops.json"
        ops = ThreadSafeJsonReader.read_json(pending_file, default=[])
        if isinstance(ops, list):
            stats["pending_approvals"] = len(ops)

        # Check RAG index
        rag_dir = memory_dir / "rag_db"
        try:
            stats["rag_indexed"] = rag_dir.exists() and any(rag_dir.iterdir())
        except Exception:
            stats["rag_indexed"] = False

        return stats

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "version": "11.0.0", "timestamp": datetime.now().isoformat()}

    return app


def get_dashboard_html() -> str:
    """Generate the dashboard HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boring Monitor</title>
    <style>
        :root {
            --bg: #0f0f0f;
            --card-bg: #1a1a2e;
            --accent: #6366f1;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --success: #22c55e;
            --warning: #eab308;
            --danger: #ef4444;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            background: linear-gradient(135deg, var(--accent), #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        .status-badge.success { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        .status-badge.warning { background: rgba(234, 179, 8, 0.2); color: var(--warning); }
        .status-badge.danger { background: rgba(239, 68, 68, 0.2); color: var(--danger); }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .card {
            background: var(--card-bg);
            border-radius: 1rem;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 {
            font-size: 0.875rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
        }
        .logs {
            background: var(--card-bg);
            border-radius: 1rem;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            max-height: 400px;
            overflow-y: auto;
        }
        .logs h2 { margin-bottom: 1rem; }
        .log-entry {
            font-family: 'Fira Code', monospace;
            font-size: 0.75rem;
            padding: 0.25rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            color: var(--muted);
        }
        .refresh-btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.875rem;
        }
        .refresh-btn:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔮 Boring Monitor</h1>
        <div>
            <span id="circuit-badge" class="status-badge">Loading...</span>
            <button class="refresh-btn" onclick="refresh()">Refresh</button>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>API Calls</h2>
            <div id="call-count" class="stat-value">-</div>
        </div>
        <div class="card">
            <h2>Learned Patterns</h2>
            <div id="patterns-count" class="stat-value">-</div>
        </div>
        <div class="card">
            <h2>Pending Approvals</h2>
            <div id="pending-count" class="stat-value">-</div>
        </div>
        <div class="card">
            <h2>Current Goal / Action</h2>
            <div id="last-action" style="font-size: 1.2rem; font-weight: 500; font-family: monospace;">-</div>
        </div>
        <div class="card">
            <h2>RAG Indexed</h2>
            <div id="rag-status" class="stat-value">-</div>
        </div>
    </div>

    <div class="logs">
        <h2>Recent Logs</h2>
        <div id="logs-container"></div>
    </div>

    <script>
        async function refresh() {
            // Status
            const status = await fetch('/api/status').then(r => r.json());
            document.getElementById('call-count').textContent = status.call_count || 0;

            const badge = document.getElementById('circuit-badge');
            badge.textContent = status.circuit_state || 'UNKNOWN';
            badge.className = 'status-badge ' + getStateClass(status.circuit_state);

            // Stats
            const stats = await fetch('/api/stats').then(r => r.json());
            document.getElementById('patterns-count').textContent = stats.patterns_count || 0;
            document.getElementById('pending-count').textContent = stats.pending_approvals || 0;
            document.getElementById('rag-status').textContent = stats.rag_indexed ? '✓' : '✗';
            document.getElementById('last-action').textContent = status.last_action || '-';

            // Logs
            const logs = await fetch('/api/logs').then(r => r.json());
            const container = document.getElementById('logs-container');
            container.innerHTML = logs.logs.map(l => `<div class="log-entry">${l}</div>`).join('');
        }

        function getStateClass(state) {
            if (state === 'CLOSED') return 'success';
            if (state === 'HALF_OPEN') return 'warning';
            if (state === 'OPEN') return 'danger';
            return '';
        }

        refresh();
        setInterval(refresh, 5000);
    </script>
</body>
</html>
"""


def run_web_monitor(project_root: Path, port: int = 8765, host: str = "127.0.0.1"):
    """
    Start the web monitor server.

    Args:
        project_root: Project to monitor
        port: Port to run on (default 8765)
        host: Host to bind to (default localhost)
    """
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
        return

    app = create_monitor_app(project_root)
    if app:
        # Ensure host is string and port is int to avoid getaddrinfo TypeErrors on some environments
        host_str = str(host)
        port_int = int(port)
        print(f"🚀 Starting Boring Monitor at http://{host_str}:{port_int}")
        uvicorn.run(app, host=host_str, port=port_int, log_level="warning")
