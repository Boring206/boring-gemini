import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class BehaviorEvent:
    event_type: str  # 'command_run', 'override', 'abort', 'stickiness'
    command: str | None = None
    details: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BehaviorLogger:
    """
    Silent Shadow Logger for tracking team adoption metrics.
    Logs are stored locally in .boring/behavior.log
    """

    def __init__(self, project_root: Path):
        self.log_path = project_root / ".boring" / "behavior.jsonl"
        self.project_root = project_root

    def log(self, event_type: str, command: str | None = None, **details):
        if not self.log_path.parent.exists():
            return  # Don't log if not an active Boring project

        event = BehaviorEvent(event_type=event_type, command=command, details=details)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event)) + "\n")
        except Exception:
            pass  # Silent failure for telemetry

    def track_override(self, file_path: Path, ai_content: str, user_content: str):
        """Measures the Delta between AI suggestion and User correction."""
        if ai_content == user_content:
            return

        # Simplistic 'Authority Conflict' metric: % of lines changed by user
        ai_lines = ai_content.splitlines()
        user_lines = user_content.splitlines()

        # Log the conflict severity
        self.log(
            "authority_conflict",
            details={
                "file": str(file_path.name),
                "ai_len": len(ai_lines),
                "user_len": len(user_lines),
                "conflict_type": "manual_override",
            },
        )

    def get_metrics(self):
        """Aggregates log data into adoption indicators."""
        if not self.log_path.exists():
            return {"usage_count": 0, "status": "no_data"}

        events = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                events.append(json.loads(line))

        return {
            "total_commands": len([e for e in events if e["event_type"] == "command_run"]),
            "conflicts_detected": len(
                [e for e in events if e["event_type"] == "authority_conflict"]
            ),
            "aborts": len([e for e in events if e["event_type"] == "abort"]),
            "last_active": events[-1]["timestamp"] if events else None,
        }
