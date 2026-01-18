"""
💀 Chaos Engineering Fixture

Designed to simulate hostile environments where dependencies are flaky,
slow, or outright malicious.

Usage:
    def test_resilience(chaos_monkey):
        with chaos_monkey(failure_rate=0.5):
            # Your code here
"""

import random
import time
from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest


# Define custom exceptions for chaos
class ChaosError(Exception):
    """Base error for chaos monkey injected failures."""

    pass


class ChaosTimeoutError(ChaosError):
    """Simulated network timeout."""

    pass


class ChaosConnectionError(ChaosError):
    """Simulated connection drop."""

    pass


class ChaosServerError(ChaosError):
    """Simulated 500 Server Error."""

    pass


class ChaosMonkey:
    """
    The agent of chaos. Intercepts calls and injects failures based on probability.
    """

    def __init__(self):
        self.failure_rate = 0.0
        self.latency_seconds = 0.0
        self.active = False
        self.targets = [
            "boring.mcp.speckit_tools.boring_speckit_plan",
            "boring.mcp.speckit_tools.boring_speckit_tasks",
            "google.genai.Client.models.generate_content",  # Target SDK
            # Add more targets as needed
        ]

    def _should_fail(self) -> bool:
        return self.active and random.random() < self.failure_rate

    def _inject_latency(self):
        if self.latency_seconds > 0:
            time.sleep(self.latency_seconds)

    def _random_exception(self) -> Exception:
        """Pick a poison."""
        return random.choice(
            [
                ChaosTimeoutError("Simulated Network Timeout (Chaos)"),
                ChaosConnectionError("Simulated Connection Reset (Chaos)"),
                ChaosServerError("Simulated 500 Internal Server Error (Chaos)"),
            ]
        )

    @contextmanager
    def unleash(
        self, failure_rate: float = 0.3, latency: float = 0.0
    ) -> Generator[None, None, None]:
        """
        Context manager to activate the Chaos Monkey.

        Args:
            failure_rate: Probability (0.0 - 1.0) of a call failing.
            latency: Artificial latency in seconds added to requests.
        """
        self.failure_rate = failure_rate
        self.latency_seconds = latency
        self.active = True

        # Setup patches
        patches = []

        # We need a wrapper that can handle both sync and async targets conceptually,
        # but for simplicity here we assume standard mocking behavior.
        # For strict typing, we might distinguish, but side_effect handles exceptions well.

        def chaos_side_effect(*args, **kwargs):
            self._inject_latency()
            if self._should_fail():
                raise self._random_exception()
            return MagicMock(name="ChaosMockSuccess")

        # In a real rigorous implementation, we would inspect the target signature.
        # Here we patch specifically the targets we know.

        try:
            for target in self.targets:
                # We use a broad patch here. In production tests, verify target existence first.
                p = patch(target, side_effect=chaos_side_effect)
                p.start()
                patches.append(p)

            yield

        finally:
            for p in patches:
                p.stop()
            self.active = False


@pytest.fixture
def chaos_monkey() -> ChaosMonkey:
    """
    Pytest fixture to provide a ChaosMonkey instance.

    Example:
        def test_retry_logic(chaos_monkey):
            with chaos_monkey.unleash(failure_rate=1.0):
                # Assert that your code handles 100% failure gracefully
                result = run_resilient_op()
                assert result.status == "FAILED_GRACEFULLY"
    """
    return ChaosMonkey()
