from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Try to import FastAPI/TestClient, but don't fail if missing (skip instead)
try:
    from fastapi.testclient import TestClient

    from boring.services.web_monitor import (
        FASTAPI_AVAILABLE,
        create_monitor_app,
    )
except ImportError:
    TestClient = None
    FASTAPI_AVAILABLE = False

    def create_monitor_app(project_root: Path):
        return None


@pytest.fixture
def monitor_app(tmp_path):
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")

    # Setup mock files
    brain_dir = tmp_path / ".boring_brain"
    brain_dir.mkdir()
    (brain_dir / "learned_patterns").mkdir()

    memory_dir = tmp_path / ".boring_memory"
    memory_dir.mkdir()

    app = create_monitor_app(tmp_path)
    if app is None:
        pytest.skip("FastAPI available but app creation failed (likely missing uvicorn)")
    return app


@pytest.fixture
def client(monitor_app):
    if not monitor_app or TestClient is None:
        pytest.skip("Could not create client")
    return TestClient(monitor_app)


class TestWebMonitor:
    def test_dashboard_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Boring Monitor" in response.text

    def test_api_status_from_file(self, client, tmp_path):
        # Path 1: loop_status.json exists
        (tmp_path / ".boring_memory" / "loop_status.json").write_text(
            '{"state": "running", "extra": "data"}', encoding="utf-8"
        )

        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "running"
        assert data["extra"] == "data"

    def test_api_status_fallback(self, client, tmp_path):
        # Path 2: loop_status.json does NOT exist
        (tmp_path / ".circuit_breaker_state").write_text('{"state": "OPEN"}', encoding="utf-8")
        (tmp_path / ".call_count").write_text("99", encoding="utf-8")

        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["circuit_state"] == "OPEN"
        assert data["call_count"] == 99
        assert "project" in data

    def test_api_stats(self, client, tmp_path):
        # Setup patterns
        p_file = tmp_path / ".boring_brain" / "learned_patterns" / "patterns.json"
        p_file.write_text('[{"id": "p1"}, {"id": "p2"}]', encoding="utf-8")

        # Setup pending
        (tmp_path / ".boring_memory" / "pending_ops.json").write_text(
            "[{}, {}, {}]", encoding="utf-8"
        )

        # Setup RAG
        (tmp_path / ".boring_memory" / "rag_db").mkdir()
        (tmp_path / ".boring_memory" / "rag_db" / "index.bin").touch()

        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["patterns_count"] == 2
        assert data["pending_approvals"] == 3
        assert data["rag_indexed"] is True

    def test_api_logs(self, client, tmp_path):
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()
        (logs_dir / "test.log").write_text("line1\nline2\nline3", encoding="utf-8")

        response = client.get("/api/logs?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 2
        assert data["logs"] == ["line2", "line3"]

    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_missing_fastapi(self):
        # Simulate missing dependencies
        from boring.services.web_monitor import create_monitor_app as actual_create

        with patch("boring.services.web_monitor.FASTAPI_AVAILABLE", False):
            app = actual_create(Path("/tmp"))
            assert app is None

    def test_run_server(self, tmp_path):
        # Mock uvicorn and create_monitor_app to avoid actual server start and class calls
        with patch("boring.services.web_monitor.uvicorn") as mock_uvicorn:
            with patch("boring.services.web_monitor.create_monitor_app") as mock_create:
                mock_create.return_value = MagicMock()  # Mock app
                with patch("boring.services.web_monitor.FASTAPI_AVAILABLE", True):
                    from boring.services.web_monitor import run_web_monitor

                    run_web_monitor(tmp_path, port=9999)
                    assert mock_uvicorn.run.called
