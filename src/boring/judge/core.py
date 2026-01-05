"""
Core LLMJudge Implementation
"""

import json
import logging
from typing import Dict, Any, List, Optional
import traceback

from .prompts import build_grade_prompt, build_comparison_prompt, build_code_comparison_prompt
from .parsers import extract_json
from ..rubrics import Rubric, CODE_QUALITY_RUBRIC
from ..llm.provider import LLMProvider
from ..quality_tracker import QualityTracker

logger = logging.getLogger(__name__)

class LLMJudge:
    """
    LLM-as-a-Judge implementation for evaluating code and plans.
    """
    
    def __init__(self, provider: LLMProvider, quality_tracker: Optional[QualityTracker] = None):
        self.cli = provider  # Renaming this would ripple too much, keeping name but typing is generalized
        self.tracker = quality_tracker  # Optional: for automatic history recording

    def grade_code(self, filename: str, content: str, rubric: Rubric = CODE_QUALITY_RUBRIC, interactive: bool = False) -> Dict[str, Any]:
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
                "prompt": prompt
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
            print(f"\n[DEBUG] Judge Exception: {e}") # Explicit print
            traceback.print_exc()
            return {"score": 0, "reasoning": str(e)}

    def compare_plans(self, plan_a: str, plan_b: str, context: str, interactive: bool = False) -> Dict[str, Any]:
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
                    "pass2": build_comparison_prompt(plan_b, plan_a, "B", "A", context)
                },
                "instructions": "Execute both prompts and compare results. If winners match, that's the final winner. If they differ, the result is TIE."
            }
        
        try:
            # First pass: A in position 1, B in position 2
            prompt_pass1 = build_comparison_prompt(plan_a, plan_b, "A", "B", context)
            response_pass1 = self.cli.chat(prompt_pass1, interactive=False)
            result_pass1 = extract_json(response_pass1)
            
            if not result_pass1:
                return {"winner": "TIE", "confidence": 0.0, "error": "Failed to parse first pass response"}
            
            # Second pass: B in position 1, A in position 2
            prompt_pass2 = build_comparison_prompt(plan_b, plan_a, "B", "A", context)
            response_pass2 = self.cli.chat(prompt_pass2, interactive=False)
            result_pass2 = extract_json(response_pass2)
            
            if not result_pass2:
                return {"winner": "TIE", "confidence": 0.0, "error": "Failed to parse second pass response"}
            
            # Extract winners (normalize to A/B/TIE)
            winner_pass1 = result_pass1.get("winner", "TIE").upper()
            winner_pass2 = result_pass2.get("winner", "TIE").upper()
            
            conf_pass1 = float(result_pass1.get("confidence", 0.5))
            conf_pass2 = float(result_pass2.get("confidence", 0.5))
            
            # Position Bias Mitigation: Check consistency
            consistent = (winner_pass1 == winner_pass2)
            
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
                    "pass2": {"winner": winner_pass2, "confidence": conf_pass2}
                },
                "reasoning": result_pass1.get("overall_reasoning", "") if consistent else "Position bias detected - inconsistent results across passes"
            }
            
        except Exception as e:
            logger.error(f"Plan comparison failed: {e}")
            return {"winner": "TIE", "confidence": 0.0, "error": str(e)}

    def compare_code(self, name_a: str, code_a: str, name_b: str, code_b: str, context: Optional[str] = None, interactive: bool = False) -> Dict[str, Any]:
        """
        Compare two code implementations (A/B Test).
        """
        if interactive:
            return {
                "status": "pending_manual_review",
                "prompts": {
                    "pass1": build_code_comparison_prompt(code_a, code_b, "A", "B", context),
                    "pass2": build_code_comparison_prompt(code_b, code_a, "B", "A", context)
                },
                "instructions": "Execute both prompts. If they agree on the winner (swapping A/B), that is the result."
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
            
            consistent = (winner_pass1 == winner_pass2)
            
            if consistent:
                final_winner = winner_pass1
                final_conf = (float(result_pass1.get("confidence", 0.5)) + float(result_pass2.get("confidence", 0.5))) / 2
            else:
                final_winner = "TIE"
                final_conf = 0.5
                
            return {
                "winner": final_winner,
                "confidence": round(final_conf, 2),
                "positionConsistency": consistent,
                "reasoning": result_pass1.get("overall_reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Code comparison failed: {e}")
            return {"winner": "TIE", "confidence": 0.0, "error": str(e)}

    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Deprecated: Internal wrapper for backward compatibility within class."""
        return extract_json(response)

    def _build_grade_prompt(self, filename: str, content: str, rubric: Rubric) -> str:
        """Compatibility wrapper for build_grade_prompt."""
        return build_grade_prompt(filename, content, rubric, str(type(self.cli)))
