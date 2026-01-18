import logging
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ServiceHealth:
    def __init__(self, name: str):
        self.name = name
        self.status = "OK"
        self.last_check = 0.0
        self.details = {}


class BoringSupervisor:
    """
    World-Class System Supervisor.
    Monitors core component health and provides diagnostics.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, root: Path = None):
        if self._initialized:
            return
        self.root = root
        self.services: dict[str, ServiceHealth] = {}
        self._initialized = True

    def check_health(self) -> dict[str, Any]:
        """Run health checks on all monitored components."""
        report = {"timestamp": time.time(), "status": "HEALTHY", "components": {}}

        # 1. Check EventStore / SQLite
        report["components"]["storage"] = self._check_storage()

        # 2. Check Circuit Breakers
        report["components"]["resilience"] = self._check_resilience()

        # 3. Check Background Workers
        report["components"]["workers"] = self._check_workers()

        # Aggregate Status
        if any(c["status"] == "FAIL" for c in report["components"].values()):
            report["status"] = "UNHEALTHY"
        elif any(c["status"] == "WARN" for c in report["components"].values()):
            report["status"] = "DEGRADED"

        return report

    def _check_storage(self) -> dict[str, Any]:
        health = {"status": "OK", "details": {}}
        db_path = self.root / ".boring" / "events.db"
        if not db_path.exists():
            health["status"] = "WARN"
            health["details"]["message"] = "Database file missing."
        else:
            try:
                import sqlite3

                conn = sqlite3.connect(db_path)
                conn.execute("SELECT 1").fetchone()
                conn.close()
                health["details"]["size_kb"] = db_path.stat().st_size / 1024
            except Exception as e:
                health["status"] = "FAIL"
                health["details"]["error"] = str(e)
        return health

    def _check_resilience(self) -> dict[str, Any]:
        from boring.utils.resilience import _registry

        health = {"status": "OK", "breakers": {}}
        for name, cb in _registry.items():
            health["breakers"][name] = cb.state.value
            if cb.state.value == "OPEN":
                health["status"] = "WARN"
        return health

    def _check_workers(self) -> dict[str, Any]:
        health = {"status": "OK", "threads": []}
        import threading

        for thread in threading.enumerate():
            if thread.name.startswith("Boring"):
                health["threads"].append({"name": thread.name, "alive": thread.is_alive()})
                if not thread.is_alive():
                    health["status"] = "WARN"
        return health


def get_supervisor(root: Path = None) -> BoringSupervisor:
    return BoringSupervisor(root)
