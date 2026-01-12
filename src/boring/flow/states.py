from dataclasses import dataclass
from enum import Enum


class FlowStage(Enum):
    SETUP = "Setup (Initialization)"
    DESIGN = "Design (Specification)"
    BUILD = "Build (Implementation)"
    POLISH = "Polish (Verification)"
    EVOLUTION = "Evolution (Learning & Dreaming)"


@dataclass
class FlowState:
    stage: FlowStage
    is_ready_for_next: bool = False
    pending_tasks: int = 0
    missing_artifacts: list[str] = None
    suggestion: str = ""
