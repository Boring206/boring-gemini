"""
Cognitive Reasoning Engine (System 2) for Boring-Gemini

This module implements the "System 2" slow thinking capability.
It enables the agent to:
1. Decompose complex goals into steps (Planning)
2. Execute steps sequentially (Acting)
3. Observe results and update memory (Observing)
4. Reflect on progress and adjust plans (Reflecting)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from boring.intelligence.context_manager import ContextManager
from boring.llm.local_llm import LocalLLM

logger = logging.getLogger(__name__)

StepStatus = Literal["pending", "active", "completed", "failed", "skipped"]


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""

    id: int
    description: str
    status: StepStatus = "pending"
    reasoning: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    observation: str = ""
    reflection: str = ""


@dataclass
class ReasoningTrace:
    """The full trace of a reasoning session."""

    goal: str
    steps: list[ReasoningStep] = field(default_factory=list)
    current_step_index: int = 0
    final_answer: str | None = None


class ReasoningEngine:
    """
    System 2 Reasoning Engine.
    Implements the ReAct (Reason+Act) or similar cognitive loops.
    """

    def __init__(self, context_manager: ContextManager | None = None):
        self.ctx_mgr = context_manager or ContextManager()
        self.llm = LocalLLM.from_settings()
        self.max_steps = 10

    def think(self, goal: str) -> ReasoningTrace:
        """
        Start a cognitive thinking process for a complex goal.
        """
        trace = ReasoningTrace(goal=goal)

        # 1. Initial Planning (Decomposition)
        initial_plan = self._generate_plan(goal)
        trace.steps = initial_plan

        logger.info(f"Reasoning Engine started for goal: {goal}")
        logger.info(f"Initial Plan: {len(initial_plan)} steps")

        return trace

    def step(self, trace: ReasoningTrace) -> ReasoningTrace:
        """
        Execute one step of the reasoning loop.
        """
        if trace.current_step_index >= len(trace.steps):
            return trace

        current_step = trace.steps[trace.current_step_index]
        current_step.status = "active"

        # 1. Reflect & Refine (Before Action)
        # Check context, decide specific tool calls

        # 2. Act (Execute Tool - Simulation for now)
        # In a real loop, this would call Main Loop or specific Tools

        # 3. Observe
        # Capture output

        # 4. Update
        current_step.status = "completed"
        trace.current_step_index += 1

        return trace

    def _generate_plan(self, goal: str) -> list[ReasoningStep]:
        """
        Use LLM to decompose goal into steps.
        """
        if not self.llm.is_available:
            # Fallback heuristic plan
            return [
                ReasoningStep(id=1, description=f"Analyze requirements for: {goal}"),
                ReasoningStep(id=2, description="Implement changes"),
                ReasoningStep(id=3, description="Verify solution"),
            ]

        prompt = f"""
        Goal: {goal}
        Context: {self.ctx_mgr.get_context_summary()}
        Decompose this goal into 3-5 high-level logical steps for an AI developer.
        Format: 1. [Step Description]
        """

        response = self.llm.complete(prompt, max_tokens=256)
        steps = []
        if response:
            lines = response.strip().split("\n")
            for i, line in enumerate(lines):
                clean_line = line.strip().lstrip("0123456789.- ").strip()
                if clean_line:
                    steps.append(ReasoningStep(id=i + 1, description=clean_line))

        if not steps:
            return [ReasoningStep(id=1, description=goal)]

        return steps
