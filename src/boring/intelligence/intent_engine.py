"""
Intent Engine for Boring-Gemini V14.0

Translates natural language user requests into actionable Boring commands.
Part of the "Zero-Prompt Implementation" strategy.
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BoringIntent:
    """Represents a recognized user intent mapped to a CLI command."""

    command: str
    confidence: float
    args: list[str] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    original_input: str = ""


class IntentEngine:
    """
    Intelligent Intent Recognition Engine.

    Strategies:
    1. Exact Keyword Match (Fastest)
    2. Fuzzy Pattern Match (Fast)
    3. LLM Inference (Smartest - Future Implementation)
    """

    def __init__(self):
        self.cmd_patterns = {
            "predict": [
                r"predict",
                r"scan",
                r"check errors?",
                r"analysis",
                r"detect risks?",
                r"future errors?",
            ],
            "fix": [r"fix", r"repair", r"heal", r"correct", r"solve", r"debug"],
            "flow": [r"start", r"go", r"begin", r"flow", r"run project", r"work on"],
            "dashboard": [r"dashboard", r"monitor", r"gui", r"ui", r"visualize", r"status"],
            "diagnose": [r"diagnose", r"doctor", r"health", r"checkup", r"system check"],
            "learn": [r"learn", r"remember", r"digest", r"knowledge"],
        }

    def infer_intent(self, user_input: str) -> BoringIntent | None:
        """
        Infer the intent from a natural language string.
        """
        user_input = user_input.strip()
        lower_input = user_input.lower()

        # 1. Exact/Prefix Match for existing CLI commands
        clean_input = re.sub(r"^boring\s+", "", lower_input)

        # 2. Pattern Matching
        best_intent = None
        highest_conf = 0.0

        for cmd, patterns in self.cmd_patterns.items():
            for pattern in patterns:
                # Check for whole word matches
                if re.search(r"\b" + pattern + r"\b", clean_input):
                    # Simple scoring: length of match / length of input (bonus for exact)
                    score = 0.8
                    if clean_input == pattern:
                        score = 1.0

                    if score > highest_conf:
                        highest_conf = score
                        best_intent = BoringIntent(
                            command=cmd,
                            confidence=score,
                            reasoning=f"Matched pattern: {pattern}",
                            original_input=user_input,
                        )

        # 3. Argument Extraction (Heuristic)
        if best_intent:
            self._enrich_arguments(best_intent, clean_input)
            return best_intent

        # 4. LLM Fallback (Smart Path)
        return self._infer_with_llm(user_input)

    def _enrich_arguments(self, intent: BoringIntent, clean_input: str):
        """Extract arguments based on command type."""
        # Simple extraction for now
        if intent.command == "predict":
            if "security" in clean_input:
                intent.kwargs["security"] = True
            if "diff" in clean_input:
                intent.kwargs["diff"] = True

        elif intent.command == "fix":
            # Extract possible file paths (simple heuristic)
            words = clean_input.split()
            for w in words:
                if "." in w and "/" in w or w.endswith(".py") or w.endswith(".md"):
                    intent.args.append(w)

    def _infer_with_llm(self, user_input: str) -> BoringIntent | None:
        """Use Local LLM to infer intent if heuristics fail."""
        try:
            from boring.llm.local_llm import LocalLLM

            llm = LocalLLM.from_settings()

            if not llm.is_available:
                return None

            prompt = f"""
                        You are the Intent Classifier for the 'boring' CLI tool.
                        Map the user request to one of these commands: {list(self.cmd_patterns.keys())}.
                        User Request: "{user_input}"
                        Return ONLY the command name (lowercase). If unsure, return "unknown".
                        """
            response = llm.complete(prompt, max_tokens=10, temperature=0.1)
            if not response:
                return None

            cmd = response.strip().lower()

            # Remove any extra punctuation
            cmd = re.sub(r"[^a-z]", "", cmd)

            if cmd in self.cmd_patterns:
                return BoringIntent(
                    command=cmd,
                    confidence=0.6,  # Lower confidence for LLM guess without validation
                    reasoning="LLM inference",
                    original_input=user_input,
                )

        except Exception:
            return None

        return None
