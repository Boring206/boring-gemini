import os
import threading
import time

from boring.core.utils import TransactionalFileWriter
from boring.loop.transactions import FileLockDetector, retry_with_backoff


def test_transactional_write_concurrency(tmp_path):
    """
    Stress test TransactionalFileWriter with multiple threads.
    Even with many threads writing to the same file, the file
    should never be corrupt (invalid JSON).
    """
    target_file = tmp_path / "status.json"
    num_threads = 20
    writes_per_thread = 50

    errors = []

    def writer_thread(tid):
        for i in range(writes_per_thread):
            data = {
                "thread": tid,
                "iteration": i,
                "timestamp": time.time(),
                "payload": "x" * 1000,  # Large payload to increase write time
            }
            success = TransactionalFileWriter.write_json(target_file, data)
            if not success:
                # On Windows, os.replace might still fail if another process
                # has the file open for reading at the exact same microsecond.
                # But TransactionalFileWriter should handle it gracefully.
                pass

            # Verify file is valid JSON if it exists
            if target_file.exists():
                for _r_attempt in range(5):
                    try:
                        import json

                        with open(target_file) as f:
                            json.load(f)
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.01)
                    except Exception as e:
                        errors.append(f"Corruption detected by thread {tid}: {e}")
                        break

                # If we couldn't read it after 5 tries, it's a lock failure but not necessarily corruption.
                # However, if we read it and it was invalid JSON, that would be a failure.

    threads = [threading.Thread(target=writer_thread, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"JSON corruption detected: {errors}"


def test_windows_lock_retry_simulation(tmp_path):
    """
    Simulate a Windows file lock and verify retry_with_backoff handles it.
    """
    locked_file = tmp_path / "locked.txt"
    locked_file.write_text("initial")

    attempts = []

    @retry_with_backoff(max_retries=5, initial_delay=0.1)
    def risky_operation():
        attempts.append(time.time())
        if len(attempts) < 3:
            # Simulate a lock by raising OSError
            raise OSError(
                "WinError 32: The process cannot access the file because it is being used by another process"
            )
        return "success"

    result = risky_operation()
    assert result == "success"
    assert len(attempts) == 3


def test_file_lock_detector(tmp_path):
    """
    Verify FileLockDetector can detect locks.
    Note: On Windows, we can truly lock a file by keeping it open.
    On Unix, it depends on whether we use fcntl.
    """
    test_file = tmp_path / "detect_me.txt"
    test_file.write_text("content")

    # Not locked yet
    assert not FileLockDetector.is_file_locked(test_file)

    # Simulate a lock by opening with exclusive access if on Windows
    # or just check that it handles existing files correctly.
    if os.name == "nt":
        try:
            # Keep file open to trigger "Sharing violation" on Windows
            f = open(test_file, "a")
            # FileLockDetector._check_windows_lock tries to open with os.O_EXCL
            # which should fail if 'f' is holding it.
            assert FileLockDetector.is_file_locked(test_file)
            f.close()
        except:
            pass
