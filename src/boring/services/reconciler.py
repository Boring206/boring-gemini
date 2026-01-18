import logging
from pathlib import Path

from boring.core.state import StateManager

logger = logging.getLogger(__name__)


class Reconciler:
    """
    The Watcher.
    Ensures consistency between persistent ProjectState and Filesystem Reality.
    """

    def __init__(self, root: Path, state_manager: StateManager):
        self.root = root
        self.sm = state_manager

    def validate_consistency(self) -> list[str]:
        """
        Check for drift and auto-correct state if needed.
        Returns a list of actions taken.
        """
        corrections = []
        state = self.sm.current

        # 1. Constitution Check
        const_path = self.root / "constitution.md"
        if state.has_constitution and not const_path.exists():
            self.sm.update(has_constitution=False)
            corrections.append("Corrected: Constitution missing -> has_constitution=False")
        elif not state.has_constitution and const_path.exists():
            self.sm.update(has_constitution=True)
            corrections.append("Corrected: Constitution found -> has_constitution=True")

        # 2. Plan Check
        plan_path = self.root / "implementation_plan.md"
        if state.has_plan and not plan_path.exists():
            self.sm.update(has_plan=False)
            corrections.append("Corrected: Plan missing -> has_plan=False")
        elif not state.has_plan and plan_path.exists():
            self.sm.update(has_plan=True)
            corrections.append("Corrected: Plan found -> has_plan=True")

        # 3. Tasks Check
        task_path = self.root / "task.md"
        if state.has_tasks and not task_path.exists():
            self.sm.update(has_tasks=False)
            corrections.append("Corrected: Tasks missing -> has_tasks=False")
        elif not state.has_tasks and task_path.exists():
            self.sm.update(has_tasks=True)
            corrections.append("Corrected: Tasks found -> has_tasks=True")

        # 4. Ledger Integrity Check
        try:
            if not self.sm.events.verify_integrity():
                logger.error("Reconciler: Event Ledger Integrity Compromised!")
                corrections.append(
                    "Integrity Check: Ledger corruption detected. Manual audit required."
                )
        except Exception as e:
            logger.warning(f"Reconciler: Failed to verify ledger: {e}")

        # 5. Stage Reconciliation (Anti-Drift)

        if corrections:
            logger.info(f"Reconciler fixes: {corrections}")

        return corrections
