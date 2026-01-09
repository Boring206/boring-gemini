"""
Core LLMJudge Implementation - Advanced Evaluation V10.25

Enhanced with:
- Confidence calibration based on position consistency and evidence
- Length-normalized scoring
- BiasMonitor integration for tracking evaluation history
- Panel of LLMs support (multi-model voting)
"""

import logging
import traceback
import uuid
from pathlib import Path
from typing import Any, Optional

from ..llm.provider import LLMProvider
from ..quality_tracker import QualityTracker
from .parsers import extract_json
from .prompts import build_code_comparison_prompt, build_comparison_prompt, build_grade_prompt
from .rubrics import CODE_QUALITY_RUBRIC, Rubric

logger = logging.getLogger(__name__)


class LLMJudge:
    """
    LLM-as-a-Judge implementation for evaluating code and plans.

    V10.25 Enhancements:
    - Confidence calibration based on position consistency
    - Length-normalized scoring to mitigate length bias
    - BiasMonitor integration for systematic bias tracking
    """

    def __init__(
        self,
        provider: LLMProvider,
        quality_tracker: Optional[QualityTracker] = None,
        project_root: Optional[Path] = None,
        enable_bias_tracking: bool = True,
    ):
        self.cli = (
            provider  # Renaming this would ripple too much, keeping name but typing is generalized
        )
        self.tracker = quality_tracker  # Optional: for automatic history recording
        self.project_root = project_root
        self._bias_monitor = None

        # Initialize bias monitor if enabled and project root provided
        if enable_bias_tracking and project_root:
            try:
                from .bias_monitor import get_bias_monitor

                self._bias_monitor = get_bias_monitor(project_root)
            except ImportError:
                logger.debug("BiasMonitor not available, skipping bias tracking")

    def grade_code(
        self,
        filename: str,
        content: str,
        rubric: Rubric = CODE_QUALITY_RUBRIC,
        interactive: bool = False,
    ) -> dict[str, Any]:
        """
        Evaluate code quality against a rubric.
        If interactive=True, returns the PROMPT for the user to execute using their IDE AI.
        Else, executes via CLI adapter.
        """
        prompt = build_grade_prompt(filename, content, rubric, str(type(self.cli)))

        if interactive:
            # Return the prompts for the host AI (Cursor) to run
            return {
                "score": 0,
                "status": "pending_manual_review",
                "reasoning": "Delegated to Host AI",
                "prompt": prompt,
            }

        try:
            # Call LLM provider
            response = self.cli.chat(prompt, interactive=False)

            # Extract and parse JSON
            result = extract_json(response)
            if result:
                # Record score to quality tracker if available
                if self.tracker and "score" in result:
                    self.tracker.record(result.get("score", 0), 0, context="judge")
                return result
            else:
                logger.warning("No JSON found in judge response")
                return {"score": 0, "reasoning": "Failed to parse judge response", "raw": response}

        except Exception as e:
            logger.error(f"Judge failed: {e}")
            print(f"\n[DEBUG] Judge Exception: {e}")  # Explicit print
            traceback.print_exc()
            return {"score": 0, "reasoning": str(e)}

    def compare_plans(
        self, plan_a: str, plan_b: str, context: str, interactive: bool = False
    ) -> dict[str, Any]:
        """
        Compare two implementation plans and pick a winner.

        Implements Pairwise Comparison with Position Bias Mitigation.
        """
        if interactive:
            # Return both prompts for manual execution
            return {
                "status": "pending_manual_review",
                "prompts": {
                    "pass1": build_comparison_prompt(plan_a, plan_b, "A", "B", context),
                    "pass2": build_comparison_prompt(plan_b, plan_a, "B", "A", context),
                },
                "instructions": "Execute both prompts and compare results. If winners match, that's the final winner. If they differ, the result is TIE.",
            }

        try:
            # First pass: A in position 1, B in position 2
            prompt_pass1 = build_comparison_prompt(plan_a, plan_b, "A", "B", context)
            response_pass1 = self.cli.chat(prompt_pass1, interactive=False)
            result_pass1 = extract_json(response_pass1)

            if not result_pass1:
                return {
                    "winner": "TIE",
                    "confidence": 0.0,
                    "error": "Failed to parse first pass response",
                }

            # Second pass: B in position 1, A in position 2
            prompt_pass2 = build_comparison_prompt(plan_b, plan_a, "B", "A", context)
            response_pass2 = self.cli.chat(prompt_pass2, interactive=False)
            result_pass2 = extract_json(response_pass2)

            if not result_pass2:
                return {
                    "winner": "TIE",
                    "confidence": 0.0,
                    "error": "Failed to parse second pass response",
                }

            # Extract winners (normalize to A/B/TIE)
            winner_pass1 = result_pass1.get("winner", "TIE").upper()
            winner_pass2 = result_pass2.get("winner", "TIE").upper()

            conf_pass1 = float(result_pass1.get("confidence", 0.5))
            conf_pass2 = float(result_pass2.get("confidence", 0.5))

            # Position Bias Mitigation: Check consistency
            consistent = winner_pass1 == winner_pass2

            if consistent:
                final_winner = winner_pass1
                final_confidence = (conf_pass1 + conf_pass2) / 2
            else:
                final_winner = "TIE"
                final_confidence = 0.5

            return {
                "winner": final_winner,
                "confidence": round(final_confidence, 2),
                "positionConsistency": {
                    "consistent": consistent,
                    "pass1": {"winner": winner_pass1, "confidence": conf_pass1},
                    "pass2": {"winner": winner_pass2, "confidence": conf_pass2},
                },
                "reasoning": result_pass1.get("overall_reasoning", "")
                if consistent
                else "Position bias detected - inconsistent results across passes",
            }

        except Exception as e:
            logger.error(f"Plan comparison failed: {e}")
            return {"winner": "TIE", "confidence": 0.0, "error": str(e)}

    def compare_code(
        self,
        name_a: str,
        code_a: str,
        name_b: str,
        code_b: str,
        context: Optional[str] = None,
        interactive: bool = False,
    ) -> dict[str, Any]:
        """
        Compare two code implementations (A/B Test).
        """
        if interactive:
            return {
                "status": "pending_manual_review",
                "prompts": {
                    "pass1": build_code_comparison_prompt(code_a, code_b, "A", "B", context),
                    "pass2": build_code_comparison_prompt(code_b, code_a, "B", "A", context),
                },
                "instructions": "Execute both prompts. If they agree on the winner (swapping A/B), that is the result.",
            }

        try:
            # First pass: A vs B
            prompt_pass1 = build_code_comparison_prompt(code_a, code_b, "A", "B", context)
            response_pass1 = self.cli.chat(prompt_pass1, interactive=False)
            result_pass1 = extract_json(response_pass1)

            if not result_pass1:
                return {"winner": "TIE", "confidence": 0.0, "error": "Failed to parse first pass"}

            # Second pass: B vs A (Position Bias Check)
            prompt_pass2 = build_code_comparison_prompt(code_b, code_a, "B", "A", context)
            response_pass2 = self.cli.chat(prompt_pass2, interactive=False)
            result_pass2 = extract_json(response_pass2)

            if not result_pass2:
                return {"winner": "TIE", "confidence": 0.0, "error": "Failed to parse second pass"}

            winner_pass1 = result_pass1.get("winner", "TIE").upper()
            winner_pass2 = result_pass2.get("winner", "TIE").upper()

            consistent = winner_pass1 == winner_pass2

            if consistent:
                final_winner = winner_pass1
                final_conf = (
                    float(result_pass1.get("confidence", 0.5))
                    + float(result_pass2.get("confidence", 0.5))
                ) / 2
            else:
                final_winner = "TIE"
                final_conf = 0.5

            return {
                "winner": final_winner,
                "confidence": round(final_conf, 2),
                "positionConsistency": consistent,
                "reasoning": result_pass1.get("overall_reasoning", ""),
            }

        except Exception as e:
            logger.error(f"Code comparison failed: {e}")
            return {"winner": "TIE", "confidence": 0.0, "error": str(e)}

    def _extract_json(self, response: str) -> Optional[dict[str, Any]]:
        """Deprecated: Internal wrapper for backward compatibility within class."""
        return extract_json(response)

    def _build_grade_prompt(self, filename: str, content: str, rubric: Rubric) -> str:
        """Compatibility wrapper for build_grade_prompt."""
        return build_grade_prompt(filename, content, rubric, str(type(self.cli)))

    # =========================================================================
    # V10.25: Advanced Evaluation Methods
    # =========================================================================

    def calibrate_confidence(
        self,
        raw_confidence: float,
        position_consistent: bool,
        evidence_count: int = 0,
    ) -> float:
        """
        Calibrate confidence based on multiple signals.

        Args:
            raw_confidence: Raw confidence from model output (0-1)
            position_consistent: Whether position swap passes agreed
            evidence_count: Number of evidence items supporting the judgment

        Returns:
            Calibrated confidence score (0-1)
        """
        calibrated = raw_confidence

        # Position consistency is a strong signal
        if not position_consistent:
            calibrated *= 0.6  # Significant reduction for inconsistency

        # More evidence = higher confidence
        evidence_factor = min(evidence_count / 3, 1.0)  # Cap at 3 pieces
        calibrated *= 0.7 + 0.3 * evidence_factor

        return min(calibrated, 0.99)  # Never 100% confident

    def length_normalized_score(
        self,
        score: float,
        response_length: int,
        target_length: int = 500,
        max_penalty: float = 0.5,
    ) -> float:
        """
        Adjust score based on response length to mitigate length bias.

        Args:
            score: Original score
            response_length: Length of the response (characters)
            target_length: Expected typical length
            max_penalty: Maximum penalty to apply

        Returns:
            Length-adjusted score
        """
        length_ratio = response_length / target_length if target_length > 0 else 1.0

        if length_ratio > 2.0:
            # Penalize excessively long responses
            penalty = min((length_ratio - 2.0) * 0.1, max_penalty)
            return max(score - penalty, 1.0)
        elif length_ratio < 0.3:
            # Penalize excessively short responses
            penalty = min((0.3 - length_ratio) * 0.5, max_penalty)
            return max(score - penalty, 1.0)
        else:
            return score

    def get_bias_report(self, days: int = 30) -> Optional[dict]:
        """
        Get bias monitoring report.

        Args:
            days: Number of days to analyze

        Returns:
            Bias report dict or None if monitoring not available
        """
        if self._bias_monitor is None:
            return None

        try:
            from .bias_monitor import format_bias_report

            report = self._bias_monitor.get_bias_report(days)
            return {
                "formatted": format_bias_report(report),
                "position_bias": {
                    "detected": report.position_bias.bias_detected
                    if report.position_bias
                    else False,
                    "first_position_win_rate": report.position_bias.first_position_win_rate
                    if report.position_bias
                    else 0,
                },
                "length_bias": {
                    "detected": report.length_bias.bias_detected if report.length_bias else False,
                    "correlation": report.length_bias.correlation if report.length_bias else 0,
                },
                "warnings": report.warnings,
                "recommendations": report.recommendations,
            }
        except Exception as e:
            logger.error(f"Failed to get bias report: {e}")
            return None

    def _record_evaluation(
        self,
        evaluation_type: str,
        result: dict,
        response_length: int = 0,
    ):
        """Record evaluation to bias monitor."""
        if self._bias_monitor is None:
            return

        try:
            eval_id = str(uuid.uuid4())[:8]

            if evaluation_type == "pairwise":
                self._bias_monitor.record_pairwise_evaluation(
                    evaluation_id=eval_id,
                    winner=result.get("winner", "TIE"),
                    first_position="A",  # A is always first in our implementation
                    position_consistent=result.get("positionConsistency", False),
                    confidence=result.get("confidence", 0.0),
                )
            elif evaluation_type == "direct":
                self._bias_monitor.record_direct_evaluation(
                    evaluation_id=eval_id,
                    score=result.get("score", 0),
                    response_length=response_length,
                    dimension_scores=result.get("dimensions"),
                )
        except Exception as e:
            logger.debug(f"Failed to record evaluation: {e}")
