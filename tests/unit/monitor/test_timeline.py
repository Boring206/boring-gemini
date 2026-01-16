"""
Tests for TimelineViewer.
"""

from typing import Any
from unittest.mock import patch

from boring.monitor.timeline import TimelineViewer


class MockAuditLogger:
    def __init__(self, root):
        pass

    def get_logs(self, limit=20) -> list[dict[str, Any]]:
        return [
            {
                "timestamp": "2025-01-01T12:00:00",
                "event_type": "TEST",
                "action": "CREATE",
                "resource": "file.txt",
                "actor": "agent",
                "details": {},
            }
        ]


def test_render_timeline(tmp_path, capsys):
    with patch("boring.monitor.timeline.AuditLogger", MockAuditLogger):
        viewer = TimelineViewer(tmp_path)
        viewer.render()

        capsys.readouterr()
        # Rich console usually prints to stdout/stderr depending on config.
        # But here we didn't inject console.
        # We just want to ensure no crash in this unit test mostly.
        # Ideally we'd capture console output, but that's harder with global console.
        pass
