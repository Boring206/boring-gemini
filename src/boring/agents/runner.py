import asyncio
import logging
import os
import sys
import time
from pathlib import Path

from boring.agents.protocol import AgentResponse, AgentTask, ChatMessage
from boring.intelligence.agent_scorer import AgentScorer

logger = logging.getLogger(__name__)


class AsyncAgentRunner:
    """
    Orchestrates multiple agents concurrently via asyncio subprocesses.
    Each agent runs in its own process (using the boring CLI) to ensure isolation and GIL bypass.
    """

    def __init__(self, project_root: Path, max_concurrency: int = 3):
        self.project_root = project_root
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.scorer = AgentScorer()  # Uses default DB path

    async def execute_task(self, task: AgentTask) -> AgentResponse:
        """
        Execute a single agent task.
        """
        start_time = time.time()
        agent_id = task.agent_name  # Use agent name as ID for scoring

        async with self.semaphore:
            # Construct structured prompt with role context
            # Role is passed via:
            # 1. Environment variable BORING_AGENT_ROLE for downstream components
            # 2. Structured prompt format for the LLM
            # 3. Optional --role flag if boring CLI supports it

            role_prefix = f"""# Agent Role: {task.agent_name}

You are acting as the **{task.agent_name}** agent in a multi-agent system.
Your responsibilities are defined by your role. Execute the following task:

"""
            full_prompt = role_prefix + task.instructions

            if task.context_files:
                full_prompt += "\n\n## Context Files:\n" + "\n".join(
                    f"- {f}" for f in task.context_files
                )

            if task.tools:
                full_prompt += "\n\n## Available Tools:\n" + "\n".join(f"- {t}" for t in task.tools)

            cmd = [
                sys.executable,
                "-m",
                "boring.main",
                "run",
                full_prompt,
                "--backend",
                "cli",
                "--calls",
                "5",  # Limit iterations for sub-agents
            ]

            # Pass model override if specified
            if task.model_override:
                cmd.extend(["--model", task.model_override])

            # Environment includes role for downstream components
            env = {
                **os.environ.copy(),
                "BORING_AGENT_ROLE": task.agent_name,
                "BORING_MULTI_AGENT": "1",  # Signal multi-agent context
            }

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await process.communicate()
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            success = process.returncode == 0
            output_text = stdout.decode().strip()
            error_text = stderr.decode().strip() if not success else None

            # Record stats
            await self.scorer.record_metric(agent_id, "latency_ms", latency_ms)
            await self.scorer.record_metric(agent_id, "success", 1.0 if success else 0.0)

            # Token usage estimation (lightweight heuristic)
            try:
                from boring.core.config import settings
                from boring.metrics.token_tracker import TokenTracker

                tracker = TokenTracker(self.project_root)
                input_tokens = tracker.estimate_tokens(full_prompt)
                output_tokens = tracker.estimate_tokens(output_text)
                tracker.track_usage(settings.DEFAULT_MODEL, input_tokens, output_tokens)
            except Exception:
                pass

            response = AgentResponse(
                messages=[
                    ChatMessage(role="user", content=full_prompt),
                    ChatMessage(role="assistant", content=output_text),
                ],
                finish_reason="stop" if success else "error",
                latency_ms=latency_ms,
                error=error_text,
            )

            return response

    async def execute_parallel(self, tasks: list[AgentTask]) -> list[AgentResponse]:
        """
        Run multiple tasks in parallel.
        """
        coroutines = [self.execute_task(t) for t in tasks]
        return await asyncio.gather(*coroutines, return_exceptions=True)
