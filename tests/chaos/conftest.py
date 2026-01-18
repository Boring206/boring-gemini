import asyncio
import contextlib
import logging
import sys
from pathlib import Path

import pytest

from boring.core.events import EventStore

# Use the lock script we just created
LOCK_SCRIPT_PATH = Path(__file__).parent / "scripts" / "lock_db.py"

logger = logging.getLogger("chaos")


class ChaosOrchestrator:
    """Helper to inject faults into the system."""

    def __init__(self, root: Path):
        self.root = root

    @contextlib.asynccontextmanager
    async def lock_database(self, db_path: Path, duration: float = 5.0):
        """
        Spawns a subprocess to hold an EXCLUSIVE lock on the SQLite DB.
        Yields control once the lock is confirmed acquired.
        """
        cmd = [sys.executable, str(LOCK_SCRIPT_PATH), str(db_path), str(duration)]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            # Wait for "LOCKED" signal
            if proc.stdout:
                line = await proc.stdout.readline()
                decoded = line.decode().strip()
                if decoded != "LOCKED":
                    # Check stderr
                    err = await proc.stderr.read()
                    raise RuntimeError(f"Failed to acquire lock: {err.decode()}")

                logger.info(f"Chaos: Database {db_path} is now LOCKED for {duration}s")

            yield

        finally:
            # Cleanup if needed (though script auto-closes)
            try:
                if proc.returncode is None:
                    proc.terminate()
                    await proc.wait()
            except Exception:
                pass


@pytest.fixture
def chaos(tmp_path):
    """Provides chaos orchestration capabilities."""
    return ChaosOrchestrator(tmp_path)


@pytest.fixture
async def event_store_async(tmp_path):
    """Provides an async EventStore initialized in tmp_path."""
    store = EventStore(tmp_path, async_mode=True)
    yield store
    store.close()


# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
