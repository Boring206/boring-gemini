import json
from datetime import datetime
from pathlib import Path


class ProjectBio:
    """
    Autonomous Knowledge Continuity Engine (Phase VII).
    Synthesizes project history into a 'Biography'.
    """

    def __init__(self, project_root: Path):
        self.root = project_root
        self.behavior_log = project_root / ".boring" / "behavior.jsonl"

    def synthesize(self) -> str:
        """Generates the project story."""
        if not self.behavior_log.exists():
            return "No biography available. This project is in its infancy."

        events = []
        with open(self.behavior_log, encoding="utf-8") as f:
            for line in f:
                events.append(json.loads(line))

        # Analysis
        total_days = (
            (datetime.now() - datetime.fromisoformat(events[0]["timestamp"])).days if events else 0
        )
        conflicts = [e for e in events if e["event_type"] == "authority_conflict"]
        self_learning = [e for e in events if e["event_type"] == "adaptive_learning"]

        bio = [
            "# 📖 Project Biography",
            f"\nThis project has been active for **{total_days + 1} days**.",
            "\n### 🛠️ Execution History",
            f"- Boring-Gemini has provided **{len(events)}** autonomous assistances.",
            f"- **{len(conflicts)}** authority corrections were made by Senior Engineers.",
            f"- The system successfully **learned and adapted** from {len(self_learning)} conflicts.",
        ]

        if self_learning:
            bio.append("\n### 🧠 Evolutionary Note")
            bio.append(
                "The project has pivoted from initial assumptions based on human intervention, leading to a more stable 'Team-Matched' reasoning state."
            )

        return "\n".join(bio)
