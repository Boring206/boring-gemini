"""
Tests for dashboard and interactive modules.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from boring.dashboard import (
        Dashboard,
        DashboardState,
        LoopMetrics,
        create_dashboard,
    )
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

from boring.interactive import (
    InteractiveSession,
    InteractiveAction,
)

pytestmark = pytest.mark.skipif(not HAS_STREAMLIT, reason="Streamlit not installed")


from boring.interactive import (
    InteractiveSession,
    InteractiveAction,
)


class TestDashboardState:
    """Tests for DashboardState."""

    def test_initial_state(self):
        """Test initial dashboard state."""
        state = DashboardState()
        
        assert state.total_loops == 0
        assert state.successful_loops == 0
        assert state.failed_loops == 0
        assert state.current_status == "IDLE"

    def test_add_log(self):
        """Test adding log messages."""
        state = DashboardState()
        
        state.add_log("Test message 1")
        state.add_log("Test message 2")
        
        assert len(state.recent_logs) == 2
        assert "Test message 1" in state.recent_logs[0]

    def test_add_log_truncates(self):
        """Test that logs are truncated to last 10."""
        state = DashboardState()
        
        for i in range(15):
            state.add_log(f"Message {i}")
        
        assert len(state.recent_logs) == 10
        assert "Message 14" in state.recent_logs[-1]


class TestLoopMetrics:
    """Tests for LoopMetrics."""

    def test_create_metrics(self):
        """Test creating loop metrics."""
        metrics = LoopMetrics(
            loop_id=1,
            status="RUNNING",
            start_time=1000.0
        )
        
        assert metrics.loop_id == 1
        assert metrics.status == "RUNNING"
        assert metrics.files_modified == []
        assert metrics.errors == []


class TestDashboard:
    """Tests for Dashboard class."""

    def test_create_dashboard(self, tmp_path):
        """Test creating a dashboard instance."""
        dashboard = create_dashboard(project_root=tmp_path)
        
        assert dashboard is not None
        assert dashboard.state is not None

    def test_update_loop_running(self, tmp_path):
        """Test updating loop to RUNNING."""
        dashboard = Dashboard(project_root=tmp_path)
        
        dashboard.update_loop(1, "RUNNING")
        
        assert dashboard.state.current_loop is not None
        assert dashboard.state.current_loop.loop_id == 1
        assert dashboard.state.current_status == "RUNNING"

    def test_update_loop_success(self, tmp_path):
        """Test updating loop to SUCCESS."""
        dashboard = Dashboard(project_root=tmp_path)
        
        dashboard.update_loop(1, "RUNNING")
        dashboard.update_loop(1, "SUCCESS")
        
        assert dashboard.state.total_loops == 1
        assert dashboard.state.successful_loops == 1
        assert dashboard.state.current_status == "IDLE"

    def test_update_loop_failed(self, tmp_path):
        """Test updating loop to FAILED."""
        dashboard = Dashboard(project_root=tmp_path)
        
        dashboard.update_loop(1, "RUNNING")
        dashboard.update_loop(1, "FAILED")
        
        assert dashboard.state.total_loops == 1
        assert dashboard.state.failed_loops == 1

    def test_update_tokens(self, tmp_path):
        """Test updating token count."""
        dashboard = Dashboard(project_root=tmp_path)
        
        dashboard.update_tokens(100)
        dashboard.update_tokens(50)
        
        assert dashboard.state.total_tokens == 150

    def test_add_file_modified(self, tmp_path):
        """Test recording modified files."""
        dashboard = Dashboard(project_root=tmp_path)
        dashboard.update_loop(1, "RUNNING")
        
        dashboard.add_file_modified("src/main.py")
        
        assert "src/main.py" in dashboard.state.current_loop.files_modified


class TestInteractiveAction:
    """Tests for InteractiveAction enum."""

    def test_action_values(self):
        """Test action enum values."""
        assert InteractiveAction.RESUME.value == "resume"
        assert InteractiveAction.ABORT.value == "abort"
        assert InteractiveAction.EDIT_PROMPT.value == "edit_prompt"


class TestInteractiveSession:
    """Tests for InteractiveSession class."""

    def test_create_session(self, tmp_path):
        """Test creating an interactive session."""
        session = InteractiveSession(
            reason="Test reason",
            project_root=tmp_path
        )
        
        assert session.reason == "Test reason"
        assert session.project_root == tmp_path

    def test_session_with_errors(self, tmp_path):
        """Test session with recent errors."""
        errors = ["Error 1", "Error 2"]
        session = InteractiveSession(
            project_root=tmp_path,
            recent_errors=errors
        )
        
        assert session.recent_errors == errors
