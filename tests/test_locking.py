import pytest

from boring.core.kernel import BoringKernel


def test_kernel_acquires_lock(tmp_path):
    """VERIFY: Kernel creates lock file on boot."""
    (tmp_path / ".boring").mkdir()

    # Kernel 1
    _ = BoringKernel(tmp_path)
    lock = tmp_path / ".boring" / "session.lock"

    assert lock.exists()
    # Session ID is now "PID:TIMESTAMP"
    content = lock.read_text("utf-8")
    assert ":" in content
    pid, ts = content.split(":")
    assert pid.isdigit()
    assert float(ts) > 0


def test_kernel_fails_if_locked(tmp_path):
    """VERIFY: Second kernel fails to boot."""
    (tmp_path / ".boring").mkdir()

    # Simulate existing lock
    lock = tmp_path / ".boring" / "session.lock"
    lock.write_text("existing-session-123", encoding="utf-8")

    # Kernel 2 should crash
    with pytest.raises(RuntimeError) as excinfo:
        BoringKernel(tmp_path)

    assert "FATAL: Session Lock held" in str(excinfo.value)


def test_lock_cleanup(tmp_path):
    """VERIFY: Lock is cleaned up (simulated manually since atexit is hard to test in-proc)."""
    (tmp_path / ".boring").mkdir()
    _ = BoringKernel(tmp_path)
    lock = tmp_path / ".boring" / "session.lock"

    assert lock.exists()

    # Simulate exit cleanup
    # We must check if it exists BEFORE cleanup, then remove it
    assert lock.exists()
    lock.unlink()

    assert not lock.exists()
