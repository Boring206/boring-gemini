import logging
import os
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import psutil, but don't fail if missing
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_process_start_time(pid: int) -> float:
    """
    Get the creation time of a process in a cross-platform way.
    Returns 0.0 if process definitely doesn't exist.
    Returns -1.0 if process exists but we can't query it (Access Denied).
    """
    # 1. Preferred: psutil (Cross-platform, Robust)
    if HAS_PSUTIL:
        try:
            p = psutil.Process(pid)
            return p.create_time()
        except psutil.NoSuchProcess:
            return 0.0
        except (psutil.AccessDenied, psutil.ZombieProcess):
            return -1.0

    # 2. Windows Fallback: ctypes
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            ACCESS_RIGHTS = 0x1000

            handle = kernel32.OpenProcess(ACCESS_RIGHTS, False, pid)
            if not handle:
                # OpenProcess failed. Check if it's because it doesn't exist.
                error = kernel32.GetLastError()
                if error == 5:  # ERROR_ACCESS_DENIED
                    return -1.0
                return 0.0

            creation_time = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel_time = wintypes.FILETIME()
            user_time = wintypes.FILETIME()

            res = kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation_time),
                ctypes.byref(exit_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time),
            )
            kernel32.CloseHandle(handle)

            if res:
                qword = (creation_time.dwHighDateTime << 32) + creation_time.dwLowDateTime
                return qword / 10000000.0
            return 0.0
        except Exception:
            return 0.0

    # 3. Linux/Unix Fallback: /proc
    else:
        try:
            stat_path = Path(f"/proc/{pid}/stat")
            if stat_path.exists():
                content = stat_path.read_text().split()
                if len(content) > 21:
                    return float(content[21])
            return 0.0
        except PermissionError:
            return -1.0
        except Exception:
            return 0.0


class RobustLock:
    """
    A robust file-based lock that prevents:
    1. Deadlocks from crashed processes (Zombie detection)
    2. Locked-out states from PID reuse (Creation Time verification)

    Format of lock file: "<PID>:<START_TIME_TIMESTAMP>"
    """

    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self.held = False
        # Cached identity of this process
        self._pid = os.getpid()
        self._start_time = get_process_start_time(self._pid)

    def acquire(self, timeout: float = 10.0) -> bool:
        """
        Attempt to acquire the lock.
        Automatically cleans up dead locks.
        """
        start = time.time()

        while True:
            # 1. Try atomic create
            if self._atomic_create():
                self.held = True
                return True

            # 2. Check if existing lock is valid
            if not self._is_lock_valid():
                # Invalid/Dead lock detected. Break it.
                logger.warning(f"Breaking zombie lock: {self.lock_file}")
                self._break_lock()
                # Retry loop immediately to grab it
                continue

            # 3. Wait
            if timeout >= 0 and (time.time() - start) > timeout:
                return False

            time.sleep(0.1)

    def release(self):
        """Release the lock if we hold it."""
        if not self.held:
            return

        try:
            # Double check we still own it (paranoia) before deleting
            # This handles edge case where we might have lost it?
            # Actually, if we assume we are the only ones deleting OUR lock, direct unlink is safe.
            # But let's verify content just to be super safe against fs races.
            if self._is_owned_by_me():
                self.lock_file.unlink(missing_ok=True)
                self.held = False
        except Exception as e:
            logger.warning(f"Error releasing lock {self.lock_file}: {e}")

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock {self.lock_file}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def _atomic_create(self) -> bool:
        """Try to create lock file atomically with O_EXCL."""
        try:
            fd = os.open(str(self.lock_file), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(f"{self._pid}:{self._start_time}")
            return True
        except OSError:
            return False

    def _break_lock(self):
        """Force delete the lock file."""
        try:
            self.lock_file.unlink(missing_ok=True)
        except OSError:
            pass

    def _is_owned_by_me(self) -> bool:
        """Verify the lock file on disk points to us."""
        try:
            content = self.lock_file.read_text(encoding="utf-8").strip()
            return content == f"{self._pid}:{self._start_time}"
        except Exception:
            return False

    def _is_lock_valid(self) -> bool:
        """
        Check if the lock file exists and points to a living process.
        Returns False if lock is zombie, empty, corrupted, or process is dead.
        Returns True if process is definitely alive.
        """
        if not self.lock_file.exists():
            # Does not exist -> ready to be taken (so effectively not valid as a block)
            # Logic inversion: This method returns True if it IS blocking us.
            # If it doesn't exist, it's NOT valid as a lock => return False?
            # Wait, calling logic is: `if not _is_lock_valid(): break_lock()`
            # If file is gone, `break_lock` does `unlink(missing_ok=True)` which is fine.
            # So returning False is correct behavior for "Constraint is gone".
            return False

        try:
            content = self.lock_file.read_text(encoding="utf-8").strip()
            if not content:
                return False  # Empty file is invalid

            # Parse PID:TIME
            parts = content.split(":")
            if len(parts) >= 2:
                # New Format (PID:TIME:...) - Forward Compatible
                pid = int(parts[0])
                lock_time = float(parts[1])

                # Check if this process is running AND has matching start time
                current_start_time = get_process_start_time(pid)

                if current_start_time == -1.0:
                    # Process exists but we can't read details (Access Denied).
                    # This happens if lock is held by a more privileged user.
                    # In this case, we MUST assume the lock is valid (blocking).
                    return True

                if current_start_time == 0.0:
                    # Process definitely dead (or unqueryable in a way we treat as dead).
                    return False

                # Allow small slush in time (e.g. 1 second) in case of rounding diffs
                if abs(current_start_time - lock_time) > 1.0:
                    # PID exists but Time is different -> PID Reuse -> Zombie Lock
                    return False

                return True

            elif len(parts) == 1:
                # Backward Compatibility (PID only)
                pid = int(parts[0])
                # Weak Check: Just check if PID exists
                if HAS_PSUTIL:
                    return psutil.pid_exists(pid)
                elif sys.platform == "win32":
                    # ctypes check from old implementation, embedded here
                    import ctypes

                    kernel32 = ctypes.windll.kernel32
                    PROCESS_QUERY_INFORMATION = 0x0400
                    SYNCHRONIZE = 0x00100000
                    handle = kernel32.OpenProcess(
                        SYNCHRONIZE | PROCESS_QUERY_INFORMATION, False, pid
                    )
                    if not handle:
                        return False
                    exit_code = ctypes.c_ulong()
                    kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                    kernel32.CloseHandle(handle)
                    return exit_code.value == 259  # STILL_ACTIVE
                else:
                    # Unix signal 0
                    try:
                        os.kill(pid, 0)
                        return True
                    except OSError:
                        return False

            return False  # Unknown format -> Invalid

        except (ValueError, OSError, IndexError):
            # Read failed or parsing failed -> Invalid
            return False


# Legacy Aliases
PIDLock = RobustLock


class SimpleFileLock(RobustLock):
    """
    Backward compatible wrapper.
    Legacy SimpleFileLock added ".lock" suffix.
    We maintain that behavior but use RobustLock logic.
    """

    def __init__(self, target_file: Path):
        super().__init__(Path(str(target_file) + ".lock"))
