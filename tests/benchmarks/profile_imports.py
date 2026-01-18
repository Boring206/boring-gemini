import sys
import time
from pathlib import Path


def profile_imports(modules):
    results = {}
    for mod in modules:
        t0 = time.perf_counter()
        try:
            # We use __import__ to dynamically import
            __import__(mod)
            t1 = time.perf_counter()
            results[mod] = (t1 - t0) * 1000
        except ImportError:
            results[mod] = -1
    return results


if __name__ == "__main__":
    heavy_modules = [
        "google.genai",
        "chromadb",
        "tensorflow",
        "typer",
        "pydantic",
        "pydantic_settings",
        "boring.core.config",
        "boring.core.kernel",
    ]

    # We might need to add src to sys.path
    project_root = Path(__file__).resolve().parents[2]
    src_path = str(project_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    print(f"Profiling module imports (Root: {project_root})...")
    times = profile_imports(heavy_modules)

    sorted_times = sorted(times.items(), key=lambda x: x[1], reverse=True)

    print("\nImport times (ms):")
    for mod, duration in sorted_times:
        status = f"{duration:.2f}ms" if duration >= 0 else "FAILED"
        print(f"  {mod:30}: {status}")
