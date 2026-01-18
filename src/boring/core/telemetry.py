from __future__ import annotations

import json
import logging
import threading
import time
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from .config import settings

T = TypeVar("T")

logger = logging.getLogger(__name__)

CORRELATION_ID: ContextVar[str | None] = ContextVar("correlation_id", default=None)


@dataclass
class TelemetryEvent:
    name: str
    type: str  # counter, gauge, span
    value: float | None = None
    duration: float | None = None
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TelemetryManager(AbstractContextManager):
    """
    Centralized telemetry and performance tracking.
    Supports in-memory buffering and asynchronous persistence.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_dir: Path | None = None):
        if self._initialized:
            return
        self.events: list[TelemetryEvent] = []
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.log_dir = log_dir or settings.LOG_DIR
        self._initialized = True

    def __enter__(self) -> TelemetryManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()

    def record_event(self, event: TelemetryEvent):
        """Record an event."""
        self.events.append(event)
        if len(self.events) > 1000:
            self.events.pop(0)

    def counter(self, name: str, value: int = 1, metadata: dict | None = None):
        """Increment a counter."""
        self.record_event(
            TelemetryEvent(name, "counter", value=float(value), metadata=metadata or {})
        )

    def gauge(self, name: str, value: float, metadata: dict | None = None):
        """Set a gauge value."""
        self.record_event(TelemetryEvent(name, "gauge", value=value, metadata=metadata or {}))

    @contextmanager
    def span(self, name: str, metadata: dict | None = None):
        """Context manager to track execution duration."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.record_event(
                TelemetryEvent(name, "span", value=None, duration=duration, metadata=metadata or {})
            )

    def flush(self):
        """Persist events to disk."""
        if not self.events:
            return

        self.log_dir.mkdir(parents=True, exist_ok=True)
        telemetry_file = self.log_dir / "telemetry.jsonl"

        try:
            with open(telemetry_file, "a", encoding="utf-8") as f:
                for event in self.events:
                    f.write(json.dumps(asdict(event)) + "\n")
            self.events = []
        except Exception as e:
            logger.debug(f"Failed to write telemetry: {e}")


_telemetry = None


def get_telemetry() -> TelemetryManager:
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryManager()
    return _telemetry
