"""
ReasoningState - System 2 Thinking (V11.0).

This state enforces a "Slow Thinking" process for complex tasks.
It compels the agent to use 'sequentialthinking' or 'criticalthinking'
before executing any code modifcations.
"""

from typing import Optional

from rich.panel import Panel

from ...logger import console, log_status
from ..base import LoopState, StateResult
from ..context import LoopContext
from .thinking import ThinkingState


class ReasoningState(ThinkingState):
    """
    State for System 2 Reasoning.
    Inherits from ThinkingState but prompts for deep thought.
    """

    @property
    def name(self) -> str:
        return "Reasoning"

    def on_enter(self, context: LoopContext) -> None:
        """Log state entry with distinct visual."""
        context.start_state()
        log_status(context.log_dir, "INFO", "[System 2] Entering Reasoning State...")
        console.print(
            Panel(
                "[bold yellow]🧠 System 2: Deep Reasoning Active...[/bold yellow]",
                border_style="yellow",
            )
        )

    def _build_prompt(self, context: LoopContext) -> str:
        """
        Override prompt to force reasoning.
        """
        base_prompt = super()._build_prompt(context)

        # Phase 21: Brain Reflex (Active Causal Memory)
        # Check if we have seen this error before
        try:
            if context.history and context.history[-1].get("role") == "user":
                last_msg = context.history[-1].get("content", "")
                # Simple heuristc: Check if last message looks like an error
                if "Error" in last_msg or "Exception" in last_msg or "Fail" in last_msg:
                    from ...intelligence import BrainManager

                    brain = BrainManager(context.project_root)
                    patterns = brain.match_error_pattern(last_msg)

                    if patterns:
                        best = patterns[0]
                        reflex_thought = (
                            f"\n\n# 🧠 BRAIN REFLEX ACTIVATED\n"
                            f"My Causal Memory indicates I have solved a similar issue before:\n"
                            f"- **Pattern**: {best.get('description', 'Unknown')}\n"
                            f"- **Solution**: {best.get('solution', 'No solution recorded')}\n"
                            f"**You should verify if this solution applies to the current context.**\n"
                        )
                        base_prompt += reflex_thought
                        log_status(
                            context.log_dir,
                            "INFO",
                            f"[Brain Reflex] Recalled solution for pattern: {best.get('pattern_id')}",
                        )
        except Exception as e:
            log_status(context.log_dir, "WARN", f"[Brain Reflex] Failed to query brain: {e}")

        # Inject System 2 Instruction
        system_2_instruction = (
            "\n\n# 🛑 SYSTEM 2 REASONING MODE ACTIVE\n"
            "You have entered a high-complexity state. You MUST NOT write code or call external tools yet.\n"
            "You MUST use the `sequentialthinking` or `criticalthinking` tool to analyze the problem first.\n"
            "1. Plan your approach step-by-step.\n"
            "2. Consider edge cases and architectural impact.\n"
            "3. Only when you have a solid plan, set 'nextThoughtNeeded' to false.\n"
            "4. Put your final plan in the specific solution thought.\n"
        )

        return base_prompt + system_2_instruction

    def next_state(self, context: LoopContext, result: StateResult) -> Optional[LoopState]:
        """
        Determine next state.
        If tools were called (likely reasoning tools), we go to PatchingState (which executes tools).
        But wait, PatchingState calls the tool.

        The 'sequentialthinking' tool just returns text.
        So PatchingState will run it, and then what?

        We need to decide when to exit ReasoningState and go to Execution (ThinkingState).

        Strategy:
        - If 'sequentialthinking' says 'nextThoughtNeeded=True', we stay in ReasoningState (loop).
        - If 'nextThoughtNeeded=False', we transition to ThinkingState (System 1) to execute the plan.
        """
        if result == StateResult.FAILURE:
            return super().next_state(context, result)

        if context.function_calls:
            # Check if we are done thinking
            for call in context.function_calls:
                if call["name"] in ["sequentialthinking", "criticalthinking"]:
                    args = call.get("args", {})
                    # If done thinking, switch to ThinkingState (Execution)
                    if args.get("nextThoughtNeeded") is False:
                        log_status(
                            context.log_dir,
                            "INFO",
                            "[System 2] Reasoning complete. Switching to Execution.",
                        )
                        console.print("[green]🧠 Plan finalized. Switching to Action.[/green]")
                        # Transition to ThinkingState by returning None (which loops back to start?)
                        # No, we need to return the NEXT state.
                        # But LoopState doesn't allow "changing valid transitions" easily unless we wire it.

                        # In StatefulAgentLoop (agent.py), it usually cycles.
                        # If we return PatchingState, it will execute the tool (which records the thought).
                        # Then PatchingState returns... ThinkingState?
                        pass

            from .patching import PatchingState

            return PatchingState()

        return None
