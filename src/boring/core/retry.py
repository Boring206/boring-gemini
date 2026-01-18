import random
from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """
    Policy for exponential backoff retries.
    """

    max_retries: int = 3
    base_delay: float = 0.5  # seconds
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for the next attempt (0-indexed).
        attempt 0 -> wait before retry 1
        """
        delay = min(self.base_delay * (self.exponential_base**attempt), self.max_delay)
        if self.jitter:
            delay = delay * random.uniform(0.5, 1.5)
        return delay
