#!/usr/bin/env python
"""
MCP Startup Optimization Script

This script analyzes and optimizes the MCP server startup time.
Target: < 300ms startup time.

Usage:
    python scripts/optimize_startup.py [--profile] [--benchmark N]
"""

import argparse
import cProfile
import pstats
import sys
import time
from io import StringIO


def measure_import_time(module_name: str) -> tuple[float, bool]:
    """Measure the time to import a module."""
    start = time.perf_counter()
    try:
        __import__(module_name)
        elapsed = time.perf_counter() - start
        return elapsed * 1000, True  # Convert to ms
    except ImportError:
        elapsed = time.perf_counter() - start
        return elapsed * 1000, False


def benchmark_mcp_startup(runs: int = 5) -> dict:
    """Benchmark MCP server startup time."""
    import subprocess

    results = []

    for i in range(runs):
        start = time.perf_counter()
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "from boring.mcp.server import get_server_instance; get_server_instance()",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        elapsed = (time.perf_counter() - start) * 1000

        if proc.returncode == 0:
            results.append(elapsed)
            print(f"  Run {i + 1}: {elapsed:.1f}ms")
        else:
            print(f"  Run {i + 1}: FAILED - {proc.stderr[:100]}")

    if results:
        return {
            "min": min(results),
            "max": max(results),
            "avg": sum(results) / len(results),
            "runs": len(results),
        }
    return {"error": "All runs failed"}


def profile_startup():
    """Profile the startup to find bottlenecks."""
    profiler = cProfile.Profile()

    profiler.enable()
    try:
        from boring.mcp.server import get_server_instance

        get_server_instance()
    except Exception as e:
        print(f"Error during profiling: {e}")
    profiler.disable()

    # Get stats
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(30)

    return stream.getvalue()


def analyze_imports():
    """Analyze import times for key modules."""
    modules = [
        # Core
        "boring.core.config",
        "boring.core.lazy_loader",
        # MCP
        "boring.mcp.instance",
        "boring.mcp.server",
        # Heavy dependencies
        "chromadb",
        "sentence_transformers",
        "faiss",
        "torch",
        "numpy",
        # Light dependencies
        "typer",
        "rich",
        "pydantic",
    ]

    print("\n📊 Import Time Analysis")
    print("=" * 60)

    total_time = 0
    results = []

    for module in modules:
        elapsed, success = measure_import_time(module)
        status = "✅" if success else "❌"
        results.append((module, elapsed, success))
        if success:
            total_time += elapsed
        print(f"  {status} {module}: {elapsed:.1f}ms")

    print("=" * 60)
    print(f"  Total (loaded only): {total_time:.1f}ms")

    # Identify slow imports (> 50ms)
    slow = [r for r in results if r[1] > 50 and r[2]]
    if slow:
        print("\n⚠️ Slow imports (> 50ms):")
        for module, elapsed, _ in slow:
            print(f"    - {module}: {elapsed:.1f}ms")

    return results


def generate_optimization_report(benchmark_results: dict, import_results: list):
    """Generate optimization recommendations."""
    print("\n📋 Optimization Report")
    print("=" * 60)

    target = 300  # Target startup time in ms
    current = benchmark_results.get("avg", 0)

    if current > 0:
        if current <= target:
            print(f"✅ Startup time ({current:.1f}ms) meets target ({target}ms)")
        else:
            print(f"❌ Startup time ({current:.1f}ms) exceeds target ({target}ms)")
            print(f"   Need to reduce by: {current - target:.1f}ms")

    # Recommendations based on slow imports
    slow_imports = [r for r in import_results if r[1] > 100 and r[2]]
    if slow_imports:
        print("\n🔧 Recommendations:")
        for module, elapsed, _ in slow_imports:
            print(f"   - Lazy-load '{module}' (saves ~{elapsed:.0f}ms)")

    print("\n📝 General Optimization Tips:")
    print("   1. Use TYPE_CHECKING for type-only imports")
    print("   2. Move heavy imports inside functions/methods")
    print("   3. Use boring.core.lazy_loader for optional dependencies")
    print("   4. Consider prewarm_in_background() for critical modules")
    print("   5. Profile regularly to catch regressions")


def main():
    parser = argparse.ArgumentParser(description="MCP Startup Optimization")
    parser.add_argument("--profile", action="store_true", help="Profile startup code")
    parser.add_argument("--benchmark", type=int, default=5, help="Number of benchmark runs")
    parser.add_argument("--imports-only", action="store_true", help="Only analyze imports")
    args = parser.parse_args()

    print("🚀 MCP Startup Optimization Tool")
    print("=" * 60)

    # Analyze imports
    import_results = analyze_imports()

    if args.imports_only:
        return

    # Benchmark startup
    print("\n⏱️ Benchmarking MCP Startup...")
    benchmark_results = benchmark_mcp_startup(args.benchmark)

    if "error" not in benchmark_results:
        print(
            f"\n📈 Results: min={benchmark_results['min']:.1f}ms, max={benchmark_results['max']:.1f}ms, avg={benchmark_results['avg']:.1f}ms"
        )

    # Profile if requested
    if args.profile:
        print("\n🔍 Profiling Startup...")
        profile_output = profile_startup()
        print("\nTop 30 cumulative time functions:")
        print(profile_output)

    # Generate report
    generate_optimization_report(benchmark_results, import_results)


if __name__ == "__main__":
    main()
