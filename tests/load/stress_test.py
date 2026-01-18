import asyncio
import logging
import random
import statistics
import time
from pathlib import Path

from boring.core.events import EventStore
from boring.core.state import StateManager

# Configure logging to show warnings/errors only for libraries, INFO for test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("load_test")


async def worker(worker_id: int, project_root: Path, iterations: int):
    """
    Simulates a user performing multiple state updates.
    """
    # Each session ID acts like a separate connected client
    session_id = f"sess_{worker_id}"

    # Initialize components
    # Sharing the same process memory, so EventStore is shared if Singleton?
    # No, EventStore is per-instance, but SQLite is shared file.
    # In a real CLI scenario, these would be separate processes.
    # But testing threads/coroutines in one process stresses asyncio/Queue/Lock too.

    start_time = time.time()
    latencies = []

    try:
        # Create dedicated manager for this "session"
        # Note: EventStore with async_mode=True means 1 writer thread per store instance.
        # If we spawn 20 workers with 20 stores, we have 20 threads writing to one DB.
        # This is a good stress test for SQLite locking!

        state_mgr = StateManager(project_root, session_id=session_id)
        # Assuming async mode is ON by default in config or passed in?
        # StateManager defaults to settings.ASYNC_LEDGER_WRITE.

        for i in range(iterations):
            step_start = time.time()

            # Simulate "think time"
            await asyncio.sleep(random.uniform(0.1, 0.5))

            # Perform Action: Set Goal or Update
            if i == 0:
                # First step: Set Goal (Sync method, wraps async append wait)
                state_mgr.set_goal(f"Goal from {worker_id}")
            else:
                # Update progress
                state_mgr.update(completed_tasks=i, total_tasks=iterations)

            latency = (time.time() - step_start) * 1000  # ms
            latencies.append(latency)

    except Exception as e:
        logger.error(f"Worker {worker_id} crashed: {e}")
        return False, latencies
    finally:
        # Cleanup
        if hasattr(state_mgr, "events"):
            state_mgr.events.close()

    total_time = time.time() - start_time
    logger.info(f"Worker {worker_id} finished {iterations} ops in {total_time:.2f}s")
    return True, latencies


async def run_stress_test(num_workers=10, iterations=5):
    """Run multiple concurrent workers."""
    import shutil
    import tempfile

    # Setup temp project
    tmp_dir = Path(tempfile.mkdtemp())
    project_root = tmp_dir / "stress_project"
    project_root.mkdir()
    (project_root / ".boring").mkdir()

    logger.info(f"Starting Stress Test: {num_workers} workers, {iterations} ops each.")
    logger.info(f"Project Path: {project_root}")

    start_global = time.time()

    tasks = [worker(i, project_root, iterations) for i in range(num_workers)]
    results = await asyncio.gather(*tasks)

    duration = time.time() - start_global

    # Analysis
    success_count = sum(1 for r in results if r[0])
    all_latencies = [l for r in results for l in r[1]]

    if not all_latencies:
        logger.error("No latencies recorded!")
        return

    avg_lat = statistics.mean(all_latencies)
    p95_lat = statistics.quantiles(all_latencies, n=20)[18]  # 95th percentile
    max_lat = max(all_latencies)

    print("-" * 40)
    print(f"Stress Test Report ({num_workers} users, {iterations} ops)")
    print("-" * 40)
    print(f"Total Time:      {duration:.2f}s")
    print(f"Througput:       {len(all_latencies) / duration:.2f} ops/sec")
    print(
        f"Success Rate:    {success_count}/{num_workers} ({(success_count / num_workers) * 100:.1f}%)"
    )
    print(f"Avg Latency:     {avg_lat:.2f} sms")
    print(f"P95 Latency:     {p95_lat:.2f} ms")
    print(f"Max Latency:     {max_lat:.2f} ms")
    print("-" * 40)

    # Verification
    # Check EventStore count
    store = EventStore(project_root)
    total_events = store.store.count()
    print(f"Total Events in DB: {total_events}")

    # Cleanup
    try:
        shutil.rmtree(tmp_dir)
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(run_stress_test(num_workers=20, iterations=10))
