import logging

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from boring.flow.nodes.base import FlowContext
from boring.flow.strategies.planning_protocol import PlanningError

logger = logging.getLogger(__name__)


class SpeckitPlanningStrategy:
    """
    Default implementation using Boring Speckit Tools (LLM-based).
    Features: Exponential Backoff Retries for Resilience.
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(PlanningError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def create_plan(self, context: FlowContext) -> str:
        try:
            from boring.mcp.speckit_tools import boring_speckit_plan

            # Identify goal
            goal = context.user_goal
            root = str(context.project_root)

            plan_result = await boring_speckit_plan(context=goal, project_path=root)

            if not plan_result or (
                isinstance(plan_result, dict) and plan_result.get("status") == "ERROR"
            ):
                msg = (
                    plan_result.get("error", "Empty result")
                    if isinstance(plan_result, dict)
                    else "Empty result"
                )
                # If it's a known non-transient error (e.g. auth), we might not want to retry?
                # For now, treat all planning failures as retryable for maximal resilience
                raise PlanningError(f"Speckit Plan Failed: {msg}")

            return str(
                plan_result.get("workflow", "") if isinstance(plan_result, dict) else plan_result
            )

        except ImportError:
            raise  # Don't retry missing deps
        except PlanningError:
            raise  # Retryable via decorator
        except Exception as e:
            raise PlanningError(f"Unexpected Planning Error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(PlanningError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def create_tasks(self, plan_content: str, context: FlowContext) -> str:
        try:
            from boring.mcp.speckit_tools import boring_speckit_tasks

            root = str(context.project_root)

            task_result = await boring_speckit_tasks(context=plan_content, project_path=root)

            if not task_result or (
                isinstance(task_result, dict) and task_result.get("status") == "ERROR"
            ):
                msg = (
                    task_result.get("error", "Empty result")
                    if isinstance(task_result, dict)
                    else "Empty result"
                )
                raise PlanningError(f"Speckit Task Gen Failed: {msg}")

            return str(
                task_result.get("workflow", "") if isinstance(task_result, dict) else task_result
            )

        except ImportError:
            raise  # Don't retry missing deps
        except PlanningError:
            raise  # Retryable via decorator
        except Exception as e:
            raise PlanningError(f"Unexpected Task Gen Error: {e}")
