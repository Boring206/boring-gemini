import statistics
import subprocess
import time

from rich.console import Console

console = Console()


def benchmark_command(cmd_list, iterations=5):
    console.print(f"Benchmarking: [cyan]{' '.join(cmd_list)}[/cyan]")
    times = []

    # Warmup
    subprocess.run(cmd_list, capture_output=True)

    for i in range(iterations):
        start = time.perf_counter()
        subprocess.run(cmd_list, capture_output=True)
        end = time.perf_counter()
        duration = (end - start) * 1000  # ms
        times.append(duration)
        console.print(f"  Run {i + 1}: {duration:.2f} ms")

    avg = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)

    console.print("\n[bold]Results:[/bold]")
    console.print(f"  Average: [green]{avg:.2f} ms[/green]")
    console.print(f"  Min:     {min_time:.2f} ms")
    console.print(f"  Max:     {max_time:.2f} ms")

    TARGET = 500
    if avg < TARGET:
        console.print(f"\n[bold green]✅ PASS: Startup is fast (<{TARGET}ms)[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠️ WARNING: Startup is slow (>{TARGET}ms)[/bold yellow]")


if __name__ == "__main__":
    # Test CLI startup (version check is usually fastest)
    benchmark_command(["boring", "version"], iterations=10)

    # Test MCP Server instantiation (import cost)
    console.print("\nBenchmarking Import Cost...")
    py_cmd = "import time; t0=time.perf_counter(); from boring.mcp.server import get_server_instance; print((time.perf_counter()-t0)*1000)"
    benchmark_command(["python", "-c", py_cmd], iterations=5)
