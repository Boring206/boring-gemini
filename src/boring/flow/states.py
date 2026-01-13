from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FlowStage(Enum):
    SETUP = "Setup (Initialization)"
    DESIGN = "Design (Specification)"
    BUILD = "Build (Implementation)"
    POLISH = "Polish (Verification)"
    EVOLUTION = "Evolution (Learning & Dreaming)"


# Progress percentage for each stage (for visualization)
STAGE_PROGRESS = {
    FlowStage.SETUP: 10,
    FlowStage.DESIGN: 30,
    FlowStage.BUILD: 60,
    FlowStage.POLISH: 85,
    FlowStage.EVOLUTION: 100,
}


# Skill suggestions for each stage
STAGE_SKILL_MAPPING = {
    FlowStage.SETUP: None,
    FlowStage.DESIGN: "Architect",
    FlowStage.BUILD: "Healer",
    FlowStage.POLISH: "Watcher",
    FlowStage.EVOLUTION: "Sage",
}


def get_progress_bar(percent: int, width: int = 10) -> str:
    """Generate a visual progress bar."""
    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {percent}%"


@dataclass
class FlowState:
    stage: FlowStage
    is_ready_for_next: bool = False
    pending_tasks: int = 0
    missing_artifacts: list[str] = field(default_factory=list)
    suggestion: str = ""

    @property
    def progress_percent(self) -> int:
        """Get the progress percentage for the current stage."""
        return STAGE_PROGRESS.get(self.stage, 0)

    @property
    def progress_bar(self) -> str:
        """Get a visual progress bar for the current stage."""
        return get_progress_bar(self.progress_percent)

    @property
    def suggested_skill(self) -> Optional[str]:
        """Get the suggested skill role for the current stage."""
        return STAGE_SKILL_MAPPING.get(self.stage)
