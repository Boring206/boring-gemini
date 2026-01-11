
from unittest.mock import patch

from boring.mcp.tools.session import (
    boring_session_auto,
    boring_session_confirm,
    boring_session_load,
    boring_session_pause,
    boring_session_start,
    boring_session_status,
)


class TestSessionTools:
    """Tests for Vibe Session MCP Tools."""

    def test_boring_session_start_success(self, tmp_path):
        with patch("boring.mcp.tools.session.detect_project_root", return_value=tmp_path):
            with patch("boring.mcp.tools.session.check_rate_limit", return_value=(True, "")):
                result = boring_session_start(goal="Test goal", project_path=str(tmp_path))
                assert "Vibe Session 已啟動" in result
                assert "Phase 1" in result

                # Verify file created
                session_dir = tmp_path / ".boring_memory" / "sessions"
                assert session_dir.exists()
                assert len(list(session_dir.glob("*.json"))) == 1

    def test_boring_session_status_no_session(self, tmp_path):
        with patch("boring.mcp.tools.session.detect_project_root", return_value=tmp_path):
            with patch("boring.mcp.tools.session.check_rate_limit", return_value=(True, "")):
                result = boring_session_status(project_path=str(tmp_path))
                assert "沒有任何 Session 記錄" in result

    def test_boring_session_flow(self, tmp_path):
        with patch("boring.mcp.tools.session.detect_project_root", return_value=tmp_path):
            with patch("boring.mcp.tools.session.check_rate_limit", return_value=(True, "")):
                # 1. Start
                boring_session_start(goal="Flow test", project_path=str(tmp_path))

                # 2. Status
                status = boring_session_status(project_path=str(tmp_path))
                assert "當前階段: ALIGNMENT" in status

                # 3. Confirm (Alignment -> Planning)
                confirm_res = boring_session_confirm(notes="Some notes", project_path=str(tmp_path))
                assert "Phase 2" in confirm_res

                status_after = boring_session_status(project_path=str(tmp_path))
                assert "當前階段: PLANNING" in status_after

    def test_boring_session_pause_resume(self, tmp_path):
        with patch("boring.mcp.tools.session.detect_project_root", return_value=tmp_path):
            with patch("boring.mcp.tools.session.check_rate_limit", return_value=(True, "")):
                start_res = boring_session_start(goal="Pause test", project_path=str(tmp_path))
                # Extract session ID from the output string using a simple heuristic
                # **Session ID**: `20240101_120000`
                session_id = start_res.split("`")[1]

                boring_session_pause(project_path=str(tmp_path))

                status = boring_session_status(project_path=str(tmp_path))
                assert "當前階段: PAUSED" in status

                # Reset simulation and load
                from boring.mcp.tools.session import _session_managers
                _session_managers.clear()

                load_res = boring_session_load(session_id=session_id, project_path=str(tmp_path))
                assert "Session 已載入" in load_res

                status_after = boring_session_status(project_path=str(tmp_path))
                assert "當前階段: PAUSED" in status_after

    def test_boring_session_auto_toggle(self, tmp_path):
        with patch("boring.mcp.tools.session.detect_project_root", return_value=tmp_path):
            with patch("boring.mcp.tools.session.check_rate_limit", return_value=(True, "")):
                boring_session_start(goal="Auto test", project_path=str(tmp_path))

                auto_res = boring_session_auto(enable=True, project_path=str(tmp_path))
                assert "自動模式已啟用" in auto_res

                status = boring_session_status(project_path=str(tmp_path))
                assert "自動模式: 開啟" in status

                manual_res = boring_session_auto(enable=False, project_path=str(tmp_path))
                assert "手動模式已啟用" in manual_res
