import logging
from pathlib import Path

from .states import FlowStage, FlowState

logger = logging.getLogger(__name__)


class FlowDetector:
    """detects the current stage of the project based on artifacts."""

    def __init__(self, project_root: Path):
        self.root = project_root

    def detect(self) -> FlowState:
        """Analyze project state and return the current flow state."""

        # 1. Check for Constitution (Setup Phase)
        constitution = self.root / "constitution.md"
        if not constitution.exists():
            return FlowState(
                stage=FlowStage.SETUP,
                suggestion="我發現這個專案還沒有「憲法」 (Constitution)。讓我們先定義好遊戲規則。",
                missing_artifacts=["constitution.md"],
            )

        # 2. Check for Plan (Design Phase)
        plan = self.root / "implementation_plan.md"
        if not plan.exists():
            return FlowState(
                stage=FlowStage.DESIGN,
                suggestion="憲法已建立。現在我們需要一個「實作計畫」 (Implementation Plan)。你想做什麼？",
                missing_artifacts=["implementation_plan.md"],
            )

        # 3. Check for Tasks (Build Phase)
        task_list = self.root / "task.md"
        if not task_list.exists():
            # Plan exists but tasks don't? Rare, but implies we need to break it down.
            return FlowState(
                stage=FlowStage.DESIGN,
                suggestion="有計畫但沒有任務清單。讓我幫您拆解任務。",
                missing_artifacts=["task.md"],
            )

        # Analyze Task Status
        pending_tasks = self._count_pending_tasks(task_list)
        if pending_tasks > 0:
            return FlowState(
                stage=FlowStage.BUILD,
                pending_tasks=pending_tasks,
                suggestion=f"檢測到 {pending_tasks} 個待辦任務。讓我們開始構建 (Build)。",
                is_ready_for_next=True,
            )

        # 4. All Tasks Done (Polish Phase)
        # Check if we have run vibe check recently (simulate check)
        return FlowState(
            stage=FlowStage.POLISH,
            suggestion="所有任務已完成！現在進入驗收與打磨階段 (Polish)。",
            is_ready_for_next=True,
        )

    def _count_pending_tasks(self, task_file: Path) -> int:
        """Count unchecked boxes in task.md"""
        if not task_file.exists():
            return 0

        try:
            content = task_file.read_text(encoding="utf-8")
            # Count "- [ ]" or "- [ ]" (ignoring x)
            return content.count("- [ ]")
        except Exception as e:
            logger.warning(f"Failed to read task file: {e}")
            return 0
