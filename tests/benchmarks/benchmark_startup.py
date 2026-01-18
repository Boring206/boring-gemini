import sys
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))


def benchmark_startup():
    print(f"Benchmarking Startup (Root: {project_root})...")

    t0 = time.time()
    # 1. Import Overhead
    from boring.core.context import BoringContext
    from boring.core.kernel import BoringKernel

    t1 = time.time()
    import_time = (t1 - t0) * 1000
    print(f"Import Time: {import_time:.2f}ms")

    # 2. Context Creation
    t2 = time.time()
    ctx = BoringContext.from_root(project_root)
    ctx.activate()
    t3 = time.time()
    ctx_time = (t3 - t2) * 1000
    print(f"Context Activate Time: {ctx_time:.2f}ms")

    # 3. Kernel Boot (includes Locking & State Hydration)
    t4 = time.time()
    try:
        kernel = BoringKernel(ctx)
        # Release lock immediately for test
        if hasattr(kernel, "_lock"):
            kernel._lock.release()
    except Exception as e:
        print(f"Kernel Boot Failed: {e}")
        return

    t5 = time.time()
    boot_time = (t5 - t4) * 1000
    print(f"Kernel Boot Time: {boot_time:.2f}ms")

    total_time = (t5 - t0) * 1000
    print(f"Total Startup Time: {total_time:.2f}ms")

    if total_time < 200:
        print("✅ PASS: Startup < 200ms")
    else:
        print("⚠️ WARN: Startup > 200ms")


if __name__ == "__main__":
    benchmark_startup()
