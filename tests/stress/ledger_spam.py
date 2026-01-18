import time
from pathlib import Path

from boring.core.config import settings
from boring.core.events import EventStore


def run_bench(name: str, async_mode: bool, count: int = 1000):
    print(f"--- Benchmarking {name} (Async={async_mode}, Count={count}) ---")

    # Use a separate temp root for clean bench
    temp_root = Path("./.bench_temp")
    if temp_root.exists():
        import shutil

        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True)

    # Force settings
    settings.PROJECT_ROOT = temp_root

    store = EventStore(temp_root, async_mode=async_mode)

    start_time = time.perf_counter()

    for i in range(count):
        store.append(
            event_type="StressEvent", payload={"i": i, "data": "x" * 100}, session_id="bench"
        )

    # If async, we must wait for completion to measure total durability time
    if async_mode:
        store.flush()

    duration = time.perf_counter() - start_time
    rps = count / duration if duration > 0 else 0

    print(f"Completed {count} events in {duration:.4f}s")
    print(f"Throughput: {rps:.2f} RPS")

    # Verify count in DB
    final_count = store.store.count()
    print(f"Final DB Count: {final_count}")

    store.close()
    return rps


if __name__ == "__main__":
    count = 1000
    # Warmup
    run_bench("Warmup", False, 100)

    sync_rps = run_bench("Sync Mode", False, count)
    async_rps = run_bench("Async Mode", True, count)

    speedup = async_rps / sync_rps if sync_rps > 0 else 0
    print(f"\nSpeedup: {speedup:.2f}x")
