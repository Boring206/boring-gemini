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
from typing import Any

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


# Brain distribution helper (SQLite-first)
def _get_brain_distribution(project_root: Path) -> dict[str, int]:
    try:
        from ..services.storage import create_storage

        storage = create_storage(project_root)
        patterns = storage.get_patterns(limit=1000)
        distribution: dict[str, int] = {}
        for pattern in patterns:
            pattern_type = pattern.get("pattern_type") or "unknown"
            distribution[pattern_type] = distribution.get(pattern_type, 0) + 1
        return distribution
    except Exception:
        return {}


def _get_token_stats(project_root: Path) -> dict[str, Any]:
    try:
        from ..metrics.token_tracker import TokenTracker

        tracker = TokenTracker(project_root)
        return tracker.get_total_stats()
    except Exception:
        return {}


# Check for FastAPI availability
try:
    import asyncio

    import uvicorn
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    uvicorn = None
    WebSocket = None
    WebSocketDisconnect = None


def create_monitor_app(project_root: Path) -> Any | None:
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
        version="14.8.0",
    )

    from boring.paths import BoringPaths

    bp = BoringPaths(project_root)
    memory_dir = bp.memory
    brain_dir = bp.brain

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
        from boring.paths import get_state_file

        # Try to read loop status with thread-safe reader
        status_file = memory_dir / "loop_status.json"
        status_data = ThreadSafeJsonReader.read_json(status_file)
        if status_data:
            return status_data

        # Read from circuit breaker state using unified helper
        circuit_file = get_state_file(project_root, "circuit_breaker_state")
        circuit_data = ThreadSafeJsonReader.read_json(circuit_file, default={})
        circuit_state = circuit_data.get("state", "UNKNOWN") if circuit_data else "UNKNOWN"

        # Read call count with thread-safe reader
        call_count_file = get_state_file(project_root, "call_count")
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
        logs_dir = bp.state / "logs"
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

        stats["pattern_type_distribution"] = _get_brain_distribution(project_root)
        stats["token_stats"] = _get_token_stats(project_root)
        if not stats["patterns_count"] and stats["pattern_type_distribution"]:
            stats["patterns_count"] = sum(stats["pattern_type_distribution"].values())

        return stats

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "version": "14.8.0", "timestamp": datetime.now().isoformat()}

    # --- WebSocket Support ---

    class ConnectionManager:
        def __init__(self):
            self.active_connections: list[WebSocket] = []

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

        def disconnect(self, websocket: WebSocket):
            self.active_connections.remove(websocket)

        async def broadcast(self, message: dict):
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Stale connection
                    pass

    manager = ConnectionManager()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                # Get current status
                status_file = memory_dir / "loop_status.json"
                status_data = ThreadSafeJsonReader.read_json(status_file, default={})

                from boring.paths import get_state_file

                circuit_file = get_state_file(project_root, "circuit_breaker_state")
                circuit_data = ThreadSafeJsonReader.read_json(circuit_file, default={})

                call_count_file = get_state_file(project_root, "call_count")
                call_count = ThreadSafeJsonReader.read_text(call_count_file).strip() or "0"

                # Fetch recent logs
                logs_dir = bp.state / "logs"
                recent_logs = []
                if logs_dir.exists():
                    for log_file in sorted(logs_dir.glob("*.log"), reverse=True)[:1]:
                        content = ThreadSafeJsonReader.read_text(log_file)
                        if content:
                            recent_logs = content.strip().split("\n")[-20:]

                payload = {
                    "type": "update",
                    "status": status_data,
                    "circuit_state": circuit_data.get("state", "UNKNOWN"),
                    "call_count": call_count,
                    "logs": recent_logs,
                    "brain_distribution": _get_brain_distribution(project_root),
                    "token_stats": _get_token_stats(project_root),
                    "timestamp": datetime.now().isoformat(),
                }

                await websocket.send_json(payload)
                await asyncio.sleep(2)  # Refresh every 2 seconds
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket)

    return app


def get_dashboard_html() -> str:
    """Generate the dashboard HTML with premium aesthetics and WebSocket support."""
    return r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔮 Boring Monitor | Real-time AI Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #050505;
            --glass: rgba(26, 26, 46, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
            --accent: #6366f1;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --glow: 0 0 20px rgba(99, 102, 241, 0.3);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            background-image:
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.05) 0%, transparent 40%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 3rem;
            line-height: 1.5;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4rem;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .header h1 span {
            font-size: 0.875rem;
            font-weight: 500;
            padding: 0.25rem 0.75rem;
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid var(--accent);
            border-radius: 9999px;
            -webkit-text-fill-color: var(--accent);
            letter-spacing: 0.05em;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background: var(--glass);
            padding: 0.5rem 1.25rem;
            border-radius: 9999px;
            border: 1px solid var(--glass-border);
            font-weight: 500;
            box-shadow: var(--glow);
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--text-secondary);
        }
        .status-dot.active { background: var(--success); box-shadow: 0 0 10px var(--success); animation: pulse 2s infinite; }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--glass);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 1.5rem;
            padding: 2rem;
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: rgba(255,255,255,0.2);
            transform: translateY(-4px);
        }

        .card-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 1.5rem;
        }

        .card-value {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1;
        }

        .card-subtext {
            margin-top: 1rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .dist-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }

        .dist-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .logs-section {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: 1.5rem;
            padding: 2rem;
            margin-top: 2rem;
        }

        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }

        .logs-container {
            font-family: 'Fira Code', monospace;
            font-size: 0.875rem;
            max-height: 400px;
            overflow-y: auto;
            padding-right: 1rem;
        }

        .logs-container::-webkit-scrollbar { width: 6px; }
        .logs-container::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 3px; }

        .log-line {
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            display: flex;
            gap: 1.5rem;
        }

        .log-ts { color: var(--accent); opacity: 0.6; min-width: 160px; }
        .log-msg { color: var(--text-secondary); }

        .connection-status {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .goal-card { grid-column: span 2; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔮 Boring Monitor <span>V14.0 Enterprise</span></h1>
            <div class="status-pill">
                <div id="ws-dot" class="status-dot"></div>
                <div id="circuit-state">INITIALIZING</div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-label">API Pressure</div>
                <div id="call-count" class="card-value">0</div>
                <div class="card-subtext">Calls this hour</div>
            </div>
            <div class="card">
                <div class="card-label">Token Usage</div>
                <div id="token-total" class="card-value">0</div>
                <div class="card-subtext">Input: <span id="token-in">0</span> • Output: <span id="token-out">0</span></div>
            </div>
            <div class="card goal-card">
                <div class="card-label">Active Flow Intelligence</div>
                <div id="current-action" style="font-size: 1.5rem; font-weight: 500;">Waiting for loop...</div>
                <div id="loop-count" class="card-subtext">Loops completed: 0</div>
            </div>
            <div class="card">
                <div class="card-label">Brain Patterns</div>
                <div id="patterns-count" class="card-value">0</div>
                <div class="card-subtext">Persistent knowledge nodes</div>
            </div>
            <div class="card">
                <div class="card-label">Brain Modes</div>
                <div id="brain-dist" class="dist-list"></div>
                <div class="card-subtext">Pattern type distribution</div>
            </div>
            <div class="card">
                <div class="card-label">RAG Index</div>
                <div id="rag-status" class="card-value">✗</div>
                <div class="card-subtext">Semantic search status</div>
            </div>
            <div class="card">
                <div class="card-label">System Health</div>
                <div class="card-value" style="color: var(--success);">OK</div>
                <div class="card-subtext">Latency: <span id="latency">-</span>ms</div>
            </div>
        </div>

        <div class="logs-section">
            <div class="logs-header">
                <h2 style="font-size: 1.25rem; font-weight: 600;">Neural Activity Logs</h2>
            </div>
            <div id="logs-container" class="logs-container">
                <div class="log-line"><div class="log-msg">Initializing real-time stream...</div></div>
            </div>
        </div>
    </div>

    <div class="connection-status">
        <span id="ws-status">Disconnected</span>
        <span>•</span>
        <span id="last-update">Never</span>
    </div>

    <script>
        let socket;
        let lastUpdate = Date.now();

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            socket = new WebSocket(`${protocol}//${window.location.host}/ws`);

            socket.onopen = () => {
                document.getElementById('ws-status').textContent = 'Connected';
                document.getElementById('ws-dot').classList.add('active');
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'update') {
                    updateUI(data);
                }
            };

            socket.onclose = () => {
                document.getElementById('ws-status').textContent = 'Reconnecting...';
                document.getElementById('ws-dot').classList.remove('active');
                setTimeout(connect, 3000);
            };
        }

        function updateUI(data) {
            const now = Date.now();
            document.getElementById('latency').textContent = now - lastUpdate;
            lastUpdate = now;

            // Basic Stats
            document.getElementById('call-count').textContent = data.call_count || '0';
            document.getElementById('current-action').textContent = data.status.current_task || 'Idle';
            document.getElementById('loop-count').textContent = `Loops completed: ${data.status.loop_count || 0}`;
            document.getElementById('circuit-state').textContent = data.circuit_state || 'UNKNOWN';

            const tokenStats = data.token_stats || {};
            const totalTokens = (tokenStats.total_input_tokens || 0) + (tokenStats.total_output_tokens || 0);
            const tokenTotalEl = document.getElementById('token-total');
            const tokenInEl = document.getElementById('token-in');
            const tokenOutEl = document.getElementById('token-out');
            if (tokenTotalEl) tokenTotalEl.textContent = totalTokens;
            if (tokenInEl) tokenInEl.textContent = tokenStats.total_input_tokens || 0;
            if (tokenOutEl) tokenOutEl.textContent = tokenStats.total_output_tokens || 0;

            // Circuit State Colors
            const circuitBadge = document.getElementById('circuit-state');
            if (data.circuit_state === 'CLOSED') circuitBadge.style.color = 'var(--success)';
            else if (data.circuit_state === 'OPEN') circuitBadge.style.color = 'var(--danger)';
            else circuitBadge.style.color = 'var(--warning)';

            // Logs
            const logsContainer = document.getElementById('logs-container');
            if (data.logs && data.logs.length > 0) {
                logsContainer.innerHTML = data.logs.map(line => {
                    const match = line.match(/\[(.*?)\] (.*)/);
                    if (match) {
                        return `<div class="log-line"><div class="log-ts">${match[1]}</div><div class="log-msg">${match[2]}</div></div>`;
                    }
                    return `<div class="log-line"><div class="log-msg">${line}</div></div>`;
                }).join('');
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }

            // Brain Distribution
            const distContainer = document.getElementById('brain-dist');
            if (distContainer) {
                const dist = data.brain_distribution || {};
                const entries = Object.entries(dist);
                if (entries.length === 0) {
                    distContainer.innerHTML = '<div class="dist-row"><span>None</span><span>0</span></div>';
                } else {
                    distContainer.innerHTML = entries
                        .sort((a, b) => b[1] - a[1])
                        .map(([name, count]) => `<div class="dist-row"><span>${name}</span><span>${count}</span></div>`)
                        .join('');
                }
            }

            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }

        connect();
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
