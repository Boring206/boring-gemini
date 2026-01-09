import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Adjust path to find src
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src"))

from boring.mcp.tools.shadow import ShadowModeLevel
from boring.tools.file_patcher import _write_file


def test_shadow_enforcement():
    print("=== Testing Shadow Mode Enforcement in file_patcher ===")

    project_root / "test_shadow_blocked.txt"
    log_dir = project_root / "logs"
    if not log_dir.exists():
        log_dir.mkdir()

    # 1. Test STRICT Mode (Should Block)
    print("\n[TEST 1] Testing STRICT Mode (Expect Block)...")
    with patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_get_guard:
        # Mock the guard to return a pending operation (simulating block)
        mock_guard_instance = MagicMock()
        mock_guard_instance.mode = ShadowModeLevel.STRICT
        # check_operation returns a PendingOperation object if blocked, None if allowed
        # Let's verify what check_operation actually returns in the real code
        # In real code: pending = guard.check_operation(...)
        # if pending: -> blocked

        # Simulating a blocked operation
        mock_op = MagicMock()
        mock_op.operation_id = "test-op-123"
        mock_guard_instance.check_operation.return_value = mock_op
        mock_guard_instance.request_approval.return_value = False  # Auto-approve failed

        mock_get_guard.return_value = mock_guard_instance

        success, action, msg = _write_file(
            file_path="test_shadow_blocked.txt",
            content="This should be blocked",
            project_root=project_root,
            log_dir=log_dir,
        )

        if not success and "Blocked by Shadow Mode" in msg:
            print("✅ PASSED: Operation was correctly blocked.")
            print(f"Message: {msg}")
        else:
            print("❌ FAILED: Operation was NOT blocked or message incorrect.")
            print(f"Success: {success}, Message: {msg}")

    # 2. Test DISABLED Mode (Should Allow)
    print("\n[TEST 2] Testing DISABLED Mode (Expect Success)...")
    with patch("boring.mcp.tools.shadow.get_shadow_guard") as mock_get_guard:
        # Mock the guard to return None (allowed)
        mock_guard_instance = MagicMock()
        mock_guard_instance.mode = ShadowModeLevel.DISABLED
        mock_guard_instance.check_operation.return_value = None

        mock_get_guard.return_value = mock_guard_instance

        success, action, msg = _write_file(
            file_path="test_shadow_allowed.txt",
            content="This should be allowed",
            project_root=project_root,
            log_dir=log_dir,
        )

        # Clean up
        allowed_file = project_root / "test_shadow_allowed.txt"
        if allowed_file.exists():
            allowed_file.unlink()

        if success:
            print("✅ PASSED: Operation was allowed.")
        else:
            print(f"❌ FAILED: Operation was blocked or failed. {msg}")


if __name__ == "__main__":
    test_shadow_enforcement()
