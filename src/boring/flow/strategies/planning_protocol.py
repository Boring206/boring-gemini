from typing import Protocol, runtime_checkable

from boring.flow.nodes.base import FlowContext


@runtime_checkable
class PlanningStrategy(Protocol):
    """
    Strategy protocol for the Architect's planning logic.
    Follows Dependency Inversion Principle (DIP).
    """

    async def create_plan(self, context: FlowContext) -> str:
        """
        Generate a high-level implementation plan (implementation_plan.md).
        Returns the content of the plan.
        Raises PlanningError on failure.
        """
        ...

    async def create_tasks(self, plan_content: str, context: FlowContext) -> str:
        """
        Break down the plan into specific tasks (task.md).
        Returns the content of the task list.
        Raises PlanningError on failure.
        """
        ...


class PlanningError(Exception):
    """Base exception for planning failures."""

    pass
