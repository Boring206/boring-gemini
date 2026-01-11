from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_fixed

from boring.core.utils import *  # noqa: F401, F403


@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
def robust_write_file(path: Path, content: str) -> None:
    """Write text to file with retries."""
    path.write_text(content, encoding="utf-8")


@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5))
def robust_read_file(path: Path) -> str:
    """Read text from file with retries."""
    return path.read_text(encoding="utf-8")
