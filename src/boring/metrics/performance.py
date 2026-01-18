import logging

from ..core.telemetry import get_telemetry

logger = logging.getLogger("boring.metrics.performance")


class PerformanceTracker:
    def __init__(self):
        self.metrics = {}

    def track(self, name: str, duration: float):
        from ..core.telemetry import TelemetryEvent

        get_telemetry().record_event(
            TelemetryEvent(name=name, type="span", duration=duration, value=None)
        )

    def get_stats(self):
        return get_telemetry().get_stats()


tracker = PerformanceTracker()


def track_performance(name: str = None):
    """Decorator to track function execution time."""
    return get_telemetry().track(name)


def track_async_performance(name: str = None):
    """Decorator to track async function execution time."""
    return get_telemetry().track(name)
