import functools
import logging
import threading
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failure detected, fast-failing
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when an operation is blocked by the circuit breaker."""

    pass


class CircuitBreaker:
    """
    World-Class Circuit Breaker implementation for external dependencies.
    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute the function, tracking success/failure."""
        with self._lock:
            self._update_state()
            if self.state == CircuitState.OPEN:
                logger.warning(f"CircuitBreaker '{self.name}' is OPEN. Fast-failing request.")
                raise CircuitBreakerError(f"Service {self.name} is currently unavailable.")

        try:
            result = func(*args, **kwargs)

            with self._lock:
                self._handle_success()
            return result

        except Exception as e:
            with self._lock:
                self._handle_failure(e)
            raise

    def _update_state(self):
        """Transition from OPEN to HALF_OPEN after timeout."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(
                    f"CircuitBreaker '{self.name}' transitioning to HALF_OPEN (Recovery Trial)."
                )
                self.state = CircuitState.HALF_OPEN

    def _handle_success(self):
        """Reset failures on success (Closing the circuit)."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"CircuitBreaker '{self.name}' recovered. Closing circuit.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _handle_failure(self, error: Exception):
        """Increment failure count and trip if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # Log failure
        logger.debug(
            f"CircuitBreaker '{self.name}' recorded failure ({self.failure_count}/{self.failure_threshold}): {error}"
        )

        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(f"CircuitBreaker '{self.name}' TRIPPED. State moving to OPEN.")
            self.state = CircuitState.OPEN


def circuit_breaker(name: str, threshold: int = 5, timeout: float = 30.0):
    """Decorator for easy CircuitBreaker application."""
    cb = CircuitBreaker(name, threshold, timeout)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        return wrapper

    return decorator


# Global Registry for monitoring
_registry: dict[str, CircuitBreaker] = {}


def get_breaker(name: str, **kwargs) -> CircuitBreaker:
    if name not in _registry:
        _registry[name] = CircuitBreaker(name, **kwargs)
    return _registry[name]
