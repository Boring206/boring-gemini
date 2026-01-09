"""
Rate Limiter Module for Boring V4.0

Provides rate limiting and call tracking functionality.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .logger import console, log_status


def init_call_tracking(call_count_file: Path, timestamp_file: Path, exit_signals_file: Path):
    """
    Initializes call counter and exit signals tracking.

    Args:
        call_count_file: File to track API call count
        timestamp_file: File to track last reset timestamp
        exit_signals_file: File to track exit signals
    """
    current_hour = datetime.now().strftime("%Y%m%d%H")
    last_reset_hour = None

    if timestamp_file.exists():
        last_reset_hour = timestamp_file.read_text().strip()

    if current_hour != last_reset_hour:
        call_count_file.write_text("0")
        timestamp_file.write_text(current_hour)
        log_status(Path("logs"), "INFO", f"Call counter reset for new hour: {current_hour}")

    if not exit_signals_file.exists():
        exit_signals_file.write_text(
            json.dumps(
                {"test_only_loops": [], "done_signals": [], "completion_indicators": []}, indent=4
            )
        )


def get_calls_made(call_count_file: Path) -> int:
    """
    Reads the current number of API calls made this hour.

    Args:
        call_count_file: Path to call count file

    Returns:
        Number of calls made
    """
    if call_count_file.exists():
        try:
            return int(call_count_file.read_text().strip())
        except ValueError:
            return 0
    return 0


def increment_call_counter(call_count_file: Path) -> int:
    """
    Increments the API call counter.

    Args:
        call_count_file: Path to call count file

    Returns:
        New call count
    """
    calls_made = get_calls_made(call_count_file) + 1
    call_count_file.write_text(str(calls_made))
    return calls_made


def can_make_call(call_count_file: Path, max_calls_per_hour: int) -> bool:
    """
    Checks if another API call can be made within the rate limit.

    Args:
        call_count_file: Path to call count file
        max_calls_per_hour: Maximum allowed calls per hour

    Returns:
        True if call can be made
    """
    return get_calls_made(call_count_file) < max_calls_per_hour


def wait_for_reset(call_count_file: Path, timestamp_file: Path, max_calls_per_hour: int):
    """
    Waits for the rate limit to reset with a countdown.

    Args:
        call_count_file: Path to call count file
        timestamp_file: Path to timestamp file
        max_calls_per_hour: Maximum allowed calls per hour
    """
    calls_made = get_calls_made(call_count_file)
    log_status(
        Path("logs"),
        "WARN",
        f"Rate limit reached ({calls_made}/{max_calls_per_hour}). Waiting for reset...",
    )

    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    wait_seconds = int((next_hour - now).total_seconds())

    console.print(f"[blue]Sleeping for {wait_seconds} seconds until next hour...[/blue]")

    with console.status("[bold green]Waiting for rate limit reset...[/bold green]") as status:
        while wait_seconds > 0:
            hours, remainder = divmod(wait_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            status.update(
                f"[yellow]Time until reset: {hours:02d}:{minutes:02d}:{seconds:02d}[/yellow]"
            )
            time.sleep(1)
            wait_seconds -= 1

    init_call_tracking(call_count_file, timestamp_file, Path(".exit_signals"))
    log_status(Path("logs"), "SUCCESS", "Rate limit reset! Ready for new calls.")


# --- Exit Detection Logic ---

MAX_CONSECUTIVE_TEST_LOOPS = 3
MAX_CONSECUTIVE_DONE_SIGNALS = 2


def should_exit_gracefully(exit_signals_file: Path) -> Optional[str]:
    """
    Determines if the loop should exit gracefully based on signals.

    Args:
        exit_signals_file: Path to exit signals file

    Returns:
        Exit reason string or None if no exit condition met
    """
    if not exit_signals_file.exists():
        return None

    signals_data = json.loads(exit_signals_file.read_text())

    test_only_loops = signals_data.get("test_only_loops", [])
    done_signals = signals_data.get("done_signals", [])
    completion_indicators = signals_data.get("completion_indicators", [])

    if len(test_only_loops) >= MAX_CONSECUTIVE_TEST_LOOPS:
        log_status(
            Path("logs"),
            "WARN",
            f"Exit condition: Too many test-focused loops ({len(test_only_loops)} >= {MAX_CONSECUTIVE_TEST_LOOPS})",
        )
        return "test_saturation"

    if len(done_signals) >= MAX_CONSECUTIVE_DONE_SIGNALS:
        log_status(
            Path("logs"),
            "WARN",
            f"Exit condition: Multiple completion signals ({len(done_signals)} >= {MAX_CONSECUTIVE_DONE_SIGNALS})",
        )
        return "completion_signals"

    if len(completion_indicators) >= 2:
        log_status(
            Path("logs"),
            "WARN",
            f"Exit condition: Strong completion indicators ({len(completion_indicators)})",
        )
        return "project_complete"

    # Check @fix_plan.md for completion
    fix_plan_file = Path("@fix_plan.md")
    if fix_plan_file.exists():
        content = fix_plan_file.read_text()
        total_items = content.count("- [ ]") + content.count("- [x]")
        completed_items = content.count("- [x]")

        if total_items > 0 and completed_items == total_items:
            log_status(
                Path("logs"),
                "WARN",
                f"Exit condition: All fix_plan.md items completed ({completed_items}/{total_items})",
            )
            return "plan_complete"

    return None
